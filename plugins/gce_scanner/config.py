import os
import logging

# Logging configuration
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# RabbitMQ configuration
RABBITMQ_URL = os.environ.get('RABBITMQ_URL', 'amqp://vapter:vapter123@rabbitmq:5672/')
GCE_SCAN_REQUEST_QUEUE = os.environ.get('RABBITMQ_GCE_SCAN_REQUEST_QUEUE', 'gce_scan_requests')
SCAN_STATUS_UPDATE_QUEUE = os.environ.get('RABBITMQ_SCAN_STATUS_UPDATE_QUEUE', 'scan_status_updates')

# API Gateway configuration
INTERNAL_API_GATEWAY_URL = os.environ.get('INTERNAL_API_GATEWAY_URL', 'http://api_gateway:8080')
API_TIMEOUT = int(os.environ.get('API_TIMEOUT', '30'))

# GCE configuration
GCE_USERNAME = os.environ.get('GCE_USERNAME', 'vapter_api')
GCE_PASSWORD = os.environ.get('GCE_PASSWORD', 'vapter_gce_password')
GCE_SOCKET_PATH = os.environ.get('GCE_SOCKET_PATH', '/mnt/gce_sockets/gvmd.sock')

# GCE scan settings
GCE_SCAN_CONFIG_ID = os.environ.get('GCE_SCAN_CONFIG_ID', 'daba56c8-73ec-11df-a475-002264764cea')  # Full and fast
GCE_SCANNER_ID = os.environ.get('GCE_SCANNER_ID', '08b69003-5fc2-4037-a479-93b440211c73')  # OpenVAS Default
GCE_PORT_LIST_ID = os.environ.get('GCE_PORT_LIST_ID', '730ef368-57e2-11e1-a90f-406186ea4fc5')  # All TCP and Nmap top 100 UDP

# GCE operation settings
GCE_POLLING_INTERVAL = int(os.environ.get('GCE_POLLING_INTERVAL', '60'))  # seconds
GCE_MAX_SCAN_TIME = int(os.environ.get('GCE_MAX_SCAN_TIME', '14400'))  # 4 hours
GCE_REPORT_FORMAT = os.environ.get('GCE_REPORT_FORMAT', 'XML')  # XML or JSON

# Retry settings
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', '3'))
RETRY_DELAY = int(os.environ.get('RETRY_DELAY', '5'))