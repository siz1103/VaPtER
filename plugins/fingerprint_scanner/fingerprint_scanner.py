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
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level.upper(), logging.INFO),
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
                self.channel.queue_declare(
                    queue=settings.FINGERPRINT_SCAN_REQUEST_QUEUE, 
                    durable=True,
                    arguments={
                        'x-message-ttl': 3600000,  # 1 hour TTL
                        'x-max-length': 10000
                    }
                )
                self.channel.queue_declare(
                    queue=settings.SCAN_STATUS_UPDATE_QUEUE, 
                    durable=True,
                                        arguments={
                        'x-message-ttl': 3600000,  # 1 hour TTL
                        'x-max-length': 10000
                    }
                )
                
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
    
    def parse_banner(self, banner: str, protocol: str) -> Tuple[str, str]:
        """Parse banner to extract service product and version
        Returns: (service_product, service_version)
        """
        if not banner:
            return ('', '')
        
        # SSH banner format: SSH-{version}-{software}
        if protocol == 'ssh' and banner.startswith('SSH-'):
            parts = banner.split('-', 2)
            if len(parts) >= 3:
                version_info = parts[2].strip()
                # Extract software name and version (e.g., "OpenSSH_9.6p1 Ubuntu-3ubuntu13.12")
                if '_' in version_info:
                    software_parts = version_info.split('_', 1)
                    service_product = software_parts[0]  # "OpenSSH"
                    # Extract just the version number
                    version_full = software_parts[1]
                    service_version = version_full.split()[0]  # "9.6p1"
                    return (service_product, service_version)
                else:
                    return ('SSH', parts[1])
        
        # SMTP banner format: 220 {hostname} ESMTP {software} {version}
        elif protocol == 'smtp' and banner.startswith('220'):
            parts = banner.split()
            if 'ESMTP' in parts:
                esmtp_index = parts.index('ESMTP')
                if esmtp_index + 1 < len(parts):
                    service_product = parts[esmtp_index + 1]  # "Exim"
                    service_version = parts[esmtp_index + 2] if esmtp_index + 2 < len(parts) else ''  # "4.92"
                    return (service_product, service_version)
        
        # HTTP Server header format: Server: {software}/{version}
        elif protocol in ['http', 'https']:
            if '/' in banner:
                parts = banner.split('/', 1)
                return (parts[0].strip(), parts[1].strip())
            elif banner:
                # Just product name without version
                return (banner.strip(), '')
        
        # FTP banner
        elif protocol == 'ftp' and banner.startswith('220'):
            # Try to extract version info from FTP banner
            parts = banner.split()
            for i, part in enumerate(parts):
                if '/' in part:
                    product_version = part.split('/', 1)
                    return (product_version[0], product_version[1])
                elif any(char.isdigit() for char in part) and i > 0:
                    # Previous part might be the product
                    return (parts[i-1], part)
        
        # Generic parsing for other protocols
        # Look for patterns like "software/version" or "software version"
        if '/' in banner:
            parts = banner.split('/', 1)
            if len(parts) >= 2:
                return (parts[0].strip(), parts[1].split()[0].strip())
        
        # If no specific parsing worked, return empty
        return ('', '')

    def fingerprint_port(self, host: str, port: int, protocol: str = 'tcp') -> Dict[str, Any]:
        """Fingerprint a single port using FingerprintX"""
        result = {
            'host': host,
            'port': port,
            'transport_protocol': protocol,  # tcp/udp
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
                    logger.debug(f"Raw FingerprintX output for {host}:{port}: {json.dumps(fingerprint_data, indent=2)}")
                    
                    # Process the raw FingerprintX output
                    # FingerprintX can return either a single object or an array
                    if fingerprint_data:
                        # Handle both single object and array response
                        if isinstance(fingerprint_data, list):
                            fp_result = fingerprint_data[0] if fingerprint_data else {}
                        else:
                            fp_result = fingerprint_data
                        
                        # Extract application protocol (ssh, http, etc.) - this goes to service_name
                        service_name = fp_result.get('protocol', 'unknown')
                        
                        # Extract metadata
                        metadata = fp_result.get('metadata', {})
                        banner = metadata.get('banner', '')
                        
                        # Parse banner to get service product and version
                        service_product, service_version = self.parse_banner(banner, service_name)
                        
                        # Even if we don't have a perfect match, if we have a protocol, it's a success
                        if service_name != 'unknown' or banner:
                            result['status'] = 'success'
                        else:
                            result['status'] = 'no_match'
                        
                        result['service_name'] = service_name  # Application protocol (ssh, http, etc.)
                        result['service_product'] = service_product  # Software name (OpenSSH, nginx, etc.)
                        result['service_version'] = service_version  # Version (9.6p1, 1.18.0, etc.)
                        result['banner'] = banner
                        result['metadata'] = metadata
                        result['raw_response'] = json.dumps(fingerprint_data)  # Store as JSON string
                        
                        logger.info(f"Fingerprinted {host}:{port}/{protocol} - service_name:{service_name} - product:{service_product} version:{service_version}")
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
                        'transport_protocol': protocol,
                        'status': 'error',
                        'error': str(e)
                    })
        
        return results
    
    def save_fingerprint_results(self, scan_id: int, target_id: int, results: List[Dict[str, Any]]) -> bool:
        """Save fingerprint results to API Gateway"""
        try:
            successful_saves = 0
            
            for result in results:
                # Save results that have useful information
                if result.get('status') in ['success', 'no_match']:
                    # Skip only if we have no useful data at all
                    if (result.get('service_name') == 'unknown' and 
                        not result.get('banner') and 
                        not result.get('metadata')):
                        continue
                
                # Prepare structured metadata
                additional_info = {
                    'host': result['host'],
                    'scan_timestamp': datetime.utcnow().isoformat(),
                    'status': result['status']
                }
                
                # Add metadata if available
                if result.get('metadata'):
                    # Convert metadata to a more readable format
                    metadata = result['metadata']
                    if isinstance(metadata, dict):
                        # Extract important fields
                        if 'banner' in metadata:
                            additional_info['banner'] = metadata['banner']
                        if 'algo' in metadata:
                            # Parse SSH algorithms
                            additional_info['ssh_algorithms'] = metadata['algo']
                        if 'passwordAuthEnabled' in metadata:
                            additional_info['password_auth_enabled'] = metadata['passwordAuthEnabled']
                        # Add any other metadata fields
                        for key, value in metadata.items():
                            if key not in ['banner', 'algo', 'passwordAuthEnabled'] and value:
                                additional_info[key] = value
                
                # Build service_info field with additional details
                service_info_parts = []
                if result.get('banner'):
                    # Extract extra info from banner that wasn't captured in product/version
                    banner = result['banner']
                    if 'Ubuntu' in banner:
                        service_info_parts.append('Ubuntu Linux')
                    elif 'Debian' in banner:
                        service_info_parts.append('Debian Linux')
                    elif 'CentOS' in banner:
                        service_info_parts.append('CentOS Linux')
                    elif 'protocol 2.0' in banner.lower():
                        service_info_parts.append('protocol 2.0')
                
                service_info = '; '.join(service_info_parts) if service_info_parts else None
                
                # Prepare data for API
                fingerprint_data = {
                    'scan': scan_id,
                    'target': target_id,
                    'port': result['port'],  # Integer port number
                    'protocol': result.get('transport_protocol', 'tcp'),  # Transport protocol (tcp/udp)
                    'service_name': result.get('service_name', 'unknown'),  # Application protocol (ssh, http, etc.)
                    'service_version': result.get('service_version', ''),  # Version (9.6p1, etc.)
                    'service_product': result.get('service_product', ''),  # Product (OpenSSH, nginx, etc.)
                    'service_info': service_info,  # Additional service information
                    'fingerprint_method': 'fingerprintx',
                    'confidence_score': 95 if result.get('status') == 'success' else 50,  # Lower confidence for no_match
                    'raw_response': result.get('raw_response', ''),
                    'additional_info': additional_info
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
                    logger.debug(f"Saved fingerprint for port {result['port']}/{result.get('transport_protocol', 'tcp')}")
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
            if result.get('status') == 'success':
                port_key = f"{result['port']}/{result.get('transport_protocol', 'tcp')}"
                summary['fingerprint_summary'][port_key] = {
                    'service': result.get('service_name', 'unknown'),  # Application protocol
                    'product': result.get('service_product', ''),      # Software name
                    'version': result.get('service_version', '')       # Version
                }
                if result.get('service_name') not in ['unknown', None, '']:
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