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
    
    def __init__(self, rabbitmq_url: str, queue_name: str):
        self.rabbitmq_url = rabbitmq_url
        self.queue_name = queue_name
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
                logger.info(f"Attempting to connect to RabbitMQ using URL: {self.rabbitmq_url.replace(self.rabbitmq_url.split('@')[0].split('//')[1], '***:***')}")
                
                # Usa URLParameters per includere automaticamente le credenziali dall'URL
                parameters = pika.URLParameters(self.rabbitmq_url)
                parameters.heartbeat = 60
                parameters.blocked_connection_timeout = 300
                parameters.connection_attempts = 3
                parameters.retry_delay = 2
                
                self.connection = pika.BlockingConnection(parameters)
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
                
                logger.info(f"Connected to RabbitMQ successfully on queue {self.queue_name}")
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
                    time.sleep(2)
        
        return False
    
    def consume(self, callback):
        """Avvia il consumer con auto-reconnection"""
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
                    auto_ack=False
                ):
                    try:
                        message = json.loads(body)
                        logger.info(f"Received message from {self.queue_name}: {message}")
                        
                        # Process message
                        callback(self.channel, method, properties, message)
                        
                        # Acknowledge message only after successful processing
                        self.channel.basic_ack(delivery_tag=method.delivery_tag)
                        self._last_activity = time.time()
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode message: {e}")
                        self.channel.basic_nack(
                            delivery_tag=method.delivery_tag,
                            requeue=False
                        )
                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)
                        self.channel.basic_nack(
                            delivery_tag=method.delivery_tag,
                            requeue=True
                        )
                        
            except ConnectionClosedByBroker as e:
                logger.error(f"Connection closed by broker: {e}")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Consumer error: {e}")
                time.sleep(5)
    
    def close(self):
        """Chiude la connessione"""
        with self._lock:
            try:
                if self.connection and not self.connection.is_closed:
                    self.connection.close()
                logger.info("RabbitMQ connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")


