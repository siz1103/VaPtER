import json
import logging
import pika
from django.conf import settings
from django.utils import timezone
from .models import Scan, ScanDetail

logger = logging.getLogger(__name__)


class RabbitMQService:
    """Service for RabbitMQ communication"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
    
    def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            # Parse RabbitMQ URL
            parameters = pika.URLParameters(settings.RABBITMQ_URL)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare all queues
            self._declare_queues()
            
            logger.info("Connected to RabbitMQ successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            return False
    
    def _declare_queues(self):
        """Declare all required queues"""
        queues = [
            settings.RABBITMQ_NMAP_SCAN_REQUEST_QUEUE,
            settings.RABBITMQ_ENUM_SCAN_REQUEST_QUEUE,
            settings.RABBITMQ_FINGERPRINT_SCAN_REQUEST_QUEUE,
            settings.RABBITMQ_WEB_SCAN_REQUEST_QUEUE,
            settings.RABBITMQ_VULN_LOOKUP_REQUEST_QUEUE,
            settings.RABBITMQ_REPORT_REQUEST_QUEUE,
            settings.RABBITMQ_SCAN_STATUS_UPDATE_QUEUE,
        ]
        
        for queue in queues:
            self.channel.queue_declare(queue=queue, durable=True)
    
    def publish_message(self, queue_name, message):
        """Publish a message to a queue"""
        try:
            if not self.connection or self.connection.is_closed:
                if not self.connect():
                    return False
            
            # Ensure message is JSON string
            if isinstance(message, dict):
                message = json.dumps(message)
            
            self.channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=message,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                )
            )
            
            logger.info(f"Published message to queue {queue_name}: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish message to {queue_name}: {str(e)}")
            return False
    
    def close(self):
        """Close RabbitMQ connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {str(e)}")


