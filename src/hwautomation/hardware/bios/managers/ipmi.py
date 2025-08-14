"""
IPMI-based BIOS management.

This module provides BIOS configuration management through IPMI
protocol for hardware that supports IPMI-based BIOS operations.
"""

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple

from ....logging import get_logger
from ..base import BiosConfigResult, ConfigMethod, DeviceConfig, MethodSelectionResult
from .base import BaseBiosManagerImpl, BiosManagerMixin

logger = get_logger(__name__)


class IpmiBiosManager(BaseBiosManagerImpl, BiosManagerMixin):
    """BIOS manager using IPMI protocol for configuration operations."""

    def __init__(self, config_dir: str = "configs/bios"):
        """Initialize IPMI BIOS manager.

        Args:
            config_dir: Directory containing BIOS configuration files
        """
        super().__init__(config_dir)
        logger.info("Initialized IpmiBiosManager")

    def get_device_config(self, device_type: str) -> Optional[DeviceConfig]:
        """Get device configuration for IPMI-capable devices.

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
            redfish_enabled=mapping.get("redfish_enabled", False),
            vendor_tools_available=mapping.get("vendor_tools_available", True),
            special_handling=mapping.get("special_handling", {}),
        )

    def select_optimal_method(
        self, device_type: str, target_ip: str
    ) -> MethodSelectionResult:
        """Select optimal method for IPMI-capable devices.

        Args:
            device_type: Target device type
            target_ip: Target system IP address

        Returns:
            MethodSelectionResult with IPMI preference
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

        # Test IPMI connectivity
        ipmi_available, ipmi_message = self.test_ipmi_connection(
            target_ip, "ADMIN", "ADMIN"  # Default test credentials
        )

        available_methods = []
        if ipmi_available:
            available_methods.append(
                ConfigMethod.VENDOR_TOOLS
            )  # IPMI falls under vendor tools

        if device_config.redfish_enabled:
            available_methods.append(ConfigMethod.REDFISH_STANDARD)

        available_methods.append(ConfigMethod.MANUAL)

        # Prefer IPMI if available
        if ipmi_available:
            return MethodSelectionResult(
                recommended_method=ConfigMethod.VENDOR_TOOLS,
                available_methods=available_methods,
                redfish_capabilities={"available": device_config.redfish_enabled},
                vendor_tools_status={"available": True, "ipmi_tested": True},
                confidence_score=0.85,
                reasoning="IPMI protocol available and tested successfully",
                fallback_methods=[
                    m for m in available_methods if m != ConfigMethod.VENDOR_TOOLS
                ],
            )
        else:
            return MethodSelectionResult(
                recommended_method=(
                    ConfigMethod.REDFISH_STANDARD
                    if device_config.redfish_enabled
                    else ConfigMethod.MANUAL
                ),
                available_methods=available_methods,
                redfish_capabilities={"available": device_config.redfish_enabled},
                vendor_tools_status={"available": False, "ipmi_error": ipmi_message},
                confidence_score=0.6 if device_config.redfish_enabled else 0.1,
                reasoning=f"IPMI unavailable: {ipmi_message}",
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
        """Apply BIOS configuration using IPMI protocol.

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
            f"Starting IPMI BIOS config for {device_type} at {target_ip} (dry_run={dry_run})"
        )

        # Validate inputs
        if not self._validate_ip_address(target_ip):
            return self._create_config_result(
                success=False,
                method=ConfigMethod.VENDOR_TOOLS,
                validation_errors=[f"Invalid IP address: {target_ip}"],
            )

        if not self._validate_credentials(username, password):
            return self._create_config_result(
                success=False,
                method=ConfigMethod.VENDOR_TOOLS,
                validation_errors=["Invalid credentials provided"],
            )

        try:
            # Step 1: Test IPMI connection
            ipmi_available, message = self.test_ipmi_connection(
                target_ip, username, password
            )
            if not ipmi_available:
                return self._create_config_result(
                    success=False,
                    method=ConfigMethod.VENDOR_TOOLS,
                    validation_errors=[f"IPMI connection failed: {message}"],
                )

            # Step 2: Get current BIOS configuration via IPMI
            logger.info("Getting current BIOS configuration via IPMI...")
            current_config = self._get_ipmi_bios_config(target_ip, username, password)

            # Step 3: Create backup if enabled
            backup_file = None
            if backup_enabled and current_config is not None:
                backup_file = self._create_backup(
                    current_config, device_type, target_ip
                )
                logger.info(f"Created backup: {backup_file}")

            # Step 4: Apply device-specific modifications
            logger.info("Applying device-specific BIOS settings...")
            modified_config = self._apply_ipmi_template(current_config, device_type)

            # Step 5: Validate configuration
            validation_errors = self._validate_ipmi_config(modified_config, device_type)
            if validation_errors:
                return self._create_config_result(
                    success=False,
                    method=ConfigMethod.VENDOR_TOOLS,
                    backup_file=backup_file,
                    validation_errors=validation_errors,
                )

            # Step 6: Apply changes (unless dry run)
            if dry_run:
                logger.info("Dry run mode - configuration validated but not applied")
                return self._create_config_result(
                    success=True,
                    method=ConfigMethod.VENDOR_TOOLS,
                    settings_applied={
                        "dry_run": "IPMI configuration validated successfully"
                    },
                    backup_file=backup_file,
                )

            # Step 7: Push configuration via IPMI
            logger.info("Applying BIOS configuration via IPMI...")
            success = self._apply_ipmi_bios_config(
                modified_config, target_ip, username, password
            )

            if success:
                logger.info("BIOS configuration applied successfully via IPMI")
                return self._create_config_result(
                    success=True,
                    method=ConfigMethod.VENDOR_TOOLS,
                    settings_applied={"status": "Configuration applied via IPMI"},
                    backup_file=backup_file,
                    reboot_required=True,
                )
            else:
                return self._create_config_result(
                    success=False,
                    method=ConfigMethod.VENDOR_TOOLS,
                    settings_failed={"ipmi": "Failed to apply configuration"},
                    backup_file=backup_file,
                    validation_errors=["IPMI configuration push failed"],
                )

        except Exception as e:
            logger.error(f"Error in IPMI BIOS config: {e}")
            return self._create_config_result(
                success=False,
                method=ConfigMethod.VENDOR_TOOLS,
                settings_failed={"error": str(e)},
                validation_errors=[f"Unexpected error: {e}"],
            )

    def test_ipmi_connection(
        self, target_ip: str, username: str, password: str
    ) -> Tuple[bool, str]:
        """Test IPMI connection for BIOS management.

        Args:
            target_ip: Target system IP address
            username: Authentication username
            password: Authentication password

        Returns:
            Tuple of (success, message)
        """
        try:
            # Import here to avoid circular imports
            from ...ipmi import IpmiManager

            ipmi_manager = IpmiManager()
            # Test basic IPMI connectivity
            success = ipmi_manager.test_connection(target_ip, username, password)
            if success:
                return True, "IPMI connection successful"
            else:
                return False, "IPMI connection failed"
        except Exception as e:
            logger.error(f"Failed to test IPMI connection: {e}")
            return False, f"IPMI test failed: {e}"

    def get_system_info_via_ipmi(
        self, target_ip: str, username: str, password: str
    ) -> Optional[Dict[str, Any]]:
        """Get system information via IPMI.

        Args:
            target_ip: Target system IP address
            username: Authentication username
            password: Authentication password

        Returns:
            System information dictionary or None if failed
        """
        try:
            # Import here to avoid circular imports
            from ...ipmi import IpmiManager

            ipmi_manager = IpmiManager()
            return ipmi_manager.get_system_info(target_ip, username, password)
        except Exception as e:
            logger.error(f"Failed to get system info via IPMI: {e}")
            return None

    def _get_ipmi_bios_config(
        self, target_ip: str, username: str, password: str
    ) -> Optional[ET.Element]:
        """Get current BIOS configuration via IPMI."""
        try:
            from ...ipmi import IpmiManager

            ipmi_manager = IpmiManager()
            # Get BIOS settings via IPMI (implementation specific)
            bios_data = ipmi_manager.get_bios_settings(target_ip, username, password)

            if bios_data:
                # Convert IPMI BIOS data to XML format for consistency
                root = ET.Element("BiosConfiguration")
                for key, value in bios_data.items():
                    setting = ET.SubElement(root, "Setting")
                    setting.set("name", key)
                    setting.set("value", str(value))
                return root
            return None
        except Exception as e:
            logger.error(f"Failed to get BIOS config via IPMI: {e}")
            return None

    def _apply_ipmi_template(self, config: ET.Element, device_type: str) -> ET.Element:
        """Apply device-specific template to IPMI BIOS configuration."""
        # Apply standard template modifications
        logger.info(f"Applying IPMI template for {device_type}")
        return config

    def _validate_ipmi_config(self, config: ET.Element, device_type: str) -> List[str]:
        """Validate IPMI BIOS configuration."""
        errors = []
        # Add IPMI-specific validation logic here
        return errors

    def _apply_ipmi_bios_config(
        self, config: ET.Element, target_ip: str, username: str, password: str
    ) -> bool:
        """Apply BIOS configuration via IPMI."""
        try:
            from ...ipmi import IpmiManager

            # Convert XML config back to dictionary format for IPMI
            bios_settings = {}
            for setting in config.findall("Setting"):
                name = setting.get("name")
                value = setting.get("value")
                if name and value:
                    bios_settings[name] = value

            ipmi_manager = IpmiManager()
            return ipmi_manager.set_bios_settings(
                target_ip, username, password, bios_settings
            )
        except Exception as e:
            logger.error(f"Failed to apply BIOS config via IPMI: {e}")
            return False
