# plugins/gce_scanner/config.py

"""Configuration settings for GCE Scanner"""

import os


class Settings:
    """Configuration settings"""
    
    # Logging
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # RabbitMQ
    RABBITMQ_URL = os.environ.get('RABBITMQ_URL', 'amqp://vapter:vapter123@rabbitmq:5672/')
    GCE_SCAN_REQUEST_QUEUE = os.environ.get('RABBITMQ_GCE_SCAN_REQUEST_QUEUE', 'gce_scan_requests')
    SCAN_STATUS_UPDATE_QUEUE = os.environ.get('RABBITMQ_SCAN_STATUS_UPDATE_QUEUE', 'scan_status_updates')
    
    # API Gateway
    INTERNAL_API_GATEWAY_URL = os.environ.get('INTERNAL_API_GATEWAY_URL', 'http://api_gateway:8080')
    API_TIMEOUT = int(os.environ.get('API_TIMEOUT', '30'))
    
    # GCE Configuration
    GCE_USERNAME = os.environ.get('GCE_USERNAME', 'vapter_api')
    GCE_PASSWORD = os.environ.get('GCE_PASSWORD', 'vapter_gce_password')
    GCE_SOCKET_PATH = os.environ.get('GCE_SOCKET_PATH', '/mnt/gce_sockets/gvmd.sock')
    
    # Scan Configuration
    GCE_SCAN_CONFIG_ID = os.environ.get('GCE_SCAN_CONFIG_ID', 'daba56c8-73ec-11df-a475-002264764cea')  # Full and fast
    GCE_SCANNER_ID = os.environ.get('GCE_SCANNER_ID', '08b69003-5fc2-4037-a479-93b440211c73')  # OpenVAS scanner
    GCE_PORT_LIST_ID = os.environ.get('GCE_PORT_LIST_ID', '730ef368-57e2-11e1-a90f-406186ea4fc5')  # All IANA assigned TCP
    
    # Timing Configuration
    GCE_POLLING_INTERVAL = int(os.environ.get('GCE_POLLING_INTERVAL', '60'))  # seconds
    GCE_MAX_SCAN_TIME = int(os.environ.get('GCE_MAX_SCAN_TIME', '14400'))  # 4 hours default
    
    # Report Configuration
    GCE_REPORT_FORMAT = os.environ.get('GCE_REPORT_FORMAT', 'XML')  # XML or JSON
    
    # Retry Configuration
    MAX_RETRIES = int(os.environ.get('MAX_RETRIES', '5'))
    RETRY_DELAY = int(os.environ.get('RETRY_DELAY', '10'))  # seconds


# Create settings instance
settings = Settings()