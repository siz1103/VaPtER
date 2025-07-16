# plugins/nmap_scanner/config.py

import os
from typing import List


class Settings:
    """Configuration settings for Nmap Scanner module"""
    
    # General settings
    MODULE_NAME: str = "nmap_scanner"
    VERSION: str = "1.0.0"
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    
    # API Gateway settings
    API_GATEWAY_URL: str = os.getenv('INTERNAL_API_GATEWAY_URL', 'http://api_gateway:8080')
    API_TIMEOUT: int = int(os.getenv('API_TIMEOUT', '30'))
    
    # RabbitMQ settings
    RABBITMQ_URL: str = os.getenv('RABBITMQ_URL', 'amqp://vapter:vapter123@rabbitmq:5672/')
    NMAP_SCAN_REQUEST_QUEUE: str = os.getenv('RABBITMQ_NMAP_SCAN_REQUEST_QUEUE', 'nmap_scan_requests')
    SCAN_STATUS_UPDATE_QUEUE: str = os.getenv('RABBITMQ_SCAN_STATUS_UPDATE_QUEUE', 'scan_status_updates')
    
    # Nmap settings
    NMAP_TIMEOUT: int = int(os.getenv('NMAP_TIMEOUT', '3600'))  # 1 hour default timeout
    MAX_PARALLEL_SCANS: int = int(os.getenv('MAX_PARALLEL_SCANS', '1'))  # Single scan at a time by default
    
    # Default nmap options
    DEFAULT_NMAP_OPTIONS: List[str] = [
        '-v',           # Verbose output
        '--reason',     # Display reason for port state
        '--packet-trace'  # Show packet trace (only if debug)
    ]
    
    # Timing templates mapping
    TIMING_TEMPLATES = {
        'paranoid': '-T0',
        'sneaky': '-T1', 
        'polite': '-T2',
        'normal': '-T3',
        'aggressive': '-T4',
        'insane': '-T5'
    }
    
    # Security settings
    ALLOWED_TARGETS: List[str] = os.getenv('ALLOWED_TARGETS', '').split(',') if os.getenv('ALLOWED_TARGETS') else []
    DENIED_TARGETS: List[str] = os.getenv('DENIED_TARGETS', '').split(',') if os.getenv('DENIED_TARGETS') else []
    
    # Scan result storage
    TEMP_RESULTS_DIR: str = os.getenv('TEMP_RESULTS_DIR', '/tmp/nmap_results')
    KEEP_RAW_OUTPUT: bool = os.getenv('KEEP_RAW_OUTPUT', 'false').lower() == 'true'
    
    @classmethod
    def validate_target(cls, target: str) -> bool:
        """Validate if target is allowed to be scanned"""
        # Check denied targets first
        if cls.DENIED_TARGETS:
            for denied in cls.DENIED_TARGETS:
                if denied and (target == denied or target.endswith(denied)):
                    return False
        
        # If allowed targets is specified, check if target is in the list
        if cls.ALLOWED_TARGETS:
            for allowed in cls.ALLOWED_TARGETS:
                if allowed and (target == allowed or target.endswith(allowed)):
                    return True
            return False  # Target not in allowed list
        
        # If no restrictions, allow all targets except private ranges in production
        return True


# Create global settings instance
settings = Settings()