"""Redfish management integration.

This module provides a unified interface for Redfish operations,
consolidating functionality from the legacy redfish_manager.py
while providing a clean, modular architecture.
"""

from typing import Any, Dict, List, Optional, Union

from hwautomation.logging import get_logger
from .base import (
    BiosAttribute,
    FirmwareComponent,
    PowerAction,
    PowerState,
    RedfishCredentials,
    RedfishError,
    RedfishOperation,
    SystemInfo,
)
from .client import RedfishDiscovery, RedfishSession, ServiceRoot
from .operations import (
    RedfishBiosOperation,
    RedfishFirmwareOperation,
    RedfishPowerOperation,
    RedfishSystemOperation,
)

logger = get_logger(__name__)


class RedfishManager:
    """Unified Redfish management interface.
    
    This class provides a high-level interface for all Redfish operations,
    maintaining backward compatibility with the legacy redfish_manager.py
    while leveraging the new modular architecture.
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 443,
        use_ssl: bool = True,
        verify_ssl: bool = False,
        timeout: int = 30,
    ):
        """Initialize Redfish manager.

        Args:
            host: BMC hostname or IP address
            username: Authentication username
            password: Authentication password
            port: BMC port (default: 443)
            use_ssl: Use HTTPS (default: True)
            verify_ssl: Verify SSL certificates (default: False)
            timeout: Request timeout in seconds (default: 30)
        """
        self.credentials = RedfishCredentials(
            host=host,
            username=username,
            password=password,
            port=port,
            use_ssl=use_ssl,
            verify_ssl=verify_ssl,
            timeout=timeout,
        )

        # Initialize operation modules
        self.power = RedfishPowerOperation(self.credentials)
        self.system = RedfishSystemOperation(self.credentials)
        self.bios = RedfishBiosOperation(self.credentials)
        self.firmware = RedfishFirmwareOperation(self.credentials)
        self.discovery = RedfishDiscovery(self.credentials)

        logger.info(f"Initialized Redfish manager for {host}")

    # Legacy compatibility methods
    @property
    def host(self) -> str:
        """Get BMC host."""
        return self.credentials.host

    @property
    def username(self) -> str:
        """Get username."""
        return self.credentials.username

    def test_connection(self) -> bool:
        """Test connection to Redfish service.

        Returns:
            True if connection successful
        """
        try:
            with RedfishSession(self.credentials) as session:
                return session.test_connection()
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    # Service discovery methods
    def get_service_root(self) -> Optional[ServiceRoot]:
        """Get Redfish service root information.

        Returns:
            Service root information if available
        """
        return self.discovery.discover_service_root()

    def discover_systems(self) -> List[SystemInfo]:
        """Discover available computer systems.

        Returns:
            List of discovered systems
        """
        return self.discovery.discover_systems()

    def validate_service(self) -> Dict[str, bool]:
        """Validate Redfish service capabilities.

        Returns:
            Dictionary of capability checks
        """
        return self.discovery.validate_service()

    # Power management methods
    def get_power_state(self, system_id: str = "1") -> Optional[PowerState]:
        """Get current power state.

        Args:
            system_id: System identifier

        Returns:
            Current power state if successful
        """
        result = self.power.get_power_state(system_id)
        return result.result if result.success else None

    def set_power_state(
        self, 
        action: Union[PowerAction, str], 
        system_id: str = "1",
        wait: bool = True
    ) -> bool:
        """Set power state.

        Args:
            action: Power action to perform
            system_id: System identifier
            wait: Wait for completion

        Returns:
            True if successful
        """
        if isinstance(action, str):
            try:
                action = PowerAction(action.lower())
            except ValueError:
                logger.error(f"Invalid power action: {action}")
                return False

        result = self.power.set_power_state(action, system_id, wait)
        return result.success

    def power_on(self, system_id: str = "1", wait: bool = True) -> bool:
        """Power on the system.

        Args:
            system_id: System identifier
            wait: Wait for power on to complete

        Returns:
            True if successful
        """
        result = self.power.power_on(system_id, wait)
        return result.success

    def power_off(self, system_id: str = "1", wait: bool = True, force: bool = False) -> bool:
        """Power off the system.

        Args:
            system_id: System identifier
            wait: Wait for power off to complete
            force: Force immediate power off

        Returns:
            True if successful
        """
        result = self.power.power_off(system_id, wait, force)
        return result.success

    def restart(self, system_id: str = "1", wait: bool = True, force: bool = False) -> bool:
        """Restart the system.

        Args:
            system_id: System identifier
            wait: Wait for restart to complete
            force: Force immediate restart

        Returns:
            True if successful
        """
        result = self.power.restart(system_id, wait, force)
        return result.success

    # System information methods
    def get_system_info(self, system_id: str = "1") -> Optional[SystemInfo]:
        """Get comprehensive system information.

        Args:
            system_id: System identifier

        Returns:
            System information if successful
        """
        result = self.system.get_system_info(system_id)
        return result.result if result.success else None

    def get_system_status(self, system_id: str = "1") -> Optional[Dict[str, str]]:
        """Get system status summary.

        Args:
            system_id: System identifier

        Returns:
            Status information if successful
        """
        result = self.system.get_system_status(system_id)
        return result.result if result.success else None

    def list_systems(self) -> List[Dict[str, str]]:
        """List all available systems.

        Returns:
            List of system summaries
        """
        result = self.system.list_systems()
        return result.result if result.success else []

    def set_indicator_led(self, state: str, system_id: str = "1") -> bool:
        """Set system indicator LED.

        Args:
            state: LED state ("On", "Off", "Blinking")
            system_id: System identifier

        Returns:
            True if successful
        """
        result = self.system.set_indicator_led(state, system_id)
        return result.success

    # BIOS management methods
    def get_bios_attributes(self, system_id: str = "1") -> Optional[Dict[str, BiosAttribute]]:
        """Get all BIOS attributes.

        Args:
            system_id: System identifier

        Returns:
            BIOS attributes if successful
        """
        result = self.bios.get_bios_attributes(system_id)
        return result.result if result.success else None

    def get_bios_attribute(self, attribute_name: str, system_id: str = "1") -> Optional[BiosAttribute]:
        """Get specific BIOS attribute.

        Args:
            attribute_name: Attribute name
            system_id: System identifier

        Returns:
            BIOS attribute if found
        """
        result = self.bios.get_bios_attribute(attribute_name, system_id)
        return result.result if result.success else None

    def set_bios_attributes(self, attributes: Dict[str, Any], system_id: str = "1") -> bool:
        """Set BIOS attributes.

        Args:
            attributes: Dictionary of attribute names and values
            system_id: System identifier

        Returns:
            True if successful
        """
        result = self.bios.set_bios_attributes(attributes, system_id)
        return result.success

    def set_bios_attribute(self, attribute_name: str, value: Any, system_id: str = "1") -> bool:
        """Set specific BIOS attribute.

        Args:
            attribute_name: Attribute name
            value: Value to set
            system_id: System identifier

        Returns:
            True if successful
        """
        result = self.bios.set_bios_attribute(attribute_name, value, system_id)
        return result.success

    def reset_bios_to_defaults(self, system_id: str = "1") -> bool:
        """Reset BIOS to default settings.

        Args:
            system_id: System identifier

        Returns:
            True if successful
        """
        result = self.bios.reset_bios_to_defaults(system_id)
        return result.success

    def get_pending_bios_settings(self, system_id: str = "1") -> Optional[Dict[str, Any]]:
        """Get pending BIOS settings.

        Args:
            system_id: System identifier

        Returns:
            Pending settings if available
        """
        result = self.bios.get_pending_bios_settings(system_id)
        return result.result if result.success else None

    # Firmware management methods
    def get_firmware_inventory(self, system_id: str = "1") -> List[FirmwareComponent]:
        """Get firmware inventory.

        Args:
            system_id: System identifier

        Returns:
            List of firmware components
        """
        result = self.firmware.get_firmware_inventory(system_id)
        return result.result if result.success else []

    def get_firmware_component(self, component_id: str) -> Optional[FirmwareComponent]:
        """Get specific firmware component.

        Args:
            component_id: Component identifier

        Returns:
            Firmware component if found
        """
        result = self.firmware.get_firmware_component(component_id)
        return result.result if result.success else None

    def update_firmware(
        self,
        firmware_uri: str,
        targets: Optional[List[str]] = None,
        apply_time: str = "Immediate"
    ) -> Optional[str]:
        """Update firmware.

        Args:
            firmware_uri: URI of firmware image
            targets: Target URIs to update
            apply_time: When to apply update

        Returns:
            Task URI if successful
        """
        result = self.firmware.update_firmware(firmware_uri, targets, apply_time)
        return result.result if result.success else None

    def get_update_status(self, task_uri: str) -> Optional[Dict[str, str]]:
        """Get firmware update status.

        Args:
            task_uri: Task URI from update operation

        Returns:
            Status information if successful
        """
        result = self.firmware.get_update_status(task_uri)
        return result.result if result.success else None

    def wait_for_update_completion(self, task_uri: str, timeout: int = 1800) -> bool:
        """Wait for firmware update completion.

        Args:
            task_uri: Task URI from update operation
            timeout: Timeout in seconds

        Returns:
            True if update completed successfully
        """
        result = self.firmware.wait_for_update_completion(task_uri, timeout)
        return result.success

    # Legacy method aliases for backward compatibility
    def get_system_power_state(self, system_id: str = "1") -> Optional[str]:
        """Legacy method: Get system power state.
        
        Args:
            system_id: System identifier
            
        Returns:
            Power state string if successful
        """
        power_state = self.get_power_state(system_id)
        return power_state.value if power_state else None

    def power_cycle(self, system_id: str = "1", wait: bool = True) -> bool:
        """Legacy method: Power cycle the system.
        
        Args:
            system_id: System identifier
            wait: Wait for completion
            
        Returns:
            True if successful
        """
        return self.restart(system_id, wait, force=True)

    def get_system_manufacturer(self, system_id: str = "1") -> Optional[str]:
        """Legacy method: Get system manufacturer.
        
        Args:
            system_id: System identifier
            
        Returns:
            Manufacturer string if available
        """
        system_info = self.get_system_info(system_id)
        return system_info.manufacturer if system_info else None

    def get_system_model(self, system_id: str = "1") -> Optional[str]:
        """Legacy method: Get system model.
        
        Args:
            system_id: System identifier
            
        Returns:
            Model string if available
        """
        system_info = self.get_system_info(system_id)
        return system_info.model if system_info else None

    def get_system_serial_number(self, system_id: str = "1") -> Optional[str]:
        """Legacy method: Get system serial number.
        
        Args:
            system_id: System identifier
            
        Returns:
            Serial number if available
        """
        system_info = self.get_system_info(system_id)
        return system_info.serial_number if system_info else None
