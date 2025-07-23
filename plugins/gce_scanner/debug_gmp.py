# plugins/gce_scanner/debug_gmp.py

"""Debug script to diagnose GMP version issues"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
GCE_SOCKET_PATH = os.environ.get('GCE_SOCKET_PATH', '/mnt/gce_sockets/gvmd.sock')
GCE_USERNAME = os.environ.get('GCE_USERNAME', 'vapter_api')
GCE_PASSWORD = os.environ.get('GCE_PASSWORD', 'vapter_gce_password')


def test_basic_connection():
    """Test basic connection without version detection"""
    print("=== Testing Basic GMP Connection ===\n")
    
    try:
        from gvm import __version__ as gvm_version
        print(f"python-gvm version: {gvm_version}")
    except:
        print("Could not determine python-gvm version")
    
    print(f"Socket path: {GCE_SOCKET_PATH}")
    print(f"Socket exists: {os.path.exists(GCE_SOCKET_PATH)}")
    
    if not os.path.exists(GCE_SOCKET_PATH):
        print("\n❌ Socket file not found!")
        return False
    
    try:
        from gvm.connections import UnixSocketConnection
        from gvm.protocols.gmp import Gmp
        from gvm.transforms import EtreeCheckCommandTransform
        
        print("\n1. Creating connection...")
        connection = UnixSocketConnection(path=GCE_SOCKET_PATH, timeout=60)
        
        print("2. Creating GMP instance...")
        transform = EtreeCheckCommandTransform()
        
        # Create GMP without specifying version
        gmp = Gmp(connection, transform=transform)
        
        print("3. Authenticating...")
        # Use context manager
        with gmp:
            result = gmp.authenticate(GCE_USERNAME, GCE_PASSWORD)
            print("   ✓ Authentication successful!")
            
            # Get version after authentication
            print("\n4. Getting version info...")
            version_response = gmp.get_version()
            
            # Parse version info
            if version_response is not None:
                version_elem = version_response.find('version')
                if version_elem is not None:
                    print(f"   GMP Version: {version_elem.text}")
                
                # Try to get protocol version
                protocol_elem = version_response.find('.//protocol_version')
                if protocol_elem is not None:
                    print(f"   Protocol Version: {protocol_elem.text}")
                
                # Print full XML for debugging
                import xml.etree.ElementTree as ET
                print("\n   Full version response:")
                print(ET.tostring(version_response, encoding='unicode'))
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_available_protocols():
    """Test what protocol versions are available"""
    print("\n=== Testing Available GMP Protocols ===\n")
    
    protocols = []
    
    # Check standard GMP
    try:
        from gvm.protocols.gmp import Gmp
        protocols.append("gvm.protocols.gmp.Gmp (standard)")
    except ImportError:
        pass
    
    # Check for versioned protocols
    for version in ['208', '214', '220', '224', '225']:
        try:
            module = __import__(f'gvm.protocols.gmpv{version}', fromlist=['Gmp'])
            protocols.append(f"gvm.protocols.gmpv{version}")
        except ImportError:
            pass
    
    # Check latest protocols
    try:
        from gvm.protocols import latest as latest_protocol
        protocols.append("gvm.protocols.latest")
    except ImportError:
        pass
    
    print("Available protocols:")
    for p in protocols:
        print(f"  - {p}")
    
    if not protocols:
        print("  ❌ No GMP protocols found!")


def test_gmp_versions():
    """Try to determine supported GMP versions"""
    print("\n=== Checking GMP Version Support ===\n")
    
    try:
        import gvm
        
        # Try to access version info
        if hasattr(gvm, 'get_protocol_version'):
            print(f"Default protocol version: {gvm.get_protocol_version()}")
        
        # Check for version constants
        for attr in dir(gvm):
            if 'version' in attr.lower() or 'protocol' in attr.lower():
                try:
                    value = getattr(gvm, attr)
                    if not callable(value):
                        print(f"{attr}: {value}")
                except:
                    pass
                    
    except Exception as e:
        print(f"Error checking versions: {e}")


if __name__ == "__main__":
    print("GMP Connection Debug Script")
    print("=" * 50)
    print()
    
    # Test available protocols
    test_available_protocols()
    
    # Test version support
    test_gmp_versions()
    
    # Test basic connection
    if test_basic_connection():
        print("\n✅ Connection test passed!")
    else:
        print("\n❌ Connection test failed!")
    
    print("\n" + "=" * 50)