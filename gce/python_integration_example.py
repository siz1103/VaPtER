# gce/python_integration_example.py

"""
Example Python integration with Greenbone Community Edition
This demonstrates how to use python-gvm library directly
"""

import os
import sys
import time
import datetime
from gvm.connections import UnixSocketConnection
from gvm.protocols.gmp import Gmp
from gvm.transforms import EtreeCheckCommandTransform
from gvm.errors import GvmError
import xml.etree.ElementTree as ET


# Configuration
GCE_SOCKET_PATH = '/run/gvmd/gvmd.sock'  # Adjust based on your setup
GCE_USERNAME = 'vapter_api'
GCE_PASSWORD = 'your_password_here'

# Common UUIDs
SCAN_CONFIG_FULL_FAST = 'daba56c8-73ec-11df-a475-002264764cea'
SCANNER_OPENVAS_DEFAULT = '08b69003-5fc2-4037-a479-93b440211c73'
PORT_LIST_ALL_TCP_NMAP_UDP = '730ef368-57e2-11e1-a90f-406186ea4fc5'


class GCEIntegration:
    """Example class for GCE integration"""
    
    def __init__(self, socket_path, username, password):
        self.socket_path = socket_path
        self.username = username
        self.password = password
        self.gmp = None
    
    def connect(self):
        """Connect and authenticate to GCE"""
        try:
            print(f"Connecting to GCE at {self.socket_path}...")
            connection = UnixSocketConnection(path=self.socket_path)
            transform = EtreeCheckCommandTransform()
            self.gmp = Gmp(connection, transform=transform)
            
            print(f"Authenticating as {self.username}...")
            self.gmp.authenticate(self.username, self.password)
            print("✓ Connected and authenticated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def list_scan_configs(self):
        """List available scan configurations"""
        print("\n=== Scan Configurations ===")
        configs = self.gmp.get_scan_configs()
        
        for config in configs.findall('config'):
            config_id = config.get('id')
            name = config.find('name').text
            print(f"  {name}")
            print(f"    ID: {config_id}")
    
    def list_port_lists(self):
        """List available port lists"""
        print("\n=== Port Lists ===")
        port_lists = self.gmp.get_port_lists()
        
        for pl in port_lists.findall('port_list'):
            pl_id = pl.get('id')
            name = pl.find('name').text
            port_count = pl.find('port_count').text if pl.find('port_count') is not None else 'N/A'
            print(f"  {name}")
            print(f"    ID: {pl_id}")
            print(f"    Ports: {port_count}")
    
    def create_and_run_scan(self, target_ip, target_name=None):
        """Create a target and run a scan"""
        if not target_name:
            target_name = f"Test Target - {target_ip}"
        
        print(f"\n=== Creating and Running Scan for {target_ip} ===")
        
        try:
            # Step 1: Create target
            print("1. Creating target...")
            target_response = self.gmp.create_target(
                name=f"{target_name} - {datetime.datetime.now().isoformat()}",
                hosts=[target_ip],
                port_list_id=PORT_LIST_ALL_TCP_NMAP_UDP
            )
            target_id = target_response.get('id')
            print(f"   ✓ Target created: {target_id}")
            
            # Step 2: Create task
            print("2. Creating scan task...")
            task_response = self.gmp.create_task(
                name=f"Scan {target_name} - {datetime.datetime.now().isoformat()}",
                config_id=SCAN_CONFIG_FULL_FAST,
                target_id=target_id,
                scanner_id=SCANNER_OPENVAS_DEFAULT,
                comment="Created by VaPtER integration example"
            )
            task_id = task_response.get('id')
            print(f"   ✓ Task created: {task_id}")
            
            # Step 3: Start task
            print("3. Starting scan...")
            self.gmp.start_task(task_id)
            print("   ✓ Scan started")
            
            # Step 4: Monitor progress
            print("4. Monitoring progress...")
            report_id = self._monitor_task(task_id)
            
            if report_id:
                print(f"   ✓ Scan completed! Report ID: {report_id}")
                return task_id, report_id
            else:
                print("   ❌ Scan failed or timed out")
                return task_id, None
                
        except GvmError as e:
            print(f"   ❌ GVM Error: {e}")
            return None, None
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None, None
    
    def _monitor_task(self, task_id, timeout=3600):
        """Monitor task progress"""
        start_time = time.time()
        last_progress = -1
        
        while time.time() - start_time < timeout:
            try:
                response = self.gmp.get_task(task_id)
                task = response.find('task')
                
                if task is None:
                    print("   ❌ Failed to get task status")
                    return None
                
                status = task.find('status').text
                progress = int(task.find('progress').text)
                
                # Show progress updates
                if progress != last_progress:
                    print(f"   Progress: {progress}% (Status: {status})")
                    last_progress = progress
                
                # Check if complete
                if status in ['Done', 'Stopped', 'Interrupted']:
                    if status == 'Done':
                        # Get report ID
                        last_report = task.find('last_report')
                        if last_report is not None:
                            report = last_report.find('report')
                            if report is not None:
                                return report.get('id')
                    return None
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                print(f"   ❌ Error monitoring task: {e}")
                time.sleep(10)
        
        print("   ❌ Timeout reached")
        return None
    
    def get_report_summary(self, report_id):
        """Get a summary of scan results"""
        print(f"\n=== Report Summary for {report_id} ===")
        
        try:
            response = self.gmp.get_report(report_id, details=True)
            report = response.find('report')
            
            if report is None:
                print("❌ Report not found")
                return
            
            # Get result counts
            result_count = report.find('.//result_count')
            if result_count is not None:
                full = result_count.find('full').text
                filtered = result_count.find('filtered').text
                print(f"Total results: {full} (filtered: {filtered})")
            
            # Get severity counts
            severity_counts = {
                'Critical': 0,
                'High': 0,
                'Medium': 0,
                'Low': 0,
                'Log': 0
            }
            
            results = report.findall('.//result')
            for result in results:
                severity_elem = result.find('severity')
                if severity_elem is not None and severity_elem.text:
                    severity = float(severity_elem.text)
                    if severity >= 9.0:
                        severity_counts['Critical'] += 1
                    elif severity >= 7.0:
                        severity_counts['High'] += 1
                    elif severity >= 4.0:
                        severity_counts['Medium'] += 1
                    elif severity > 0.0:
                        severity_counts['Low'] += 1
                    else:
                        severity_counts['Log'] += 1
            
            print("\nSeverity breakdown:")
            for level, count in severity_counts.items():
                if count > 0:
                    print(f"  {level}: {count}")
            
            # Show a few high severity vulnerabilities
            print("\nHigh severity findings:")
            high_vulns = []
            for result in results:
                severity_elem = result.find('severity')
                if severity_elem is not None and severity_elem.text:
                    severity = float(severity_elem.text)
                    if severity >= 7.0:
                        nvt = result.find('nvt')
                        if nvt is not None:
                            name = nvt.find('name').text
                            high_vulns.append((severity, name))
            
            # Sort by severity and show top 5
            high_vulns.sort(reverse=True)
            for severity, name in high_vulns[:5]:
                print(f"  [{severity}] {name}")
            
            if len(high_vulns) > 5:
                print(f"  ... and {len(high_vulns) - 5} more")
                
        except Exception as e:
            print(f"❌ Error getting report: {e}")
    
    def cleanup_test_data(self):
        """Clean up test targets and tasks"""
        print("\n=== Cleaning up test data ===")
        
        # Note: Be careful with this in production!
        # This example shows how to find and delete test data
        
        try:
            # Find test targets
            targets = self.gmp.get_targets()
            for target in targets.findall('target'):
                name = target.find('name').text
                if 'Test Target' in name or 'VaPtER' in name:
                    target_id = target.get('id')
                    print(f"Deleting target: {name}")
                    self.gmp.delete_target(target_id)
            
            print("✓ Cleanup completed")
            
        except Exception as e:
            print(f"❌ Cleanup error: {e}")
    
    def disconnect(self):
        """Disconnect from GCE"""
        if self.gmp:
            self.gmp.__exit__(None, None, None)
            print("\n✓ Disconnected from GCE")


def main():
    """Main example execution"""
    print("=== GCE Python Integration Example ===\n")
    
    # Create integration instance
    gce = GCEIntegration(GCE_SOCKET_PATH, GCE_USERNAME, GCE_PASSWORD)
    
    # Connect
    if not gce.connect():
        return
    
    try:
        # Show available configurations
        gce.list_scan_configs()
        gce.list_port_lists()
        
        # Example: Run a scan
        # Uncomment to test (replace with your target IP)
        # task_id, report_id = gce.create_and_run_scan('192.168.1.100', 'Test Server')
        # if report_id:
        #     gce.get_report_summary(report_id)
        
        # Example: Get existing report
        # Uncomment and replace with actual report ID
        # gce.get_report_summary('your-report-id-here')
        
        # Cleanup (careful!)
        # gce.cleanup_test_data()
        
    finally:
        gce.disconnect()


if __name__ == "__main__":
    # Check if running inside container or host
    if not os.path.exists(GCE_SOCKET_PATH):
        print(f"Socket not found at {GCE_SOCKET_PATH}")
        print("This script should be run where the GCE socket is accessible")
        print("Either inside the GCE container or with proper volume mounts")
        sys.exit(1)
    
    main()