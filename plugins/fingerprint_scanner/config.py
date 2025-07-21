import os
from typing import List


class settings:
    """Configuration settings for Fingerprint Scanner module"""
    
    # General settings
    MODULE_NAME: str = "fingerprint_scanner"
    VERSION: str = "1.0.0"
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # API Gateway settings
    API_GATEWAY_URL: str = os.getenv('INTERNAL_API_GATEWAY_URL', 'http://api_gateway:8080')
    API_TIMEOUT: int = int(os.getenv('API_TIMEOUT', '30'))
    
    # RabbitMQ settings
    RABBITMQ_URL: str = os.getenv('RABBITMQ_URL', 'amqp://vapter:vapter123@rabbitmq:5672/')
    FINGERPRINT_SCAN_REQUEST_QUEUE: str = os.getenv('RABBITMQ_FINGERPRINT_SCAN_REQUEST_QUEUE', 'fingerprint_scan_requests')
    SCAN_STATUS_UPDATE_QUEUE: str = os.getenv('RABBITMQ_SCAN_STATUS_UPDATE_QUEUE', 'scan_status_updates')
    
    # Fingerprint settings
    FINGERPRINT_TIMEOUT_PER_PORT: int = int(os.getenv('FINGERPRINT_TIMEOUT_PER_PORT', '60'))  # 60 seconds per port
    MAX_CONCURRENT_FINGERPRINTS: int = int(os.getenv('MAX_CONCURRENT_FINGERPRINTS', '10'))  # Max concurrent port scans
    
    # FingerprintX settings
    FINGERPRINTX_PATH: str = os.getenv('FINGERPRINTX_PATH', '/usr/local/bin/fingerprintx')
    FINGERPRINTX_OPTIONS: List[str] = [
        '--json',  # JSON output
        '-v',      # Verbose
    ]
    
    # Scan result storage
    TEMP_RESULTS_DIR: str = os.getenv('TEMP_RESULTS_DIR', '/tmp/fingerprint_results')
    KEEP_RAW_OUTPUT: bool = os.getenv('KEEP_RAW_OUTPUT', 'false').lower() == 'true'
    
    # Retry settings
    MAX_RETRIES: int = int(os.getenv('FINGERPRINT_MAX_RETRIES', '3'))
    RETRY_DELAY: int = int(os.getenv('FINGERPRINT_RETRY_DELAY', '5'))  # seconds
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings"""
        # Check if FingerprintX is available
        if not os.path.exists(cls.FINGERPRINTX_PATH):
            return False
        
        # Create temp directory if it doesn't exist
        os.makedirs(cls.TEMP_RESULTS_DIR, exist_ok=True)
        
        return True


# Create global settings instance