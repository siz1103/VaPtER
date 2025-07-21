import json
import logging
import signal
import sys
import time
import subprocess
import concurrent.futures
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
import requests
import pika
from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class FingerprintScanner:
    """Fingerprint scanning module for VaPtER platform"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.should_stop = False
        self.current_scan_id = None
        
        # Validate configuration
        if not settings.validate_config():
            logger.error("Configuration validation failed")
            sys.exit(1)
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.should_stop = True
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        sys.exit(0)
    
    def connect_rabbitmq(self) -> bool:
        """Connect to RabbitMQ"""
        try:
            parameters = pika.URLParameters(settings.RABBITMQ_URL)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare queues
            self.channel.queue_declare(queue=settings.FINGERPRINT_SCAN_REQUEST_QUEUE, durable=True)
            self.channel.queue_declare(queue=settings.SCAN_STATUS_UPDATE_QUEUE, durable=True)
            
            logger.info("Connected to RabbitMQ successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            return False
    
    def publish_status_update(self, scan_id: int, status: str, message: str = None, error_details: str = None) -> bool:
        """Publish status update to RabbitMQ"""
        try:
            status_message = {
                'scan_id': scan_id,
                'module': 'fingerprint',
                'status': status,
                'timestamp': datetime.utcnow().isoformat(),
            }
            
            if message:
                status_message['message'] = message
            if error_details:
                status_message['error_details'] = error_details
            
            self.channel.basic_publish(
                exchange='',
                routing_key=settings.SCAN_STATUS_UPDATE_QUEUE,
                body=json.dumps(status_message),
                properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
            )
            
            logger.info(f"Published status update for scan {scan_id}: {status}")
            return True
        except Exception as e:
            logger.error(f"Failed to publish status update: {str(e)}")
            return False
    
    def get_scan_data(self, scan_id: int) -> Optional[Dict[str, Any]]:
        """Get scan data from API Gateway"""
        try:
            url = f"{settings.API_GATEWAY_URL}/api/orchestrator/scans/{scan_id}/"
            response = requests.get(url, timeout=settings.API_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get scan data: {str(e)}")
            return None
    
    def extract_ports_from_nmap(self, nmap_results: Dict[str, Any]) -> List[Tuple[str, int, str]]:
        """Extract open ports from nmap results
        Returns: List of tuples (ip, port, protocol)
        """
        ports = []
        if not nmap_results or 'hosts' not in nmap_results:
            return ports
        
        for host in nmap_results.get('hosts', []):
            host_ip = host.get('ip')
            if not host_ip:
                continue
            
            for port_info in host.get('ports', []):
                if port_info.get('state') == 'open':
                    port_num = int(port_info.get('portid', 0))
                    protocol = port_info.get('protocol', 'tcp')
                    if port_num > 0:
                        ports.append((host_ip, port_num, protocol))
                        logger.debug(f"Found open port: {host_ip}:{port_num}/{protocol}")
        
        return ports
    
    def fingerprint_port(self, host: str, port: int, protocol: str = 'tcp') -> Dict[str, Any]:
        """Fingerprint a single port using FingerprintX"""
        result = {
            'host': host,
            'port': port,
            'protocol': protocol,
            'service_name': None,
            'service_version': None,
            'service_product': None,
            'confidence': 0,
            'raw_response': None,
            'error': None
        }
        
        try:
            # Build FingerprintX command
            cmd = [
                settings.FINGERPRINTX_PATH,
                '--json',
                '-t', f"{settings.FINGERPRINT_TIMEOUT_PER_PORT}s",
                f"{host}:{port}"
            ]
            
            logger.debug(f"Running FingerprintX: {' '.join(cmd)}")
            
            # Execute FingerprintX
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=settings.FINGERPRINT_TIMEOUT_PER_PORT + 10  # Add buffer
            )
            
            if process.returncode == 0 and process.stdout:
                try:
                    # Parse JSON output
                    output = json.loads(process.stdout.strip())
                    if output:
                        # FingerprintX returns array of results
                        if isinstance(output, list) and len(output) > 0:
                            fp_result = output[0]
                            result['service_name'] = fp_result.get('service', 'unknown')
                            result['service_version'] = fp_result.get('version')
                            result['service_product'] = fp_result.get('product')
                            result['confidence'] = 90  # FingerprintX doesn't provide confidence
                            result['raw_response'] = process.stdout
                            
                            logger.info(f"Fingerprinted {host}:{port}/{protocol} - {result['service_name']} {result['service_version'] or ''}")
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse FingerprintX output for {host}:{port}")
                    result['error'] = "Invalid JSON output"
            else:
                logger.warning(f"FingerprintX failed for {host}:{port}: {process.stderr}")
                result['error'] = process.stderr or "No output"
                
        except subprocess.TimeoutExpired:
            logger.warning(f"Fingerprint timeout for {host}:{port}/{protocol}")
            result['error'] = "Timeout"
        except Exception as e:
            logger.error(f"Error fingerprinting {host}:{port}/{protocol}: {str(e)}")
            result['error'] = str(e)
        
        return result
    
    def fingerprint_all_ports(self, ports: List[Tuple[str, int, str]]) -> List[Dict[str, Any]]:
        """Fingerprint all ports concurrently"""
        results = []
        total_ports = len(ports)
        
        logger.info(f"Starting fingerprinting for {total_ports} ports")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_FINGERPRINTS) as executor:
            # Submit all fingerprint tasks
            future_to_port = {
                executor.submit(self.fingerprint_port, host, port, protocol): (host, port, protocol)
                for host, port, protocol in ports
            }
            
            # Process completed tasks
            completed = 0
            for future in concurrent.futures.as_completed(future_to_port):
                completed += 1
                host, port, protocol = future_to_port[future]
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    if completed % 10 == 0 or completed == total_ports:
                        logger.info(f"Fingerprint progress: {completed}/{total_ports} ports completed")
                        
                except Exception as e:
                    logger.error(f"Exception processing {host}:{port}/{protocol}: {str(e)}")
                    results.append({
                        'host': host,
                        'port': port,
                        'protocol': protocol,
                        'error': str(e)
                    })
        
        return results
    
    def save_fingerprint_results(self, scan_id: int, target_id: int, results: List[Dict[str, Any]]) -> bool:
        """Save fingerprint results via API"""
        try:
            # Prepare fingerprint details for bulk creation
            fingerprint_details = []
            
            for result in results:
                if result.get('error'):
                    continue  # Skip failed fingerprints
                
                detail = {
                    'scan': scan_id,
                    'target': target_id,
                    'port': result['port'],
                    'protocol': result['protocol'],
                    'service_name': result.get('service_name'),
                    'service_version': result.get('service_version'),
                    'service_product': result.get('service_product'),
                    'service_info': None,  # Could be populated with additional info
                    'fingerprint_method': 'fingerprintx',
                    'confidence_score': result.get('confidence', 0),
                    'raw_response': result.get('raw_response'),
                    'additional_info': {
                        'host': result['host'],
                        'scan_timestamp': datetime.utcnow().isoformat()
                    }
                }
                fingerprint_details.append(detail)
            
            if fingerprint_details:
                # Send to API
                url = f"{settings.API_GATEWAY_URL}/api/orchestrator/fingerprint-details/bulk_create/"
                response = requests.post(
                    url,
                    json={'fingerprint_details': fingerprint_details},
                    timeout=settings.API_TIMEOUT
                )
                response.raise_for_status()
                logger.info(f"Saved {len(fingerprint_details)} fingerprint results")
            
            # Prepare summary for scan parsed_finger_results
            summary = self.create_fingerprint_summary(results)
            
            # Update scan with parsed results
            scan_url = f"{settings.API_GATEWAY_URL}/api/orchestrator/scans/{scan_id}/"
            scan_update = {
                'parsed_finger_results': summary
            }
            
            response = requests.patch(
                scan_url,
                json=scan_update,
                timeout=settings.API_TIMEOUT
            )
            response.raise_for_status()
            logger.info(f"Updated scan {scan_id} with fingerprint summary")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save fingerprint results: {str(e)}")
            return False
    
    def create_fingerprint_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create summary of fingerprint results for scan"""
        summary = {
            'scan_start': datetime.utcnow().isoformat(),
            'scan_end': datetime.utcnow().isoformat(),
            'total_ports_scanned': len(results),
            'services_identified': 0,
            'fingerprint_summary': {}
        }
        
        for result in results:
            if not result.get('error') and result.get('service_name'):
                port_key = f"{result['port']}/{result['protocol']}"
                summary['fingerprint_summary'][port_key] = {
                    'service': result['service_name'],
                    'version': result.get('service_version'),
                    'product': result.get('service_product'),
                    'confidence': result.get('confidence', 0)
                }
                summary['services_identified'] += 1
        
        return summary
    
    def process_message(self, channel, method, properties, body):
        """Process fingerprint scan request from RabbitMQ"""
        try:
            message = json.loads(body.decode('utf-8'))
            scan_id = message.get('scan_id')
            target_id = message.get('target_id')
            
            logger.info(f"Received fingerprint request: scan_id={scan_id}")
            
            # Validate message
            if not scan_id:
                logger.error(f"Invalid fingerprin