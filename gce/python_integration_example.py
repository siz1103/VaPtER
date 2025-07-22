# gce/python_integration_example.py
# Esempio di integrazione Python con Greenbone Community Edition per VaPtER

"""
Questo file mostra come integrare GCE con VaPtER usando python-gvm.
Richiede: pip install python-gvm
"""

import os
import sys
from typing import Dict, List, Optional
from gvm.connections import UnixSocketConnection, TLSConnection
from gvm.protocols.gmp import Gmp
from gvm.errors import GvmError
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GCEConnector:
    """Connector per Greenbone Community Edition"""
    
    def __init__(self, username: str, password: str, socket_path: str = '/run/gvmd/gvmd.sock'):
        self.username = username
        self.password = password
        self.socket_path = socket_path
        self.gmp = None
    
    def connect(self):
        """Connetti a GCE via Unix socket"""
        try:
            # Per container Docker, usa Unix socket
            connection = UnixSocketConnection(path=self.socket_path)
            self.gmp = Gmp(connection)
            self.gmp.authenticate(self.username, self.password)
            logger.info("Successfully connected to GCE")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to GCE: {e}")
            return False
    
    def create_target(self, name: str, hosts: List[str], port_list_id: Optional[str] = None) -> Optional[str]:
        """Crea un nuovo target"""
        try:
            # Se non specificata, usa la port list "All IANA assigned TCP"
            if not port_list_id:
                port_lists = self.gmp.get_port_lists()
                for pl in port_lists.xpath('port_list'):
                    if "All IANA assigned TCP" in pl.find('name').text:
                        port_list_id = pl.get('id')
                        break
            
            resp = self.gmp.create_target(
                name=name,
                hosts=hosts,
                port_list_id=port_list_id
            )
            target_id = resp.get('id')
            logger.info(f"Created target {name} with ID: {target_id}")
            return target_id
        except GvmError as e:
            logger.error(f"Failed to create target: {e}")
            return None
    
    def create_scan_task(self, name: str, target_id: str, scanner_id: str = None, 
                        config_id: str = None) -> Optional[str]:
        """Crea una nuova task di scansione"""
        try:
            # Se non specificato, usa scanner e config di default
            if not scanner_id:
                scanners = self.gmp.get_scanners()
                scanner_id = scanners.xpath('scanner')[0].get('id')
            
            if not config_id:
                configs = self.gmp.get_scan_configs()
                # Cerca "Full and fast"
                for cfg in configs.xpath('config'):
                    if "Full and fast" in cfg.find('name').text:
                        config_id = cfg.get('id')
                        break
            
            resp = self.gmp.create_task(
                name=name,
                config_id=config_id,
                target_id=target_id,
                scanner_id=scanner_id
            )
            task_id = resp.get('id')
            logger.info(f"Created scan task {name} with ID: {task_id}")
            return task_id
        except GvmError as e:
            logger.error(f"Failed to create task: {e}")
            return None
    
    def start_scan(self, task_id: str) -> bool:
        """Avvia una scansione"""
        try:
            self.gmp.start_task(task_id)
            logger.info(f"Started scan task {task_id}")
            return True
        except GvmError as e:
            logger.error(f"Failed to start scan: {e}")
            return False
    
    def get_scan_status(self, task_id: str) -> Dict:
        """Ottieni lo stato di una scansione"""
        try:
            resp = self.gmp.get_task(task_id)
            task = resp.xpath('task')[0]
            
            status = {
                'id': task_id,
                'name': task.find('name').text,
                'status': task.find('status').text,
                'progress': task.find('progress').text if task.find('progress') is not None else '0'
            }
            
            # Se c'è un report
            last_report = task.find('last_report')
            if last_report is not None:
                report = last_report.find('report')
                if report is not None:
                    status['report_id'] = report.get('id')
            
            return status
        except GvmError as e:
            logger.error(f"Failed to get scan status: {e}")
            return {}
    
    def get_scan_results(self, report_id: str) -> List[Dict]:
        """Ottieni i risultati di una scansione"""
        try:
            resp = self.gmp.get_report(report_id)
            results = []
            
            for result in resp.xpath('report/report/results/result'):
                vuln = {
                    'name': result.find('name').text,
                    'severity': result.find('severity').text,
                    'host': result.find('host').text,
                    'port': result.find('port').text,
                    'description': result.find('description').text if result.find('description') is not None else ''
                }
                results.append(vuln)
            
            return results
        except GvmError as e:
            logger.error(f"Failed to get scan results: {e}")
            return []
    
    def disconnect(self):
        """Disconnetti da GCE"""
        if self.gmp:
            self.gmp.disconnect()
            logger.info("Disconnected from GCE")


# Esempio di utilizzo per VaPtER
def example_integration():
    """Esempio di come VaPtER potrebbe usare GCE"""
    
    # Configurazione
    GCE_USERNAME = os.getenv('GCE_ADMIN_USER', 'admin')
    GCE_PASSWORD = os.getenv('GCE_ADMIN_PASSWORD', 'admin')
    
    # Connetti a GCE
    gce = GCEConnector(GCE_USERNAME, GCE_PASSWORD)
    if not gce.connect():
        return
    
    try:
        # 1. Crea un target
        target_id = gce.create_target(
            name="VaPtER Test Target",
            hosts=["192.168.1.100", "192.168.1.101"]
        )
        
        if target_id:
            # 2. Crea una task di scansione
            task_id = gce.create_scan_task(
                name="VaPtER Vulnerability Scan",
                target_id=target_id
            )
            
            if task_id:
                # 3. Avvia la scansione
                if gce.start_scan(task_id):
                    print(f"Scan started! Task ID: {task_id}")
                    
                    # 4. Monitora lo stato (in produzione, questo sarebbe asincrono)
                    import time
                    while True:
                        status = gce.get_scan_status(task_id)
                        print(f"Scan progress: {status.get('progress')}%")
                        
                        if status.get('status') == 'Done':
                            print("Scan completed!")
                            
                            # 5. Ottieni i risultati
                            if 'report_id' in status:
                                results = gce.get_scan_results(status['report_id'])
                                print(f"Found {len(results)} vulnerabilities")
                                for vuln in results[:5]:  # Mostra prime 5
                                    print(f"- {vuln['name']} (Severity: {vuln['severity']})")
                            break
                        
                        time.sleep(30)  # Check ogni 30 secondi
    
    finally:
        gce.disconnect()


if __name__ == "__main__":
    example_integration()