# plugins/nmap_scanner/nmap_scanner.py

import json
import logging
import signal
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, Any, Optional, List
import subprocess
import requests
import pika
from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class NmapScanner:
    """Nmap scanning module for VaPtER platform"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.should_stop = False
        self.current_scan_id = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def connect_rabbitmq(self) -> bool:
        """Connect to RabbitMQ"""
        try:
            parameters = pika.URLParameters(settings.RABBITMQ_URL)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare queues
            self.channel.queue_declare(queue=settings.NMAP_SCAN_REQUEST_QUEUE, durable=True)
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
                'module': 'nmap',
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
    
    def get_scan_parameters(self, scan_type_id: int) -> Optional[Dict[str, Any]]:
        """Get scan parameters from API Gateway"""
        try:
            url = f"{settings.API_GATEWAY_URL}/api/orchestrator/scan-types/{scan_type_id}/"
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            scan_type_data = response.json()
            logger.info(f"Retrieved scan type {scan_type_id}: {scan_type_data['name']}")
            
            # If port_list is an ID, fetch the full port_list details
            if scan_type_data.get('port_list') and isinstance(scan_type_data['port_list'], int):
                port_list_id = scan_type_data['port_list']
                port_list_data = self.get_port_list_details(port_list_id)
                if port_list_data:
                    scan_type_data['port_list'] = port_list_data
                else:
                    logger.warning(f"Failed to get port_list details for ID {port_list_id}")
                    scan_type_data['port_list'] = None
            
            return scan_type_data
        except Exception as e:
            logger.error(f"Failed to get scan parameters: {str(e)}")
            return None
    
    def get_port_list_details(self, port_list_id: int) -> Optional[Dict[str, Any]]:
        """Get port list details from API Gateway"""
        try:
            url = f"{settings.API_GATEWAY_URL}/api/orchestrator/port-lists/{port_list_id}/"
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            port_list_data = response.json()
            logger.info(f"Retrieved port list {port_list_id}: {port_list_data['name']}")
            
            return port_list_data
        except Exception as e:
            logger.error(f"Failed to get port list details: {str(e)}")
            return None
    
    def build_nmap_command(self, target_host: str, scan_type_data: Dict[str, Any]) -> List[str]:
        """Build nmap command based on scan type configuration"""
        
        cmd = ['nmap']
        
        # Basic flags
        cmd.extend(['-v', '-oX', '-'])  # Verbose output to XML on stdout
        
        # Discovery options
        if scan_type_data.get('only_discovery'):
            cmd.extend(['-sn'])  # Ping scan only
            logger.info("Configured for discovery-only scan")
        else:
            # Port scanning
            cmd.extend(['-sS'])  # TCP SYN scan
            
            # Port specification
            port_list = scan_type_data.get('port_list')
            logger.info(f"Port list data: {port_list}")
            
            if port_list and isinstance(port_list, dict):
                ports = []
                tcp_ports = port_list.get('tcp_ports')
                udp_ports = port_list.get('udp_ports')
                
                if tcp_ports:
                    ports.append(f"T:{tcp_ports}")
                    logger.info(f"Added TCP ports: {tcp_ports}")
                
                if udp_ports:
                    cmd.extend(['-sU'])  # UDP scan
                    ports.append(f"U:{udp_ports}")
                    logger.info(f"Added UDP ports: {udp_ports}")
                
                if ports:
                    cmd.extend(['-p', ','.join(ports)])
                    cmd.extend(['--open'])
                else:
                    cmd.extend(['--open'])
                    logger.warning("No ports specified in port_list, using default ports")
            else:
                logger.info("No port_list specified, using default ports")
            
            # Service/version detection
            if not scan_type_data.get('be_quiet'):
                cmd.extend(['-sV'])  # Version detection
                cmd.extend(['-O'])   # OS detection
                cmd.extend(['-sC'])  # Default scripts
                logger.info("Added service detection and OS detection")
        
        # Timing and performance
        if scan_type_data.get('be_quiet'):
            cmd.extend(['-T2'])  # Polite timing
            logger.info("Using polite timing (-T2)")
        else:
            cmd.extend(['-T4'])  # Aggressive timing
            logger.info("Using aggressive timing (-T4)")
        
        # Host discovery
        if scan_type_data.get('consider_alive'):
            cmd.extend(['-Pn'])  # Skip host discovery
            logger.info("Skipping host discovery (-Pn)")
        
        # Target
        cmd.append(target_host)
        
        logger.info(f"Built nmap command: {' '.join(cmd)}")
        return cmd
    
    def execute_nmap_scan(self, cmd: List[str], scan_id: int) -> Optional[str]:
        """Execute nmap scan and return XML output"""
        try:
            logger.info(f"Starting nmap scan for scan_id {scan_id}")
            self.publish_status_update(scan_id, 'running', 'Executing nmap scan')
            
            # Execute nmap command
            start_time = time.time()
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            duration = time.time() - start_time
            
            if process.returncode == 0:
                logger.info(f"Nmap scan completed successfully in {duration:.2f} seconds")
                self.publish_status_update(
                    scan_id, 
                    'parsing', 
                    f'Nmap scan completed in {duration:.2f}s, parsing results'
                )
                return stdout
            else:
                error_msg = f"Nmap scan failed with return code {process.returncode}: {stderr}"
                logger.error(error_msg)
                self.publish_status_update(scan_id, 'error', error_details=error_msg)
                return None
                
        except Exception as e:
            error_msg = f"Error executing nmap scan: {str(e)}"
            logger.error(error_msg)
            self.publish_status_update(scan_id, 'error', error_details=error_msg)
            return None
    
    def parse_nmap_xml(self, xml_output: str) -> Dict[str, Any]:
        """Parse nmap XML output and extract relevant information"""
        try:
            root = ET.fromstring(xml_output)
            
            results = {
                'scan_info': {},
                'hosts': [],
                'stats': {}
            }
            
            # Parse scan info
            scaninfo = root.find('scaninfo')
            if scaninfo is not None:
                results['scan_info'] = {
                    'type': scaninfo.get('type'),
                    'protocol': scaninfo.get('protocol'),
                    'numservices': scaninfo.get('numservices'),
                    'services': scaninfo.get('services')
                }
            
            # Parse hosts
            for host in root.findall('host'):
                host_data = {
                    'state': host.find('status').get('state') if host.find('status') is not None else 'unknown',
                    'addresses': [],
                    'hostnames': [],
                    'ports': [],
                    'os': {}
                }
                
                # Parse addresses
                for address in host.findall('address'):
                    host_data['addresses'].append({
                        'addr': address.get('addr'),
                        'addrtype': address.get('addrtype')
                    })
                
                # Parse hostnames
                hostnames = host.find('hostnames')
                if hostnames is not None:
                    for hostname in hostnames.findall('hostname'):
                        host_data['hostnames'].append({
                            'name': hostname.get('name'),
                            'type': hostname.get('type')
                        })
                
                # Parse ports
                ports = host.find('ports')
                if ports is not None:
                    for port in ports.findall('port'):
                        port_data = {
                            'protocol': port.get('protocol'),
                            'portid': port.get('portid'),
                            'state': port.find('state').get('state') if port.find('state') is not None else 'unknown'
                        }
                        
                        # Parse service info
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
                        
                        # Parse script results
                        scripts = []
                        for script in port.findall('script'):
                            scripts.append({
                                'id': script.get('id'),
                                'output': script.get('output')
                            })
                        if scripts:
                            port_data['scripts'] = scripts
                        
                        host_data['ports'].append(port_data)
                
                # Parse OS detection
                os_element = host.find('os')
                if os_element is not None:
                    osmatch = os_element.find('osmatch')
                    if osmatch is not None:
                        host_data['os'] = {
                            'name': osmatch.get('name'),
                            'accuracy': osmatch.get('accuracy'),
                            'line': osmatch.get('line')
                        }
                        
                        # Parse OS classes
                        osclass = osmatch.find('osclass')
                        if osclass is not None:
                            host_data['os'].update({
                                'type': osclass.get('type'),
                                'vendor': osclass.get('vendor'),
                                'osfamily': osclass.get('osfamily'),
                                'osgen': osclass.get('osgen')
                            })
                
                results['hosts'].append(host_data)
            
            # Parse run stats
            runstats = root.find('runstats')
            if runstats is not None:
                finished = runstats.find('finished')
                hosts = runstats.find('hosts')
                
                if finished is not None:
                    results['stats']['finished'] = {
                        'time': finished.get('time'),
                        'timestr': finished.get('timestr'),
                        'elapsed': finished.get('elapsed')
                    }
                
                if hosts is not None:
                    results['stats']['hosts'] = {
                        'up': hosts.get('up'),
                        'down': hosts.get('down'),
                        'total': hosts.get('total')
                    }
            
            logger.info(f"Successfully parsed nmap XML - found {len(results['hosts'])} hosts")
            return results
            
        except Exception as e:
            logger.error(f"Error parsing nmap XML: {str(e)}")
            raise
    
    def send_results_to_api(self, scan_id: int, parsed_results: Dict[str, Any]) -> bool:
        """Send parsed results to API Gateway"""
        try:
            url = f"{settings.API_GATEWAY_URL}/api/orchestrator/scans/{scan_id}/"
            
            payload = {
                'parsed_nmap_results': parsed_results,
                'status': 'Nmap Scan Completed',
                'completed_at': datetime.utcnow().isoformat()
            }
            
            response = requests.patch(url, json=payload, timeout=30)
            response.raise_for_status()
            
            logger.info(f"Successfully sent results to API for scan {scan_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send results to API: {str(e)}")
            return False
    
    def process_scan_request(self, channel, method, properties, body):
        """Process incoming scan request"""
        try:
            # Parse message
            message = json.loads(body.decode('utf-8'))
            scan_id = message.get('scan_id')
            scan_type_id = message.get('scan_type_id')
            target_host = message.get('target_host')
            
            logger.info(f"Received scan request: scan_id={scan_id}, scan_type_id={scan_type_id}, target={target_host}")
            
            # Validate message
            if not all([scan_id, scan_type_id, target_host]):
                logger.error(f"Invalid scan request: {message}")
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            
            self.current_scan_id = scan_id
            
            # Publish initial status
            self.publish_status_update(scan_id, 'received', 'Scan request received by Nmap module')
            
            # Get scan parameters
            logger.info(f"Getting scan parameters for scan_type_id={scan_type_id}")
            scan_type_data = self.get_scan_parameters(scan_type_id)
            if not scan_type_data:
                self.publish_status_update(scan_id, 'error', error_details='Failed to retrieve scan parameters')
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            
            logger.info(f"Scan type data: {scan_type_data}")
            
            # Build nmap command
            try:
                nmap_cmd = self.build_nmap_command(target_host, scan_type_data)
                logger.info(f"Built nmap command successfully: {' '.join(nmap_cmd)}")
            except Exception as e:
                error_msg = f"Failed to build nmap command: {str(e)}"
                logger.error(error_msg)
                self.publish_status_update(scan_id, 'error', error_details=error_msg)
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            
            # Execute scan
            xml_output = self.execute_nmap_scan(nmap_cmd, scan_id)
            if not xml_output:
                # Error already published in execute_nmap_scan
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            
            # Parse results
            try:
                parsed_results = self.parse_nmap_xml(xml_output)
                logger.info(f"Parsed results successfully: {len(parsed_results.get('hosts', []))} hosts found")
            except Exception as e:
                error_msg = f"Failed to parse nmap results: {str(e)}"
                logger.error(error_msg)
                self.publish_status_update(scan_id, 'error', error_details=error_msg)
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            
            # Send results to API
            if self.send_results_to_api(scan_id, parsed_results):
                self.publish_status_update(scan_id, 'completed', 'Nmap scan completed successfully')
                channel.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(f"Scan {scan_id} completed successfully")
            else:
                self.publish_status_update(scan_id, 'error', error_details='Failed to send results to API')
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            
            self.current_scan_id = None
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in scan request: {str(e)}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"Error processing scan request: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {repr(e)}")
            if self.current_scan_id:
                self.publish_status_update(self.current_scan_id, 'error', error_details=str(e))
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def start_consuming(self):
        """Start consuming messages from RabbitMQ"""
        try:
            if not self.connect_rabbitmq():
                return False
            
            # Set QoS
            self.channel.basic_qos(prefetch_count=1)
            
            # Setup consumer
            self.channel.basic_consume(
                queue=settings.NMAP_SCAN_REQUEST_QUEUE,
                on_message_callback=self.process_scan_request,
                auto_ack=False
            )
            
            logger.info(f"Nmap Scanner started, waiting for messages on {settings.NMAP_SCAN_REQUEST_QUEUE}")
            
            # Start consuming
            while not self.should_stop:
                try:
                    self.connection.process_data_events(time_limit=1)
                except KeyboardInterrupt:
                    break
            
            return True
            
        except Exception as e:
            logger.error(f"Error in consumer: {str(e)}")
            return False
        finally:
            self._cleanup()
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info('Received shutdown signal. Stopping nmap scanner...')
        self.should_stop = True
        
        # If we're currently processing a scan, mark it as failed
        if self.current_scan_id:
            self.publish_status_update(
                self.current_scan_id, 
                'error', 
                error_details='Scanner shutdown during scan execution'
            )
    
    def _cleanup(self):
        """Cleanup connections"""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.stop_consuming()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            
            logger.info("Nmap scanner stopped gracefully")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")


def main():
    """Main entry point"""
    logger.info("Starting VaPtER Nmap Scanner")
    
    scanner = NmapScanner()
    success = scanner.start_consuming()
    
    if not success:
        logger.error("Failed to start nmap scanner")
        sys.exit(1)


if __name__ == "__main__":
    main()