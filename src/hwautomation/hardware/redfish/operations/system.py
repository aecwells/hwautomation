"""Redfish system information operations.

This module provides system information and basic management operations
through the Redfish API.
"""

from __future__ import annotations
from typing import Dict, List, Optional

from hwautomation.logging import get_logger
from ..base import (
    BaseRedfishOperation,
    HealthStatus,
    RedfishCredentials,
    RedfishOperation,
    SystemInfo,
)
from ..client import RedfishSession

logger = get_logger(__name__)


class RedfishSystemOperation(BaseRedfishOperation):
    """Redfish system information operations."""

    def __init__(self, credentials: RedfishCredentials):
        """Initialize system operations.
        
        Args:
            credentials: Redfish connection credentials
        """
        self.credentials = credentials

    @property
    def operation_name(self) -> str:
        """Get operation name."""
        return "System Information"

    def get_system_info(self, system_id: str = "1") -> RedfishOperation[SystemInfo]:
        """Get comprehensive system information.

        Args:
            system_id: System identifier (default: "1")

        Returns:
            Operation result with system information
        """
        try:
            with RedfishSession(self.credentials) as session:
                system_uri = f"/redfish/v1/Systems/{system_id}"
                response = session.get(system_uri)

                if not response.success:
                    return RedfishOperation(
                        success=False,
                        error_message=f"Failed to get system info: {response.error_message}",
                        response=response,
                    )

                if not response.data:
                    return RedfishOperation(
                        success=False,
                        error_message="No system data received",
                        response=response,
                    )

                data = response.data
                
                # Parse status information
                status_data = data.get("Status", {})
                try:
                    health = HealthStatus(status_data.get("Health", "Unknown"))
                except ValueError:
                    health = HealthStatus.UNKNOWN

                # Extract processor information
                processors = self._extract_processor_info(data.get("ProcessorSummary", {}))
                
                # Extract memory information
                memory = self._extract_memory_info(data.get("MemorySummary", {}))

                # Extract network interfaces
                network_interfaces = self._get_network_interfaces(session, data)

                # Extract storage information
                storage = self._get_storage_info(session, data)

                # Create system info object
                system_info = SystemInfo(
                    id=data.get("Id", system_id),
                    name=data.get("Name", "Unknown"),
                    description=data.get("Description"),
                    manufacturer=data.get("Manufacturer"),
                    model=data.get("Model"),
                    serial_number=data.get("SerialNumber"),
                    sku=data.get("SKU"),
                    part_number=data.get("PartNumber"),
                    uuid=data.get("UUID"),
                    asset_tag=data.get("AssetTag"),
                    power_state=data.get("PowerState"),
                    health=health,
                    health_status=health.value if health else None,
                    bios_version=data.get("BiosVersion"),
                    processor_count=processors.get("count") if processors else None,
                    memory_total_gb=memory.get("total_size_gib") if memory else None,
                    processor_summary=processors,
                    memory_summary=memory,
                    network_interfaces=network_interfaces,
                    storage_summary=storage,
                )

                return RedfishOperation(
                    success=True,
                    result=system_info,
                    response=response,
                )

        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return RedfishOperation(
                success=False,
                error_message=str(e),
            )

    def get_system_status(self, system_id: str = "1") -> RedfishOperation[Dict[str, str]]:
        """Get system status summary.

        Args:
            system_id: System identifier

        Returns:
            Operation result with status information
        """
        try:
            with RedfishSession(self.credentials) as session:
                system_uri = f"/redfish/v1/Systems/{system_id}"
                response = session.get(system_uri)

                if not response.success:
                    return RedfishOperation(
                        success=False,
                        error_message=f"Failed to get system status: {response.error_message}",
                        response=response,
                    )

                if not response.data:
                    return RedfishOperation(
                        success=False,
                        error_message="No system data received",
                        response=response,
                    )

                data = response.data
                status_data = data.get("Status", {})

                status_summary = {
                    "state": status_data.get("State", "Unknown"),
                    "health": status_data.get("Health", "Unknown"),
                    "power_state": data.get("PowerState", "Unknown"),
                    "boot_source": self._get_boot_source(data),
                    "indicator_led": data.get("IndicatorLED", "Unknown"),
                }

                return RedfishOperation(
                    success=True,
                    result=status_summary,
                    response=response,
                )

        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return RedfishOperation(
                success=False,
                error_message=str(e),
            )

    def list_systems(self) -> RedfishOperation[List[Dict[str, str]]]:
        """List all available computer systems.

        Returns:
            Operation result with list of systems
        """
        try:
            with RedfishSession(self.credentials) as session:
                response = session.get("/redfish/v1/Systems")

                if not response.success:
                    return RedfishOperation(
                        success=False,
                        error_message=f"Failed to list systems: {response.error_message}",
                        response=response,
                    )

                if not response.data:
                    return RedfishOperation(
                        success=False,
                        error_message="No systems data received",
                        response=response,
                    )

                members = response.data.get("Members", [])
                systems = []

                # Get basic info for each system
                for member in members:
                    system_uri = member.get("@odata.id")
                    if not system_uri:
                        continue

                    system_response = session.get(system_uri)
                    if system_response.success and system_response.data:
                        data = system_response.data
                        systems.append({
                            "id": data.get("Id", "Unknown"),
                            "name": data.get("Name", "Unknown"),
                            "uri": system_uri,
                            "manufacturer": data.get("Manufacturer", "Unknown"),
                            "model": data.get("Model", "Unknown"),
                            "power_state": data.get("PowerState", "Unknown"),
                            "health": data.get("Status", {}).get("Health", "Unknown"),
                        })

                return RedfishOperation(
                    success=True,
                    result=systems,
                    response=response,
                )

        except Exception as e:
            logger.error(f"Failed to list systems: {e}")
            return RedfishOperation(
                success=False,
                error_message=str(e),
            )

    def set_indicator_led(self, state: str, system_id: str = "1") -> RedfishOperation[bool]:
        """Set system indicator LED state.

        Args:
            state: LED state ("On", "Off", "Blinking")
            system_id: System identifier

        Returns:
            Operation result
        """
        valid_states = ["On", "Off", "Blinking"]
        if state not in valid_states:
            return RedfishOperation(
                success=False,
                error_message=f"Invalid LED state. Valid states: {valid_states}",
            )

        try:
            with RedfishSession(self.credentials) as session:
                system_uri = f"/redfish/v1/Systems/{system_id}"
                data = {"IndicatorLED": state}
                
                response = session.patch(system_uri, data)

                if not response.success:
                    return RedfishOperation(
                        success=False,
                        error_message=f"Failed to set indicator LED: {response.error_message}",
                        response=response,
                    )

                logger.info(f"Indicator LED set to {state}")
                return RedfishOperation(
                    success=True,
                    result=True,
                    response=response,
                )

        except Exception as e:
            logger.error(f"Failed to set indicator LED: {e}")
            return RedfishOperation(
                success=False,
                error_message=str(e),
            )

    def _extract_processor_info(self, processor_data: Dict) -> Optional[Dict]:
        """Extract processor summary information.

        Args:
            processor_data: Processor summary data

        Returns:
            Processor information dictionary
        """
        if not processor_data:
            return None

        return {
            "count": processor_data.get("Count"),
            "model": processor_data.get("Model"),
            "status": processor_data.get("Status", {}).get("Health"),
        }

    def _extract_memory_info(self, memory_data: Dict) -> Optional[Dict]:
        """Extract memory summary information.

        Args:
            memory_data: Memory summary data

        Returns:
            Memory information dictionary
        """
        if not memory_data:
            return None

        return {
            "total_size_gib": memory_data.get("TotalSystemMemoryGiB"),
            "status": memory_data.get("Status", {}).get("Health"),
        }

    def _get_boot_source(self, system_data: Dict) -> str:
        """Extract boot source information.

        Args:
            system_data: System data

        Returns:
            Boot source string
        """
        boot_data = system_data.get("Boot", {})
        return boot_data.get("BootSourceOverrideTarget", "Unknown")

    def _get_network_interfaces(self, session: RedfishSession, system_data: Dict) -> List[Dict]:
        """Get network interface information.

        Args:
            session: Redfish session
            system_data: System data

        Returns:
            List of network interface information
        """
        interfaces = []
        
        # Try different possible locations for network interfaces
        network_interfaces_uri = None
        
        # Check for NetworkInterfaces
        if "NetworkInterfaces" in system_data:
            network_interfaces_uri = system_data["NetworkInterfaces"].get("@odata.id")
        
        # Check for EthernetInterfaces
        if not network_interfaces_uri and "EthernetInterfaces" in system_data:
            network_interfaces_uri = system_data["EthernetInterfaces"].get("@odata.id")

        if not network_interfaces_uri:
            return interfaces

        try:
            response = session.get(network_interfaces_uri)
            if response.success and response.data:
                members = response.data.get("Members", [])
                for member in members[:5]:  # Limit to first 5 interfaces
                    interface_uri = member.get("@odata.id")
                    if interface_uri:
                        interface_data = session.get(interface_uri)
                        if interface_data.success and interface_data.data:
                            data = interface_data.data
                            interfaces.append({
                                "id": data.get("Id", "Unknown"),
                                "name": data.get("Name", "Unknown"),
                                "mac_address": data.get("MACAddress"),
                                "status": data.get("Status", {}).get("Health"),
                            })
        except Exception as e:
            logger.warning(f"Failed to get network interfaces: {e}")

        return interfaces

    def _get_storage_info(self, session: RedfishSession, system_data: Dict) -> Optional[Dict]:
        """Get storage summary information.

        Args:
            session: Redfish session
            system_data: System data

        Returns:
            Storage summary information
        """
        storage_uri = None
        
        if "Storage" in system_data:
            storage_uri = system_data["Storage"].get("@odata.id")
        elif "SimpleStorage" in system_data:
            storage_uri = system_data["SimpleStorage"].get("@odata.id")

        if not storage_uri:
            return None

        try:
            response = session.get(storage_uri)
            if response.success and response.data:
                members = response.data.get("Members", [])
                return {
                    "controllers_count": len(members),
                    "status": "Available" if members else "Unknown",
                }
        except Exception as e:
            logger.warning(f"Failed to get storage info: {e}")

        return None