class NmapScanner:
    def __init__(self):
        # Configuration
        self.api_gateway_url = os.environ.get('INTERNAL_API_GATEWAY_URL', 'http://api_gateway:8080')
        self.rabbitmq_url = os.environ.get('RABBITMQ_URL', 'amqp://vapter:vapter123@rabbitmq:5672/')
        
        # Log configuration for debugging
        logger.info(f"Initializing NmapScanner with API Gateway: {self.api_gateway_url}")
        logger.info(f"RabbitMQ URL configured: {self.rabbitmq_url.replace(self.rabbitmq_url.split('@')[0].split('//')[1], '***:***')}")
        
        # Initialize connections using the full URL with credentials
        self.consumer_connection = RabbitMQConnection(
            self.rabbitmq_url,
            os.environ.get('RABBITMQ_NMAP_SCAN_REQUEST_QUEUE', 'nmap_scan_requests')
        )
        
        self.publisher_connection = RabbitMQConnection(
            self.rabbitmq_url,
            os.environ.get('RABBITMQ_SCAN_STATUS_UPDATE_QUEUE', 'scan_status_updates')
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
    
    def build_nmap_command(self, target: str, scan_params: Dict[str, Any]) -> List[str]:
        """Costruisce il comando nmap basato sui parametri"""
        command = ['nmap']
        
        # Add scan type flags
        if scan_params.get('scan_type'):
            command.append(scan_params['scan_type'])
        
        # Add timing template
        if scan_params.get('timing_template'):
            command.append(f"-T{scan_params['timing_template']}")
        
        # Add port specification
        if scan_params.get('ports'):
            command.extend(['-p', scan_params['ports']])
        
        # Add script scan if requested
        if scan_params.get('scripts'):
            command.extend(['--script', scan_params['scripts']])
        
        # Add version detection
        if scan_params.get('version_detection'):
            command.append('-sV')
        
        # Add OS detection
        if scan_params.get('os_detection'):
            command.append('-O')
        
        # Add traceroute
        if scan_params.get('traceroute'):
            command.append('--traceroute')
        
        # Always output XML for parsing
        command.extend(['-oX', '-'])
        
        # Add target
        command.append(target)
        
        logger.info(f"Built nmap command: {' '.join(command)}")
        return command
    
    def execute_nmap_scan(self, command: List[str]) -> Optional[str]:
        """Esegue la scansione nmap"""
        try:
            logger.info("Executing nmap scan...")
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode == 0:
                logger.info("Nmap scan completed successfully")
                return result.stdout
            else:
                logger.error(f"Nmap scan failed: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Nmap scan timed out")
            return None
        except Exception as e:
            logger.error(f"Error executing nmap scan: {e}")
            return None
    
    def parse_nmap_results(self, xml_output: str) -> Dict[str, Any]:
        """Analizza i risultati XML di nmap"""
        try:
            root = ET.fromstring(xml_output)
            results = {
                'hosts': [],
                'scan_info': {},
                'statistics': {}
            }
            
            # Parse scan info
            for scaninfo in root.findall('scaninfo'):
                results['scan_info'][scaninfo.get('protocol')] = {
                    'type': scaninfo.get('type'),
                    'numservices': scaninfo.get('numservices'),
                    'services': scaninfo.get('services')
                }
            
            # Parse hosts
            for host in root.findall('host'):
                host_data = {
                    'status': host.find('status').get('state'),
                    'addresses': [],
                    'hostnames': [],
                    'ports': [],
                    'os': []
                }
                
                # Addresses
                for address in host.findall('address'):
                    host_data['addresses'].append({
                        'addr': address.get('addr'),
                        'addrtype': address.get('addrtype')
                    })
                
                # Hostnames
                hostnames = host.find('hostnames')
                if hostnames is not None:
                    for hostname in hostnames.findall('hostname'):
                        host_data['hostnames'].append({
                            'name': hostname.get('name'),
                            'type': hostname.get('type')
                        })
                
                # Ports
                ports = host.find('ports')
                if ports is not None:
                    for port in ports.findall('port'):
                        port_data = {
                            'portid': port.get('portid'),
                            'protocol': port.get('protocol'),
                            'state': port.find('state').get('state'),
                            'service': {}
                        }
                        
                        service = port.find('service')
                        if service is not None:
                            port_data['service'] = {
                                'name': service.get('name'),
                                'product': service.get('product'),
                                'version': service.get('version'),
                                'extrainfo': service.get('extrainfo'),
                                'method': service.get('method'),
                                'conf': service.get('conf')
                            }
                        
                        host_data['ports'].append(port_data)
                
                # OS detection
                os_elem = host.find('os')
                if os_elem is not None:
                    for osmatch in os_elem.findall('osmatch'):
                        host_data['os'].append({
                            'name': osmatch.get('name'),
                            'accuracy': osmatch.get('accuracy')
                        })
                
                results['hosts'].append(host_data)
            
            # Parse statistics
            runstats = root.find('runstats')
            if runstats is not None:
                finished = runstats.find('finished')
                if finished is not None:
                    results['statistics'] = {
                        'timestr': finished.get('timestr'),
                        'elapsed': finished.get('elapsed'),
                        'exit': finished.get('exit')
                    }
                
                hosts_elem = runstats.find('hosts')
                if hosts_elem is not None:
                    results['statistics']['hosts'] = {
                        'up': hosts_elem.get('up'),
                        'down': hosts_elem.get('down'),
                        'total': hosts_elem.get('total')
                    }
            
            return results
            
        except Exception as e:
            logger.error(f"Error parsing nmap results: {e}")
            return {}
    
    def send_results_to_api(self, scan_id: int, results: Dict[str, Any]) -> bool:
        """Invia i risultati all'API Gateway"""
        try:
            url = f"{self.api_gateway_url}/api/orchestrator/scans/{scan_id}/"
            payload = {
                'nmap_results': results,
                'status': 'completed'
            }
            
            response = requests.put(url, json=payload, timeout=30)
            
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
        
        try:
            # Update status
            self.publish_status_update(scan_id, 'initializing', 'Starting nmap scan')
            
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
        
        logger.info(f"Nmap Scanner started, waiting for messages...")
        
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