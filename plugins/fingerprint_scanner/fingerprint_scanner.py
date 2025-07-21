# plugins/fingerprint_scanner/fingerprint_scanner.py

"""
VaPtER Fingerprint Scanner Service

This service handles fingerprinting of services running on open ports.
It integrates with the VaPtER vulnerability assessment platform.

Features:
- Service identification using FingerprintX
- Integration with nmap results
- Parallel scanning capabilities
- Progress tracking and status updates
- Result storage via API Gateway
"""

import json
import logging
import os
import sys
import time
import pika
import requests
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - **%(name)s** - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Settings:
    """Configuration settings for the fingerprint scanner"""
    
    def __init__(self):
        # API Gateway settings
        self.API_GATEWAY_URL = os.getenv('INTERNAL_API_GATEWAY_URL', 'http://api_gateway:8080')
        self.API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))
        
        # RabbitMQ settings
        self.RABBITMQ_URL = os.getenv('RABBITMQ_URL', 'amqp://vapter:vapter123@rabbitmq:5672/')
        self.FINGERPRINT_SCAN_REQUEST_QUEUE = os.getenv('RABBITMQ_FINGERPRINT_SCAN_REQUEST_QUEUE', 'fingerprint_scan_requests')
        self.SCAN_STATUS_UPDATE_QUEUE = os.getenv('RABBITMQ_SCAN_STATUS_UPDATE_QUEUE', 'scan_status_updates')
        
        # Fingerprint settings
        self.FINGERPRINT_TIMEOUT_PER_PORT = int(os.getenv('FINGERPRINT_TIMEOUT_PER_PORT', '60'))
        self.MAX_CONCURRENT_FINGERPRINTS = int(os.getenv('MAX_CONCURRENT_FINGERPRINTS', '10'))
        self.FINGERPRINT_MAX_RETRIES = int(os.getenv('FINGERPRINT_MAX_RETRIES', '3'))
        self.FINGERPRINT_RETRY_DELAY = int(os.getenv('FINGERPRINT_RETRY_DELAY', '5'))
        
        # Output settings
        self.TEMP_RESULTS_DIR = os.getenv('TEMP_RESULTS_DIR', '/tmp/fingerprint_results')
        self.KEEP_RAW_OUTPUT = os.getenv('KEEP_RAW_OUTPUT', 'false').lower() == 'true'


settings = Settings()


