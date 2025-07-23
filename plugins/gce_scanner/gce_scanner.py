# plugins/gce_scanner/gce_scanner.py

"""
GCE (Greenbone Community Edition) Scanner Plugin

This plugin integrates with GCE to perform vulnerability scans on targets
that have already been scanned with nmap (and optionally fingerprinted).
"""

import json
import logging
import sys
import time
import traceback
from datetime import datetime
import xml.etree.ElementTree as ET

import pika
import pika.exceptions
import requests
import xmltodict
from gvm.connections import UnixSocketConnection
from gvm.errors import GvmError
from gvm.protocols.gmp import Gmp
from gvm.transforms import EtreeTransform

from config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class GCEScanner:
    """GCE Scanner implementation"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.current_scan_id = None
        self.should_stop = False
        # Separate connection for publishing updates
        self.publisher_connection = None
        self.publisher_channel = None
    
    def connect_rabbitmq(self):
        """Connect to RabbitMQ with proper heartbeat configuration"""
        try:
            # Parse the URL to add heartbeat parameter
            params = pika.URLParameters(settings.RABBITMQ_URL)
            
            # Set heartbeat to 600 seconds (10 minutes) to handle long operations
            params.heartbeat = 600
            
            # Set connection timeout
            params.connection_attempts = 3
            params.retry_delay = 2
            
            # Establish connection
            self.connection = pika.BlockingConnection(params)
            self.channel = self.connection.channel()
            
            # Ensure queue exists - use passive to check if exists
            try:
                self.channel.queue_declare(
                    queue=settings.GCE_SCAN_REQUEST_QUEUE,
                    durable=True,
                    passive=True  # Don't try to create, just check if exists
                )
            except pika.exceptions.ChannelClosedByBroker:
                # Queue doesn't exist, create it without extra arguments
                self.channel = self.connection.channel()
                self.channel.queue_declare(
                    queue=settings.GCE_SCAN_REQUEST_QUEUE,
                    durable=True
                )
            
            logger.info("Connected to RabbitMQ successfully with heartbeat=600s")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            return False
    
    def connect_publisher(self):
        """Create a separate connection for publishing status updates"""
        try:
            params = pika.URLParameters(settings.RABBITMQ_URL)
            params.heartbeat = 600
            
            self.publisher_connection = pika.BlockingConnection(params)
            self.publisher_channel = self.publisher_connection.channel()
            
            # Ensure status update queue exists
            try:
                self.publisher_channel.queue_declare(
                    queue=settings.SCAN_STATUS_UPDATE_QUEUE,
                    durable=True,
                    passive=True
                )
            except pika.exceptions.ChannelClosedByBroker:
                # Queue doesn't exist, create it
                self.publisher_channel = self.publisher_connection.channel()
                self.publisher_channel.queue_declare(
                    queue=settings.SCAN_STATUS_UPDATE_QUEUE,
                    durable=True
                )
            
            logger.info("Publisher connection established")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create publisher connection: {str(e)}")
            return False
    
    def ensure_publisher_connection(self):
        """Ensure publisher connection is active, reconnect if needed"""
        try:
            if self.publisher_connection and not self.publisher_connection.is_closed:
                # Test the connection with a passive declare
                self.publisher_channel.queue_declare(
                    queue=settings.SCAN_STATUS_UPDATE_QUEUE,
                    durable=True,
                    passive=True
                )
                return True
        except:
            pass
        
        # Connection is dead, reconnect
        logger.info("Publisher connection lost, reconnecting...")
        return self.connect_publisher()
    
    def connect_gce(self):
        """Connect to GCE via Unix socket"""
        try:
            logger.info(f"Connecting to GCE via socket: {settings.GCE_SOCKET_PATH}")
            connection = UnixSocketConnection(path=settings.GCE_SOCKET_PATH)
            transform = EtreeTransform()
            gmp = Gmp(connection, transform=transform)
            return gmp
            
        except Exception as e:
            logger.error(f"Failed to connect to GCE: {str(e)}")
            raise
    
    def publish_status_update(self, scan_id, status, message='', error_details=None):
        """Publish scan status update to RabbitMQ with connection handling"""
        try:
            # Ensure publisher connection is active
            if not self.ensure_publisher_connection():
                logger.error("Failed to establish publisher connection")
                return
            
            update_message = {
                'scan_id': scan_id,
                'status': status,
                'plugin': 'gce',
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if message:
                update_message['message'] = message
            if error_details:
                update_message['error_details'] = error_details
            
            self.publisher_channel.basic_publish(
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
            # Don't raise exception to avoid interrupting the main flow
    
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
                progress_element = task.find('progress')
                
                # Handle progress value correctly
                if progress_element is not None and progress_element.text:
                    try:
                        progress = int(progress_element.text)
                        # Ensure progress is within valid range
                        progress = max(0, min(100, progress))
                    except ValueError:
                        progress = 0
                else:
                    progress = 0
                
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
                report_xml = ET.tostring(response, encoding='unicode')
                return report_xml
            else:
                # For JSON, we need to convert XML to JSON
                response = gmp.get_report(report_id, details=True)
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
                'gce_task_id': str(task_id),
                'gce_scan_progress': progress,
                'gce_scan_status': status
            }
            
            response = requests.patch(url, json=data, timeout=settings.API_TIMEOUT)
            response.raise_for_status()
            
        except Exception as e:
            logger.error(f"Failed to update scan progress: {e}")
    
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
                    logger.info(f"GCE Report XML: {report_content}")
                    
                    # Prepare results
                    results_data = {
                        'gce_task_id': str(gce_task_id),
                        'gce_report_id': str(report_id),
                        'gce_target_id': str(gce_target_id),
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
            # Connect to RabbitMQ
            if not self.connect_rabbitmq():
                return False
            
            # Connect publisher
            if not self.connect_publisher():
                return False
            
            # Set QoS
            self.channel.basic_qos(prefetch_count=1)
            
            # Setup consumer with proper error handling
            def safe_callback(channel, method, properties, body):
                try:
                    self.process_scan_request(channel, method, properties, body)
                except Exception as e:
                    logger.error(f"Unhandled exception in callback: {str(e)}")
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            
            # Start consuming
            self.channel.basic_consume(
                queue=settings.GCE_SCAN_REQUEST_QUEUE,
                on_message_callback=safe_callback,
                auto_ack=False
            )
            
            logger.info(f"GCE Scanner started, waiting for messages on {settings.GCE_SCAN_REQUEST_QUEUE}")
            
            # Start consuming with periodic connection check
            while True:
                try:
                    self.channel.start_consuming()
                except pika.exceptions.ConnectionClosed:
                    logger.warning("RabbitMQ connection lost, reconnecting...")
                    time.sleep(5)
                    if not self.connect_rabbitmq():
                        logger.error("Failed to reconnect to RabbitMQ")
                        break
                except KeyboardInterrupt:
                    logger.info("Interrupted by user")
                    break
                except Exception as e:
                    logger.error(f"Unexpected error: {str(e)}")
                    time.sleep(5)
            
        except Exception as e:
            logger.error(f"Error in consumer: {str(e)}")
            return False
            
        finally:
            self.cleanup_connections()
            logger.info("GCE Scanner stopped")
    
    def cleanup_connections(self):
        """Clean up all connections"""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.stop_consuming()
                self.channel.close()
        except:
            pass
        
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except:
            pass
        
        try:
            if self.publisher_channel and not self.publisher_channel.is_closed:
                self.publisher_channel.close()
        except:
            pass
        
        try:
            if self.publisher_connection and not self.publisher_connection.is_closed:
                self.publisher_connection.close()
        except:
            pass


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