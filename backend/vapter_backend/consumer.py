# backend/vapter_backend/consumer.py

import os
import json
import logging
import time
import django
from datetime import datetime, timezone
import threading
from typing import Dict, Any, Optional

import pika
from pika.exceptions import AMQPConnectionError, AMQPChannelError, ConnectionClosedByBroker

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vapter_backend.settings')
django.setup()

from orchestrator_api.models import Scan

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RabbitMQConnection:
    """Gestisce le connessioni RabbitMQ con reconnection automatica e heartbeat robusto"""
    
    def __init__(self, host: str, port: int, queue_name: str, heartbeat: int = 60):
        self.host = host
        self.port = port
        self.queue_name = queue_name
        self.heartbeat = heartbeat
        self.connection = None
        self.channel = None
        self._lock = threading.Lock()
        self._reconnect_delay = 5
        self._max_reconnect_delay = 300
        
    def connect(self) -> bool:
        """Stabilisce la connessione con retry logic"""
        retry_count = 0
        current_delay = self._reconnect_delay
        
        while True:
            try:
                logger.info(f"Attempting to connect to RabbitMQ at {self.host}:{self.port}")
                
                connection_params = pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    heartbeat=self.heartbeat,
                    blocked_connection_timeout=300,
                    connection_attempts=3,
                    retry_delay=2
                )
                
                self.connection = pika.BlockingConnection(connection_params)
                self.channel = self.connection.channel()
                
                # Declare queue
                self.channel.queue_declare(
                    queue=self.queue_name,
                    durable=True,
                    arguments={
                        'x-message-ttl': 3600000,  # 1 hour TTL
                        'x-max-length': 10000
                    }
                )
                
                logger.info(f"Connected to RabbitMQ successfully")
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
                    self.connection.process_data_events(time_limit=0)
                    return True
                else:
                    logger.warning("Connection lost, attempting to reconnect...")
                    return self.connect()
            except Exception as e:
                logger.error(f"Connection check failed: {e}")
                return self.connect()
    
    def publish(self, message: Dict[str, Any], routing_key: str, max_retries: int = 3) -> bool:
        """Pubblica un messaggio con retry logic"""
        for attempt in range(max_retries):
            try:
                if not self.ensure_connection():
                    continue
                
                # Declare target queue
                self.channel.queue_declare(queue=routing_key, durable=True)
                
                self.channel.basic_publish(
                    exchange='',
                    routing_key=routing_key,
                    body=json.dumps(message),
                    properties=pika.BasicProperties(
                        delivery_mode=2,  # Make message persistent
                        expiration='3600000'  # 1 hour expiration
                    )
                )
                
                logger.info(f"Published message to queue {routing_key}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to publish message (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    
        return False
    
    def consume(self, callback):
        """Consuma messaggi con reconnection automatica"""
        while True:
            try:
                if not self.ensure_connection():
                    time.sleep(5)
                    continue
                
                # Set QoS
                self.channel.basic_qos(prefetch_count=1)
                
                # Start consuming
                logger.info(f"Consuming from queue: {self.queue_name}")
                logger.info("Waiting for messages. To exit press CTRL+C")
                
                for method, properties, body in self.channel.consume(
                    queue=self.queue_name,
                    auto_ack=False
                ):
                    try:
                        message = json.loads(body.decode('utf-8'))
                        logger.info(f"Received message: {message}")
                        
                        # Process message
                        callback(self, method, properties, message)
                        
                        # Acknowledge message
                        self.channel.basic_ack(delivery_tag=method.delivery_tag)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in message: {e}")
                        self.channel.basic_nack(
                            delivery_tag=method.delivery_tag,
                            requeue=False  # Don't requeue invalid messages
                        )
                    except Exception as e:
                        logger.error(f"Error processing message: {e}", exc_info=True)
                        self.channel.basic_nack(
                            delivery_tag=method.delivery_tag,
                            requeue=True
                        )
                        
            except (AMQPConnectionError, AMQPChannelError, ConnectionClosedByBroker) as e:
                logger.error(f"Connection error during consume: {e}")
                time.sleep(5)
            except KeyboardInterrupt:
                logger.info("Shutdown requested...")
                break
            except Exception as e:
                logger.error(f"Unexpected error during consume: {e}", exc_info=True)
                time.sleep(5)
    
    def close(self):
        """Chiude la connessione"""
        with self._lock:
            try:
                if self.channel and not self.channel.is_closed:
                    self.channel.close()
                if self.connection and not self.connection.is_closed:
                    self.connection.close()
                logger.info("RabbitMQ connection closed")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")


class ScanStatusConsumer:
    def __init__(self):
        # RabbitMQ configuration
        self.rabbitmq_host = os.environ.get('RABBITMQ_HOST', 'rabbitmq')
        self.rabbitmq_port = int(os.environ.get('RABBITMQ_PORT', '5672'))
        
        # Initialize connection
        self.connection = RabbitMQConnection(
            self.rabbitmq_host,
            self.rabbitmq_port,
            os.environ.get('RABBITMQ_SCAN_STATUS_UPDATE_QUEUE', 'scan_status_updates'),
            heartbeat=60
        )
        
        # Plugin queues mapping
        self.plugin_queues = {
            'finger': os.environ.get('RABBITMQ_FINGERPRINT_SCAN_REQUEST_QUEUE', 'fingerprint_scan_requests'),
            'gce': os.environ.get('RABBITMQ_GCE_SCAN_REQUEST_QUEUE', 'gce_scan_requests'),
            'web': os.environ.get('RABBITMQ_WEB_SCAN_REQUEST_QUEUE', 'web_scan_requests'),
            'vuln': os.environ.get('RABBITMQ_VULN_LOOKUP_REQUEST_QUEUE', 'vuln_lookup_requests')
        }
    
    def process_message(self, connection: RabbitMQConnection, method, properties, message: Dict[str, Any]):
        """Processa un messaggio di aggiornamento stato"""
        try:
            scan_id = message.get('scan_id')
            module = message.get('module') or message.get('plugin')  # Support both 'module' and 'plugin'
            status = message.get('status')
            
            # Validate message
            if not all([scan_id, module, status]):
                logger.error(f"Invalid message format - missing required fields: {message}")
                return
            
            # Update scan status
            try:
                scan = Scan.objects.get(id=scan_id)
                
                # Update module status
                module_status_field = f"{module}_status"
                if hasattr(scan, module_status_field):
                    setattr(scan, module_status_field, status)
                    logger.info(f"Updated scan {scan_id} status for module {module}: {status}")
                
                # Update timestamps
                if status == 'completed':
                    completed_field = f"{module}_completed_at"
                    if hasattr(scan, completed_field):
                        setattr(scan, completed_field, datetime.now(timezone.utc))
                
                # Handle progress updates
                if 'progress' in message:
                    progress_field = f"{module}_progress"
                    if hasattr(scan, progress_field):
                        setattr(scan, progress_field, message['progress'])
                
                # Save changes
                scan.save()
                
                # Check if this is nmap completion to trigger next plugins
                if module == 'nmap' and status == 'completed':
                    self.trigger_next_plugins(scan)
                
                logger.info(f"Successfully processed message for scan {scan_id}")
                
            except Scan.DoesNotExist:
                logger.error(f"Scan {scan_id} not found")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            raise
    
    def trigger_next_plugins(self, scan: Scan):
        """Attiva i plugin successivi dopo il completamento di nmap"""
        try:
            logger.info(f"Nmap scan completed for scan {scan.id}")
            
            # Check which plugins are enabled
            enabled_plugins = {
                'finger': scan.fingerprint_enabled,
                'gce': scan.gce_enabled,
                'web': scan.web_enabled,
                'vuln': scan.vuln_enabled
            }
            
            logger.info(f"Plugin status - Finger: {enabled_plugins['finger']}, "
                       f"Gce: {enabled_plugins['gce']}, Web: {enabled_plugins['web']}, "
                       f"Vuln: {enabled_plugins['vuln']}")
            
            # Queue messages for enabled plugins
            for plugin, enabled in enabled_plugins.items():
                if enabled:
                    queue_name = self.plugin_queues.get(plugin)
                    if queue_name:
                        message = {
                            'scan_id': scan.id,
                            'target_id': scan.target.id,
                            'target_host': scan.target.host,
                            'plugin': plugin,
                            'timestamp': datetime.now(timezone.utc).isoformat()
                        }
                        
                        logger.info(f"queue_name: {queue_name}")
                        logger.info(f"message: {message}")
                        
                        if self.connection.publish(message, queue_name):
                            logger.info(f"Queued {plugin} scan for scan {scan.id}")
                        else:
                            logger.error(f"Failed to queue {plugin} scan for scan {scan.id}")
                    
        except Exception as e:
            logger.error(f"Error triggering next plugins: {e}", exc_info=True)
    
    def run(self):
        """Avvia il consumer"""
        logger.info("Starting scan status consumer...")
        
        # Connect to RabbitMQ
        if not self.connection.connect():
            logger.error("Failed to connect to RabbitMQ")
            return
        
        try:
            # Start consuming
            self.connection.consume(self.process_message)
        except KeyboardInterrupt:
            logger.info("Shutdown requested...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            self.connection.close()
            logger.info("Scan status consumer stopped")


def main():
    consumer = ScanStatusConsumer()
    consumer.run()


if __name__ == "__main__":
    main()