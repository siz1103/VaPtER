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
            
            logger.info(f"Nmap scan completed for scan {scan.id}")
            logger.info(f"Plugin status - Finger: {scan_type.plugin_finger}, Enum: {scan_type.plugin_enum}, "
                       f"Web: {scan_type.plugin_web}, Vuln: {scan_type.plugin_vuln_lookup}")
            
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
                
                logger.info(f"Scan {scan.id} completed - no more plugins to run")
                
                # TODO: Start report generation if enabled
                # ScanOrchestratorService._start_report_generation(scan)
                
                return True
                
        except Exception as e:
            logger.error(f"Error processing nmap completion for scan {scan.id}: {str(e)}")
            return False
    
    @staticmethod
    def process_fingerprint_completion(scan):
        """Process fingerprint scan completion and start next phase"""
        try:
            scan_type = scan.scan_type
            
            logger.info(f"Fingerprint scan completed for scan {scan.id}")
            
            # Update status
            scan.status = 'Finger Scan Completed'
            scan.save()
            
            # Check which plugin should run next
            next_plugin = None
            
            if scan_type.plugin_enum and not scan.parsed_enum_results:
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
                
                logger.info(f"Scan {scan.id} completed after fingerprinting")
                
                return True
                
        except Exception as e:
            logger.error(f"Error processing fingerprint completion for scan {scan.id}: {str(e)}")
            return False
        
    @staticmethod
    def process_plugin_completion(scan, plugin_name):
        """Process plugin completion and start next phase"""
        try:
            scan_type = scan.scan_type
            
            # TEMPORARY: Skip until plugins are implemented
            logger.warning(f"Plugin completion called for {plugin_name} but plugins not implemented yet")
            scan.status = 'Completed'
            scan.completed_at = timezone.now()
            scan.save()
            return True
            
            # TODO: Re-enable when plugins are implemented
            """
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
                # ScanOrchestratorService._start_report_generation(scan)
                
                return True
            """
                
        except Exception as e:
            logger.error(f"Error processing {plugin_name} completion for scan {scan.id}: {str(e)}")
            return False
    
    @staticmethod
    def _start_plugin_scan(scan, plugin_name):
        """Start a specific plugin scan"""
        try:
            queue_mapping = {
                'fingerprint': 'fingerprint_scan_requests',
                'enum': 'enum_scan_requests',
                'web': 'web_scan_requests',
                'vuln_lookup': 'vuln_lookup_requests'
            }
            
            status_mapping = {
                'fingerprint': 'Finger Scan Running',
                'enum': 'Enum Scan Running',
                'web': 'Web Scan Running',
                'vuln_lookup': 'Vuln Lookup Running'
            }
            
            queue_name = queue_mapping.get(plugin_name)
            new_status = status_mapping.get(plugin_name)
            
            if not queue_name or not new_status:
                logger.error(f"Unknown plugin: {plugin_name}")
                return False
            
            # Update scan status
            scan.status = new_status
            scan.save()
            
            # Prepare message for plugin
            message = {
                'scan_id': scan.id,
                'target_id': scan.target.id,
                'target_host': scan.target.address,
                'plugin': plugin_name,
                'timestamp': timezone.now().isoformat()
            }
            
            logger.info(f"queue_name: {queue_name}")
            logger.info(f"message: {message}")
            # Send to appropriate queue
            return RabbitMQService.publish_message(queue_name, message)
            
        except Exception as e:
            logger.error(f"Error starting {plugin_name} scan for scan {scan.id}: {str(e)}")
            return False
    
    @staticmethod
    def _start_report_generation(scan):
        """Start report generation"""
        try:
            # TEMPORARY: Skip report generation
            logger.warning(f"Report generation requested for scan {scan.id} but not implemented")
            return False
            
            # TODO: Re-enable when report generator is implemented
            """
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
            """
            
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
                    
                    # Process nmap completion
                    ScanOrchestratorService.process_nmap_completion(scan)
                    
                elif status == 'failed':
                    scan.status = 'Failed'
                    scan.error_message = error_details or message or 'Nmap scan failed'
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
                    
                    # Process plugin completion
                    ScanOrchestratorService.process_plugin_completion(scan, 'fingerprint')
                    
                elif status == 'failed':
                    scan.status = 'Failed'
                    scan.error_message = error_details or message or 'Fingerprint scan failed'
                    scan.completed_at = timezone.now()

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
                    
                    # Process plugin completion
                    ScanOrchestratorService.process_plugin_completion(scan, 'enum')
                    
                elif status == 'failed':
                    scan.status = 'Failed'
                    scan.error_message = error_details or message or 'Enumeration scan failed'
                    scan.completed_at = timezone.now()

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
                    
                    # Process plugin completion
                    ScanOrchestratorService.process_plugin_completion(scan, 'web')
                    
                elif status == 'failed':
                    scan.status = 'Failed'
                    scan.error_message = error_details or message or 'Web scan failed'
                    scan.completed_at = timezone.now()

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
                    
                    # Process plugin completion
                    ScanOrchestratorService.process_plugin_completion(scan, 'vuln_lookup')
                    
                elif status == 'failed':
                    scan.status = 'Failed'
                    scan.error_message = error_details or message or 'Vulnerability lookup failed'
                    scan.completed_at = timezone.now()

            elif module == 'report':
                if status == 'running':
                    scan.status = 'Report Generation Running'
                elif status == 'completed':
                    scan.status = 'Completed'
                    scan.completed_at = timezone.now()
                elif status == 'failed':
                    scan.status = 'Failed'
                    scan.error_message = error_details or message or 'Report generation failed'
                    scan.completed_at = timezone.now()




            # Save scan changes
            scan.save()


            logger.info(f"Updated scan {scan_id} status for module {module}: {status}")
            return True

        except Scan.DoesNotExist:
            logger.error(f"Scan {scan_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error updating scan status: {str(e)}")
            return False
        
