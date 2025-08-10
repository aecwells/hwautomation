"""Redfish service discovery and validation.

This module provides functionality to discover and validate
Redfish services on BMC endpoints.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import urljoin

from hwautomation.logging import get_logger

from ..base import RedfishCredentials, RedfishError
from .session import RedfishSession

logger = get_logger(__name__)


@dataclass
class ServiceRoot:
    """Redfish service root information."""

    redfish_version: str
    uuid: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    vendor: Optional[str] = None
    product: Optional[str] = None
    protocol_features_supported: Optional[Dict] = None
    systems_uri: Optional[str] = None
    chassis_uri: Optional[str] = None
    managers_uri: Optional[str] = None
    session_service_uri: Optional[str] = None
    account_service_uri: Optional[str] = None
    update_service_uri: Optional[str] = None
    task_service_uri: Optional[str] = None


@dataclass
class SystemInfo:
    """System information from Redfish."""

    id: str
    name: str
    uri: str
    status: Optional[str] = None
    health: Optional[str] = None
    state: Optional[str] = None
    power_state: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    sku: Optional[str] = None
    part_number: Optional[str] = None
    uuid: Optional[str] = None
    bios_version: Optional[str] = None
    processor_summary: Optional[Dict] = None
    memory_summary: Optional[Dict] = None


class RedfishDiscovery:
    """Redfish service discovery."""

    def __init__(self, credentials: RedfishCredentials):
        """Initialize discovery client.

        Args:
            credentials: Redfish connection credentials
        """
        self.credentials = credentials

    def discover_service_root(self) -> Optional[ServiceRoot]:
        """Discover Redfish service root.

        Returns:
            Service root information if available
        """
        try:
            with RedfishSession(self.credentials) as session:
                response = session.get("/redfish/v1/")

                if not response.success or not response.data:
                    logger.warning("Failed to get service root")
                    return None

                data = response.data

                return ServiceRoot(
                    redfish_version=data.get("RedfishVersion", "Unknown"),
                    uuid=data.get("UUID"),
                    name=data.get("Name"),
                    description=data.get("Description"),
                    vendor=data.get("Vendor"),
                    product=data.get("Product"),
                    protocol_features_supported=data.get("ProtocolFeaturesSupported"),
                    systems_uri=self._get_uri(data, "Systems"),
                    chassis_uri=self._get_uri(data, "Chassis"),
                    managers_uri=self._get_uri(data, "Managers"),
                    session_service_uri=self._get_uri(data, "SessionService"),
                    account_service_uri=self._get_uri(data, "AccountService"),
                    update_service_uri=self._get_uri(data, "UpdateService"),
                    task_service_uri=self._get_uri(data, "TaskService"),
                )

        except Exception as e:
            logger.error(f"Service root discovery failed: {e}")
            return None

    def discover_systems(self) -> List[SystemInfo]:
        """Discover computer systems.

        Returns:
            List of discovered systems
        """
        systems = []

        try:
            with RedfishSession(self.credentials) as session:
                # Get service root first
                service_root = self.discover_service_root()
                if not service_root or not service_root.systems_uri:
                    logger.warning("No systems URI available")
                    return systems

                # Get systems collection
                response = session.get(service_root.systems_uri)
                if not response.success or not response.data:
                    logger.warning("Failed to get systems collection")
                    return systems

                members = response.data.get("Members", [])
                logger.info(f"Found {len(members)} systems")

                # Get details for each system
                for member in members:
                    system_uri = member.get("@odata.id")
                    if not system_uri:
                        continue

                    system_info = self._get_system_details(session, system_uri)
                    if system_info:
                        systems.append(system_info)

        except Exception as e:
            logger.error(f"System discovery failed: {e}")

        return systems

    def validate_service(self) -> Dict[str, bool]:
        """Validate Redfish service capabilities.

        Returns:
            Dictionary of capability checks
        """
        capabilities = {
            "service_root": False,
            "systems": False,
            "managers": False,
            "chassis": False,
            "power_control": False,
            "bios_settings": False,
            "firmware_update": False,
        }

        try:
            with RedfishSession(self.credentials) as session:
                # Test service root
                service_root = self.discover_service_root()
                if service_root:
                    capabilities["service_root"] = True

                    # Test systems
                    if service_root.systems_uri:
                        systems = self.discover_systems()
                        capabilities["systems"] = len(systems) > 0

                        # Test system-specific capabilities
                        if systems:
                            system = systems[0]  # Test first system
                            capabilities["power_control"] = self._test_power_control(
                                session, system.uri
                            )
                            capabilities["bios_settings"] = self._test_bios_settings(
                                session, system.uri
                            )

                    # Test managers
                    if service_root.managers_uri:
                        capabilities["managers"] = self._test_managers(
                            session, service_root.managers_uri
                        )

                    # Test chassis
                    if service_root.chassis_uri:
                        capabilities["chassis"] = self._test_chassis(
                            session, service_root.chassis_uri
                        )

                    # Test firmware update
                    if service_root.update_service_uri:
                        capabilities["firmware_update"] = self._test_update_service(
                            session, service_root.update_service_uri
                        )

        except Exception as e:
            logger.error(f"Service validation failed: {e}")

        return capabilities

    def _get_uri(self, data: Dict, key: str) -> Optional[str]:
        """Extract URI from data dictionary.

        Args:
            data: Response data
            key: Key to extract

        Returns:
            URI string if found
        """
        item = data.get(key)
        if isinstance(item, dict):
            return item.get("@odata.id")
        return None

    def _get_system_details(
        self, session: RedfishSession, system_uri: str
    ) -> Optional[SystemInfo]:
        """Get detailed system information.

        Args:
            session: Redfish session
            system_uri: System URI

        Returns:
            System information if available
        """
        try:
            response = session.get(system_uri)
            if not response.success or not response.data:
                return None

            data = response.data

            # Extract processor summary
            processor_summary = None
            processors = data.get("ProcessorSummary", {})
            if processors:
                processor_summary = {
                    "count": processors.get("Count"),
                    "model": processors.get("Model"),
                    "status": processors.get("Status", {}).get("Health"),
                }

            # Extract memory summary
            memory_summary = None
            memory = data.get("MemorySummary", {})
            if memory:
                memory_summary = {
                    "total_size_gib": memory.get("TotalSystemMemoryGiB"),
                    "status": memory.get("Status", {}).get("Health"),
                }

            # Extract status
            status_obj = data.get("Status", {})

            return SystemInfo(
                id=data.get("Id", "Unknown"),
                name=data.get("Name", "Unknown"),
                uri=system_uri,
                status=status_obj.get("State"),
                health=status_obj.get("Health"),
                power_state=data.get("PowerState"),
                manufacturer=data.get("Manufacturer"),
                model=data.get("Model"),
                serial_number=data.get("SerialNumber"),
                sku=data.get("SKU"),
                part_number=data.get("PartNumber"),
                uuid=data.get("UUID"),
                bios_version=data.get("BiosVersion"),
                processor_summary=processor_summary,
                memory_summary=memory_summary,
            )

        except Exception as e:
            logger.error(f"Failed to get system details for {system_uri}: {e}")
            return None

    def _test_power_control(self, session: RedfishSession, system_uri: str) -> bool:
        """Test power control capability.

        Args:
            session: Redfish session
            system_uri: System URI

        Returns:
            True if power control is available
        """
        try:
            response = session.get(system_uri)
            if not response.success or not response.data:
                return False

            # Check for Actions with Reset
            actions = response.data.get("Actions", {})
            reset_action = actions.get("#ComputerSystem.Reset")

            return reset_action is not None

        except Exception:
            return False

    def _test_bios_settings(self, session: RedfishSession, system_uri: str) -> bool:
        """Test BIOS settings capability.

        Args:
            session: Redfish session
            system_uri: System URI

        Returns:
            True if BIOS settings are available
        """
        try:
            response = session.get(system_uri)
            if not response.success or not response.data:
                return False

            # Check for Bios link
            bios_uri = response.data.get("Bios", {}).get("@odata.id")
            if not bios_uri:
                return False

            # Try to access BIOS settings
            bios_response = session.get(bios_uri)
            return bios_response.success

        except Exception:
            return False

    def _test_managers(self, session: RedfishSession, managers_uri: str) -> bool:
        """Test managers availability.

        Args:
            session: Redfish session
            managers_uri: Managers URI

        Returns:
            True if managers are available
        """
        try:
            response = session.get(managers_uri)
            return response.success and bool(response.data.get("Members"))

        except Exception:
            return False

    def _test_chassis(self, session: RedfishSession, chassis_uri: str) -> bool:
        """Test chassis availability.

        Args:
            session: Redfish session
            chassis_uri: Chassis URI

        Returns:
            True if chassis are available
        """
        try:
            response = session.get(chassis_uri)
            return response.success and bool(response.data.get("Members"))

        except Exception:
            return False

    def _test_update_service(self, session: RedfishSession, update_uri: str) -> bool:
        """Test update service availability.

        Args:
            session: Redfish session
            update_uri: Update service URI

        Returns:
            True if update service is available
        """
        try:
            response = session.get(update_uri)
            return response.success

        except Exception:
            return False
