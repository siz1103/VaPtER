# backend/test_gce_integration.py

"""Test script to verify GCE plugin integration from backend"""

import os
import sys
import django
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vapter_backend.settings')
django.setup()

from orchestrator_api.models import Scan, Target, Customer, ScanType
from orchestrator_api.services import RabbitMQService


def test_send_gce_scan_request():
    """Test sending a scan request to GCE plugin"""
    
    print("=== Testing GCE Plugin Integration ===\n")
    
    # Get test data
    try:
        # Get a scan that has completed nmap
        scan = Scan.objects.filter(
            status__in=['Nmap Scan Completed', 'Finger Scan Completed']
        ).first()
        
        if not scan:
            print("❌ No completed nmap scans found. Please run an nmap scan first.")
            return False
        
        print(f"✓ Found scan: {scan.id} - Status: {scan.status}")
        print(f"  Target: {scan.target.name} ({scan.target.address})")
        
        # Check if scan type has GCE enabled
        if not scan.scan_type.plugin_gce:
            print("❌ Scan type does not have GCE plugin enabled")
            print("  Please enable plugin_gce in the scan type")
            return False
        
        print("✓ GCE plugin is enabled for this scan type")
        
        # Prepare message
        message = {
            'scan_id': scan.id,
            'target_id': scan.target.id,
            'target_host': scan.target.address,
            'plugin': 'gce',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        print(f"\nSending message to GCE plugin:")
        print(json.dumps(message, indent=2))
        
        # Send to RabbitMQ
        rabbitmq = RabbitMQService()
        success = rabbitmq.publish_message('gce_scan_requests', message)
        rabbitmq.close()
        
        if success:
            print("\n✓ Message sent successfully!")
            print("\nNow check the GCE scanner logs:")
            print("  docker-compose logs -f gce_scanner")
            return True
        else:
            print("\n❌ Failed to send message")
            return False
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_gce_api_endpoints():
    """Test GCE-related API endpoints"""
    
    print("\n=== Testing GCE API Endpoints ===\n")
    
    import requests
    
    base_url = "http://localhost:8080/api/orchestrator"
    
    # Test endpoints
    endpoints = [
        {
            'name': 'List GCE Results',
            'method': 'GET',
            'url': f'{base_url}/gce-results/'
        },
        {
            'name': 'GCE Progress Update',
            'method': 'PATCH',
            'url': f'{base_url}/scans/1/gce-progress/',
            'data': {
                'gce_task_id': '550e8400-e29b-41d4-a716-446655440000',
                'gce_scan_progress': 50,
                'gce_scan_status': 'Running'
            }
        }
    ]
    
    for endpoint in endpoints:
        try:
            print(f"Testing: {endpoint['name']}")
            print(f"  {endpoint['method']} {endpoint['url']}")
            
            if endpoint['method'] == 'GET':
                response = requests.get(endpoint['url'])
            elif endpoint['method'] == 'PATCH':
                response = requests.patch(
                    endpoint['url'],
                    json=endpoint.get('data', {}),
                    headers={'Content-Type': 'application/json'}
                )
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code in [200, 201]:
                print("  ✓ Success")
                if endpoint['method'] == 'GET' and 'results' in response.json():
                    print(f"  Found {len(response.json()['results'])} results")
            else:
                print(f"  ❌ Error: {response.text[:200]}")
                
        except Exception as e:
            print(f"  ❌ Exception: {str(e)}")
        
        print()


def main():
    """Run all tests"""
    
    print("GCE Integration Test Suite")
    print("=" * 50)
    print()
    
    # Test 1: Send scan request
    if test_send_gce_scan_request():
        print("\n✓ Scan request test passed")
    else:
        print("\n❌ Scan request test failed")
    
    # Test 2: API endpoints
    test_gce_api_endpoints()
    
    print("\n" + "=" * 50)
    print("Tests completed")


if __name__ == "__main__":
    main()