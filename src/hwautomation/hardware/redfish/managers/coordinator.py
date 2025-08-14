"""
Redfish Coordinator Manager

Coordinates all specialized Redfish managers and provides the unified interface
that replaces the original manager.py functionality.
"""

from typing import Any, Dict, List, Optional, Union

from hwautomation.logging import get_logger

from ..base import (
    BiosAttribute,
    FirmwareComponent,
    PowerAction,
    PowerState,
    RedfishCapabilities,
    RedfishCredentials,
    SystemInfo,
)
from ..client import ServiceRoot
from .base import BaseRedfishManager, RedfishManagerError
from .bios import RedfishBiosManager
from .firmware import RedfishFirmwareManager
from .power import RedfishPowerManager
from .system import RedfishSystemManager

logger = get_logger(__name__)


class RedfishCoordinator(BaseRedfishManager):
    """
    Unified Redfish management coordinator.

    This class coordinates all specialized Redfish managers and provides
    the same interface as the original RedfishManager for backward compatibility.
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 443,
        use_ssl: bool = True,
        use_https: Optional[bool] = None,  # Legacy compatibility
        verify_ssl: bool = False,
        timeout: int = 30,
    ):
        """Initialize Redfish coordinator.

        Args:
            host: Redfish service host
            username: Authentication username
            password: Authentication password
            port: Service port
            use_ssl: Use SSL/TLS connection
            use_https: Legacy parameter (maps to use_ssl)
            verify_ssl: Verify SSL certificates
            timeout: Connection timeout
        """
        # Handle legacy use_https parameter
        if use_https is not None:
            use_ssl = use_https

        # Create credentials
        credentials = RedfishCredentials(
            host=host,
            username=username,
            password=password,
            port=port,
            use_ssl=use_ssl,
            verify_ssl=verify_ssl,
            timeout=timeout,
        )

        super().__init__(credentials)

        # Initialize specialized managers
        self.power = RedfishPowerManager(credentials)
        self.bios = RedfishBiosManager(credentials)
        self.firmware = RedfishFirmwareManager(credentials)
        self.system = RedfishSystemManager(credentials)

        logger.info(f"Redfish coordinator initialized for {host}:{port}")

    def get_supported_operations(self) -> Dict[str, bool]:
        """Get all supported operations across managers."""
        operations = {}

        # Combine operations from all managers
        operations.update(self.power.get_supported_operations())
        operations.update(self.bios.get_supported_operations())
        operations.update(self.firmware.get_supported_operations())
        operations.update(self.system.get_supported_operations())

        return operations

    # Legacy property compatibility
    @property
    def username(self) -> str:
        """Get username."""
        return self.credentials.username

    @property
    def password(self) -> str:
        """Get password."""
        return self.credentials.password

    @property
    def session(self):
        """Get a session object for legacy compatibility."""
        # Return a mock session object that behaves like requests.Session
        # This is primarily for test compatibility
        import requests

        return requests.Session()

    def test_connection(self) -> Union[bool, tuple]:
        """Test connection to Redfish service.

        Returns:
            For legacy compatibility, returns (success, message) tuple
        """
        try:
            success = super().test_connection()

            if success:
                try:
                    system_info = self.get_system_info()
                    if system_info:
                        message = f"Redfish connection successful to {system_info.manufacturer} {system_info.model}"
                    else:
                        message = "Redfish connection successful"
                except:
                    message = "Redfish connection successful"
            else:
                message = "Redfish connection failed"

            # Return tuple for legacy compatibility
            return success, message

        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False, f"Redfish connection failed: {str(e)}"

    # System Discovery and Information Methods
    def get_service_root(self) -> Optional[ServiceRoot]:
        """Get Redfish service root information."""
        return self.system.get_service_root()

    def discover_systems(self) -> List[SystemInfo]:
        """Discover all systems via Redfish."""
        return self.system.discover_systems()

    def validate_service(self) -> Dict[str, bool]:
        """Validate Redfish service capabilities."""
        return self.system.validate_service()

    def get_system_info(self, system_id: str = "1") -> Optional[SystemInfo]:
        """Get detailed system information."""
        return self.system.get_system_info(system_id)

    def get_system_status(self, system_id: str = "1") -> Optional[Dict[str, str]]:
        """Get system status information."""
        return self.system.get_system_status(system_id)

    def list_systems(self) -> List[Dict[str, str]]:
        """List all available systems."""
        return self.system.list_systems()

    def set_indicator_led(self, state: str, system_id: str = "1") -> bool:
        """Set system indicator LED state."""
        return self.system.set_indicator_led(state, system_id)

    def get_system_manufacturer(self, system_id: str = "1") -> Optional[str]:
        """Get system manufacturer."""
        return self.system.get_system_manufacturer(system_id)

    def get_system_model(self, system_id: str = "1") -> Optional[str]:
        """Get system model."""
        return self.system.get_system_model(system_id)

    def get_system_serial_number(self, system_id: str = "1") -> Optional[str]:
        """Get system serial number."""
        return self.system.get_system_serial_number(system_id)

    def discover_service_root(self) -> Optional[Dict[str, Any]]:
        """Discover Redfish service root (legacy compatibility)."""
        return self.system.discover_service_root()

    def discover_capabilities(self) -> RedfishCapabilities:
        """Discover system capabilities."""
        return self.system.discover_capabilities()

    # Power Management Methods
    def get_power_state(self, system_id: str = "1") -> Optional[PowerState]:
        """Get current power state."""
        return self.power.get_power_state(system_id)

    def set_power_state(
        self,
        action: Union[PowerAction, str],
        system_id: str = "1",
        wait: bool = True,
    ) -> bool:
        """Set power state."""
        return self.power.set_power_state(action, system_id, wait)

    def power_on(self, system_id: str = "1", wait: bool = True) -> bool:
        """Power on the system."""
        return self.power.power_on(system_id, wait)

    def power_off(
        self, system_id: str = "1", wait: bool = True, force: bool = False
    ) -> bool:
        """Power off the system."""
        return self.power.power_off(system_id, wait, force)

    def restart(
        self, system_id: str = "1", wait: bool = True, force: bool = False
    ) -> bool:
        """Restart the system."""
        return self.power.restart(system_id, wait, force)

    def power_cycle(self, system_id: str = "1", wait: bool = True) -> bool:
        """Power cycle the system."""
        return self.power.power_cycle(system_id, wait)

    def get_system_power_state(self, system_id: str = "1") -> Optional[str]:
        """Get system power state as string (legacy compatibility)."""
        return self.power.get_system_power_state(system_id)

    # BIOS Management Methods
    def get_bios_attributes(
        self, system_id: str = "1"
    ) -> Optional[Dict[str, BiosAttribute]]:
        """Get all BIOS attributes."""
        return self.bios.get_bios_attributes(system_id)

    def get_bios_attribute(
        self, attribute_name: str, system_id: str = "1"
    ) -> Optional[BiosAttribute]:
        """Get specific BIOS attribute."""
        return self.bios.get_bios_attribute(attribute_name, system_id)

    def set_bios_attributes(
        self, attributes: Dict[str, Any], system_id: str = "1"
    ) -> bool:
        """Set BIOS attributes."""
        return self.bios.set_bios_attributes(attributes, system_id)

    def set_bios_attribute(
        self, attribute_name: str, value: Any, system_id: str = "1"
    ) -> bool:
        """Set specific BIOS attribute."""
        return self.bios.set_bios_attribute(attribute_name, value, system_id)

    def reset_bios_to_defaults(self, system_id: str = "1") -> bool:
        """Reset BIOS to default settings."""
        return self.bios.reset_bios_to_defaults(system_id)

    def get_pending_bios_settings(
        self, system_id: str = "1"
    ) -> Optional[Dict[str, Any]]:
        """Get pending BIOS settings."""
        return self.bios.get_pending_bios_settings(system_id)

    def get_bios_settings(self, system_id: str = "1") -> Optional[Dict[str, Any]]:
        """Get current BIOS settings (legacy compatibility)."""
        return self.bios.get_bios_settings(system_id)

    # Firmware Management Methods
    def get_firmware_inventory(self, system_id: str = "1") -> List[FirmwareComponent]:
        """Get firmware inventory."""
        return self.firmware.get_firmware_inventory(system_id)

    def get_firmware_component(self, component_id: str) -> Optional[FirmwareComponent]:
        """Get specific firmware component information."""
        return self.firmware.get_firmware_component(component_id)

    def update_firmware(
        self,
        image_uri: str,
        component_id: Optional[str] = None,
        system_id: str = "1",
        transfer_protocol: str = "HTTP",
    ) -> Optional[str]:
        """Update firmware component."""
        return self.firmware.update_firmware(
            image_uri, component_id, system_id, transfer_protocol
        )

    def get_update_status(self, task_uri: str) -> Optional[Dict[str, str]]:
        """Get firmware update status."""
        return self.firmware.get_update_status(task_uri)

    def wait_for_update_completion(self, task_uri: str, timeout: int = 1800) -> bool:
        """Wait for firmware update to complete."""
        return self.firmware.wait_for_update_completion(task_uri, timeout)

    # Comprehensive Status Methods
    def get_comprehensive_status(self, system_id: str = "1") -> Dict[str, Any]:
        """Get comprehensive system status across all managers.

        Args:
            system_id: System identifier

        Returns:
            Comprehensive status dictionary
        """
        status = {
            "system_id": system_id,
            "connection_status": "unknown",
            "system_info": None,
            "power_state": None,
            "bios_info": None,
            "firmware_info": None,
            "capabilities": {},
            "errors": [],
        }

        try:
            # Test connection
            connection_test = self.test_connection()
            status["connection_status"] = (
                "connected" if connection_test[0] else "disconnected"
            )

            if connection_test[0]:
                # Get system information
                try:
                    status["system_info"] = self.system.get_system_summary(system_id)
                except Exception as e:
                    status["errors"].append(f"System info error: {e}")

                # Get power state
                try:
                    power_state = self.get_power_state(system_id)
                    status["power_state"] = power_state.value if power_state else None
                except Exception as e:
                    status["errors"].append(f"Power state error: {e}")

                # Get BIOS info
                try:
                    bios_attributes = self.get_bios_attributes(system_id)
                    status["bios_info"] = {
                        "total_attributes": (
                            len(bios_attributes) if bios_attributes else 0
                        ),
                        "sample_attributes": (
                            list(bios_attributes.keys())[:5] if bios_attributes else []
                        ),
                    }
                except Exception as e:
                    status["errors"].append(f"BIOS info error: {e}")

                # Get firmware info
                try:
                    status["firmware_info"] = self.firmware.get_firmware_summary(
                        system_id
                    )
                except Exception as e:
                    status["errors"].append(f"Firmware info error: {e}")

                # Get capabilities
                try:
                    status["capabilities"] = self.discover_capabilities()
                except Exception as e:
                    status["errors"].append(f"Capabilities error: {e}")

        except Exception as e:
            status["errors"].append(f"General error: {e}")

        return status
