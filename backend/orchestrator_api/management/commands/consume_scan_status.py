import json
import logging
import signal
import sys
import pika
from django.core.management.base import BaseCommand
from django.conf import settings
from orchestrator_api.services import ScanStatusService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Django management command to consume scan status updates from RabbitMQ
    
    Usage: python manage.py consume_scan_status
    """
    
    help = 'Consume scan status updates from RabbitMQ'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.connection = None
        self.channel = None
        self.should_stop = False
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--queue',
            type=str,
            default=settings.RABBITMQ_SCAN_STATUS_UPDATE_QUEUE,
            help='Queue name to consume from'
        )
        parser.add_argument(
            '--prefetch',
            type=int,
            default=1,
            help='Number of messages to prefetch'
        )
    
    def handle(self, *args, **options):
        """Main command handler"""
        self.stdout.write(
            self.style.SUCCESS('Starting scan status consumer...')
        )
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # Connect to RabbitMQ
        if not self._connect_rabbitmq():
            self.stdout.write(
                self.style.ERROR('Failed to connect to RabbitMQ')
            )
            return
        
        # Setup queue and start consuming
        queue_name = options['queue']
        prefetch_count = options['prefetch']
        
        try:
            # Declare queue (in case it doesn't exist)
            self.channel.queue_declare(queue=queue_name, durable=True)
            
            # Set QoS
            self.channel.basic_qos(prefetch_count=prefetch_count)
            
            # Setup consumer
            self.channel.basic_consume(
                queue=queue_name,
                on_message_callback=self._process_message,
                auto_ack=False
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'Consuming from queue: {queue_name}')
            )
            self.stdout.write(
                self.style.SUCCESS('Waiting for messages. To exit press CTRL+C')
            )
            
            # Start consuming
            while not self.should_stop:
                try:
                    self.connection.process_data_events(time_limit=1)
                except KeyboardInterrupt:
                    break
            
        except Exception as e:
            logger.error(f"Error in consumer: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'Consumer error: {str(e)}')
            )
        finally:
            self._cleanup()
    
    def _connect_rabbitmq(self):
        """Connect to RabbitMQ"""
        try:
            parameters = pika.URLParameters(settings.RABBITMQ_URL)
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            logger.info("Connected to RabbitMQ")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            return False
    
    def _process_message(self, channel, method, properties, body):
        """Process incoming message"""
        try:
            # Parse message
            message = json.loads(body.decode('utf-8'))
            
            # Log received message
            logger.info(f"Received message: {message}")
            
            # Extract required fields
            scan_id = message.get('scan_id')
            module = message.get('module')
            status = message.get('status')
            message_text = message.get('message')
            error_details = message.get('error_details')
            
            # Validate required fields
            if not scan_id or not module or not status:
                logger.error(f"Invalid message format: {message}")
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                return
            
            # Update scan status
            success = ScanStatusService.update_scan_status(
                scan_id=scan_id,
                module=module,
                status=status,
                message=message_text,
                error_details=error_details
            )
            
            if success:
                # Acknowledge message
                channel.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(f"Successfully processed message for scan {scan_id}")
            else:
                # Reject message (don't requeue to avoid infinite loop)
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                logger.error(f"Failed to process message for scan {scan_id}")
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {str(e)}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            # Reject and requeue in case of temporary error
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.stdout.write(
            self.style.WARNING('Received shutdown signal. Stopping consumer...')
        )
        self.should_stop = True
    
    def _cleanup(self):
        """Cleanup connections"""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.stop_consuming()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            
            self.stdout.write(
                self.style.SUCCESS('Consumer stopped gracefully')
            )
            logger.info("Consumer stopped gracefully")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'Cleanup error: {str(e)}')
            )