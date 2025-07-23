# gce/plugins/gce_scanner/gce_scanner.py

import os
import json
import logging
import time
import socket
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
import threading

import pika
from pika.exceptions import AMQPConnectionError, AMQPChannelError, ConnectionClosedByBroker
import requests
from gvm.connections import UnixSocketConnection
from gvm.protocols.gmp import Gmp
from gvm.transforms import EtreeTransform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RabbitMQConnection:
    """Gestisce le connessioni RabbitMQ con reconnection automatica e heartbeat robusto"""
    
    def __init__(self, host: str, port: int, queue_name: str, heartbeat: int = 60):
        self.host = host
        self.port = port
        self.queue_name = queue_name
        self.heartbeat = heartbeat
        self.connection = None
        self.channel = None
        self._lock = threading.Lock()
        self._last_activity = time.time()
        self._reconnect_delay = 5
        self._max_reconnect_delay = 300
        
    def connect(self) -> bool:
        """Stabilisce la connessione con retry logic"""
        retry_count = 0
        current_delay = self._reconnect_delay
        
        while True:
            try:
                logger.info(f"Attempting to connect to RabbitMQ at {self.host}:{self.port} (attempt {retry_count + 1})")
                
                connection_params = pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    heartbeat=self.heartbeat,
                    blocked_connection_timeout=300,
                    connection_attempts=3,
                    retry_delay=2
                )
                
                self.connection = pika.BlockingConnection(connection_params)
                self.channel = self.connection.channel()
                
                # Declare queue with durability
                self.channel.queue_declare(
                    queue=self.queue_name,
                    durable=True,
                    arguments={
                        'x-message-ttl': 3600000,  # 1 hour TTL
                        'x-max-length': 10000
                    }
                )
                
                logger.info(f"Connected to RabbitMQ successfully with heartbeat={self.heartbeat}s")
                self._last_activity = time.time()
                return True
                
            except Exception as e:
                retry_count += 1
                logger.error(f"Failed to connect to RabbitMQ: {e}")
                
                if retry_count >= 10:
                    logger.error("Max reconnection attempts reached")
                    raise
                
                logger.info(f"Retrying in {current_delay} seconds...")
                time.sleep(current_delay)
                current_delay = min(current_delay * 2, self._max_reconnect_delay)
    
    def ensure_connection(self) -> bool:
        """Verifica e ripristina la connessione se necessario"""
        with self._lock:
            try:
                if self.connection and not self.connection.is_closed:
                    # Send heartbeat frame
                    self.connection.process_data_events(time_limit=0)
                    self._last_activity = time.time()
                    return True
                else:
                    logger.warning("Connection lost, attempting to reconnect...")
                    return self.connect()
            except Exception as e:
                logger.error(f"Connection check failed: {e}")
                return self.connect()
    
    def publish(self, message: Dict[str, Any], max_retries: int = 3) -> bool:
        """Pubblica un messaggio con retry logic"""
        for attempt in range(max_retries):
            try:
                if not self.ensure_connection():
                    continue
                
                self.channel.basic_publish(
                    exchange='',
                    routing_key=self.queue_name,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Make message persistent
                        expiration='3600000'  # 1 hour expiration
                    )
                )
                
                logger.info(f"Published message to queue {self.queue_name}")
                self._last_activity = time.time()
                return True
                
            except Exception as e:
                logger.error(f"Failed to publish message (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        return False
    
    def consume(self, callback, auto_ack: bool = False):
        """Consuma messaggi con reconnection automatica"""
        while True:
            try:
                if not self.ensure_connection():
                    time.sleep(5)
                    continue
                
                # Set QoS
                self.channel.basic_qos(prefetch_count=1)
                
                # Start consuming
                for method, properties, body in self.channel.consume(
                    queue=self.queue_name,
                    auto_ack=auto_ack
                ):
                    try:
                        self._last_activity = time.time()
                        message = json.loads(body.decode('utf-8'))
                        
                        # Process message
                        callback(self.channel, method, properties, message)
                        
                        if not auto_ack:
                            self.channel.basic_ack(delivery_tag=method.delivery_tag)
                            
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
                        if not auto_ack:
                            self.channel.basic_nack(
                                delivery_tag=method.delivery_tag,
                                requeue=True
                            )
                        
            except (AMQPConnectionError, AMQPChannelError, ConnectionClosedByBroker) as e:
                logger.error(f"Connection error during consume: {e}")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error during consume: {e}")
                time.sleep(5)
    
    def close(self):
        """Chiude la connessione in modo pulito"""
        with self._lock:
            try:
                if self.channel and not self.channel.is_closed:
                    self.channel.close()
                if self.connection and not self.connection.is_closed:
                    self.connection.close()
                logger.info("RabbitMQ connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")


class GCEScanner:
    def __init__(self):
        # Configuration from environment
        self.api_gateway_url = os.environ.get('INTERNAL_API_GATEWAY_URL', 'http://api_gateway:5000')
        self.gce_socket = os.environ.get('GCE_SOCKET_PATH', '/mnt/gce_sockets/gvmd.sock')
        self.gce_username = os.environ.get('GCE_USERNAME', 'vapter_api')
        self.gce_password = os.environ.get('GCE_PASSWORD', 'vapter_api')
        
        # RabbitMQ configuration
        self.rabbitmq_host = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
        self.rabbitmq_port = int(os.environ.get('RABBITMQ_PORT', '5672'))
        
        # Initialize connections
        self.consumer_connection = RabbitMQConnection(
            self.rabbitmq_host,
            self.rabbitmq_port,
            os.environ.get('RABBITMQ_GCE_SCAN_REQUEST_QUEUE', 'gce_scan_requests'),
            heartbeat=60
        )
        
        self.publisher_connection = RabbitMQConnection(
            self.rabbitmq_host,
            self.rabbitmq_port,
            os.environ.get('RABBITMQ_SCAN_STATUS_UPDATE_QUEUE', 'scan_status_updates'),
            heartbeat=60
        )
        
        # GCE configuration
        self.scan_config_id = os.environ.get('GCE_SCAN_CONFIG_ID', 'daba56c8-73ec-11df-a475-002264764cea')
        self.port_list_id = os.environ.get('GCE_PORT_LIST_ID', 'c7e03b6c-3bbe-11e1-a057-406186ea4fc5')
        
    def publish_status_update(self, scan_id: int, status: str, message: str = None, error_details: str = None):
        """Pubblica un aggiornamento di stato con formato corretto"""
        update = {
            'scan_id': scan_id,
            'module': 'gce',  # Usa 'module' invece di 'plugin' per compatibilità
            'status': status,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        if message:
            update['message'] = message
        if error_details:
            update['error_details'] = error_details
            
        success = self.publisher_connection.publish(update)
        if success:
            logger.info(f"Published status update for scan {scan_id}: {status}")
        else:
            logger.error(f"Failed to publish status update for scan {scan_id}")
    
    def connect_to_gce(self) -> Optional[Gmp]:
        """Connette a GCE via Unix socket"""
        try:
            logger.info(f"Connecting to GCE via socket: {self.gce_socket}")
            
            # Check if socket exists
            if not os.path.exists(self.gce_socket):
                raise FileNotFoundError(f"GCE socket not found: {self.gce_socket}")
            
            # Create connection
            connection = UnixSocketConnection(path=self.gce_socket, timeout=60)
            transform = EtreeTransform()
            
            with Gmp(connection=connection, transform=transform) as gmp:
                # Authenticate
                logger.info("Authenticating with GCE...")
                gmp.authenticate(self.gce_username, self.gce_password)
                logger.info("Authenticated with GCE successfully")
                
                return gmp
                
        except Exception as e:
            logger.error(f"Failed to connect to GCE: {e}")
            return None
    
    def create_target(self, gmp: Gmp, host: str, name: str) -> Optional[str]:
        """Crea un target in GCE"""
        try:
            target_name = f"VaPtER - {name} - {host} - {datetime.now(timezone.utc).isoformat()}"
            logger.info(f"Creating GCE target: {target_name}")
            
            resp = gmp.create_target(
                name=target_name,
                hosts=[host],
                port_list_id=self.port_list_id
            )
            
            target_id = resp.get('id')
            logger.info(f"Created GCE target with ID: {target_id}")
            return target_id
            
        except Exception as e:
            logger.error(f"Failed to create target: {e}")
            return None
    
    def create_task(self, gmp: Gmp, target_id: str, scan_id: int) -> Optional[str]:
        """Crea un task in GCE"""
        try:
            task_name = f"VaPtER Scan - Scan {scan_id} - {datetime.now(timezone.utc).isoformat()}"
            logger.info(f"Creating GCE task: {task_name}")
            
            resp = gmp.create_task(
                name=task_name,
                config_id=self.scan_config_id,
                target_id=target_id,
                comment="Automated vulnerability scan initiated by VaPtER"
            )
            
            task_id = resp.get('id')
            logger.info(f"Created GCE task with ID: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            return None
    
    def start_scan(self, gmp: Gmp, task_id: str) -> bool:
        """Avvia la scansione GCE"""
        try:
            logger.info(f"Starting GCE scan for task: {task_id}")
            gmp.start_task(task_id)
            logger.info("GCE scan started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start scan: {e}")
            return False
    
    def monitor_scan(self, gmp: Gmp, task_id: str, scan_id: int) -> Tuple[bool, Optional[str]]:
        """Monitora il progresso della scansione con heartbeat"""
        try:
            start_time = datetime.now(timezone.utc)
            last_progress = -1
            heartbeat_interval = 30  # Send heartbeat every 30 seconds
            last_heartbeat = time.time()
            
            while True:
                # Check task status
                resp = gmp.get_task(task_id)
                task = resp.find('task')
                
                if task is None:
                    logger.error("Task not found in response")
                    return False, None
                
                status = task.find('status').text
                progress_elem = task.find('progress')
                progress = int(progress_elem.text) if progress_elem is not None else 0
                
                # Log progress if changed
                if progress != last_progress:
                    logger.info(f"Scan progress: {progress}% (status: {status})")
                    last_progress = progress
                    
                    # Send progress update
                    self.publisher_connection.publish({
                        'scan_id': scan_id,
                        'module': 'gce',
                        'status': 'running',
                        'progress': progress,
                        'timestamp': datetime.now(timezone.utc).isoformat()
                    })
                
                # Send heartbeat
                if time.time() - last_heartbeat > heartbeat_interval:
                    self.publisher_connection.ensure_connection()
                    last_heartbeat = time.time()
                
                # Check if scan is complete
                if status in ['Done', 'Stopped', 'Stop Requested']:
                    report_elem = task.find('.//report[@id]')
                    if report_elem is not None:
                        report_id = report_elem.get('id')
                        logger.info(f"Scan completed with status: {status}")
                        logger.info(f"Report ID: {report_id}")
                        return True, report_id
                    else:
                        logger.error("Scan completed but no report ID found")
                        return False, None
                
                # Check for timeout (4 hours)
                if (datetime.now(timezone.utc) - start_time).total_seconds() > 14400:
                    logger.error("Scan timeout reached (4 hours)")
                    return False, None
                
                # Wait before next check
                time.sleep(30)
                
        except Exception as e:
            logger.error(f"Error monitoring scan: {e}")
            return False, None
    
    def get_report(self, gmp: Gmp, report_id: str) -> Optional[str]:
        """Recupera il report GCE in formato XML"""
        try:
            logger.info(f"Retrieving report: {report_id}")
            
            # Get full report with results
            resp = gmp.get_report(
                report_id,
                report_format_id=None,  # Use default XML format
                filter_string="rows=-1"  # Get all results
            )
            
            # Convert to string
            report_xml = ET.tostring(resp, encoding='unicode')
            logger.info(f"GCE Report XML: {report_xml[:2000]}...")  # Log first 2000 chars
            
            return report_xml
            
        except Exception as e:
            logger.error(f"Failed to get report: {e}")
            return None
    
    def send_results_to_api(self, scan_id: int, results: Dict[str, Any]) -> bool:
        """Invia i risultati all'API Gateway"""
        try:
            url = f"{self.api_gateway_url}/api/orchestrator/scans/{scan_id}/gce-results/"
            
            response = requests.post(
                url,
                json=results,
                headers={'Content-Type': 'application/json'},
                timeout=60
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Successfully sent GCE results for scan {scan_id}")
                return True
            else:
                logger.error(f"Failed to send results: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending results to API: {e}")
            return False
    
    def process_scan_request(self, channel, method, properties, message: Dict[str, Any]):
        """Processa una richiesta di scansione GCE"""
        scan_id = message.get('scan_id')
        target_host = message.get('target_host')
        target_name = message.get('target_name', target_host)
        
        logger.info(f"Processing GCE scan request for scan {scan_id}, target {target_host}")
        
        # Update status to running
        self.publish_status_update(scan_id, 'running', 'Starting GCE scan')
        
        gmp = None
        try:
            # Connect to GCE
            gmp = self.connect_to_gce()
            if not gmp:
                raise Exception("Failed to connect to GCE")
            
            # Create target
            target_id = self.create_target(gmp, target_host, target_name)
            if not target_id:
                raise Exception("Failed to create target")
            
            # Create task
            task_id = self.create_task(gmp, target_id, scan_id)
            if not task_id:
                raise Exception("Failed to create task")
            
            # Start scan
            if not self.start_scan(gmp, task_id):
                raise Exception("Failed to start scan")
            
            # Monitor scan with heartbeat
            success, report_id = self.monitor_scan(gmp, task_id, scan_id)
            
            if success and report_id:
                # Get report
                report_xml = self.get_report(gmp, report_id)
                
                if report_xml:
                    # Prepare results
                    results = {
                        'gce_task_id': task_id,
                        'gce_report_id': report_id,
                        'report_xml': report_xml,
                        'gce_scan_completed_at': datetime.now(timezone.utc).isoformat()
                    }
                    
                    # Send to API
                    if self.send_results_to_api(scan_id, results):
                        self.publish_status_update(scan_id, 'completed', 'GCE scan completed successfully')
                    else:
                        self.publish_status_update(scan_id, 'error', error_details='Failed to send results to API')
                else:
                    self.publish_status_update(scan_id, 'error', error_details='Failed to retrieve report')
            else:
                self.publish_status_update(scan_id, 'error', error_details='Scan failed or timed out')
                
        except Exception as e:
            logger.error(f"Error processing scan request: {e}", exc_info=True)
            self.publish_status_update(scan_id, 'error', error_details=str(e))
            
        finally:
            # Clean up GCE connection
            if gmp:
                try:
                    gmp.disconnect()
                except:
                    pass
    
    def run(self):
        """Avvia il GCE scanner"""
        logger.info("Starting GCE Scanner...")
        
        # Connect to RabbitMQ
        if not self.consumer_connection.connect():
            logger.error("Failed to connect consumer to RabbitMQ")
            return
            
        if not self.publisher_connection.connect():
            logger.error("Failed to connect publisher to RabbitMQ")
            return
        
        logger.info(f"GCE Scanner started, waiting for messages on {self.consumer_connection.queue_name}")
        
        try:
            # Start consuming messages
            self.consumer_connection.consume(self.process_scan_request)
        except KeyboardInterrupt:
            logger.info("Shutdown requested...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.consumer_connection.close()
            self.publisher_connection.close()
            logger.info("GCE Scanner stopped")


if __name__ == "__main__":
    scanner = GCEScanner()
    scanner.run()