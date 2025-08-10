"""Main BIOS configuration manager - coordinates all BIOS operations.

This module provides the primary interface for BIOS configuration management,
orchestrating between device handlers, configuration loaders, parsers, and
operation handlers to provide a unified API.
"""

import os
import tempfile
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Type, Union

from ...logging import get_logger
from .base import (
    BaseBiosManager,
    BaseDeviceHandler,
    BiosConfigResult,
    ConfigMethod,
    DeviceConfig,
    MethodSelectionResult,
    OperationStatus,
)
from .config.loader import ConfigurationLoader
from .config.validator import ConfigurationValidator
from .devices.factory import DeviceHandlerFactory
from .operations.pull import PullOperationHandler
from .operations.push import PushOperationHandler
from .operations.validate import ValidationOperationHandler
from .parsers.factory import ParserFactory

logger = get_logger(__name__)


class BiosConfigManager(BaseBiosManager):
    """Main BIOS configuration manager.

    Coordinates all BIOS configuration operations including device detection,
    method selection, configuration pulling/pushing, and validation.
    """

    def __init__(self, config_dir: str = "configs/bios"):
        """Initialize BIOS configuration manager.

        Args:
            config_dir: Directory containing BIOS configuration files
        """
        super().__init__()
        self.config_dir = config_dir

        # Initialize core components
        self.config_loader = ConfigurationLoader(config_dir)
        self.config_validator = ConfigurationValidator(config_dir)
        self.device_factory = DeviceHandlerFactory()
        self.parser_factory = ParserFactory()

        # Initialize operation handlers
        self.pull_handler = PullOperationHandler()
        self.push_handler = PushOperationHandler()
        self.validation_handler = ValidationOperationHandler()

        # Load configurations
        self._load_configurations()

        logger.info(f"Initialized BiosConfigManager with config_dir: {config_dir}")

    def _load_configurations(self) -> None:
        """Load all configuration files."""
        try:
            self.device_mappings = self.config_loader.load_device_mappings()
            self.template_rules = self.config_loader.load_template_rules()
            self.preserve_settings = self.config_loader.load_preserve_settings()
            logger.info("Successfully loaded all BIOS configurations")
        except Exception as e:
            logger.error(f"Failed to load BIOS configurations: {e}")
            # Initialize with empty configs to prevent crashes
            self.device_mappings = {}
            self.template_rules = {}
            self.preserve_settings = {}

    def get_device_config(self, device_type: str) -> Optional[DeviceConfig]:
        """Get device configuration for the specified device type.

        Args:
            device_type: Target device type (e.g., 'a1.c5.large')

        Returns:
            DeviceConfig object or None if not found
        """
        if device_type not in self.device_mappings:
            logger.warning(f"Device type '{device_type}' not found in mappings")
            return None

        mapping = self.device_mappings[device_type]

        # Extract vendor information from hardware_specs if available
        vendor = "Unknown"
        if "hardware_specs" in mapping and "vendor" in mapping["hardware_specs"]:
            vendor = mapping["hardware_specs"]["vendor"].title()
        elif "manufacturer" in mapping:
            vendor = mapping["manufacturer"]

        # Map vendor names to standard format
        vendor_mapping = {"hpe": "HPE", "dell": "Dell", "supermicro": "Supermicro"}
        vendor = vendor_mapping.get(vendor.lower(), vendor)

        # Extract model information
        model = "Unknown"
        if "hardware_specs" in mapping and "cpu_name" in mapping["hardware_specs"]:
            model = mapping["hardware_specs"]["cpu_name"]
        elif "model" in mapping:
            model = mapping["model"]

        # Create motherboard list
        motherboard = []
        if "motherboard" in mapping:
            motherboard = mapping["motherboard"]
        else:
            # Create from vendor and model info
            motherboard = [vendor, model]

        return DeviceConfig(
            device_type=device_type,
            manufacturer=vendor,
            model=model,
            motherboard=motherboard,
            redfish_enabled=mapping.get(
                "redfish_enabled", True
            ),  # Assume true for modern servers
            vendor_tools_available=mapping.get("vendor_tools_available", True),
            special_handling=mapping.get("special_handling", {}),
        )

    def select_optimal_method(
        self, device_type: str, target_ip: str
    ) -> MethodSelectionResult:
        """Select the optimal BIOS configuration method for the device.

        Args:
            device_type: Target device type
            target_ip: Target system IP address

        Returns:
            MethodSelectionResult with recommended method and analysis
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

        # Get device handler
        handler = self.device_factory.get_handler(device_type, device_config)
        if not handler:
            return MethodSelectionResult(
                recommended_method=ConfigMethod.MANUAL,
                available_methods=[ConfigMethod.MANUAL],
                redfish_capabilities={},
                vendor_tools_status={},
                confidence_score=0.0,
                reasoning=f"No handler available for device type: {device_type}",
                fallback_methods=[],
            )

        # Get supported methods from handler
        supported_methods = handler.get_supported_methods()

        # For now, prefer Redfish if available, otherwise use vendor tools
        if ConfigMethod.REDFISH_STANDARD in supported_methods:
            recommended = ConfigMethod.REDFISH_STANDARD
            confidence = 0.9
            reasoning = "Redfish standard method preferred for compatibility"
        elif ConfigMethod.VENDOR_TOOLS in supported_methods:
            recommended = ConfigMethod.VENDOR_TOOLS
            confidence = 0.8
            reasoning = "Vendor tools method selected as fallback"
        else:
            recommended = ConfigMethod.MANUAL
            confidence = 0.1
            reasoning = "No automated methods available"

        return MethodSelectionResult(
            recommended_method=recommended,
            available_methods=supported_methods,
            redfish_capabilities={"available": device_config.redfish_enabled},
            vendor_tools_status={"available": device_config.vendor_tools_available},
            confidence_score=confidence,
            reasoning=reasoning,
            fallback_methods=[m for m in supported_methods if m != recommended],
        )

    def pull_current_config(
        self, target_ip: str, username: str, password: str
    ) -> ET.Element:
        """Pull current BIOS configuration from target system.

        Args:
            target_ip: Target system IP address
            username: Authentication username
            password: Authentication password

        Returns:
            XML Element containing current configuration
        """
        return self.pull_handler.execute(
            target_ip=target_ip, username=username, password=password
        )

    def apply_template(self, config: ET.Element, device_type: str) -> ET.Element:
        """Apply template modifications to configuration.

        Args:
            config: Current configuration XML
            device_type: Target device type

        Returns:
            Modified configuration XML
        """
        # Get device handler
        device_config = self.get_device_config(device_type)
        if not device_config:
            logger.warning(f"No device config for {device_type}, returning unmodified")
            return config

        handler = self.device_factory.get_handler(device_type, device_config)
        if not handler:
            logger.warning(f"No handler for {device_type}, returning unmodified")
            return config

        # Apply device-specific template modifications
        return handler.apply_device_specific_settings(config)

    def validate_config(self, config: ET.Element, device_type: str) -> List[str]:
        """Validate modified configuration.

        Args:
            config: Configuration XML to validate
            device_type: Target device type

        Returns:
            List of validation errors (empty if valid)
        """
        return self.validation_handler.execute(
            config=config,
            device_type=device_type,
            device_mappings=self.device_mappings,
            template_rules=self.template_rules,
        )

    def push_config(
        self, config: ET.Element, target_ip: str, username: str, password: str
    ) -> bool:
        """Push modified configuration to target system.

        Args:
            config: Modified configuration XML
            target_ip: Target system IP address
            username: Authentication username
            password: Authentication password

        Returns:
            True if successful, False otherwise
        """
        result = self.push_handler.execute(
            config=config, target_ip=target_ip, username=username, password=password
        )
        return result.success

    def apply_bios_config_smart(
        self,
        device_type: str,
        target_ip: str,
        username: str,
        password: str,
        dry_run: bool = False,
        backup_enabled: bool = True,
    ) -> BiosConfigResult:
        """Apply BIOS configuration using smart method selection.

        This is the main high-level interface for BIOS configuration that
        automatically selects the best method and handles the full workflow.

        Args:
            device_type: Target device type (e.g., 'a1.c5.large')
            target_ip: Target system IP address
            username: Authentication username
            password: Authentication password
            dry_run: If True, validate but don't apply changes
            backup_enabled: If True, create backup before changes

        Returns:
            BiosConfigResult with operation details
        """
        logger.info(
            f"Starting smart BIOS config for {device_type} at {target_ip} (dry_run={dry_run})"
        )

        try:
            # Step 1: Select optimal method
            method_result = self.select_optimal_method(device_type, target_ip)
            logger.info(
                f"Selected method: {method_result.recommended_method.value} "
                f"(confidence: {method_result.confidence_score:.2f})"
            )

            # Step 2: Pull current configuration
            logger.info("Pulling current BIOS configuration...")
            current_config = self.pull_current_config(target_ip, username, password)

            # Step 3: Create backup if enabled
            backup_file = None
            if backup_enabled:
                backup_file = self._create_backup(
                    current_config, device_type, target_ip
                )
                logger.info(f"Created backup: {backup_file}")

            # Step 4: Apply template modifications
            logger.info("Applying template modifications...")
            modified_config = self.apply_template(current_config, device_type)

            # Step 5: Validate modified configuration
            logger.info("Validating modified configuration...")
            validation_errors = self.validate_config(modified_config, device_type)

            if validation_errors:
                logger.warning(f"Validation errors found: {validation_errors}")
                return BiosConfigResult(
                    success=False,
                    method_used=method_result.recommended_method,
                    settings_applied={},
                    settings_failed={},
                    backup_file=backup_file,
                    validation_errors=validation_errors,
                )

            # Step 6: Apply changes (unless dry run)
            if dry_run:
                logger.info("Dry run mode - configuration validated but not applied")
                return BiosConfigResult(
                    success=True,
                    method_used=method_result.recommended_method,
                    settings_applied={
                        "dry_run": "Configuration validated successfully"
                    },
                    settings_failed={},
                    backup_file=backup_file,
                    validation_errors=[],
                    reboot_required=False,
                )

            # Step 7: Push configuration
            logger.info("Pushing modified configuration...")
            push_success = self.push_config(
                modified_config, target_ip, username, password
            )

            if push_success:
                logger.info("BIOS configuration applied successfully")
                return BiosConfigResult(
                    success=True,
                    method_used=method_result.recommended_method,
                    settings_applied={"status": "Configuration applied successfully"},
                    settings_failed={},
                    backup_file=backup_file,
                    validation_errors=[],
                )
            else:
                logger.error("Failed to push BIOS configuration")
                return BiosConfigResult(
                    success=False,
                    method_used=method_result.recommended_method,
                    settings_applied={},
                    settings_failed={"push": "Failed to apply configuration"},
                    backup_file=backup_file,
                    validation_errors=["Configuration push failed"],
                )

        except Exception as e:
            logger.error(f"Error in smart BIOS config: {e}")
            return BiosConfigResult(
                success=False,
                method_used=ConfigMethod.MANUAL,
                settings_applied={},
                settings_failed={"error": str(e)},
                validation_errors=[f"Unexpected error: {e}"],
            )

    def _create_backup(
        self, config: ET.Element, device_type: str, target_ip: str
    ) -> str:
        """Create backup of current configuration.

        Args:
            config: Current configuration XML
            device_type: Device type for naming
            target_ip: Target IP for naming

        Returns:
            Path to backup file
        """
        # Create backup filename with timestamp
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"bios_backup_{device_type}_{target_ip}_{timestamp}.xml"

        # Use temp directory for backups
        backup_dir = os.path.join(tempfile.gettempdir(), "bios_backups")
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, backup_filename)

        # Save backup
        ET.indent(config)
        tree = ET.ElementTree(config)
        tree.write(backup_path, encoding="utf-8", xml_declaration=True)

        return backup_path

    def list_available_device_types(self) -> List[str]:
        """Get list of all available device types.

        Returns:
            List of device type strings
        """
        return list(self.device_mappings.keys())

    def get_device_type_info(self, device_type: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a device type.

        Args:
            device_type: Device type to query

        Returns:
            Dictionary with device information or None if not found
        """
        device_config = self.get_device_config(device_type)
        if not device_config:
            return None

        # Get handler to check supported methods
        handler = self.device_factory.get_handler(device_type, device_config)
        supported_methods = handler.get_supported_methods() if handler else []

        return {
            "device_type": device_config.device_type,
            "manufacturer": device_config.manufacturer,
            "model": device_config.model,
            "motherboard": device_config.motherboard,
            "redfish_enabled": device_config.redfish_enabled,
            "vendor_tools_available": device_config.vendor_tools_available,
            "supported_methods": [m.value for m in supported_methods],
            "special_handling": device_config.special_handling,
        }

    async def apply_bios_config_phase3(
        self,
        device_type: str,
        target_ip: str,
        username: str = "ADMIN",
        password: Optional[str] = None,
        dry_run: bool = False,
        prefer_performance: bool = True,
        enable_monitoring: bool = True,
    ) -> Dict[str, Any]:
        """
        Real-time monitored BIOS configuration with advanced error recovery.
        
        This is a bridge method that delegates to the advanced monitoring functionality.
        TODO: Migrate the full phase3 implementation to the modular system.
        
        Args:
            device_type: Device type template to apply
            target_ip: Target system IP address
            username: BMC username
            password: BMC password
            dry_run: If True, only show what would be changed
            prefer_performance: If True, optimize for speed over reliability
            enable_monitoring: If True, enable real-time progress monitoring

        Returns:
            Dictionary with operation results including monitoring data
        """
        # For now, delegate to the regular apply_bios_config_smart method
        # TODO: Implement full phase3 monitoring capabilities in modular system
        logger.warning(
            "apply_bios_config_phase3 called - using fallback to apply_bios_config_smart. "
            "Full phase3 monitoring implementation needed in modular system."
        )
        
        result = self.apply_bios_config_smart(
            device_type=device_type,
            target_ip=target_ip,
            username=username,
            password=password,
            dry_run=dry_run
        )
        
        # Convert BiosConfigResult to phase3 format
        return {
            "success": result.success,
            "target_ip": target_ip,
            "device_type": device_type,
            "operation_id": None,
            "monitoring_enabled": enable_monitoring,
            "method_analysis": {"method": result.method_used.value if result.method_used else "unknown"},
            "execution_phases": [{"phase": "configuration", "success": result.success}],
            "real_time_progress": [],
            "error_recovery_actions": [],
            "validation_results": {"success": result.success},
            "performance_metrics": {},
            "dry_run": dry_run,
            "settings_applied": result.settings_applied,
            "settings_failed": result.settings_failed,
            "validation_errors": result.validation_errors or [],
        }

    def get_device_types(self) -> List[str]:
        """Get list of available device types."""
        device_mappings = self.config_loader.load_device_mappings()
        return list(device_mappings.get("device_types", {}).keys())

    def test_redfish_connection(self, target_ip: str, username: str, password: str) -> tuple[bool, str]:
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
            from ..redfish import RedfishManager
            
            with RedfishManager(target_ip, username, password) as redfish:
                return redfish.test_connection()
        except Exception as e:
            logger.error(f"Failed to test Redfish connection: {e}")
            return False, f"Connection test failed: {e}"

    def get_system_info_via_redfish(self, target_ip: str, username: str, password: str):
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
            from ..redfish import RedfishManager
            
            with RedfishManager(target_ip, username, password) as redfish:
                return redfish.get_system_info()
        except Exception as e:
            logger.error(f"Failed to get system info via Redfish: {e}")
            return None

    def determine_bios_config_method(self, target_ip: str, device_type: str, username: str, password: str) -> str:
        """Determine the best BIOS configuration method.
        
        Args:
            target_ip: Target system IP address
            device_type: Device type identifier
            username: Authentication username
            password: Authentication password
            
        Returns:
            Method string: 'redfish', 'vendor_tool', or 'hybrid'
        """
        try:
            # Import here to avoid circular imports
            from ..redfish import RedfishManager
            
            with RedfishManager(target_ip, username, password) as redfish:
                # Test connection first
                success, _ = redfish.test_connection()
                if not success:
                    return "vendor_tool"
                
                # Check capabilities
                capabilities = redfish.discover_capabilities()
                if capabilities and capabilities.supports_bios_config:
                    return "redfish"
                else:
                    return "vendor_tool"
        except Exception as e:
            logger.error(f"Failed to determine BIOS config method: {e}")
            return "vendor_tool"
