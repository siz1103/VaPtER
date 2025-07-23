# plugins/gce_scanner/test_gce.py

"""Test script to verify GCE connection and basic operations"""

import os
import sys
import logging
from gvm.connections import UnixSocketConnection
from gvm.transforms import EtreeCheckCommandTransform
from gvm.errors import GvmError

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
GCE_SOCKET_PATH = os.environ.get('GCE_SOCKET_PATH', '/mnt/gce_sockets/gvmd.sock')
GCE_USERNAME = os.environ.get('GCE_USERNAME', 'vapter_api')
GCE_PASSWORD = os.environ.get('GCE_PASSWORD', 'vapter_gce_password')


def get_gmp_connection():
    """Get GMP connection"""
    connection = UnixSocketConnection(path=GCE_SOCKET_PATH)
    transform = EtreeCheckCommandTransform()
    
    # Create standard GMP connection
    from gvm.protocols.gmp import Gmp
    gmp = Gmp(connection, transform=transform)
    logger.info("Using GMP protocol")
    return gmp


def test_gce_connection():
    """Test basic connection to GCE"""
    logger.info("Testing GCE connection...")
    
    try:
        # Check if socket exists
        if not os.path.exists(GCE_SOCKET_PATH):
            logger.error(f"Socket file not found: {GCE_SOCKET_PATH}")
            logger.info("Make sure GCE is running and the socket is mounted correctly")
            return False
        
        logger.info(f"Socket file found at: {GCE_SOCKET_PATH}")
        
        # Create connection with automatic version detection
        with get_gmp_connection() as gmp:
            # Try to authenticate
            logger.info(f"Authenticating as '{GCE_USERNAME}'...")
            gmp.authenticate(GCE_USERNAME, GCE_PASSWORD)
            logger.info("✓ Authentication successful!")
            
            # Get GMP version
            version_response = gmp.get_version()
            version = version_response.find('version').text if version_response is not None else "Unknown"
            logger.info(f"✓ GMP Version: {version}")
            
            # List scan configs
            logger.info("\nAvailable scan configurations:")
            configs = gmp.get_scan_configs()
            for config in configs.findall('config'):
                config_id = config.get('id')
                config_name = config.find('name').text
                logger.info(f"  - {config_name} (ID: {config_id})")
            
            # List port lists
            logger.info("\nAvailable port lists:")
            port_lists = gmp.get_port_lists()
            for port_list in port_lists.findall('port_list'):
                pl_id = port_list.get('id')
                pl_name = port_list.find('name').text
                logger.info(f"  - {pl_name} (ID: {pl_id})")
            
            # List scanners
            logger.info("\nAvailable scanners:")
            scanners = gmp.get_scanners()
            for scanner in scanners.findall('scanner'):
                scanner_id = scanner.get('id')
                scanner_name = scanner.find('name').text
                logger.info(f"  - {scanner_name} (ID: {scanner_id})")
            
            logger.info("\n✓ All tests passed! GCE integration is working correctly.")
            return True
            
    except FileNotFoundError as e:
        logger.error(f"Socket file not found: {e}")
        logger.info("Please check that GCE is running and volumes are mounted correctly")
        return False
        
    except GvmError as e:
        logger.error(f"GVM Error: {e}")
        logger.info("Please check your credentials and GCE configuration")
        return False
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_create_dummy_target():
    """Test creating a dummy target"""
    logger.info("\nTesting target creation...")
    
    try:
        with get_gmp_connection() as gmp:
            gmp.authenticate(GCE_USERNAME, GCE_PASSWORD)
            
            # Create a test target
            target_name = "VaPtER Test Target - DELETE ME"
            test_host = "192.168.1.1"
            port_list_id = "33d0cd82-57c6-11e1-8ed1-406186ea4fc5"  # All IANA assigned TCP
            
            logger.info(f"Creating test target: {target_name}")
            response = gmp.create_target(
                name=target_name,
                hosts=[test_host],
                port_list_id=port_list_id
            )
            
            target_id = response.get('id')
            logger.info(f"✓ Target created successfully! ID: {target_id}")
            
            # Delete the test target
            logger.info("Cleaning up test target...")
            gmp.delete_target(target_id)
            logger.info("✓ Test target deleted successfully!")
            
            return True
            
    except Exception as e:
        logger.error(f"Failed to create/delete target: {e}")
        return False


if __name__ == "__main__":
    logger.info("=== GCE Integration Test ===\n")
    
    # Run tests
    if test_gce_connection():
        test_create_dummy_target()
    else:
        sys.exit(1)
    
    logger.info("\n=== Test completed ===")