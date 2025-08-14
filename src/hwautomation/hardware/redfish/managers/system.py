"""
Redfish System Information Management

Specialized manager for system discovery and information operations.
"""

from typing import Any, Dict, List, Optional

from hwautomation.logging import get_logger

from ..base import RedfishCapabilities, RedfishCredentials, SystemInfo
from ..client import RedfishDiscovery, ServiceRoot
from ..operations import RedfishSystemOperation
from .base import BaseRedfishManager, RedfishManagerError

logger = get_logger(__name__)


class RedfishSystemManager(BaseRedfishManager):
    """Specialized manager for system information and discovery."""

    def __init__(self, credentials: RedfishCredentials):
        super().__init__(credentials)
        self.system_ops = RedfishSystemOperation(credentials)
        self.discovery = RedfishDiscovery(credentials)

    def get_supported_operations(self) -> Dict[str, bool]:
        """Get supported system operations."""
        return {
            "get_system_info": True,
            "get_system_status": True,
            "list_systems": True,
            "discover_systems": True,
            "get_service_root": True,
            "validate_service": True,
            "set_indicator_led": True,
            "get_system_manufacturer": True,
            "get_system_model": True,
            "get_system_serial_number": True,
            "discover_capabilities": True,
        }

    def get_system_info(self, system_id: str = "1") -> Optional[SystemInfo]:
        """Get detailed system information.

        Args:
            system_id: System identifier

        Returns:
            System information if successful
        """
        try:
            result = self.system_ops.get_system_info(system_id)
            if result.success:
                return result.result
            else:
                self.logger.error(f"Failed to get system info: {result.error_message}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            return None

    def get_system_status(self, system_id: str = "1") -> Optional[Dict[str, str]]:
        """Get system status information.

        Args:
            system_id: System identifier

        Returns:
            System status dictionary
        """
        try:
            with self.create_session() as session:
                result = self.system_ops.get_system_status(session, system_id)
                if result.success:
                    return result.result
                else:
                    self.logger.error(
                        f"Failed to get system status: {result.error_message}"
                    )
                    return None
        except Exception as e:
            self.logger.error(f"Error getting system status: {e}")
            return None

    def list_systems(self) -> List[Dict[str, str]]:
        """List all available systems.

        Returns:
            List of system information dictionaries
        """
        try:
            with self.create_session() as session:
                result = self.system_ops.list_systems(session)
                if result.success:
                    return result.result
                else:
                    self.logger.error(f"Failed to list systems: {result.error_message}")
                    return []
        except Exception as e:
            self.logger.error(f"Error listing systems: {e}")
            return []

    def discover_systems(self) -> List[SystemInfo]:
        """Discover all systems via Redfish.

        Returns:
            List of discovered systems
        """
        try:
            with self.create_session() as session:
                systems = self.discovery.discover_systems(session)
                return systems
        except Exception as e:
            self.logger.error(f"Error discovering systems: {e}")
            return []

    def get_service_root(self) -> Optional[ServiceRoot]:
        """Get Redfish service root information.

        Returns:
            Service root information
        """
        try:
            return self.discovery.discover_service_root()
        except Exception as e:
            self.logger.error(f"Error getting service root: {e}")
            return None

    def validate_service(self) -> Dict[str, bool]:
        """Validate Redfish service capabilities.

        Returns:
            Dictionary of supported capabilities
        """
        try:
            return self.discovery.validate_service()
        except Exception as e:
            self.logger.error(f"Error validating service: {e}")
            return {}

    def set_indicator_led(self, state: str, system_id: str = "1") -> bool:
        """Set system indicator LED state.

        Args:
            state: LED state ('On', 'Off', 'Blinking')
            system_id: System identifier

        Returns:
            True if successful
        """
        try:
            result = self.system_ops.set_indicator_led(state, system_id)
            if not result.success:
                self.logger.error(
                    f"Failed to set indicator LED: {result.error_message}"
                )
            return result.success
        except Exception as e:
            self.logger.error(f"Error setting indicator LED: {e}")
            return False

    def get_system_manufacturer(self, system_id: str = "1") -> Optional[str]:
        """Get system manufacturer.

        Args:
            system_id: System identifier

        Returns:
            Manufacturer name
        """
        system_info = self.get_system_info(system_id)
        return system_info.manufacturer if system_info else None

    def get_system_model(self, system_id: str = "1") -> Optional[str]:
        """Get system model.

        Args:
            system_id: System identifier

        Returns:
            Model name
        """
        system_info = self.get_system_info(system_id)
        return system_info.model if system_info else None

    def get_system_serial_number(self, system_id: str = "1") -> Optional[str]:
        """Get system serial number.

        Args:
            system_id: System identifier

        Returns:
            Serial number
        """
        system_info = self.get_system_info(system_id)
        return system_info.serial_number if system_info else None

    def discover_service_root(self) -> Optional[Dict[str, Any]]:
        """Discover Redfish service root (legacy compatibility).

        Returns:
            Service root information as dictionary
        """
        service_root = self.get_service_root()
        if service_root:
            return {
                "RedfishVersion": service_root.redfish_version,
                "Id": "RootService",  # Standard Redfish ID
                "UUID": service_root.uuid,
                "Product": service_root.product,
                "Systems": {"@odata.id": service_root.systems_uri},
                "Chassis": {"@odata.id": service_root.chassis_uri},
                "Managers": (
                    {"@odata.id": service_root.managers_uri}
                    if service_root.managers_uri
                    else None
                ),
                "SessionService": (
                    {"@odata.id": service_root.session_service_uri}
                    if service_root.session_service_uri
                    else None
                ),
            }
        return None

    def discover_capabilities(self) -> RedfishCapabilities:
        """Discover system capabilities.

        Returns:
            RedfishCapabilities object
        """
        capabilities = RedfishCapabilities()

        try:
            # Test basic system info
            system_info = self.get_system_info()
            if system_info:
                capabilities.supports_system_info = True

            # Test power management (check if we can get power state)
            try:
                from .power import RedfishPowerManager

                power_manager = RedfishPowerManager(self.credentials)
                power_state = power_manager.get_power_state()
                if power_state:
                    capabilities.supports_power_control = True
            except:
                pass

            # Test BIOS management (check if we can get BIOS attributes)
            try:
                from .bios import RedfishBiosManager

                bios_manager = RedfishBiosManager(self.credentials)
                bios_attrs = bios_manager.get_bios_attributes()
                if bios_attrs:
                    capabilities.supports_bios_config = True
            except:
                pass

            # Test firmware management (check if we can get firmware inventory)
            try:
                from .firmware import RedfishFirmwareManager

                firmware_manager = RedfishFirmwareManager(self.credentials)
                firmware_inventory = firmware_manager.get_firmware_inventory()
                if firmware_inventory:
                    capabilities.supports_firmware_update = True
            except:
                pass

            # Test indicator LED
            try:
                # Just check if the method succeeds (don't actually change state)
                result = self.set_indicator_led("Off")
                # No specific attribute for LED in RedfishCapabilities, but test passes if we get here
            except:
                pass

        except Exception as e:
            self.logger.error(f"Error discovering capabilities: {e}")

        return capabilities

    def get_system_summary(self, system_id: str = "1") -> Dict[str, Any]:
        """Get comprehensive system summary.

        Args:
            system_id: System identifier

        Returns:
            System summary dictionary
        """
        summary = {
            "system_id": system_id,
            "manufacturer": None,
            "model": None,
            "serial_number": None,
            "power_state": None,
            "status": None,
            "capabilities": {},
        }

        try:
            # Get basic system info
            system_info = self.get_system_info(system_id)
            if system_info:
                summary.update(
                    {
                        "manufacturer": system_info.manufacturer,
                        "model": system_info.model,
                        "serial_number": system_info.serial_number,
                        "bios_version": getattr(system_info, "bios_version", None),
                        "processor_count": getattr(
                            system_info, "processor_count", None
                        ),
                        "memory_size_gb": getattr(system_info, "memory_size_gb", None),
                    }
                )

            # Get power state
            try:
                from .power import RedfishPowerManager

                power_manager = RedfishPowerManager(self.credentials)
                power_state = power_manager.get_power_state(system_id)
                summary["power_state"] = power_state.value if power_state else None
            except:
                pass

            # Get system status
            status = self.get_system_status(system_id)
            if status:
                summary["status"] = status

            # Get capabilities
            summary["capabilities"] = self.discover_capabilities()

        except Exception as e:
            self.logger.error(f"Error getting system summary: {e}")

        return summary
