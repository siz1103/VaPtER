# plugins/nmap_scanner/nmap_scanner.py

import os
import json
import logging
import time
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import threading

import pika
from pika.exceptions import AMQPConnectionError, AMQPChannelError, ConnectionClosedByBroker
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RabbitMQConnection:
    """Gestisce le connessioni RabbitMQ con reconnection automatica e heartbeat robusto"""
    
    def __init__(self, host: str, port: int, user: str, pwd: str, queue_name: str, heartbeat: int = 60):
        self.host = host
        self.port = port
        self.credentials = pika.PlainCredentials(user, pwd)
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
                logger.info(f"Attempting to connect to RabbitMQ at {self.host}:{self.port}")
                
                connection_params = pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    credentials=self.credentials,
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
                logger.info(f"Consuming from queue: {self.queue_name}")
                
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
            except KeyboardInterrupt:
                logger.info("Shutdown requested...")
                break
            except Exception as e:
                logger.error(f"Unexpected error during consume: {e}", exc_info=True)
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


class NmapScanner:
    def __init__(self):
        # Configuration
        self.api_gateway_url = os.environ.get('INTERNAL_API_GATEWAY_URL', 'http://api_gateway:5000')
        self.rabbitmq_host = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
        self.rabbitmq_port = int(os.environ.get('RABBITMQ_PORT', '5672'))
        self.rabbitmq_user = os.environ.get('RABBITMQ_USER', 'guest')
        self.rabbitmq_pass = os.environ.get('RABBITMQ_PASSWORD', 'guest')

        # Initialize connections
        self.consumer_connection = RabbitMQConnection(
            self.rabbitmq_host,
            self.rabbitmq_port,
            self.rabbitmq_user,
            self.rabbitmq_pass,
            os.environ.get('RABBITMQ_NMAP_SCAN_REQUEST_QUEUE', 'nmap_scan_requests'),
            heartbeat=60
        )
        
        self.publisher_connection = RabbitMQConnection(
            self.rabbitmq_host,
            self.rabbitmq_port,
            self.rabbitmq_user,
            self.rabbitmq_pass,
            os.environ.get('RABBITMQ_SCAN_STATUS_UPDATE_QUEUE', 'scan_status_updates'),
            heartbeat=60
        )
    
    def publish_status_update(self, scan_id: int, status: str, message: str = None):
        """Pubblica un aggiornamento di stato"""
        update = {
            'scan_id': scan_id,
            'module': 'nmap',  # Usa sempre 'module' per consistenza
            'status': status,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        if message:
            update['message'] = message
            
        success = self.publisher_connection.publish(update)
        if success:
            logger.info(f"Published status update for scan {scan_id}: {status}")
        else:
            logger.error(f"Failed to publish status update for scan {scan_id}")
    
    def get_scan_parameters(self, scan_type_id: int) -> Optional[Dict[str, Any]]:
        """Recupera i parametri di scansione dall'API Gateway"""
        try:
            url = f"{self.api_gateway_url}/api/orchestrator/scan_types/{scan_type_id}/"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get scan parameters: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting scan parameters: {e}")
            return None
    
    def build_nmap_command(self, target_host: str, scan_params: Dict[str, Any]) -> List[str]:
        """Costruisce il comando nmap basato sui parametri"""
        cmd = ['nmap']
        
        # Add scan type flags
        if scan_params.get('syn_scan'):
            cmd.append('-sS')
        if scan_params.get('udp_scan'):
            cmd.append('-sU')
        if scan_params.get('service_version'):
            cmd.append('-sV')
        if scan_params.get('os_detection'):
            cmd.append('-O')
        if scan_params.get('script_scan'):
            cmd.append('-sC')
        if scan_params.get('aggressive'):
            cmd.append('-A')
        
        # Timing template
        timing = scan_params.get('timing_template', 'T3')
        cmd.append(f'-{timing}')
        
        # Port specification
        port_spec = scan_params.get('port_specification', '-')
        if port_spec != '-':
            cmd.extend(['-p', port_spec])
        
        # Output format
        cmd.extend(['-oX', '-'])  # XML output to stdout
        
        # Target
        cmd.append(target_host)
        
        logger.info(f"Nmap command: {' '.join(cmd)}")
        return cmd
    
    def execute_nmap_scan(self, command: List[str]) -> Optional[str]:
        """Esegue la scansione nmap e ritorna l'output XML"""
        try:
            start_time = time.time()
            
            # Execute nmap
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            elapsed_time = time.time() - start_time
            
            if result.returncode == 0:
                logger.info(f"Nmap scan completed successfully in {elapsed_time:.2f}s")
                return result.stdout
            else:
                logger.error(f"Nmap scan failed with code {result.returncode}: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Nmap scan timed out")
            return None
        except Exception as e:
            logger.error(f"Error executing nmap: {e}")
            return None
    
    def parse_nmap_results(self, xml_output: str) -> Dict[str, Any]:
        """Parse i risultati XML di nmap"""
        try:
            root = ET.fromstring(xml_output)
            
            results = {
                'hosts': [],
                'scan_info': {},
                'raw_xml': xml_output
            }
            
            # Parse scan info
            scaninfo = root.find('scaninfo')
            if scaninfo is not None:
                results['scan_info'] = {
                    'type': scaninfo.get('type'),
                    'protocol': scaninfo.get('protocol'),
                    'services': scaninfo.get('services')
                }
            
            # Parse hosts
            for host in root.findall('host'):
                host_data = {
                    'address': None,
                    'hostname': None,
                    'state': None,
                    'ports': []
                }
                
                # Address
                address = host.find('address')
                if address is not None:
                    host_data['address'] = address.get('addr')
                
                # Hostname
                hostnames = host.find('hostnames')
                if hostnames is not None:
                    hostname = hostnames.find('hostname')
                    if hostname is not None:
                        host_data['hostname'] = hostname.get('name')
                
                # State
                status = host.find('status')
                if status is not None:
                    host_data['state'] = status.get('state')
                
                # Ports
                ports = host.find('ports')
                if ports is not None:
                    for port in ports.findall('port'):
                        port_data = {
                            'protocol': port.get('protocol'),
                            'portid': port.get('portid'),
                            'state': None,
                            'service': {}
                        }
                        
                        # Port state
                        state = port.find('state')
                        if state is not None:
                            port_data['state'] = state.get('state')
                        
                        # Service info
                        service = port.find('service')
                        if service is not None:
                            port_data['service'] = {
                                'name': service.get('name'),
                                'product': service.get('product'),
                                'version': service.get('version'),
                                'extrainfo': service.get('extrainfo')
                            }
                        
                        host_data['ports'].append(port_data)
                
                results['hosts'].append(host_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error parsing nmap results: {e}")
            return {}
    
    def send_results_to_api(self, scan_id: int, results: Dict[str, Any]) -> bool:
        """Invia i risultati all'API Gateway"""
        try:
            # Add metadata
            results['nmap_scan_completed_at'] = datetime.now(timezone.utc).isoformat()
            
            # Send results
            url = f"{self.api_gateway_url}/api/orchestrator/scans/{scan_id}/"
            response = requests.patch(
                url,
                json={'nmap_results': results},
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Successfully sent results for scan {scan_id}")
                return True
            else:
                logger.error(f"Failed to send results: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending results to API: {e}")
            return False
    
    def process_scan_request(self, channel, method, properties, message: Dict[str, Any]):
        """Processa una richiesta di scansione"""
        scan_id = message.get('scan_id')
        scan_type_id = message.get('scan_type_id')
        target_host = message.get('target_host')
        
        logger.info(f"Processing scan request: scan_id={scan_id}, target={target_host}")
        
        # Update status
        self.publish_status_update(scan_id, 'received', 'Scan request received by Nmap module')
        
        try:
            # Get scan parameters
            scan_params = self.get_scan_parameters(scan_type_id)
            if not scan_params:
                raise Exception("Failed to get scan parameters")
            
            # Build nmap command
            command = self.build_nmap_command(target_host, scan_params)
            
            # Update status
            self.publish_status_update(scan_id, 'running', 'Executing nmap scan')
            
            # Execute scan
            xml_output = self.execute_nmap_scan(command)
            if not xml_output:
                raise Exception("Nmap scan failed")
            
            # Parse results
            self.publish_status_update(scan_id, 'parsing', 'Parsing scan results')
            results = self.parse_nmap_results(xml_output)
            
            # Send results to API
            if self.send_results_to_api(scan_id, results):
                self.publish_status_update(scan_id, 'completed', 'Nmap scan completed successfully')
            else:
                self.publish_status_update(scan_id, 'error', 'Failed to send results to API')
                
        except Exception as e:
            logger.error(f"Error processing scan request: {e}", exc_info=True)
            self.publish_status_update(scan_id, 'error', f'Scan failed: {str(e)}')
    
    def run(self):
        """Avvia lo scanner"""
        logger.info("Starting Nmap Scanner...")
        
        # Connect to RabbitMQ
        if not self.consumer_connection.connect():
            logger.error("Failed to connect consumer to RabbitMQ")
            return
            
        if not self.publisher_connection.connect():
            logger.error("Failed to connect publisher to RabbitMQ")
            return
        
        logger.info(f"Nmap Scanner started, waiting for messages on {self.consumer_connection.queue_name}")
        
        try:
            # Start consuming
            self.consumer_connection.consume(self.process_scan_request)
        except KeyboardInterrupt:
            logger.info("Shutdown requested...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.consumer_connection.close()
            self.publisher_connection.close()
            logger.info("Nmap Scanner stopped")


if __name__ == "__main__":
    scanner = NmapScanner()
    scanner.run()