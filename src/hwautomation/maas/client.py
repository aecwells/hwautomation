"""
MAAS API client for hardware automation.
Handles authentication and API interactions with MAAS server.
"""

import requests
from typing import List, Dict, Optional
from oauthlib.oauth1 import SIGNATURE_PLAINTEXT
from requests_oauthlib import OAuth1Session


class MaasClient:
    """MAAS API client for server management"""
    
    def __init__(self, host: str, consumer_key: str, consumer_token: str, secret: str):
        """
        Initialize MAAS client.
        
        Args:
            host: MAAS server URL (e.g., "http://192.168.100.253:5240/MAAS")
            consumer_key: OAuth consumer key
            consumer_token: OAuth consumer token  
            secret: OAuth secret
        """
        self.host = host.rstrip('/')
        self.consumer_key = consumer_key
        self.consumer_token = consumer_token
        self.secret = secret
        
        # Create OAuth session
        self.session = OAuth1Session(
            consumer_key,
            resource_owner_key=consumer_token,
            resource_owner_secret=secret,
            signature_method=SIGNATURE_PLAINTEXT
        )
    
    def _extract_owner_name(self, machine: Dict) -> str:
        """Safely extract owner name from machine data"""
        owner = machine.get('owner')
        if owner:
            if isinstance(owner, dict):
                return owner.get('username', 'None')
            elif isinstance(owner, str):
                return owner
        return 'None'
    
    def get_machines(self) -> List[Dict]:
        """Get list of all machines from MAAS"""
        try:
            response = self.session.get(f"{self.host}/api/2.0/machines/")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to get machines from MAAS: {e}")
            return []
    
    def get_machine(self, system_id: str) -> Optional[Dict]:
        """Get specific machine by system ID"""
        try:
            response = self.session.get(f"{self.host}/api/2.0/machines/{system_id}/")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Failed to get machine {system_id}: {e}")
            return None
    
    def commission_machine(self, system_id: str, enable_ssh: bool = True) -> bool:
        """Commission a machine"""
        try:
            data = {'enable_ssh': 1 if enable_ssh else 0}
            response = self.session.post(
                f"{self.host}/api/2.0/machines/{system_id}/op-commission",
                data=data
            )
            response.raise_for_status()
            print(f"Successfully commissioned machine {system_id}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to commission machine {system_id}: {e}")
            return False

    def force_commission_machine(self, system_id: str, enable_ssh: bool = True) -> bool:
        """
        Force commissioning of a machine - releases it first if needed, then commissions
        
        This is useful for machines in 'Ready' status without IP addresses or
        when you need to restart the commissioning process from scratch.
        """
        try:
            # Get current machine status
            machine = self.get_machine(system_id)
            if not machine:
                print(f"Machine {system_id} not found")
                return False
            
            current_status = machine.get('status_name', '')
            print(f"Current machine status: {current_status}")
            
            # If machine is in a deployed state, release it first
            if current_status in ['Deployed', 'Deploying']:
                print(f"Releasing machine {system_id} from deployed state...")
                if not self.release_machine(system_id):
                    print(f"Failed to release machine {system_id}")
                    return False
                
                # Wait a moment for the release to process
                import time
                time.sleep(2)
            
            # If machine is in Ready state without proper IP, abort any existing operation first
            if current_status in ['Ready', 'Commissioned']:
                print(f"Machine in {current_status} state - attempting to force recommission...")
                
                # Try to abort any existing operations first
                try:
                    abort_response = self.session.post(
                        f"{self.host}/api/2.0/machines/{system_id}/op-abort"
                    )
                    # Don't fail if abort doesn't work - machine might not have anything to abort
                    print(f"Attempted to abort existing operations on {system_id}")
                except:
                    print(f"No operations to abort on {system_id}")
            
            # Now commission the machine
            print(f"Starting commissioning for {system_id}...")
            data = {'enable_ssh': 1 if enable_ssh else 0}
            response = self.session.post(
                f"{self.host}/api/2.0/machines/{system_id}/op-commission",
                data=data
            )
            response.raise_for_status()
            print(f"Successfully started force commissioning for machine {system_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to force commission machine {system_id}: {e}")
            return False

    def abort_machine_operation(self, system_id: str) -> bool:
        """Abort any running operation on a machine"""
        try:
            response = self.session.post(
                f"{self.host}/api/2.0/machines/{system_id}/op-abort"
            )
            response.raise_for_status()
            print(f"Successfully aborted operations on machine {system_id}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to abort operations on machine {system_id}: {e}")
            return False
    
    def deploy_machine(self, system_id: str, os_name: str = None) -> bool:
        """Deploy a machine"""
        try:
            data = {}
            if os_name:
                data['distro_series'] = os_name
                
            response = self.session.post(
                f"{self.host}/api/2.0/machines/{system_id}/op-deploy",
                data=data
            )
            response.raise_for_status()
            print(f"Successfully deployed machine {system_id}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to deploy machine {system_id}: {e}")
            return False
    
    def release_machine(self, system_id: str) -> bool:
        """Release a machine"""
        try:
            response = self.session.post(
                f"{self.host}/api/2.0/machines/{system_id}/op-release"
            )
            response.raise_for_status()
            print(f"Successfully released machine {system_id}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Failed to release machine {system_id}: {e}")
            return False
    
    def get_machine_status(self, system_id: str) -> Optional[str]:
        """Get machine status"""
        machine = self.get_machine(system_id)
        return machine.get('status_name') if machine else None
    
    def get_machine_ip(self, system_id: str) -> Optional[str]:
        """Get machine IP address from interface set"""
        machine = self.get_machine(system_id)
        if not machine:
            return None
            
        # Extract IP from interface_set -> discovered array
        interface_set = machine.get('interface_set')
        if interface_set:  # Check if interface_set is not None
            for interface in interface_set:
                if interface and 'discovered' in interface:
                    discovered_list = interface.get('discovered')
                    if discovered_list:  # Check if discovered is not None
                        for discovered in discovered_list:
                            if discovered and discovered.get('ip_address'):
                                return discovered['ip_address']
        return None
    
    def get_machines_by_status(self, status: str) -> List[Dict]:
        """Get machines filtered by status"""
        machines = self.get_machines()
        return [m for m in machines if m.get('status_name') == status]
    
    def get_ready_machines(self) -> List[Dict]:
        """Get machines in 'Ready' status"""
        return self.get_machines_by_status('Ready')
    
    def get_deployed_machines(self) -> List[Dict]:
        """Get machines in 'Deployed' status"""
        return self.get_machines_by_status('Deployed')
    
    def get_available_machines(self) -> List[Dict]:
        """Get machines available for commissioning (Ready, New, Failed commissioning)"""
        machines = self.get_machines()
        available_statuses = ['Ready', 'New', 'Failed commissioning', 'Failed testing']
        return [m for m in machines if m.get('status_name') in available_statuses]
    
    def get_machines_summary(self) -> List[Dict]:
        """Get simplified machine information for selection UI"""
        machines = self.get_machines()
        summary = []
        
        for machine in machines:
            # Extract key information for display
            machine_info = {
                'system_id': machine.get('system_id', ''),
                'hostname': machine.get('hostname', machine.get('fqdn', 'Unknown')),
                'status': machine.get('status_name', 'Unknown'),
                'architecture': machine.get('architecture', 'Unknown'),
                'cpu_count': machine.get('cpu_count', 0),
                'memory': machine.get('memory', 0),  # MB
                'storage': sum([bd.get('size', 0) for bd in machine.get('blockdevice_set', [])]),  # bytes
                'power_type': machine.get('power_type', 'Unknown'),
                'ip_addresses': self._extract_ip_addresses(machine),
                'tags': [tag.get('name', '') for tag in machine.get('tag_names', [])],
                'owner': self._extract_owner_name(machine),
                'created': machine.get('created', ''),
                'updated': machine.get('updated', ''),
                'bios_boot_method': machine.get('bios_boot_method', 'Unknown'),
            }
            
            # Format storage size for display
            if machine_info['storage'] > 0:
                storage_gb = machine_info['storage'] / (1024**3)
                machine_info['storage_display'] = f"{storage_gb:.1f} GB"
            else:
                machine_info['storage_display'] = "Unknown"
            
            # Format memory for display
            if machine_info['memory'] > 0:
                memory_gb = machine_info['memory'] / 1024
                machine_info['memory_display'] = f"{memory_gb:.1f} GB"
            else:
                machine_info['memory_display'] = "Unknown"
            
            summary.append(machine_info)
        
        return summary
    
    def _extract_ip_addresses(self, machine: Dict) -> List[str]:
        """Extract all IP addresses from machine interfaces"""
        ip_addresses = []
        
        interface_set = machine.get('interface_set')
        if interface_set:  # Check if interface_set is not None
            for interface in interface_set:
                if not interface:  # Skip None interfaces
                    continue
                    
                # Get discovered IPs
                discovered_list = interface.get('discovered')
                if discovered_list:  # Check if discovered is not None
                    for discovered in discovered_list:
                        if discovered and discovered.get('ip_address'):
                            ip_addresses.append(discovered['ip_address'])
                
                # Get static IPs
                links_list = interface.get('links')
                if links_list:  # Check if links is not None
                    for link in links_list:
                        if link and link.get('ip_address'):
                            ip_addresses.append(link['ip_address'])
        
        return list(set(ip_addresses))  # Remove duplicates
    
    def get_machine_details(self, system_id: str) -> Optional[Dict]:
        """Get detailed machine information including hardware specs"""
        machine = self.get_machine(system_id)
        if not machine:
            return None
        
        # Extract detailed hardware information  
        details = {
            'basic_info': {
                'system_id': machine.get('system_id'),
                'hostname': machine.get('hostname', machine.get('fqdn', 'Unknown')),
                'status': machine.get('status_name'),
                'architecture': machine.get('architecture'),
                'owner': machine.get('owner', {}).get('username', 'None') if machine.get('owner') else 'None',
                'created': machine.get('created'),
                'updated': machine.get('updated'),
            },
            'hardware': {
                'cpu_count': machine.get('cpu_count', 0),
                'memory': machine.get('memory', 0),
                'storage_devices': [],
                'network_interfaces': [],
                'power_type': machine.get('power_type'),
                'bios_boot_method': machine.get('bios_boot_method'),
            },
            'network': {
                'ip_addresses': self._extract_ip_addresses(machine),
                'boot_interface': machine.get('boot_interface', {}).get('name', 'Unknown'),
            },
            'tags': [tag.get('name', '') for tag in machine.get('tag_names', [])],
            'raw_machine_data': machine  # Include full data for debugging
        }
        
        # Extract storage device details
        for block_device in machine.get('blockdevice_set', []):
            storage_info = {
                'name': block_device.get('name', 'Unknown'),
                'model': block_device.get('model', 'Unknown'),
                'size': block_device.get('size', 0),
                'size_display': f"{block_device.get('size', 0) / (1024**3):.1f} GB" if block_device.get('size') else "Unknown",
                'block_size': block_device.get('block_size', 0),
                'type': block_device.get('type', 'Unknown')
            }
            details['hardware']['storage_devices'].append(storage_info)
        
        # Extract network interface details
        for interface in machine.get('interface_set', []):
            interface_info = {
                'name': interface.get('name', 'Unknown'),
                'type': interface.get('type', 'Unknown'),  
                'mac_address': interface.get('mac_address', 'Unknown'),
                'enabled': interface.get('enabled', False),
                'ip_addresses': []
            }
            
            # Get IP addresses for this interface
            if 'discovered' in interface:
                for discovered in interface['discovered']:
                    if 'ip_address' in discovered:
                        interface_info['ip_addresses'].append({
                            'ip': discovered['ip_address'],
                            'type': 'discovered'
                        })
            
            if 'links' in interface:
                for link in interface['links']:
                    if 'ip_address' in link:
                        interface_info['ip_addresses'].append({
                            'ip': link['ip_address'],
                            'type': 'static'
                        })
            
            details['hardware']['network_interfaces'].append(interface_info)
        
        return details

    def tag_machine(self, system_id: str, tag: str) -> bool:
        """Apply a tag to a machine"""
        try:
            # For now, just log the tag operation - MAAS API for tags can be complex
            # In a full implementation, this would use the MAAS tags API
            print(f"Would apply tag '{tag}' to machine {system_id}")
            return True
        except Exception as e:
            print(f"Failed to tag machine {system_id}: {e}")
            return False

    def mark_machine_ready(self, system_id: str) -> bool:
        """Mark a machine as ready (this is typically done automatically by MAAS after commissioning)"""
        try:
            # In MAAS, machines become "Ready" automatically after successful commissioning
            # This method is primarily for logging/tracking purposes
            machine = self.get_machine(system_id)
            if machine:
                status = self.get_machine_status(system_id)
                print(f"Machine {system_id} status: {status}")
                return status in ['Ready', 'Deployed']
            return False
        except Exception as e:
            print(f"Failed to check machine ready status {system_id}: {e}")
            return False


def create_maas_client(config: Dict = None) -> MaasClient:
    """
    Create MAAS client with default or provided configuration.
    
    Args:
        config: Configuration dictionary with MAAS credentials
        
    Returns:
        Configured MaasClient instance
    """
    if config is None:
        # Load configuration from environment
        from ..utils.env_config import load_config
        full_config = load_config()
        config = full_config.get('maas', {})
    
    # Use host if available, otherwise fall back to url
    host = config.get('host') or config.get('url', '')
    if not host:
        raise ValueError("MAAS host/url must be provided in configuration")
    
    # Map config keys to MaasClient parameters
    # Prioritize config.yaml format (token_key/token_secret) over old format
    consumer_token = config.get('token_key') or config.get('consumer_token')
    secret = config.get('token_secret') or config.get('secret')
    
    return MaasClient(
        host=host,
        consumer_key=config.get('consumer_key', ''),
        consumer_token=consumer_token or '',
        secret=secret or ''
    )
