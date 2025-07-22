# plugins/gce_scanner/gce_scanner.py

import json
import logging
import time
import signal
import sys
import traceback
from datetime import datetime
from uuid import UUID

import pika
import requests
from gvm.connections import UnixSocketConnection
from gvm.protocols.gmp import Gmp
from gvm.transforms import EtreeCheckCommandTransform
from gvm.errors import GvmError
from gvm.protocols.gmpv224 import Gmp as Gmp224  # Support for newer GMP versions
import xmltodict

import config as settings

logger = logging.getLogger(__name__)


class GCEScanner:
    """GCE (Greenbone Community Edition) Scanner Plugin for VaPtER"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.should_stop = False
        self.current_scan_id = None
        self.gmp_connection = None
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info('Received shutdown signal. Stopping scanner...')
        self.should_stop = True
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        sys.exit(0)
    
    def connect_rabbitmq(self):
        """Connect to RabbitMQ"""
        try:
            parameters = pika.URLParameters(settings.RABBITMQ_URL)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare queues
            self.channel.queue_declare(queue=settings.GCE_SCAN_REQUEST_QUEUE, durable=True)
            self.channel.queue_declare(queue=settings.SCAN_STATUS_UPDATE_QUEUE, durable=True)
            
            logger.info("Connected to RabbitMQ successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            return False
    
    def connect_gce(self):
        """Connect to GCE via Unix socket with automatic version detection"""
        try:
            connection = UnixSocketConnection(path=settings.GCE_SOCKET_PATH)
            transform = EtreeCheckCommandTransform()
            
            # First try with the latest GMP protocol
            try:
                # Try with GMP 22.4+ protocol
                from gvm.protocols.gmpv224 import Gmp as Gmp224
                gmp = Gmp224(connection, transform=transform)
                
                # Test connection by getting version
                version_response = gmp.get_version()
                version = version_response.find('version').text if version_response is not None else "Unknown"
                logger.info(f"Connected to GCE with GMP version: {version}")
                return gmp
                
            except (ImportError, GvmError) as e:
                logger.warning(f"Failed with Gmp224, trying standard Gmp: {e}")
                
                # Fallback to standard Gmp
                connection = UnixSocketConnection(path=settings.GCE_SOCKET_PATH)
                gmp = Gmp(connection, transform=transform)
                
                # Test connection
                version_response = gmp.get_version()
                version = version_response.find('version').text if version_response is not None else "Unknown"
                logger.info(f"Connected to GCE with GMP version: {version}")
                return gmp
                
        except FileNotFoundError:
            logger.error(f"GCE socket not found at {settings.GCE_SOCKET_PATH}")
            raise
        except Exception as e:
            logger.error(f"Failed to connect to GCE: {str(e)}")
            raise
    
    def publish_status_update(self, scan_id, status, message=None, error_details=None):
        """Publish scan status update to RabbitMQ"""
        try:
            update_message = {
                'scan_id': scan_id,
                'module': 'gce',
                'status': status,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if message:
                update_message['message'] = message
            if error_details:
                update_message['error_details'] = error_details
            
            self.channel.basic_publish(
                exchange='',
                routing_key=settings.SCAN_STATUS_UPDATE_QUEUE,
                body=json.dumps(update_message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                )
            )
            
            logger.info(f"Published status update for scan {scan_id}: {status}")
        except Exception as e:
            logger.error(f"Failed to publish status update: {str(e)}")
    
    def get_scan_params(self, scan_type_id):
        """Get scan parameters from API"""
        try:
            url = f"{settings.INTERNAL_API_GATEWAY_URL}/api/orchestrator/scan-types/{scan_type_id}/"
            response = requests.get(url, timeout=settings.API_TIMEOUT)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get scan parameters: {str(e)}")
            return None
    
    def create_gce_target(self, gmp, target_ip, target_name):
        """Create target in GCE"""
        try:
            target_name_gce = f"VaPtER - {target_name} - {target_ip} - {datetime.now().isoformat()}"
            
            logger.info(f"Creating GCE target: {target_name_gce}")
            response = gmp.create_target(
                name=target_name_gce,
                hosts=[target_ip],
                port_list_id=settings.GCE_PORT_LIST_ID
            )
            
            target_id = response.get('id')
            logger.info(f"Created GCE target with ID: {target_id}")
            return target_id
            
        except Exception as e:
            logger.error(f"Failed to create GCE target: {str(e)}")
            raise
    
    def create_gce_task(self, gmp, target_id, scan_name):
        """Create scan task in GCE"""
        try:
            task_name = f"VaPtER Scan - {scan_name} - {datetime.now().isoformat()}"
            task_comment = "Automated vulnerability scan initiated by VaPtER"
            
            logger.info(f"Creating GCE task: {task_name}")
            response = gmp.create_task(
                name=task_name,
                config_id=settings.GCE_SCAN_CONFIG_ID,
                target_id=target_id,
                scanner_id=settings.GCE_SCANNER_ID,
                comment=task_comment
            )
            
            task_id = response.get('id')
            logger.info(f"Created GCE task with ID: {task_id}")
            return task_id
            
        except Exception as e:
            logger.error(f"Failed to create GCE task: {str(e)}")
            raise
    
    def start_gce_scan(self, gmp, task_id):
        """Start the scan task in GCE"""
        try:
            logger.info(f"Starting GCE scan for task: {task_id}")
            gmp.start_task(task_id)
            logger.info(f"GCE scan started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start GCE scan: {str(e)}")
            raise
    
    def monitor_scan_progress(self, gmp, task_id, scan_id):
        """Monitor scan progress and wait for completion"""
        start_time = time.time()
        last_progress = -1
        
        while True:
            try:
                # Check if we should stop
                if self.should_stop:
                    logger.info("Stopping scan monitoring due to shutdown signal")
                    return None
                
                # Check timeout
                elapsed_time = time.time() - start_time
                if elapsed_time > settings.GCE_MAX_SCAN_TIME:
                    logger.error(f"Scan timeout reached ({settings.GCE_MAX_SCAN_TIME}s)")
                    return None
                
                # Get task status
                response = gmp.get_task(task_id)
                task = response.find('task')
                
                if task is None:
                    logger.error("Failed to get task status")
                    return None
                
                status = task.find('status').text
                progress = int(task.find('progress').text)
                
                # Log progress if changed
                if progress != last_progress:
                    logger.info(f"Scan progress: {progress}% (status: {status})")
                    last_progress = progress
                    
                    # Send progress update to API
                    self.update_scan_progress(scan_id, task_id, progress, status)
                
                # Check if scan is complete
                if status in ['Done', 'Stopped', 'Interrupted']:
                    logger.info(f"Scan completed with status: {status}")
                    
                    # Get report ID
                    last_report = task.find('last_report')
                    if last_report is not None:
                        report_element = last_report.find('report')
                        if report_element is not None:
                            report_id = report_element.get('id')
                            logger.info(f"Report ID: {report_id}")
                            return report_id
                    
                    logger.warning("No report found for completed scan")
                    return None
                
                # Wait before next check
                time.sleep(settings.GCE_POLLING_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error monitoring scan progress: {str(e)}")
                time.sleep(settings.GCE_POLLING_INTERVAL)
    
    def get_scan_report(self, gmp, report_id):
        """Get the full scan report from GCE"""
        try:
            logger.info(f"Retrieving report: {report_id}")
            
            # Get report in specified format
            if settings.GCE_REPORT_FORMAT == 'XML':
                response = gmp.get_report(report_id, details=True)
                # Convert etree to string
                import xml.etree.ElementTree as ET
                report_xml = ET.tostring(response, encoding='unicode')
                return report_xml
            else:
                # For JSON, we need to convert XML to JSON
                response = gmp.get_report(report_id, details=True)
                import xml.etree.ElementTree as ET
                report_xml = ET.tostring(response, encoding='unicode')
                report_dict = xmltodict.parse(report_xml)
                return json.dumps(report_dict, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to get scan report: {str(e)}")
            raise
    
    def update_scan_progress(self, scan_id, task_id, progress, status):
        """Update scan progress in backend"""
        try:
            url = f"{settings.INTERNAL_API_GATEWAY_URL}/api/orchestrator/scans/{scan_id}/gce-progress/"
            data = {
                'gce_task_id': task_id,
                'gce_scan_progress': progress,
                'gce_scan_status': status
            }
            
            response = requests.patch(url, json=data, timeout=settings.API_TIMEOUT)
            response.raise_for_status()
            
        except Exception as e:
            logger.error(f"Failed to update scan progress: {str(e)}")
    
    def send_results_to_api(self, scan_id, results_data):
        """Send scan results to API"""
        try:
            url = f"{settings.INTERNAL_API_GATEWAY_URL}/api/orchestrator/scans/{scan_id}/gce-results/"
            
            response = requests.post(url, json=results_data, timeout=settings.API_TIMEOUT)
            response.raise_for_status()
            
            logger.info(f"Successfully sent GCE results for scan {scan_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send results to API: {str(e)}")
            return False
    
    def process_scan_request(self, channel, method, properties, body):
        """Process incoming scan request"""
        try:
            # Parse message
            message = json.loads(body.decode('utf-8'))
            scan_id = message['scan_id']
            target_id = message['target_id']
            target_host = message['target_host']
            
            logger.info(f"Processing GCE scan request for scan {scan_id}, target {target_host}")
            
            self.current_scan_id = scan_id
            self.publish_status_update(scan_id, 'running', 'Starting GCE scan')
            
            # Connect to GCE
            with self.connect_gce() as gmp:
                # Authenticate
                gmp.authenticate(settings.GCE_USERNAME, settings.GCE_PASSWORD)
                logger.info("Authenticated with GCE successfully")
                
                # Get target details from API
                target_url = f"{settings.INTERNAL_API_GATEWAY_URL}/api/orchestrator/targets/{target_id}/"
                target_response = requests.get(target_url, timeout=settings.API_TIMEOUT)
                target_data = target_response.json()
                
                # Create target in GCE
                gce_target_id = self.create_gce_target(gmp, target_host, target_data.get('name', 'Unknown'))
                
                # Create scan task
                gce_task_id = self.create_gce_task(gmp, gce_target_id, f"Scan {scan_id}")
                
                # Update backend with GCE IDs
                self.update_scan_progress(scan_id, gce_task_id, 0, 'Created')
                
                # Start scan
                self.start_gce_scan(gmp, gce_task_id)
                
                # Record start time
                start_time = datetime.utcnow()
                
                # Monitor scan progress
                report_id = self.monitor_scan_progress(gmp, gce_task_id, scan_id)
                
                if report_id:
                    # Get full report
                    report_content = self.get_scan_report(gmp, report_id)
                    
                    # Prepare results
                    results_data = {
                        'gce_task_id': gce_task_id,
                        'gce_report_id': report_id,
                        'gce_target_id': gce_target_id,
                        'report_format': settings.GCE_REPORT_FORMAT,
                        'full_report': report_content,
                        'gce_scan_started_at': start_time.isoformat(),
                        'gce_scan_completed_at': datetime.utcnow().isoformat()
                    }
                    
                    # Send results to API
                    if self.send_results_to_api(scan_id, results_data):
                        self.publish_status_update(scan_id, 'completed', 'GCE scan completed successfully')
                        channel.basic_ack(delivery_tag=method.delivery_tag)
                    else:
                        self.publish_status_update(scan_id, 'error', error_details='Failed to send results to API')
                        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                else:
                    self.publish_status_update(scan_id, 'error', error_details='Scan failed or timed out')
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            
            self.current_scan_id = None
            
        except GvmError as e:
            logger.error(f"GCE API error: {str(e)}")
            if self.current_scan_id:
                self.publish_status_update(self.current_scan_id, 'error', error_details=f"GCE error: {str(e)}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            
        except Exception as e:
            logger.error(f"Error processing scan request: {str(e)}")
            logger.error(traceback.format_exc())
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
                queue=settings.GCE_SCAN_REQUEST_QUEUE,
                on_message_callback=self.process_scan_request,
                auto_ack=False
            )
            
            logger.info(f"GCE Scanner started, waiting for messages on {settings.GCE_SCAN_REQUEST_QUEUE}")
            
            # Start consuming
            self.channel.start_consuming()
            
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
            self.channel.stop_consuming()
            
        except Exception as e:
            logger.error(f"Error in consumer: {str(e)}")
            return False
            
        finally:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            logger.info("GCE Scanner stopped")


def main():
    """Main entry point"""
    logger.info("Starting GCE Scanner...")
    
    scanner = GCEScanner()
    
    # Retry connection if it fails
    retry_count = 0
    while retry_count < settings.MAX_RETRIES:
        try:
            scanner.start_consuming()
            break
        except Exception as e:
            retry_count += 1
            logger.error(f"Failed to start scanner (attempt {retry_count}/{settings.MAX_RETRIES}): {str(e)}")
            if retry_count < settings.MAX_RETRIES:
                time.sleep(settings.RETRY_DELAY)
            else:
                logger.error("Max retries reached. Exiting.")
                sys.exit(1)


if __name__ == "__main__":
    main()