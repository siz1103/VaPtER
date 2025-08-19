# common/rabbitmq_utils.py

import json
import logging
import time
import threading
from typing import Dict, Any, Callable, Optional

import pika
from pika.exceptions import AMQPConnectionError, AMQPChannelError, ConnectionClosedByBroker

logger = logging.getLogger(__name__)


class RabbitMQConnection:
    """
    Gestisce le connessioni RabbitMQ con:
    - Reconnection automatica
    - Heartbeat robusto
    - Retry logic con exponential backoff
    - Thread safety
    """
    
    def __init__(self, 
                 host: str, 
                 port: int, 
                 queue_name: str, 
                 heartbeat: int = 60,
                 prefetch_count: int = 1,
                 durable: bool = True):
        """
        Inizializza la connessione RabbitMQ.
        
        Args:
            host: Hostname del server RabbitMQ
            port: Porta del server RabbitMQ
            queue_name: Nome della coda
            heartbeat: Intervallo heartbeat in secondi
            prefetch_count: Numero di messaggi da prefetch
            durable: Se la coda deve essere durabile
        """
        self.host = host
        self.port = port
        self.queue_name = queue_name
        self.heartbeat = heartbeat
        self.prefetch_count = prefetch_count
        self.durable = durable
        
        self.connection = None
        self.channel = None
        
        self._lock = threading.Lock()
        self._last_activity = time.time()
        self._reconnect_delay = 5
        self._max_reconnect_delay = 300
        self._connection_attempts = 0
        self._max_connection_attempts = 10
        
    def connect(self) -> bool:
        """
        Stabilisce la connessione con retry logic.
        
        Returns:
            True se la connessione è riuscita, False altrimenti
        """
        retry_count = 0
        current_delay = self._reconnect_delay
        
        while retry_count < self._max_connection_attempts:
            try:
                retry_count += 1
                logger.info(f"Attempting to connect to RabbitMQ at {self.host}:{self.port} "
                           f"(attempt {retry_count}/{self._max_connection_attempts})")
                
                # Parametri di connessione
                connection_params = pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    heartbeat=self.heartbeat,
                    blocked_connection_timeout=300,
                    connection_attempts=3,
                    retry_delay=2,
                    socket_timeout=10,
                    stack_timeout=10
                )
                
                # Crea connessione
                self.connection = pika.BlockingConnection(connection_params)
                self.channel = self.connection.channel()
                
                # Configura channel
                self.channel.basic_qos(prefetch_count=self.prefetch_count)
                
                # Dichiara coda con parametri di durabilità
                queue_args = {
                    'x-message-ttl': 3600000,  # 1 hour TTL
                    'x-max-length': 10000,     # Max 10k messaggi
                    'x-overflow': 'drop-head'   # Rimuovi i messaggi più vecchi
                }
                
                self.channel.queue_declare(
                    queue=self.queue_name,
                    durable=self.durable,
                    arguments=queue_args
                )
                
                logger.info(f"Connected to RabbitMQ successfully with heartbeat={self.heartbeat}s")
                self._last_activity = time.time()
                self._connection_attempts = 0
                return True
                
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ: {e}")
                
                if retry_count >= self._max_connection_attempts:
                    logger.error("Max reconnection attempts reached")
                    return False
                
                logger.info(f"Retrying in {current_delay} seconds...")
                time.sleep(current_delay)
                current_delay = min(current_delay * 2, self._max_reconnect_delay)
        
        return False
    
    def ensure_connection(self) -> bool:
        """
        Verifica e ripristina la connessione se necessario.
        
        Returns:
            True se la connessione è attiva, False altrimenti
        """
        with self._lock:
            try:
                if self.connection and not self.connection.is_closed:
                    # Invia heartbeat frame
                    self.connection.process_data_events(time_limit=0)
                    self._last_activity = time.time()
                    return True
                else:
                    logger.warning("Connection lost, attempting to reconnect...")
                    return self.connect()
            except Exception as e:
                logger.error(f"Connection check failed: {e}")
                return self.connect()
    
    def publish(self, 
                message: Dict[str, Any], 
                routing_key: Optional[str] = None,
                max_retries: int = 3,
                persistent: bool = True) -> bool:
        """
        Pubblica un messaggio con retry logic.
        
        Args:
            message: Messaggio da pubblicare (dict)
            routing_key: Routing key (default: queue_name)
            max_retries: Numero massimo di tentativi
            persistent: Se il messaggio deve essere persistente
            
        Returns:
            True se pubblicato con successo, False altrimenti
        """
        if routing_key is None:
            routing_key = self.queue_name
            
        for attempt in range(max_retries):
            try:
                if not self.ensure_connection():
                    continue
                
                # Prepara proprietà del messaggio
                properties = pika.BasicProperties(
                    delivery_mode=2 if persistent else 1,
                    expiration='3600000',  # 1 hour expiration
                    content_type='application/json',
                    timestamp=int(time.time())
                )
                
                # Pubblica messaggio
                self.channel.basic_publish(
                    exchange='',
                    routing_key=routing_key,
                    body=json.dumps(message),
                    properties=properties
                )
                
                logger.debug(f"Published message to queue {routing_key}")
                self._last_activity = time.time()
                return True
                
            except Exception as e:
                logger.error(f"Failed to publish message (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        return False
    
    def consume(self, 
                callback: Callable,
                auto_ack: bool = False,
                exclusive: bool = False,
                consumer_tag: Optional[str] = None):
        """
        Consuma messaggi con reconnection automatica.
        
        Args:
            callback: Funzione callback(channel, method, properties, body_dict)
            auto_ack: Se fare auto-acknowledge dei messaggi
            exclusive: Se il consumer è esclusivo
            consumer_tag: Tag del consumer
        """
        while True:
            try:
                if not self.ensure_connection():
                    time.sleep(5)
                    continue
                
                # Configura consumer
                logger.info(f"Starting consumer on queue: {self.queue_name}")
                
                # Callback wrapper per gestire JSON parsing
                def message_callback(ch, method, properties, body):
                    try:
                        self._last_activity = time.time()
                        
                        # Parse JSON body
                        message = json.loads(body.decode('utf-8'))
                        
                        # Chiama callback utente
                        callback(ch, method, properties, message)
                        
                        # Acknowledge se non auto_ack
                        if not auto_ack:
                            ch.basic_ack(delivery_tag=method.delivery_tag)
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Invalid JSON in message: {e}")
                        if not auto_ack:
                            ch.basic_nack(
                                delivery_tag=method.delivery_tag,
                                requeue=False  # Non rimettere in coda messaggi malformati
                            )
                    except Exception as e:
                        logger.error(f"Error in message callback: {e}", exc_info=True)
                        if not auto_ack:
                            ch.basic_nack(
                                delivery_tag=method.delivery_tag,
                                requeue=True
                            )
                
                # Start consuming
                self.channel.basic_consume(
                    queue=self.queue_name,
                    on_message_callback=message_callback,
                    auto_ack=auto_ack,
                    exclusive=exclusive,
                    consumer_tag=consumer_tag
                )
                
                # Process events
                logger.info("Consumer started, waiting for messages...")
                self.channel.start_consuming()
                
            except (AMQPConnectionError, AMQPChannelError, ConnectionClosedByBroker) as e:
                logger.error(f"Connection error during consume: {e}")
                try:
                    self.channel.stop_consuming()
                except:
                    pass
                time.sleep(5)
            except KeyboardInterrupt:
                logger.info("Shutdown requested...")
                try:
                    self.channel.stop_consuming()
                except:
                    pass
                break
            except Exception as e:
                logger.error(f"Unexpected error during consume: {e}", exc_info=True)
                try:
                    self.channel.stop_consuming()
                except:
                    pass
                time.sleep(5)
    
    def close(self):
        """Chiude la connessione in modo pulito."""
        with self._lock:
            try:
                if self.channel and not self.channel.is_closed:
                    self.channel.close()
                if self.connection and not self.connection.is_closed:
                    self.connection.close()
                logger.info("RabbitMQ connection closed gracefully")
            except Exception as e:
                logger.error(f"Error closing connection: {e}")
    
    def __enter__(self):
        """Context manager entry."""
        if self.connect():
            return self
        else:
            raise AMQPConnectionError("Failed to connect to RabbitMQ")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


class RabbitMQPublisher(RabbitMQConnection):
    """Publisher specializzato con connection pooling."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._publish_lock = threading.Lock()
    
    def publish_batch(self, messages: list, routing_key: Optional[str] = None) -> int:
        """
        Pubblica un batch di messaggi.
        
        Args:
            messages: Lista di messaggi da pubblicare
            routing_key: Routing key
            
        Returns:
            Numero di messaggi pubblicati con successo
        """
        published = 0
        with self._publish_lock:
            for message in messages:
                if self.publish(message, routing_key):
                    published += 1
        return published


class RabbitMQRPC:
    """
    Implementa pattern RPC con RabbitMQ.
    Utile per richieste sincrone con timeout.
    """
    
    def __init__(self, connection: RabbitMQConnection):
        self.connection = connection
        self.callback_queue = None
        self.response = None
        self.correlation_id = None
        
    def on_response(self, ch, method, props, body):
        """Callback per le risposte RPC."""
        if self.correlation_id == props.correlation_id:
            self.response = json.loads(body.decode('utf-8'))
    
    def call(self, message: Dict[str, Any], timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Effettua una chiamata RPC.
        
        Args:
            message: Messaggio da inviare
            timeout: Timeout in secondi
            
        Returns:
            Risposta o None se timeout
        """
        import uuid
        
        self.response = None
        self.correlation_id = str(uuid.uuid4())
        
        # Crea callback queue
        result = self.connection.channel.queue_declare(queue='', exclusive=True)
        self.callback_queue = result.method.queue
        
        # Setup consumer
        self.connection.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )
        
        # Pubblica richiesta
        self.connection.channel.basic_publish(
            exchange='',
            routing_key=self.connection.queue_name,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.correlation_id,
            ),
            body=json.dumps(message)
        )
        
        # Attendi risposta con timeout
        start_time = time.time()
        while self.response is None:
            self.connection.connection.process_data_events(time_limit=0.1)
            if time.time() - start_time > timeout:
                logger.warning(f"RPC call timed out after {timeout}s")
                break
        
        return self.response