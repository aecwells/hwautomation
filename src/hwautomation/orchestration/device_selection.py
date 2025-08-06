"""
Device Selection Service

Provides functionality to list, filter, and select MaaS machines for commissioning
without requiring manual entry of Machine IDs.
"""

import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..maas.client import MaasClient
from ..utils.env_config import load_config

logger = logging.getLogger(__name__)

class MachineStatus(Enum):
    """MaaS machine status categories"""
    AVAILABLE = "available"      # Ready, New, Failed commissioning
    COMMISSIONED = "commissioned" # Commissioned, Testing
    DEPLOYED = "deployed"        # Deployed
    OTHER = "other"             # All other statuses

@dataclass
class MachineFilter:
    """Filter criteria for machine selection"""
    status_category: Optional[MachineStatus] = None
    min_cpu_count: Optional[int] = None
    min_memory_gb: Optional[float] = None
    min_storage_gb: Optional[float] = None
    architecture: Optional[str] = None
    power_type: Optional[str] = None
    has_tags: Optional[List[str]] = None
    exclude_tags: Optional[List[str]] = None
    hostname_pattern: Optional[str] = None

class DeviceSelectionService:
    """Service for selecting MaaS devices for commissioning"""
    
    def __init__(self, maas_client: MaasClient = None, config: Dict = None):
        """
        Initialize device selection service
        
        Args:
            maas_client: MaaS client instance (will create if None)
            config: Configuration dictionary
        """
        if maas_client:
            self.maas_client = maas_client
        else:
            # Create MaaS client from config
            if config is None:
                config = {}
            
            from ..maas.client import create_maas_client
            self.maas_client = create_maas_client(config)
    
    def list_available_machines(self, machine_filter: MachineFilter = None) -> List[Dict]:
        """
        List machines available for commissioning with optional filtering
        
        Args:
            machine_filter: Filter criteria to apply
            
        Returns:
            List of machine summaries matching the filter
        """
        try:
            # Get machine summaries from MaaS
            machines = self.maas_client.get_machines_summary()
            
            if machine_filter:
                machines = self._apply_filters(machines, machine_filter)
            
            # Sort by hostname for consistent ordering
            machines.sort(key=lambda m: m.get('hostname', '').lower())
            
            return machines
            
        except Exception as e:
            logger.error(f"Failed to list available machines: {e}")
            return []
    
    def get_machine_by_hostname(self, hostname: str) -> Optional[Dict]:
        """
        Find machine by hostname
        
        Args:
            hostname: Machine hostname to search for
            
        Returns:
            Machine summary if found, None otherwise
        """
        try:
            machines = self.maas_client.get_machines_summary()
            for machine in machines:
                if machine.get('hostname', '').lower() == hostname.lower():
                    return machine
            return None
            
        except Exception as e:
            logger.error(f"Failed to find machine by hostname {hostname}: {e}")
            return None
    
    def get_machine_details(self, system_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific machine
        
        Args:
            system_id: MaaS system ID
            
        Returns:
            Detailed machine information
        """
        try:
            return self.maas_client.get_machine_details(system_id)
        except Exception as e:
            logger.error(f"Failed to get machine details for {system_id}: {e}")
            return None
    
    def validate_machine_for_commissioning(self, system_id: str) -> Tuple[bool, str]:
        """
        Validate that a machine is suitable for commissioning
        
        Args:
            system_id: MaaS system ID
            
        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            machine = self.maas_client.get_machine(system_id)
            if not machine:
                return False, f"Machine {system_id} not found in MaaS"
            
            status = machine.get('status_name', '')
            
            # Check if machine is in a commissionable state
            commissionable_statuses = [
                'Ready', 'New', 'Failed commissioning', 'Failed testing',
                'Failed deployment', 'Broken'
            ]
            
            if status not in commissionable_statuses:
                return False, f"Machine is in '{status}' status, not available for commissioning"
            
            # Check if machine has an owner (shouldn't commission owned machines)
            if machine.get('owner') and machine.get('owner').get('username'):
                owner = machine.get('owner').get('username')
                return False, f"Machine is owned by '{owner}', cannot commission"
            
            # Additional checks
            if not machine.get('power_type') or machine.get('power_type') == 'manual':
                logger.warning(f"Machine {system_id} has manual power type - may require manual intervention")
            
            return True, "Machine is available for commissioning"
            
        except Exception as e:
            logger.error(f"Failed to validate machine {system_id}: {e}")
            return False, f"Validation error: {str(e)}"
    
    def suggest_device_type(self, system_id: str) -> Optional[str]:
        """
        Suggest appropriate device type based on machine specifications
        
        Args:
            system_id: MaaS system ID
            
        Returns:
            Suggested device type string
        """
        try:
            details = self.get_machine_details(system_id)
            if not details:
                return None
            
            hardware = details.get('hardware', {})
            cpu_count = hardware.get('cpu_count', 0)
            memory_mb = hardware.get('memory', 0)
            memory_gb = memory_mb / 1024 if memory_mb > 0 else 0
            
            # Basic device type suggestions based on specs
            if cpu_count >= 32 and memory_gb >= 64:
                return 's2.c2.large'
            elif cpu_count >= 16 and memory_gb >= 32:
                return 's2.c2.medium'
            elif cpu_count >= 8 and memory_gb >= 16:
                return 's2.c2.small'
            else:
                return 's2.c2.small'  # Default fallback
                
        except Exception as e:
            logger.error(f"Failed to suggest device type for {system_id}: {e}")
            return 's2.c2.small'  # Default fallback
    
    def _apply_filters(self, machines: List[Dict], machine_filter: MachineFilter) -> List[Dict]:
        """Apply filtering criteria to machine list"""
        filtered = []
        
        for machine in machines:
            # Status category filter
            if machine_filter.status_category:
                machine_status = self._categorize_status(machine.get('status', ''))
                if machine_status != machine_filter.status_category:
                    continue
            
            # CPU count filter
            if machine_filter.min_cpu_count:
                if machine.get('cpu_count', 0) < machine_filter.min_cpu_count:
                    continue
            
            # Memory filter
            if machine_filter.min_memory_gb:
                memory_gb = machine.get('memory', 0) / 1024 if machine.get('memory', 0) > 0 else 0
                if memory_gb < machine_filter.min_memory_gb:
                    continue
            
            # Storage filter
            if machine_filter.min_storage_gb:
                storage_gb = machine.get('storage', 0) / (1024**3) if machine.get('storage', 0) > 0 else 0
                if storage_gb < machine_filter.min_storage_gb:
                    continue
            
            # Architecture filter
            if machine_filter.architecture:
                if machine.get('architecture', '').lower() != machine_filter.architecture.lower():
                    continue
            
            # Power type filter
            if machine_filter.power_type:
                if machine.get('power_type', '').lower() != machine_filter.power_type.lower():
                    continue
            
            # Tag filters
            machine_tags = [tag.lower() for tag in machine.get('tags', [])]
            
            if machine_filter.has_tags:
                required_tags = [tag.lower() for tag in machine_filter.has_tags]
                if not all(tag in machine_tags for tag in required_tags):
                    continue
            
            if machine_filter.exclude_tags:
                excluded_tags = [tag.lower() for tag in machine_filter.exclude_tags]
                if any(tag in machine_tags for tag in excluded_tags):
                    continue
            
            # Hostname pattern filter
            if machine_filter.hostname_pattern:
                hostname = machine.get('hostname', '').lower()
                pattern = machine_filter.hostname_pattern.lower()
                if pattern not in hostname:
                    continue
            
            filtered.append(machine)
        
        return filtered
    
    def _categorize_status(self, status: str) -> MachineStatus:
        """Categorize MaaS machine status"""
        status_lower = status.lower()
        
        available_statuses = ['ready', 'new', 'failed commissioning', 'failed testing', 'failed deployment', 'broken']
        commissioned_statuses = ['commissioning', 'testing', 'allocated']
        deployed_statuses = ['deployed', 'deploying']
        
        if status_lower in available_statuses:
            return MachineStatus.AVAILABLE
        elif status_lower in commissioned_statuses:
            return MachineStatus.COMMISSIONED
        elif status_lower in deployed_statuses:
            return MachineStatus.DEPLOYED
        else:
            return MachineStatus.OTHER
    
    def get_status_summary(self) -> Dict[str, int]:
        """Get summary of machine statuses"""
        try:
            machines = self.maas_client.get_machines_summary()
            
            summary = {
                'total': len(machines),
                'available': 0,
                'commissioned': 0,
                'deployed': 0,
                'other': 0
            }
            
            for machine in machines:
                category = self._categorize_status(machine.get('status', ''))
                if category == MachineStatus.AVAILABLE:
                    summary['available'] += 1
                elif category == MachineStatus.COMMISSIONED:
                    summary['commissioned'] += 1
                elif category == MachineStatus.DEPLOYED:
                    summary['deployed'] += 1
                else:
                    summary['other'] += 1
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get status summary: {e}")
            return {'total': 0, 'available': 0, 'commissioned': 0, 'deployed': 0, 'other': 0}