class FingerprintScanner:
    """Main fingerprint scanner class"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.current_scan_id = None
        
        # Ensure temp directory exists
        os.makedirs(settings.TEMP_RESULTS_DIR, exist_ok=True)
        
        # Test FingerprintX installation
        self.test_fingerprintx()
    
    def test_fingerprintx(self):
        """Test if FingerprintX is installed and working"""
        try:
            result = subprocess.run(['fingerprintx', '-h'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"FingerprintX is installed: {result.stdout.strip()}")
            else:
                logger.error("FingerprintX is not properly installed")
                sys.exit(1)
        except FileNotFoundError:
            logger.error("FingerprintX not found. Please ensure it's installed.")
            sys.exit(1)
    
    def connect_rabbitmq(self) -> bool:
        """Connect to RabbitMQ"""
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                parameters = pika.URLParameters(settings.RABBITMQ_URL)
                self.connection = pika.BlockingConnection(parameters)
                self.channel = self.connection.channel()
                
                # Declare queues
                self.channel.queue_declare(queue=settings.FINGERPRINT_SCAN_REQUEST_QUEUE, durable=True)
                self.channel.queue_declare(queue=settings.SCAN_STATUS_UPDATE_QUEUE, durable=True)
                
                logger.info("Successfully connected to RabbitMQ")
                return True
                
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    
        return False
    
    def publish_status_update(self, scan_id: int, status: str, message: str = None, error_details: str = None) -> bool:
        """Publish scan status update to RabbitMQ"""
        try:
            status_message = {
                'scan_id': scan_id,
                'module': 'fingerprint',
                'status': status,
                'timestamp': datetime.utcnow().isoformat()
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
        Returns: List of tuples (ip_or_hostname, port, protocol)
        """
        logger.info(f"Extracting ports from nmap results")
        ports = []
        
        if not nmap_results or 'hosts' not in nmap_results:
            logger.warning("No hosts found in nmap results")
            return ports
        
        for host in nmap_results.get('hosts', []):
            # Extract IP address
            host_ip = None
            addresses = host.get('addresses', [])
            for addr in addresses:
                if addr.get('addrtype') == 'ipv4':
                    host_ip = addr.get('addr')
                    break
            
            if not host_ip:
                logger.warning(f"No IPv4 address found for host, skipping")
                continue
            
            # Extract hostname if available (preferred over IP)
            host_target = host_ip  # Default to IP
            hostnames = host.get('hostnames', [])
            if hostnames and len(hostnames) > 0:
                hostname = hostnames[0].get('name')
                if hostname:
                    host_target = hostname
                    logger.info(f"Using hostname '{hostname}' instead of IP '{host_ip}'")
            
            logger.info(f"Processing host: {host_target} (IP: {host_ip})")
            
            # Extract ports
            for port_info in host.get('ports', []):
                if port_info.get('state') == 'open':
                    port_num = int(port_info.get('portid', 0))
                    protocol = port_info.get('protocol', 'tcp')
                    if port_num > 0:
                        ports.append((host_target, port_num, protocol))
                        logger.debug(f"Found open port: {host_target}:{port_num}/{protocol}")
        
        logger.info(f"Total open ports found: {len(ports)}")
        return ports
    
    def fingerprint_port(self, host: str, port: int, protocol: str = 'tcp') -> Dict[str, Any]:
        """Fingerprint a single port using FingerprintX"""
        result = {
            'host': host,
            'port': port,
            'protocol': protocol,
            'status': 'unknown',
            'error': None
        }
        
        try:
            # Build FingerprintX command
            cmd = [
                'fingerprintx',
                '--json',
                '--timeout', f'{settings.FINGERPRINT_TIMEOUT_PER_PORT}',
                '--targets', f'{host}:{port}'
            ]
            
            logger.debug(f"Running: {' '.join(cmd)}")
            
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
                    fingerprint_data = json.loads(process.stdout.strip())
                    
                    # FingerprintX returns an array of results
                    if isinstance(fingerprint_data, list) and len(fingerprint_data) > 0:
                        fp_result = fingerprint_data[0]
                        
                        result['status'] = 'success'
                        result['service_name'] = fp_result.get('service', 'unknown')
                        result['service_version'] = fp_result.get('version', '')
                        result['service_product'] = fp_result.get('product', '')
                        result['banner'] = fp_result.get('banner', '')
                        result['confidence'] = fp_result.get('confidence', 0)
                        result['raw_response'] = process.stdout
                        
                        logger.info(f"Fingerprinted {host}:{port} - {result['service_name']} {result['service_version']}")
                    else:
                        result['status'] = 'no_match'
                        result['raw_response'] = process.stdout
                        logger.debug(f"No fingerprint match for {host}:{port}")
                        
                except json.JSONDecodeError as e:
                    result['status'] = 'error'
                    result['error'] = f"Failed to parse FingerprintX output: {str(e)}"
                    result['raw_response'] = process.stdout
                    logger.error(f"JSON decode error for {host}:{port}: {str(e)}")
            else:
                result['status'] = 'error'
                result['error'] = process.stderr or 'Unknown error'
                logger.error(f"FingerprintX failed for {host}:{port}: {result['error']}")
                
        except subprocess.TimeoutExpired:
            result['status'] = 'timeout'
            result['error'] = f'Timeout after {settings.FINGERPRINT_TIMEOUT_PER_PORT}s'
            logger.warning(f"Timeout scanning {host}:{port}")
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            logger.error(f"Exception scanning {host}:{port}: {str(e)}")
        
        return result
    
    def fingerprint_all_ports(self, ports: List[Tuple[str, int, str]]) -> List[Dict[str, Any]]:
        """Fingerprint all ports using parallel execution"""
        results = []
        total_ports = len(ports)
        
        if total_ports == 0:
            return results
        
        logger.info(f"Starting fingerprinting of {total_ports} ports with max {settings.MAX_CONCURRENT_FINGERPRINTS} concurrent scans")
        
        with ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_FINGERPRINTS) as executor:
            # Submit all tasks
            future_to_port = {
                executor.submit(self.fingerprint_port, host, port, protocol): (host, port, protocol)
                for host, port, protocol in ports
            }
            
            # Process results as they complete
            completed = 0
            for future in as_completed(future_to_port):
                completed += 1
                host, port, protocol = future_to_port[future]
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Publish progress update
                    progress = int((completed / total_ports) * 100)
                    self.publish_status_update(
                        self.current_scan_id,
                        'running',
                        f'Fingerprinting progress: {completed}/{total_ports} ports ({progress}%)'
                    )
                    
                except Exception as e:
                    logger.error(f"Failed to get result for {host}:{port}: {str(e)}")
                    results.append({
                        'host': host,
                        'port': port,
                        'protocol': protocol,
                        'status': 'error',
                        'error': str(e)
                    })
        
        return results
    
    def save_fingerprint_results(self, scan_id: int, target_id: int, results: List[Dict[str, Any]]) -> bool:
        """Save fingerprint results to API Gateway"""
        try:
            successful_saves = 0
            
            for result in results:
                # Skip failed fingerprints unless we want to save errors
                if result.get('status') not in ['success', 'no_match']:
                    continue
                
                # Prepare data for API
                fingerprint_data = {
                    'scan': scan_id,
                    'target': target_id,
                    'port': result['port'],
                    'protocol': result['protocol'],
                    'service_name': result.get('service_name', 'unknown'),
                    'service_version': result.get('service_version', ''),
                    'service_product': result.get('service_product', ''),
                    'fingerprint_method': 'fingerprintx',
                    'confidence_score': result.get('confidence', 0),
                    'raw_response': result.get('raw_response', ''),
                    'additional_info': {
                        'host': result['host'],
                        'banner': result.get('banner', ''),
                        'scan_timestamp': datetime.utcnow().isoformat(),
                        'status': result['status']
                    }
                }
                
                # Send to API
                url = f"{settings.API_GATEWAY_URL}/api/orchestrator/fingerprint-details/"
                response = requests.post(
                    url,
                    json=fingerprint_data,
                    timeout=settings.API_TIMEOUT
                )
                
                if response.status_code == 201:
                    successful_saves += 1
                    logger.debug(f"Saved fingerprint for port {result['port']}")
                else:
                    logger.error(f"Failed to save fingerprint: {response.status_code} - {response.text}")
            
            logger.info(f"Successfully saved {successful_saves}/{len(results)} fingerprint results")
            
            # Generate summary for scan update
            summary = self.generate_fingerprint_summary(results)
            
            # Update scan with summary
            scan_url = f"{settings.API_GATEWAY_URL}/api/orchestrator/scans/{scan_id}/"
            scan_update = {
                'fingerprint_summary': summary
            }
            
            response = requests.patch(
                scan_url,
                json=scan_update,
                timeout=settings.API_TIMEOUT
            )
            
            if response.status_code not in [200, 201]:
                logger.warning(f"Failed to update scan summary: {response.status_code}")
            
            return successful_saves > 0
            
        except Exception as e:
            logger.error(f"Failed to save fingerprint results: {str(e)}")
            return False
    
    def generate_fingerprint_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of fingerprint results"""
        summary = {
            'total_ports_scanned': len(results),
            'services_identified': 0,
            'fingerprint_summary': {}
        }
        
        for result in results:
            if result.get('status') == 'success' and result.get('service_name') not in ['unknown', 'error'] and result.get('service_name'):
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
                logger.error(f"Invalid fingerprint request: {message}")
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            
            self.current_scan_id = scan_id
            
            # Publish initial status
            self.publish_status_update(scan_id, 'started', 'Fingerprint scan started')
            
            # Get scan data
            scan_data = self.get_scan_data(scan_id)
            if not scan_data:
                self.publish_status_update(scan_id, 'error', error_details='Failed to retrieve scan data')
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            
            # Extract ports from nmap results
            nmap_results = scan_data.get('parsed_nmap_results', {})
            if not nmap_results:
                self.publish_status_update(scan_id, 'error', error_details='No nmap results available')
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            
            ports = self.extract_ports_from_nmap(nmap_results)
            if not ports:
                logger.warning(f"No open ports found for scan {scan_id}")
                self.publish_status_update(scan_id, 'completed', 'No open ports to fingerprint')
                channel.basic_ack(delivery_tag=method.delivery_tag)
                return
            
            logger.info(f"Found {len(ports)} open ports to fingerprint")
            
            # Perform fingerprinting
            fingerprint_results = self.fingerprint_all_ports(ports)
            
            # Save results
            if self.save_fingerprint_results(scan_id, target_id or scan_data['target'], fingerprint_results):
                self.publish_status_update(scan_id, 'completed', f'Fingerprinted {len(fingerprint_results)} ports successfully')
            else:
                self.publish_status_update(scan_id, 'error', error_details='Failed to save fingerprint results')
            
            # Acknowledge message
            channel.basic_ack(delivery_tag=method.delivery_tag)
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            self.publish_status_update(
                self.current_scan_id, 
                'error', 
                error_details=f"Processing error: {str(e)}"
            )
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def start_consuming(self):
        """Start consuming messages from RabbitMQ"""
        if not self.connect_rabbitmq():
            logger.error("Failed to connect to RabbitMQ, exiting...")
            sys.exit(1)
        
        try:
            # Set QoS
            self.channel.basic_qos(prefetch_count=1)
            
            # Start consuming
            self.channel.basic_consume(
                queue=settings.FINGERPRINT_SCAN_REQUEST_QUEUE,
                on_message_callback=self.process_message,
                auto_ack=False
            )
            
            logger.info(f"Started consuming from queue: {settings.FINGERPRINT_SCAN_REQUEST_QUEUE}")
            
            # Start consuming (blocking)
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("Interrupted by user, shutting down...")
            self.channel.stop_consuming()
            self.connection.close()
        except Exception as e:
            logger.error(f"Error in consumer: {str(e)}")
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            sys.exit(1)


def main():
    """Main entry point"""
    logger.info("Starting VaPtER Fingerprint Scanner...")
    scanner = FingerprintScanner()
    scanner.start_consuming()


if __name__ == "__main__":
    main()