class ScanOrchestratorService:
    """Service for orchestrating scan workflows"""
    
    @staticmethod
    def start_scan(scan):
        """Start a scan by publishing to appropriate queue"""
        try:
            # Update scan status
            scan.status = 'Queued'
            scan.started_at = timezone.now()
            scan.save()
            
            # Create scan details record
            scan_detail, created = ScanDetail.objects.get_or_create(scan=scan)
            
            # Prepare message for nmap scanner
            message = {
                'scan_id': scan.id,
                'scan_type_id': scan.scan_type.id,
                'target_host': scan.target.address,
                'target_name': scan.target.name,
                'customer_id': str(scan.target.customer.id),
                'timestamp': timezone.now().isoformat()
            }
            
            # Publish to nmap queue
            rabbitmq_service = RabbitMQService()
            success = rabbitmq_service.publish_message(
                settings.RABBITMQ_NMAP_SCAN_REQUEST_QUEUE,
                message
            )
            
            if success:
                logger.info(f"Successfully queued scan {scan.id} for target {scan.target.address}")
            else:
                # Failed to queue, mark as failed
                scan.status = 'Failed'
                scan.error_message = 'Failed to queue scan in RabbitMQ'
                scan.save()
                logger.error(f"Failed to queue scan {scan.id}")
            
            rabbitmq_service.close()
            return success
            
        except Exception as e:
            logger.error(f"Error starting scan {scan.id}: {str(e)}")
            scan.status = 'Failed'
            scan.error_message = f'Error starting scan: {str(e)}'
            scan.save()
            return False
    
    @staticmethod
    def process_nmap_completion(scan):
        """Process nmap scan completion and start next phase"""
        try:
            scan_type = scan.scan_type
            
            # Check which plugins should run next
            next_plugin = None
            
            if scan_type.plugin_finger and not scan.parsed_finger_results:
                next_plugin = 'fingerprint'
            elif scan_type.plugin_enum and not scan.parsed_enum_results:
                next_plugin = 'enum'
            elif scan_type.plugin_web and not scan.parsed_web_results:
                next_plugin = 'web'
            elif scan_type.plugin_vuln_lookup and not scan.parsed_vuln_results:
                next_plugin = 'vuln_lookup'
            
            if next_plugin:
                return ScanOrchestratorService._start_plugin_scan(scan, next_plugin)
            else:
                # No more plugins, mark as completed
                scan.status = 'Completed'
                scan.completed_at = timezone.now()
                scan.save()
                
                # Start report generation if enabled
                ScanOrchestratorService._start_report_generation(scan)
                
                return True
                
        except Exception as e:
            logger.error(f"Error processing nmap completion for scan {scan.id}: {str(e)}")
            return False
    
    @staticmethod
    def process_plugin_completion(scan, plugin_name):
        """Process plugin completion and start next phase"""
        try:
            scan_type = scan.scan_type
            
            # Determine next plugin based on current one
            next_plugin = None
            
            if plugin_name == 'fingerprint' and scan_type.plugin_enum and not scan.parsed_enum_results:
                next_plugin = 'enum'
            elif plugin_name in ['fingerprint', 'enum'] and scan_type.plugin_web and not scan.parsed_web_results:
                next_plugin = 'web'
            elif plugin_name in ['fingerprint', 'enum', 'web'] and scan_type.plugin_vuln_lookup and not scan.parsed_vuln_results:
                next_plugin = 'vuln_lookup'
            
            if next_plugin:
                return ScanOrchestratorService._start_plugin_scan(scan, next_plugin)
            else:
                # All plugins completed
                scan.status = 'Completed'
                scan.completed_at = timezone.now()
                scan.save()
                
                # Start report generation
                ScanOrchestratorService._start_report_generation(scan)
                
                return True
                
        except Exception as e:
            logger.error(f"Error processing {plugin_name} completion for scan {scan.id}: {str(e)}")
            return False
    
    @staticmethod
    def _start_plugin_scan(scan, plugin_name):
        """Start a specific plugin scan"""
        try:
            # Map plugin names to queues and status
            plugin_config = {
                'fingerprint': {
                    'queue': settings.RABBITMQ_FINGERPRINT_SCAN_REQUEST_QUEUE,
                    'status': 'Finger Scan Running'
                },
                'enum': {
                    'queue': settings.RABBITMQ_ENUM_SCAN_REQUEST_QUEUE,
                    'status': 'Enum Scan Running'
                },
                'web': {
                    'queue': settings.RABBITMQ_WEB_SCAN_REQUEST_QUEUE,
                    'status': 'Web Scan Running'
                },
                'vuln_lookup': {
                    'queue': settings.RABBITMQ_VULN_LOOKUP_REQUEST_QUEUE,
                    'status': 'Vuln Lookup Running'
                }
            }
            
            if plugin_name not in plugin_config:
                logger.error(f"Unknown plugin: {plugin_name}")
                return False
            
            config = plugin_config[plugin_name]
            
            # Update scan status
            scan.status = config['status']
            scan.save()
            
            # Prepare message
            message = {
                'scan_id': scan.id,
                'target_host': scan.target.address,
                'target_name': scan.target.name,
                'nmap_results': scan.parsed_nmap_results,
                'timestamp': timezone.now().isoformat()
            }
            
            # Publish to plugin queue
            rabbitmq_service = RabbitMQService()
            success = rabbitmq_service.publish_message(config['queue'], message)
            rabbitmq_service.close()
            
            if success:
                logger.info(f"Started {plugin_name} scan for scan {scan.id}")
            else:
                scan.status = 'Failed'
                scan.error_message = f'Failed to start {plugin_name} scan'
                scan.save()
            
            return success
            
        except Exception as e:
            logger.error(f"Error starting {plugin_name} scan for scan {scan.id}: {str(e)}")
            return False
    
    @staticmethod
    def _start_report_generation(scan):
        """Start report generation"""
        try:
            message = {
                'scan_id': scan.id,
                'timestamp': timezone.now().isoformat()
            }
            
            rabbitmq_service = RabbitMQService()
            success = rabbitmq_service.publish_message(
                settings.RABBITMQ_REPORT_REQUEST_QUEUE,
                message
            )
            rabbitmq_service.close()
            
            if success:
                scan.status = 'Report Generation Running'
                scan.save()
                logger.info(f"Started report generation for scan {scan.id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error starting report generation for scan {scan.id}: {str(e)}")
            return False


