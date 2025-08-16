"""Configuration loading and management for BIOS system.

This module handles loading and validation of BIOS configuration files
including device mappings, template rules, and preserve settings.

Updated to use the unified configuration system with backward compatibility.
"""

import os
from typing import Any, Dict, List

import yaml

from ....config import BiosConfigAdapter, UnifiedConfigLoader
from ....logging import get_logger
from ..base import BaseConfigLoader

logger = get_logger(__name__)


class ConfigurationLoader(BaseConfigLoader):
    """Loads and manages BIOS configuration files.

    Updated to use unified configuration with backward compatibility.
    Falls back to legacy files if unified config is not available.
    """

    def __init__(self, config_dir: str):
        """Initialize configuration loader.

        Args:
            config_dir: Directory containing BIOS configuration files
        """
        super().__init__(config_dir)
        self.device_mappings_file = os.path.join(config_dir, "device_mappings.yaml")
        self.template_rules_file = os.path.join(config_dir, "template_rules.yaml")
        self.preserve_settings_file = os.path.join(config_dir, "preserve_settings.yaml")

        # Initialize unified config system with fallback
        self._use_unified = self._check_unified_config_available()
        if self._use_unified:
            try:
                self.unified_loader = UnifiedConfigLoader()
                self.bios_adapter = BiosConfigAdapter(self.unified_loader)
                logger.info("Using unified configuration system for BIOS config")
            except Exception as e:
                logger.warning(
                    f"Failed to initialize unified config, falling back to legacy: {e}"
                )
                self._use_unified = False
        else:
            logger.info("Using legacy configuration files for BIOS config")

    def _check_unified_config_available(self) -> bool:
        """Check if unified configuration is available."""
        try:
            # Check if unified config file exists
            unified_path = self._get_unified_config_path()
            return os.path.exists(unified_path)
        except Exception:
            return False

    def _get_unified_config_path(self) -> str:
        """Get path to unified configuration file."""
        # Look for unified config relative to this file's location
        # Go up from: src/hwautomation/hardware/bios/config/loader.py to project root
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
                )
            )
        )
        return os.path.join(
            project_root, "configs", "devices", "unified_device_config.yaml"
        )

    def load_config(self) -> Dict[str, Any]:
        """Load all configuration files.

        Returns:
            Dictionary containing all loaded configurations
        """
        return {
            "device_mappings": self.load_device_mappings(),
            "template_rules": self.load_template_rules(),
            "preserve_settings": self.load_preserve_settings(),
        }

    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to files.

        Args:
            config: Configuration dictionary to save

        Returns:
            True if successful, False otherwise
        """
        try:
            if "device_mappings" in config:
                self._save_yaml_file(
                    self.device_mappings_file, config["device_mappings"]
                )

            if "template_rules" in config:
                self._save_yaml_file(self.template_rules_file, config["template_rules"])

            if "preserve_settings" in config:
                self._save_yaml_file(
                    self.preserve_settings_file, config["preserve_settings"]
                )

            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration structure and content.

        Args:
            config: Configuration to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Validate device mappings
        if "device_mappings" in config:
            errors.extend(self._validate_device_mappings(config["device_mappings"]))

        # Validate template rules
        if "template_rules" in config:
            errors.extend(self._validate_template_rules(config["template_rules"]))

        # Validate preserve settings
        if "preserve_settings" in config:
            errors.extend(self._validate_preserve_settings(config["preserve_settings"]))

        return errors

    def load_device_mappings(self) -> Dict[str, Any]:
        """Load device mappings configuration.

        Uses unified configuration if available, otherwise falls back to legacy file.

        Returns:
            Dictionary containing device mappings
        """
        if self._use_unified:
            try:
                # Use unified configuration through adapter
                return self.bios_adapter.load_device_mappings()
            except Exception as e:
                logger.warning(
                    f"Failed to load from unified config, falling back to legacy: {e}"
                )
                # Fall back to legacy method

        # Legacy method
        raw_data = self._load_yaml_file(self.device_mappings_file, {})

        # Handle nested structure if present
        if "device_types" in raw_data:
            return raw_data["device_types"]
        else:
            return raw_data

    def load_template_rules(self) -> Dict[str, Any]:
        """Load template rules configuration.

        Returns:
            Dictionary containing template rules
        """
        return self._load_yaml_file(self.template_rules_file, {})

    def load_preserve_settings(self) -> Dict[str, Any]:
        """Load preserve settings configuration.

        Returns:
            Dictionary containing preserve settings
        """
        return self._load_yaml_file(self.preserve_settings_file, {})

    def _load_yaml_file(self, file_path: str, default: Any = None) -> Any:
        """Load YAML file with error handling.

        Args:
            file_path: Path to YAML file
            default: Default value if file doesn't exist or fails to load

        Returns:
            Loaded data or default value
        """
        if not os.path.exists(file_path):
            logger.warning(f"Configuration file not found: {file_path}")
            return default if default is not None else {}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data is None:
                    logger.warning(f"Empty configuration file: {file_path}")
                    return default if default is not None else {}
                return data
        except Exception as e:
            logger.error(f"Failed to load YAML file {file_path}: {e}")
            return default if default is not None else {}

    def _save_yaml_file(self, file_path: str, data: Any) -> None:
        """Save data to YAML file.

        Args:
            file_path: Path to YAML file
            data: Data to save
        """
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)

    def _validate_device_mappings(self, mappings: Dict[str, Any]) -> List[str]:
        """Validate device mappings structure.

        Args:
            mappings: Device mappings to validate

        Returns:
            List of validation errors
        """
        errors = []

        if not isinstance(mappings, dict):
            errors.append("Device mappings must be a dictionary")
            return errors

        for device_type, config in mappings.items():
            if not isinstance(config, dict):
                errors.append(
                    f"Device mapping for '{device_type}' must be a dictionary"
                )
                continue

            # Check required fields
            required_fields = ["manufacturer", "model", "motherboard"]
            for field in required_fields:
                if field not in config:
                    errors.append(
                        f"Missing required field '{field}' in device mapping for '{device_type}'"
                    )

            # Validate motherboard field
            if "motherboard" in config and not isinstance(config["motherboard"], list):
                errors.append(f"Motherboard field for '{device_type}' must be a list")

        return errors

    def _validate_template_rules(self, rules: Dict[str, Any]) -> List[str]:
        """Validate template rules structure.

        Args:
            rules: Template rules to validate

        Returns:
            List of validation errors
        """
        errors = []

        if not isinstance(rules, dict):
            errors.append("Template rules must be a dictionary")
            return errors

        for device_type, device_rules in rules.items():
            if not isinstance(device_rules, dict):
                errors.append(
                    f"Template rules for '{device_type}' must be a dictionary"
                )
                continue

            # Validate rule structure
            for setting_name, setting_rules in device_rules.items():
                if not isinstance(setting_rules, dict):
                    errors.append(
                        f"Template rule '{setting_name}' for '{device_type}' must be a dictionary"
                    )
                    continue

        return errors

    # Enhanced methods using unified configuration
    def get_device_by_type(self, device_type: str) -> Dict[str, Any]:
        """
        Get complete device information by type.

        Uses unified config if available for enhanced information.

        Args:
            device_type: Device type identifier

        Returns:
            Dictionary with device information
        """
        if self._use_unified:
            try:
                device_info = self.unified_loader.get_device_by_type(device_type)
                if device_info:
                    return {
                        "device_type": device_info.device_type,
                        "vendor": device_info.vendor,
                        "motherboard": device_info.motherboard,
                        "config": device_info.device_config,
                        "vendor_info": device_info.vendor_info,
                        "motherboard_info": device_info.motherboard_info,
                    }
            except Exception as e:
                logger.warning(f"Failed to get device from unified config: {e}")

        # Fallback to legacy device mappings
        device_mappings = self.load_device_mappings()
        return device_mappings.get(device_type, {})

    def get_motherboards_for_device(self, device_type: str) -> List[str]:
        """
        Get motherboards for a device type.

        Args:
            device_type: Device type identifier

        Returns:
            List of motherboard names
        """
        if self._use_unified:
            try:
                device_info = self.unified_loader.get_device_by_type(device_type)
                return [device_info.motherboard] if device_info else []
            except Exception as e:
                logger.warning(f"Failed to get motherboards from unified config: {e}")

        # Fallback to legacy
        device_config = self.load_device_mappings().get(device_type, {})
        return device_config.get("motherboards", [])

    def get_vendor_for_device(self, device_type: str) -> str:
        """
        Get vendor for a device type.

        Args:
            device_type: Device type identifier

        Returns:
            Vendor name or empty string if not found
        """
        if self._use_unified:
            try:
                device_info = self.unified_loader.get_device_by_type(device_type)
                return device_info.vendor if device_info else ""
            except Exception as e:
                logger.warning(f"Failed to get vendor from unified config: {e}")

        # Fallback to legacy
        device_config = self.load_device_mappings().get(device_type, {})
        return device_config.get("vendor", "")

    def list_all_device_types(self) -> List[str]:
        """
        List all available device types.

        Returns:
            Sorted list of device type names
        """
        if self._use_unified:
            try:
                return self.unified_loader.list_all_device_types()
            except Exception as e:
                logger.warning(f"Failed to list devices from unified config: {e}")

        # Fallback to legacy
        device_mappings = self.load_device_mappings()
        return sorted(device_mappings.keys())

    def validate_device_type(self, device_type: str) -> bool:
        """
        Validate that a device type exists.

        Args:
            device_type: Device type to validate

        Returns:
            True if device type exists, False otherwise
        """
        if self._use_unified:
            try:
                return self.unified_loader.validate_device_type(device_type)
            except Exception as e:
                logger.warning(f"Failed to validate device from unified config: {e}")

        # Fallback to legacy
        device_mappings = self.load_device_mappings()
        return device_type in device_mappings

    def get_configuration_stats(self) -> Dict[str, Any]:
        """
        Get configuration statistics.

        Returns:
            Dictionary with configuration statistics
        """
        if self._use_unified:
            try:
                stats = self.unified_loader.get_stats()
                return {
                    "source": "unified",
                    "vendors": stats.vendors,
                    "motherboards": stats.motherboards,
                    "device_types": stats.device_types,
                    "version": self.unified_loader.get_version(),
                    "last_updated": self.unified_loader.get_last_updated(),
                }
            except Exception as e:
                logger.warning(f"Failed to get stats from unified config: {e}")

        # Fallback to legacy
        device_mappings = self.load_device_mappings()
        vendors = set()
        motherboards = set()

        for device_config in device_mappings.values():
            if "vendor" in device_config:
                vendors.add(device_config["vendor"])
            if "motherboards" in device_config:
                motherboards.update(device_config["motherboards"])

        return {
            "source": "legacy",
            "vendors": len(vendors),
            "motherboards": len(motherboards),
            "device_types": len(device_mappings),
            "version": "legacy",
            "last_updated": "unknown",
        }

    def _validate_template_rules(self, rules: Dict[str, Any]) -> List[str]:
        """Validate template rules structure.

        Args:
            rules: Template rules to validate

        Returns:
            List of validation errors
        """
        errors = []

        if not isinstance(rules, dict):
            errors.append("Template rules must be a dictionary")
            return errors

        for device_type, device_rules in rules.items():
            if not isinstance(device_rules, dict):
                errors.append(
                    f"Template rules for '{device_type}' must be a dictionary"
                )
                continue

            # Validate rule structure
            for setting_name, setting_rules in device_rules.items():
                if not isinstance(setting_rules, dict):
                    errors.append(
                        f"Template rule '{setting_name}' for '{device_type}' must be a dictionary"
                    )
                    continue

                # Check for required rule fields
                if "action" not in setting_rules:
                    errors.append(
                        f"Missing 'action' field in rule '{setting_name}' for '{device_type}'"
                    )

        return errors

    def _validate_preserve_settings(self, settings: Dict[str, Any]) -> List[str]:
        """Validate preserve settings structure.

        Args:
            settings: Preserve settings to validate

        Returns:
            List of validation errors
        """
        errors = []

        if not isinstance(settings, dict):
            errors.append("Preserve settings must be a dictionary")
            return errors

        for device_type, preserved_settings in settings.items():
            if not isinstance(preserved_settings, list):
                errors.append(f"Preserve settings for '{device_type}' must be a list")

        return errors

    def reload_configurations(self) -> None:
        """Reload all configuration files."""
        logger.info("Reloading BIOS configurations...")
        # This method can be called to refresh configs without recreating the loader
        pass

    def get_config_file_paths(self) -> Dict[str, str]:
        """Get paths to all configuration files.

        Returns:
            Dictionary mapping config names to file paths
        """
        return {
            "device_mappings": self.device_mappings_file,
            "template_rules": self.template_rules_file,
            "preserve_settings": self.preserve_settings_file,
        }
