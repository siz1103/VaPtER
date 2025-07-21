import subprocess
import json
import sys
import logging
import os
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_fingerprintx_installation():
    """Test if FingerprintX is properly installed and accessible"""
    try:
        # Check if binary exists
        if not os.path.exists(settings.FINGERPRINTX_PATH):
            logger.error(f"FingerprintX not found at {settings.FINGERPRINTX_PATH}")
            return False
        
        # Try to run version command
        result = subprocess.run([settings.FINGERPRINTX_PATH, '-h'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info("FingerprintX is installed and accessible")
            return True
        else:
            logger.error(f"FingerprintX execution failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Failed to check FingerprintX installation: {str(e)}")
        return False


def test_basic_fingerprint():
    """Test basic fingerprint functionality on a known service"""
    try:
        logger.info("Testing basic fingerprint on localhost:22 (SSH)...")
        
        cmd = [
            settings.FINGERPRINTX_PATH,
            '--json',
            '-t', '10s',
            '127.0.0.1:22'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            logger.info("Basic fingerprint test completed")
            if result.stdout:
                try:
                    output = json.loads(result.stdout.strip())
                    logger.info(f"Fingerprint result: {json.dumps(output, indent=2)}")
                except json.JSONDecodeError:
                    logger.warning("Could not parse JSON output")
            return True
        else:
            logger.error(f"Fingerprint test failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error during fingerprint test: {str(e)}")
        return False


def test_rabbitmq_connection():
    """Test RabbitMQ connectivity"""
    try:
        import pika
        
        logger.info("Testing RabbitMQ connection...")
        parameters = pika.URLParameters(settings.RABBITMQ_URL)
        connection = pika.BlockingConnection(parameters)
        connection.close()
        logger.info("RabbitMQ connection successful")
        return True
    except Exception as e:
        logger.error(f"RabbitMQ connection failed: {str(e)}")
        return False


def test_api_gateway_connection():
    """Test API Gateway connectivity"""
    try:
        import requests
        
        logger.info("Testing API Gateway connection...")
        response = requests.get(f"{settings.API_GATEWAY_URL}/health/", timeout=5)
        if response.status_code == 200:
            logger.info("API Gateway connection successful")
            return True
        else:
            logger.error(f"API Gateway returned status: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"API Gateway connection failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    logger.info("Starting Fingerprint Scanner tests...")
    
    tests = [
        ("FingerprintX Installation", test_fingerprintx_installation),
        ("Basic Fingerprint", test_basic_fingerprint),
        ("RabbitMQ Connection", test_rabbitmq_connection),
        ("API Gateway Connection", test_api_gateway_connection),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\nRunning test: {test_name}")
        try:
            if test_func():
                logger.info(f"✓ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"✗ {test_name} FAILED")
                failed += 1
        except Exception as e:
            logger.error(f"✗ {test_name} FAILED with exception: {str(e)}")
            failed += 1
    
    logger.info(f"\nTest Summary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())