class NmapResultsParser:
    """Service for parsing nmap results and extracting relevant data"""
    
    @staticmethod
    def extract_open_ports(parsed_nmap_results):
        """
        Extract open ports from nmap results
        
        Returns:
            dict: {"tcp": [...], "udp": [...]}
        """
        open_ports = {"tcp": [], "udp": []}
        
        try:
            if not parsed_nmap_results or 'hosts' not in parsed_nmap_results:
                return open_ports
            
            # Assumiamo sempre un singolo host
            hosts = parsed_nmap_results.get('hosts', [])
            if not hosts:
                return open_ports
            
            host = hosts[0]  # Prendiamo sempre il primo host
            ports = host.get('ports', [])
            
            for port in ports:
                protocol = port.get('protocol', 'tcp')
                port_data = {
                    'port': int(port.get('portid', 0)),
                    'state': port.get('state', 'unknown')
                }
                
                # Aggiungi informazioni sul servizio se disponibili
                service = port.get('service', {})
                if service:
                    port_data['service'] = service.get('name', '')
                    if service.get('product'):
                        port_data['product'] = service.get('product')
                    if service.get('version'):
                        port_data['version'] = service.get('version')
                    if service.get('extrainfo'):
                        port_data['extrainfo'] = service.get('extrainfo')
                
                # Aggiungi solo porte aperte
                if port_data['state'] == 'open':
                    if protocol == 'tcp':
                        open_ports['tcp'].append(port_data)
                    elif protocol == 'udp':
                        open_ports['udp'].append(port_data)
            
            # Ordina le porte per numero
            open_ports['tcp'].sort(key=lambda x: x['port'])
            open_ports['udp'].sort(key=lambda x: x['port'])
            
            logger.info(f"Extracted {len(open_ports['tcp'])} TCP and {len(open_ports['udp'])} UDP open ports")
            
        except Exception as e:
            logger.error(f"Error extracting open ports: {str(e)}")
        
        return open_ports
    
    @staticmethod
    def extract_os_guess(parsed_nmap_results):
        """
        Extract OS guess from nmap results
        
        Returns:
            dict: OS information or empty dict
        """
        os_guess = {}
        
        try:
            if not parsed_nmap_results or 'hosts' not in parsed_nmap_results:
                return os_guess
            
            # Assumiamo sempre un singolo host
            hosts = parsed_nmap_results.get('hosts', [])
            if not hosts:
                return os_guess
            
            host = hosts[0]  # Prendiamo sempre il primo host
            os_info = host.get('os', {})
            
            if os_info:
                # Estrai informazioni OS
                os_guess = {
                    'name': os_info.get('name', ''),
                    'accuracy': os_info.get('accuracy', ''),
                    'line': os_info.get('line', '')
                }
                
                # Aggiungi informazioni aggiuntive se disponibili
                if os_info.get('vendor'):
                    os_guess['vendor'] = os_info.get('vendor')
                if os_info.get('type'):
                    os_guess['type'] = os_info.get('type')
                if os_info.get('osfamily'):
                    os_guess['osfamily'] = os_info.get('osfamily')
                if os_info.get('osgen'):
                    os_guess['osgen'] = os_info.get('osgen')
                
                logger.info(f"Extracted OS guess: {os_guess.get('name', 'Unknown')} with {os_guess.get('accuracy', '0')}% accuracy")
            
        except Exception as e:
            logger.error(f"Error extracting OS guess: {str(e)}")
        
        return os_guess
    
    @staticmethod
    def process_nmap_results(scan):
        """
        Process nmap results and update ScanDetail
        
        Args:
            scan: Scan instance with parsed_nmap_results
        """
        try:
            if not scan.parsed_nmap_results:
                logger.warning(f"No nmap results to process for scan {scan.id}")
                return
            
            # Crea o ottieni ScanDetail
            scan_detail, created = ScanDetail.objects.get_or_create(scan=scan)
            
            # Estrai porte aperte
            open_ports = NmapResultsParser.extract_open_ports(scan.parsed_nmap_results)
            scan_detail.open_ports = open_ports
            
            # Estrai OS guess
            os_guess = NmapResultsParser.extract_os_guess(scan.parsed_nmap_results)
            scan_detail.os_guess = os_guess
            
            # Salva
            scan_detail.save()
            
            logger.info(f"Successfully processed nmap results for scan {scan.id}")
            
        except Exception as e:
            logger.error(f"Error processing nmap results for scan {scan.id}: {str(e)}")