class ScanStatusService:
    """Service for updating scan status based on RabbitMQ messages"""
    
    @staticmethod
    def update_scan_status(scan_id, module, status, message=None, error_details=None):
        """Update scan status based on module status update"""
        try:
            scan = Scan.objects.get(id=scan_id)
            scan_detail = scan.details if hasattr(scan, 'details') else None
            
            # Update status based on module and status
            if module == 'nmap':
                if status == 'running':
                    scan.status = 'Nmap Scan Running'
                    if scan_detail:
                        scan_detail.nmap_started_at = timezone.now()
                        scan_detail.save()
                elif status == 'completed':
                    scan.status = 'Nmap Scan Completed'
                    if scan_detail:
                        scan_detail.nmap_completed_at = timezone.now()
                        scan_detail.save()
                    # Process next phase
                    ScanOrchestratorService.process_nmap_completion(scan)
                elif status == 'error':
                    scan.status = 'Failed'
                    scan.error_message = error_details or 'Nmap scan failed'
                    scan.completed_at = timezone.now()
            
            elif module == 'fingerprint':
                if status == 'running':
                    scan.status = 'Finger Scan Running'
                    if scan_detail:
                        scan_detail.finger_started_at = timezone.now()
                        scan_detail.save()
                elif status == 'completed':
                    scan.status = 'Finger Scan Completed'
                    if scan_detail:
                        scan_detail.finger_completed_at = timezone.now()
                        scan_detail.save()
                    ScanOrchestratorService.process_plugin_completion(scan, 'fingerprint')
                elif status == 'error':
                    scan.status = 'Failed'
                    scan.error_message = error_details or 'Fingerprint scan failed'
            
            elif module == 'enum':
                if status == 'running':
                    scan.status = 'Enum Scan Running'
                    if scan_detail:
                        scan_detail.enum_started_at = timezone.now()
                        scan_detail.save()
                elif status == 'completed':
                    scan.status = 'Enum Scan Completed'
                    if scan_detail:
                        scan_detail.enum_completed_at = timezone.now()
                        scan_detail.save()
                    ScanOrchestratorService.process_plugin_completion(scan, 'enum')
                elif status == 'error':
                    scan.status = 'Failed'
                    scan.error_message = error_details or 'Enumeration scan failed'
            
            elif module == 'web':
                if status == 'running':
                    scan.status = 'Web Scan Running'
                    if scan_detail:
                        scan_detail.web_started_at = timezone.now()
                        scan_detail.save()
                elif status == 'completed':
                    scan.status = 'Web Scan Completed'
                    if scan_detail:
                        scan_detail.web_completed_at = timezone.now()
                        scan_detail.save()
                    ScanOrchestratorService.process_plugin_completion(scan, 'web')
                elif status == 'error':
                    scan.status = 'Failed'
                    scan.error_message = error_details or 'Web scan failed'
            
            elif module == 'vuln_lookup':
                if status == 'running':
                    scan.status = 'Vuln Lookup Running'
                    if scan_detail:
                        scan_detail.vuln_started_at = timezone.now()
                        scan_detail.save()
                elif status == 'completed':
                    scan.status = 'Vuln Lookup Completed'
                    if scan_detail:
                        scan_detail.vuln_completed_at = timezone.now()
                        scan_detail.save()
                    ScanOrchestratorService.process_plugin_completion(scan, 'vuln_lookup')
                elif status == 'error':
                    scan.status = 'Failed'
                    scan.error_message = error_details or 'Vulnerability lookup failed'
            
            elif module == 'report':
                if status == 'running':
                    scan.status = 'Report Generation Running'
                elif status == 'completed':
                    scan.status = 'Completed'
                    scan.completed_at = timezone.now()
                elif status == 'error':
                    # Report generation failure shouldn't fail the entire scan
                    # Just log the error but keep scan as completed
                    logger.error(f"Report generation failed for scan {scan_id}: {error_details}")
                    if scan.status == 'Report Generation Running':
                        scan.status = 'Completed'
                        scan.completed_at = timezone.now()
            
            scan.save()
            logger.info(f"Updated scan {scan_id} status: {module} -> {status}")
            
            return True
            
        except Scan.DoesNotExist:
            logger.error(f"Scan {scan_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error updating scan {scan_id} status: {str(e)}")
            return False