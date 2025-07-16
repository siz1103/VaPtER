# plugins/nmap_scanner/test_nmap.py

import subprocess
import json
import sys
import logging
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_nmap_installation():
    """Test if nmap is properly installed and accessible"""
    try:
        result = subprocess.run(['nmap', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_info = result.stdout.strip()
            logger.info(f"Nmap is installed: {version_info.split()[1]}")
            return True
        else:
            logger.error(f"Nmap version check failed: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Failed to check nmap installation: {str(e)}")
        return False


def test_basic_scan():
    """Test basic nmap functionality with localhost scan"""
    try:
        logger.info("Testing basic nmap scan on localhost...")
        
        cmd = ['nmap', '-sn', '-oX', '-', '127.0.0.1']
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            logger.info("Basic nmap scan successful")
            logger.debug(f"XML output length: {len(result.stdout)} characters")
            return True
        else:
            logger.error(f"Basic nmap scan failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error during basic scan test: {str(e)}")
        return False


def test_xml_parsing():
    """Test XML parsing functionality"""
    try:
        from nmap_scanner import NmapScanner
        
        logger.info("Testing XML parsing...")
        
        # Sample nmap XML output for testing
        sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE nmaprun>
<nmaprun scanner="nmap" args="nmap -sn 127.0.0.1" start="1641024000" startstr="Sat Jan  1 10:00:00 2025" version="7.80" xmloutputversion="1.04">
<scaninfo type="ping" protocol="ip" numservices="0" services=""/>
<verbose level="0"/>
<debugging level="0"/>
<host starttime="1641024000" endtime="1641024001">
<status state="up" reason="localhost-response" reason_ttl="0"/>
<address addr="127.0.0.1" addrtype="ipv4"/>
<hostnames>
<hostname name="localhost" type="PTR"/>
</hostnames>
<times srtt="1000" rttvar="0" to="100000"/>
</host>
<runstats>
<finished time="1641024001" timestr="Sat Jan  1 10:00:01 2025" elapsed="1.00" summary="Nmap done at Sat Jan  1 10:00:01 2025; 1 IP address (1 host up) scanned in 1.00 seconds" exit="success"/>
<hosts up="1" down="0" total="1"/>
</runstats>
</nmaprun>"""
        
        scanner = NmapScanner()
        parsed = scanner.parse_nmap_xml(sample_xml)
        
        logger.info(f"XML parsing successful - found {len(parsed['hosts'])} hosts")
        return True
        
    except Exception as e:
        logger.error(f"XML parsing test failed: {str(e)}")
        return False


def test_configuration():
    """Test configuration loading"""
    try:
        logger.info("Testing configuration...")
        
        logger.info(f"API Gateway URL: {settings.API_GATEWAY_URL}")
        logger.info(f"RabbitMQ URL: {settings.RABBITMQ_URL}")
        logger.info(f"Nmap Request Queue: {settings.NMAP_SCAN_REQUEST_QUEUE}")
        logger.info(f"Status Update Queue: {settings.SCAN_STATUS_UPDATE_QUEUE}")
        logger.info(f"Log Level: {settings.LOG_LEVEL}")
        
        return True
        
    except Exception as e:
        logger.error(f"Configuration test failed: {str(e)}")
        return False


def test_target_validation():
    """Test target validation functionality"""
    try:
        logger.info("Testing target validation...")
        
        # Test valid targets
        valid_targets = ['127.0.0.1', 'localhost', 'google.com', '192.168.1.1']
        for target in valid_targets:
            if settings.validate_target(target):
                logger.info(f"Target {target}: VALID")
            else:
                logger.warning(f"Target {target}: INVALID")
        
        return True
        
    except Exception as e:
        logger.error(f"Target validation test failed: {str(e)}")
        return False


def main():
    """Run all tests"""
    logger.info("=== VaPtER Nmap Scanner Test Suite ===")
    
    tests = [
        ("Nmap Installation", test_nmap_installation),
        ("Basic Scan", test_basic_scan),
        ("XML Parsing", test_xml_parsing),
        ("Configuration", test_configuration),
        ("Target Validation", test_target_validation),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {str(e)}")
            results[test_name] = False
    
    # Summary
    logger.info("\n=== Test Results Summary ===")
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        logger.info("🎉 All tests passed! Nmap scanner is ready.")
        return 0
    else:
        logger.error("❌ Some tests failed. Please check the logs.")
        return 1


if __name__ == "__main__":
    sys.exit(main())