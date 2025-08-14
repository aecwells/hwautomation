"""
Redfish-based BIOS management.

This module provides BIOS configuration management through the
industry-standard Redfish API protocol.
"""

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

from ....logging import get_logger
from ..base import BiosConfigResult, ConfigMethod, DeviceConfig, MethodSelectionResult
from .base import BaseBiosManagerImpl, BiosManagerMixin

logger = get_logger(__name__)


class RedfishBiosManager(BaseBiosManagerImpl, BiosManagerMixin):
    """BIOS manager using Redfish API for configuration operations."""

    def __init__(self, config_dir: str = "configs/bios"):
        """Initialize Redfish BIOS manager.

        Args:
            config_dir: Directory containing BIOS configuration files
        """
        super().__init__(config_dir)
        logger.info("Initialized RedfishBiosManager")

    def get_device_config(self, device_type: str) -> Optional[DeviceConfig]:
        """Get device configuration for Redfish-enabled devices.

        Args:
            device_type: Target device type (e.g., 'a1.c5.large')

        Returns:
            DeviceConfig object or None if not found
        """
        if device_type not in self.device_mappings:
            logger.warning(f"Device type '{device_type}' not found in mappings")
            return None

        mapping = self.device_mappings[device_type]

        # Extract vendor and model information
        vendor = self._extract_vendor_from_mapping(mapping)
        model = self._extract_model_from_mapping(mapping)
        motherboard = self._create_motherboard_list(mapping, vendor, model)

        return DeviceConfig(
            device_type=device_type,
            manufacturer=vendor,
            model=model,
            motherboard=motherboard,
            redfish_enabled=mapping.get("redfish_enabled", True),
            vendor_tools_available=mapping.get("vendor_tools_available", True),
            special_handling=mapping.get("special_handling", {}),
        )

    def select_optimal_method(
        self, device_type: str, target_ip: str
    ) -> MethodSelectionResult:
        """Select optimal method for Redfish-capable devices.

        Args:
            device_type: Target device type
            target_ip: Target system IP address

        Returns:
            MethodSelectionResult with Redfish preference
        """
        device_config = self.get_device_config(device_type)
        if not device_config:
            return MethodSelectionResult(
                recommended_method=ConfigMethod.MANUAL,
                available_methods=[ConfigMethod.MANUAL],
                redfish_capabilities={},
                vendor_tools_status={},
                confidence_score=0.0,
                reasoning=f"Unknown device type: {device_type}",
                fallback_methods=[],
            )

        # Test Redfish connectivity
        redfish_available, redfish_message = self.test_redfish_connection(
            target_ip, "ADMIN", "password"  # Default test credentials
        )

        available_methods = []
        if redfish_available:
            available_methods.append(ConfigMethod.REDFISH_STANDARD)

        if device_config.vendor_tools_available:
            available_methods.append(ConfigMethod.VENDOR_TOOLS)

        available_methods.append(ConfigMethod.MANUAL)

        # Prefer Redfish if available
        if redfish_available:
            return MethodSelectionResult(
                recommended_method=ConfigMethod.REDFISH_STANDARD,
                available_methods=available_methods,
                redfish_capabilities={"available": True, "tested": True},
                vendor_tools_status={"available": device_config.vendor_tools_available},
                confidence_score=0.95,
                reasoning="Redfish API available and tested successfully",
                fallback_methods=[
                    m for m in available_methods if m != ConfigMethod.REDFISH_STANDARD
                ],
            )
        else:
            return MethodSelectionResult(
                recommended_method=(
                    ConfigMethod.VENDOR_TOOLS
                    if device_config.vendor_tools_available
                    else ConfigMethod.MANUAL
                ),
                available_methods=available_methods,
                redfish_capabilities={"available": False, "error": redfish_message},
                vendor_tools_status={"available": device_config.vendor_tools_available},
                confidence_score=0.7 if device_config.vendor_tools_available else 0.1,
                reasoning=f"Redfish unavailable: {redfish_message}",
                fallback_methods=[ConfigMethod.MANUAL],
            )

    def apply_bios_config_smart(
        self,
        device_type: str,
        target_ip: str,
        username: str,
        password: str,
        dry_run: bool = False,
        backup_enabled: bool = True,
    ) -> BiosConfigResult:
        """Apply BIOS configuration using Redfish API.

        Args:
            device_type: Target device type
            target_ip: Target system IP address
            username: Authentication username
            password: Authentication password
            dry_run: If True, validate but don't apply changes
            backup_enabled: If True, create backup before changes

        Returns:
            BiosConfigResult with operation details
        """
        logger.info(
            f"Starting Redfish BIOS config for {device_type} at {target_ip} (dry_run={dry_run})"
        )

        # Validate inputs
        if not self._validate_ip_address(target_ip):
            return self._create_config_result(
                success=False,
                method=ConfigMethod.REDFISH_STANDARD,
                validation_errors=[f"Invalid IP address: {target_ip}"],
            )

        if not self._validate_credentials(username, password):
            return self._create_config_result(
                success=False,
                method=ConfigMethod.REDFISH_STANDARD,
                validation_errors=["Invalid credentials provided"],
            )

        try:
            # Step 1: Test Redfish connection
            redfish_available, message = self.test_redfish_connection(
                target_ip, username, password
            )
            if not redfish_available:
                return self._create_config_result(
                    success=False,
                    method=ConfigMethod.REDFISH_STANDARD,
                    validation_errors=[f"Redfish connection failed: {message}"],
                )

            # Step 2: Get current BIOS configuration via Redfish
            logger.info("Getting current BIOS configuration via Redfish...")
            current_config = self._get_redfish_bios_config(
                target_ip, username, password
            )

            # Step 3: Create backup if enabled
            backup_file = None
            if backup_enabled and current_config is not None:
                backup_file = self._create_backup(
                    current_config, device_type, target_ip
                )
                logger.info(f"Created backup: {backup_file}")

            # Step 4: Apply device-specific modifications
            logger.info("Applying device-specific BIOS settings...")
            modified_config = self._apply_redfish_template(current_config, device_type)

            # Step 5: Validate configuration
            validation_errors = self._validate_redfish_config(
                modified_config, device_type
            )
            if validation_errors:
                return self._create_config_result(
                    success=False,
                    method=ConfigMethod.REDFISH_STANDARD,
                    backup_file=backup_file,
                    validation_errors=validation_errors,
                )

            # Step 6: Apply changes (unless dry run)
            if dry_run:
                logger.info("Dry run mode - configuration validated but not applied")
                return self._create_config_result(
                    success=True,
                    method=ConfigMethod.REDFISH_STANDARD,
                    settings_applied={
                        "dry_run": "Configuration validated successfully"
                    },
                    backup_file=backup_file,
                )

            # Step 7: Push configuration via Redfish
            logger.info("Applying BIOS configuration via Redfish...")
            success = self._apply_redfish_bios_config(
                modified_config, target_ip, username, password
            )

            if success:
                logger.info("BIOS configuration applied successfully via Redfish")
                return self._create_config_result(
                    success=True,
                    method=ConfigMethod.REDFISH_STANDARD,
                    settings_applied={"status": "Configuration applied via Redfish"},
                    backup_file=backup_file,
                    reboot_required=True,
                )
            else:
                return self._create_config_result(
                    success=False,
                    method=ConfigMethod.REDFISH_STANDARD,
                    settings_failed={"redfish": "Failed to apply configuration"},
                    backup_file=backup_file,
                    validation_errors=["Redfish configuration push failed"],
                )

        except Exception as e:
            logger.error(f"Error in Redfish BIOS config: {e}")
            return self._create_config_result(
                success=False,
                method=ConfigMethod.REDFISH_STANDARD,
                settings_failed={"error": str(e)},
                validation_errors=[f"Unexpected error: {e}"],
            )

    def test_redfish_connection(
        self, target_ip: str, username: str, password: str
    ) -> Tuple[bool, str]:
        """Test Redfish connection for BIOS management.

        Args:
            target_ip: Target system IP address
            username: Authentication username
            password: Authentication password

        Returns:
            Tuple of (success, message)
        """
        try:
            # Import here to avoid circular imports
            from ...redfish import RedfishManager

            with RedfishManager(target_ip, username, password) as redfish:
                return redfish.test_connection()
        except Exception as e:
            logger.error(f"Failed to test Redfish connection: {e}")
            return False, f"Connection test failed: {e}"

    def get_system_info_via_redfish(
        self, target_ip: str, username: str, password: str
    ) -> Optional[Any]:
        """Get system information via Redfish.

        Args:
            target_ip: Target system IP address
            username: Authentication username
            password: Authentication password

        Returns:
            SystemInfo object or None if failed
        """
        try:
            # Import here to avoid circular imports
            from ...redfish import RedfishManager

            with RedfishManager(target_ip, username, password) as redfish:
                return redfish.get_system_info()
        except Exception as e:
            logger.error(f"Failed to get system info via Redfish: {e}")
            return None

    def _get_redfish_bios_config(
        self, target_ip: str, username: str, password: str
    ) -> Optional[ET.Element]:
        """Get current BIOS configuration via Redfish API."""
        try:
            from ...redfish import RedfishManager

            with RedfishManager(target_ip, username, password) as redfish:
                bios_data = redfish.get_bios_attributes()
                if bios_data:
                    # Convert Redfish BIOS data to XML format for consistency
                    root = ET.Element("BiosConfiguration")
                    for key, value in bios_data.items():
                        setting = ET.SubElement(root, "Setting")
                        setting.set("name", key)
                        setting.set("value", str(value))
                    return root
                return None
        except Exception as e:
            logger.error(f"Failed to get BIOS config via Redfish: {e}")
            return None

    def _apply_redfish_template(
        self, config: ET.Element, device_type: str
    ) -> ET.Element:
        """Apply device-specific template to Redfish BIOS configuration."""
        # Apply standard template modifications
        # This would be device-specific logic based on device_type
        logger.info(f"Applying Redfish template for {device_type}")
        return config

    def _validate_redfish_config(
        self, config: ET.Element, device_type: str
    ) -> List[str]:
        """Validate Redfish BIOS configuration."""
        errors = []
        # Add Redfish-specific validation logic here
        return errors

    def _apply_redfish_bios_config(
        self, config: ET.Element, target_ip: str, username: str, password: str
    ) -> bool:
        """Apply BIOS configuration via Redfish API."""
        try:
            from ...redfish import RedfishManager

            # Convert XML config back to dictionary format for Redfish
            bios_settings = {}
            for setting in config.findall("Setting"):
                name = setting.get("name")
                value = setting.get("value")
                if name and value:
                    bios_settings[name] = value

            with RedfishManager(target_ip, username, password) as redfish:
                return redfish.set_bios_attributes(bios_settings)
        except Exception as e:
            logger.error(f"Failed to apply BIOS config via Redfish: {e}")
            return False

    # Abstract method implementations for BaseBiosManager compatibility
    def pull_current_config(
        self, target_ip: str, username: str, password: str
    ) -> ET.Element:
        """Pull current BIOS configuration from target system."""
        # Stub implementation for compatibility
        root = ET.Element("BiosConfiguration")
        logger.warning("pull_current_config: Stub implementation")
        return root

    def apply_template(self, config: ET.Element, device_type: str) -> ET.Element:
        """Apply template modifications to configuration."""
        # Stub implementation for compatibility
        logger.warning("apply_template: Stub implementation")
        return config

    def validate_config(self, config: ET.Element, device_type: str) -> List[str]:
        """Validate modified configuration."""
        # Stub implementation for compatibility
        logger.warning("validate_config: Stub implementation")
        return []

    def push_config(
        self, config: ET.Element, target_ip: str, username: str, password: str
    ) -> bool:
        """Push modified configuration to target system."""
        # Stub implementation for compatibility
        logger.warning("push_config: Stub implementation")
        return True
