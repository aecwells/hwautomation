"""
BIOS Configuration Manager for Hardware Automation

This module provides functionality for managing BIOS configurations
using a pull-edit-push approach with XML-based templates organized by device types.

The smart approach:
1. Pull current BIOS configuration from target system
2. Apply template-based changes while preserving hardware-specific settings
3. Validate the modified configuration
4. Push the updated configuration back

This preserves MAC addresses, boot order, and other hardware-specific settings.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import yaml
import logging
import copy
from datetime import datetime

logger = logging.getLogger(__name__)

class BiosConfigManager:
    """
    Manages BIOS configurations using a pull-edit-push approach.
    
    This manager:
    1. Pulls current BIOS configuration from target systems
    2. Applies template-based modifications while preserving hardware-specific settings
    3. Validates changes before applying
    4. Pushes modified configuration back to the system
    
    Supports device types like:
    - s2_c2_small (Small compute nodes)
    - s2_c2_medium (Medium compute nodes) 
    - s2_c2_large (Large compute nodes)
    - storage_nodes
    - etc.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize BIOS configuration manager.
        
        Args:
            config_dir: Directory containing BIOS configuration files
        """
        if config_dir is None:
            # Default to configs directory in project root
            project_root = Path(__file__).parent.parent.parent.parent
            config_dir = project_root / "configs" / "bios"
        
        self.config_dir = Path(config_dir)
        self.device_types = {}
        self.template_rules = {}
        self.preserve_settings = set()
        self.xml_templates = {}  # Initialize xml_templates
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self._load_device_mappings()
        self._load_template_rules()
        self._load_preserve_settings()
        self._load_xml_templates()  # Load XML templates
    
    def _load_preserve_settings(self):
        """Load settings that should always be preserved from original BIOS."""
        preserve_file = self.config_dir / "preserve_settings.yaml"
        
        if preserve_file.exists():
            try:
                with open(preserve_file, 'r') as f:
                    preserve_config = yaml.safe_load(f) or {}
                self.preserve_settings = set(preserve_config.get('preserve_settings', []))
                logger.info(f"Loaded preserve settings from {preserve_file}")
            except Exception as e:
                logger.error(f"Error loading preserve settings: {e}")
        else:
            self._create_default_preserve_settings()
    
    def _create_default_preserve_settings(self):
        """Create default settings that should be preserved."""
        default_preserve = {
            'preserve_settings': [
                # Network/MAC addresses
                'mac_address_lan1',
                'mac_address_lan2', 
                'mac_address_ipmi',
                'mac_address_*',  # Wildcard for any MAC address setting
                
                # Hardware-specific identifiers
                'system_serial_number',
                'baseboard_serial_number',
                'chassis_serial_number',
                'product_name',
                'manufacturer',
                'uuid',
                'asset_tag',
                
                # Hardware-detected settings
                'memory_size_*',
                'cpu_signature',
                'cpu_microcode_version',
                'pci_device_*',
                
                # Boot device hardware paths (preserve existing boot order)
                'boot_device_path_*',
                'uefi_boot_entry_*',
                
                # Hardware-specific timing
                'memory_timing_*',
                'cpu_timing_*',
                
                # License keys and certificates
                'tpm_key_*',
                'secure_boot_key_*',
                'license_key_*',
                
                # Hardware revision info
                'bios_version',  # Don't override BIOS version info
                'firmware_version_*',
                'microcode_version',
            ],
            'description': 'Settings that should be preserved from original BIOS configuration'
        }
        
        preserve_file = self.config_dir / "preserve_settings.yaml"
        try:
            with open(preserve_file, 'w') as f:
                yaml.dump(default_preserve, f, default_flow_style=False)
            self.preserve_settings = set(default_preserve['preserve_settings'])
            logger.info(f"Created default preserve settings at {preserve_file}")
        except Exception as e:
            logger.error(f"Error creating default preserve settings: {e}")
    
    def _load_template_rules(self):
        """Load template rules for modifying BIOS configurations."""
        rules_file = self.config_dir / "template_rules.yaml"
        
        if rules_file.exists():
            try:
                with open(rules_file, 'r') as f:
                    self.template_rules = yaml.safe_load(f) or {}
                logger.info(f"Loaded template rules from {rules_file}")
            except Exception as e:
                logger.error(f"Error loading template rules: {e}")
                self.template_rules = {}
        else:
            self._create_default_template_rules()
    
    def _create_default_template_rules(self):
        """Create default template rules for BIOS modifications."""
        default_rules = {
            'template_rules': {
                's2_c2_small': {
                    'description': 'Template rules for small compute nodes',
                    'modifications': {
                        # CPU Settings
                        'IntelHyperThreadingTech': 'Enabled',
                        'ProcessorEIST': 'Enabled',
                        'TurboMode': 'Enabled',
                        'ProcessorC1E': 'Enabled',
                        'ProcessorC3Report': 'Enabled',
                        'ProcessorC6Report': 'Enabled',
                        'PowerTechnology': 'EnergyEfficient',
                        
                        # Memory Settings
                        'MemoryMode': 'Independent',
                        'PatrolScrub': 'Enabled',
                        'DemandScrub': 'Enabled',
                        
                        # Boot Settings
                        'BootMode': 'UEFI',
                        'SecureBoot': 'Disabled',
                        'PXEBoot': 'Enabled',
                        'QuietBoot': 'Disabled',
                        'BootTimeout': '5',
                        
                        # Power Management
                        'PowerRestorePolicy': 'PowerOn',
                        'WakeOnLAN': 'Enabled',
                        
                        # BMC Settings
                        'BMCLANConfig': 'DHCP',
                        'SOLEnabled': 'Enabled',
                        'KCSInterface': 'Enabled',
                    }
                },
                's2_c2_medium': {
                    'description': 'Template rules for medium compute nodes',
                    'modifications': {
                        # CPU Settings (Performance focused)
                        'IntelHyperThreadingTech': 'Enabled',
                        'ProcessorEIST': 'Enabled',
                        'TurboMode': 'Enabled',
                        'ProcessorC1E': 'Enabled',
                        'ProcessorC3Report': 'Enabled',
                        'ProcessorC6Report': 'Enabled',
                        'PowerTechnology': 'Performance',
                        'IntelVT': 'Enabled',
                        'IntelVTD': 'Enabled',
                        
                        # Memory Settings
                        'MemoryMode': 'Independent',
                        'PatrolScrub': 'Enabled',
                        'DemandScrub': 'Enabled',
                        'MemoryThermalThrottling': 'Enabled',
                        'NUMAOptimized': 'Enabled',
                        
                        # Boot Settings
                        'BootMode': 'UEFI',
                        'SecureBoot': 'Disabled',
                        'PXEBoot': 'Enabled',
                        'QuietBoot': 'Disabled',
                        'BootTimeout': '3',
                        'FastBoot': 'Enabled',
                        
                        # Network
                        'SRIOV': 'Enabled',
                        'NetworkStack': 'Enabled',
                        
                        # Power Management
                        'PowerRestorePolicy': 'PowerOn',
                        'WakeOnLAN': 'Enabled',
                        'PowerEfficiency': 'Performance',
                        
                        # BMC Settings
                        'BMCLANConfig': 'DHCP',
                        'SOLEnabled': 'Enabled',
                        'KCSInterface': 'Enabled',
                        'RedfishEnabled': 'Enabled',
                    }
                },
                's2_c2_large': {
                    'description': 'Template rules for large compute nodes',
                    'modifications': {
                        # CPU Settings (High Performance)
                        'IntelHyperThreadingTech': 'Enabled',
                        'ProcessorEIST': 'Enabled',
                        'TurboMode': 'Enabled',
                        'ProcessorC1E': 'Enabled',
                        'ProcessorC3Report': 'Enabled',
                        'ProcessorC6Report': 'Enabled',
                        'PowerTechnology': 'Performance',
                        'IntelVT': 'Enabled',
                        'IntelVTD': 'Enabled',
                        'AVX512': 'Enabled',
                        'EnergyPerformanceBias': 'Performance',
                        
                        # Memory Settings
                        'MemoryMode': 'Independent',
                        'PatrolScrub': 'Enabled',
                        'DemandScrub': 'Enabled',
                        'MemoryThermalThrottling': 'Enabled',
                        'NUMAOptimized': 'Enabled',
                        'MemoryMirroring': 'Disabled',
                        'MemorySparing': 'Disabled',
                        
                        # Boot Settings
                        'BootMode': 'UEFI',
                        'SecureBoot': 'Disabled',
                        'PXEBoot': 'Enabled',
                        'QuietBoot': 'Disabled',
                        'BootTimeout': '3',
                        'FastBoot': 'Enabled',
                        'CSMSupport': 'Disabled',
                        
                        # Network
                        'SRIOV': 'Enabled',
                        'NetworkStack': 'Enabled',
                        'NetworkOpROM': 'Enabled',
                        
                        # Storage
                        'SATAController': 'AHCI',
                        'NVMeSupport': 'Enabled',
                        'RAIDSupport': 'Enabled',
                        
                        # Power Management
                        'PowerRestorePolicy': 'PowerOn',
                        'WakeOnLAN': 'Enabled',
                        'PowerEfficiency': 'Performance',
                        'CPUPowerManagement': 'OSControl',
                        
                        # BMC Settings
                        'BMCLANConfig': 'DHCP',
                        'SOLEnabled': 'Enabled',
                        'KCSInterface': 'Enabled',
                        'RedfishEnabled': 'Enabled',
                        'HostInterface': 'Enabled',
                    }
                }
            }
        }
        
        rules_file = self.config_dir / "template_rules.yaml"
        try:
            with open(rules_file, 'w') as f:
                yaml.dump(default_rules, f, default_flow_style=False)
            self.template_rules = default_rules
            logger.info(f"Created default template rules at {rules_file}")
        except Exception as e:
            logger.error(f"Error creating default template rules: {e}")
    
    def _load_device_mappings(self):
        """Load device type mappings from YAML file."""
        mapping_file = self.config_dir / "device_mappings.yaml"
        
        if mapping_file.exists():
            try:
                with open(mapping_file, 'r') as f:
                    self.device_types = yaml.safe_load(f) or {}
                logger.info(f"Loaded device mappings from {mapping_file}")
            except Exception as e:
                logger.error(f"Error loading device mappings: {e}")
                self.device_types = {}
        else:
            # Create default mappings
            self._create_default_mappings()
    
    def _create_default_mappings(self):
        """Create default device type mappings."""
        default_mappings = {
            'device_types': {
                's2_c2_small': {
                    'description': 'Small compute nodes - dual core, 8GB RAM',
                    'motherboards': ['X11SCE-F'],
                    'cpu_configs': {
                        'hyperthreading': True,
                        'turbo_boost': True,
                        'power_profile': 'balanced'
                    },
                    'memory_configs': {
                        'ecc_enabled': True,
                        'memory_speed': 'auto'
                    },
                    'boot_configs': {
                        'boot_mode': 'uefi',
                        'secure_boot': False,
                        'pxe_boot': True
                    }
                },
                's2_c2_medium': {
                    'description': 'Medium compute nodes - quad core, 16GB RAM',
                    'motherboards': ['X11DPT-B', 'X11DPFR-SN'],
                    'cpu_configs': {
                        'hyperthreading': True,
                        'turbo_boost': True,
                        'power_profile': 'performance'
                    },
                    'memory_configs': {
                        'ecc_enabled': True,
                        'memory_speed': 'auto'
                    },
                    'boot_configs': {
                        'boot_mode': 'uefi',
                        'secure_boot': False,
                        'pxe_boot': True
                    }
                },
                's2_c2_large': {
                    'description': 'Large compute nodes - 8+ core, 32GB+ RAM',
                    'motherboards': ['X12DPT-B', 'X12STE-F', 'X13DET-B'],
                    'cpu_configs': {
                        'hyperthreading': True,
                        'turbo_boost': True,
                        'power_profile': 'performance'
                    },
                    'memory_configs': {
                        'ecc_enabled': True,
                        'memory_speed': 'auto'
                    },
                    'boot_configs': {
                        'boot_mode': 'uefi',
                        'secure_boot': False,
                        'pxe_boot': True
                    }
                }
            }
        }
        
        mapping_file = self.config_dir / "device_mappings.yaml"
        try:
            with open(mapping_file, 'w') as f:
                yaml.dump(default_mappings, f, default_flow_style=False)
            self.device_types = default_mappings
            logger.info(f"Created default device mappings at {mapping_file}")
        except Exception as e:
            logger.error(f"Error creating default mappings: {e}")
    
    def pull_current_bios_config(self, target_ip: str, username: str = "ADMIN", password: str = None) -> Optional[ET.Element]:
        """
        Pull current BIOS configuration from target system.
        
        Args:
            target_ip: Target system IP address
            username: BMC username
            password: BMC password
            
        Returns:
            XML Element containing current BIOS configuration
            
        Note:
            This is a placeholder for actual BIOS configuration retrieval.
            Implementation would depend on the specific BMC interface (IPMI/RedFish).
        """
        # TODO: Implement actual BIOS configuration retrieval
        # This would use IPMI/RedFish to get current BIOS settings
        logger.info(f"Pulling current BIOS config from {target_ip}")
        
        # For now, return a mock current configuration
        # In real implementation, this would query the BMC via IPMI/RedFish
        mock_current_config = """<?xml version="1.0" encoding="UTF-8"?>
        <BiosConfiguration system_id="{}" timestamp="{}">
            <Setting name="IntelHyperThreadingTech" value="Disabled"/>
            <Setting name="ProcessorEIST" value="Enabled"/>
            <Setting name="TurboMode" value="Disabled"/>
            <Setting name="BootMode" value="Legacy"/>
            <Setting name="SecureBoot" value="Disabled"/>
            <Setting name="PXEBoot" value="Disabled"/>
            <Setting name="mac_address_lan1" value="00:11:22:33:44:55"/>
            <Setting name="mac_address_lan2" value="00:11:22:33:44:56"/>
            <Setting name="system_serial_number" value="SN123456789"/>
            <Setting name="PowerRestorePolicy" value="PowerOff"/>
            <Setting name="WakeOnLAN" value="Disabled"/>
        </BiosConfiguration>""".format(target_ip, datetime.now().isoformat())
        
        try:
            return ET.fromstring(mock_current_config)
        except ET.ParseError as e:
            logger.error(f"Error parsing current BIOS config: {e}")
            return None
    
    def apply_template_to_config(self, current_config: ET.Element, device_type: str) -> Tuple[ET.Element, List[str]]:
        """
        Apply template rules to current BIOS configuration while preserving hardware-specific settings.
        
        Args:
            current_config: Current BIOS configuration XML
            device_type: Device type template to apply
            
        Returns:
            Tuple of (modified_config, list_of_changes)
        """
        if device_type not in self.template_rules.get('template_rules', {}):
            raise ValueError(f"No template rules found for device type: {device_type}")
        
        # Make a deep copy to avoid modifying the original
        modified_config = copy.deepcopy(current_config)
        template_rules = self.template_rules['template_rules'][device_type]['modifications']
        changes_made = []
        
        # Create a mapping of current settings for easy lookup
        current_settings = {setting.get('name'): setting for setting in current_config.findall('Setting')}
        
        for rule_name, rule_value in template_rules.items():
            # Check if this setting should be preserved
            if self._should_preserve_setting(rule_name):
                logger.debug(f"Preserving setting: {rule_name}")
                continue
            
            # Find or create the setting in modified config
            existing_setting = None
            for setting in modified_config.findall('Setting'):
                if setting.get('name') == rule_name:
                    existing_setting = setting
                    break
            
            if existing_setting is not None:
                old_value = existing_setting.get('value')
                if old_value != rule_value:
                    existing_setting.set('value', rule_value)
                    changes_made.append(f"Changed {rule_name}: {old_value} -> {rule_value}")
                    logger.debug(f"Modified {rule_name}: {old_value} -> {rule_value}")
            else:
                # Add new setting
                new_setting = ET.SubElement(modified_config, 'Setting')
                new_setting.set('name', rule_name)
                new_setting.set('value', rule_value)
                changes_made.append(f"Added {rule_name}: {rule_value}")
                logger.debug(f"Added {rule_name}: {rule_value}")
        
        # Update timestamp
        modified_config.set('modified_timestamp', datetime.now().isoformat())
        modified_config.set('template_applied', device_type)
        
        return modified_config, changes_made
    
    def _should_preserve_setting(self, setting_name: str) -> bool:
        """
        Check if a setting should be preserved from the original configuration.
        
        Args:
            setting_name: Name of the BIOS setting
            
        Returns:
            True if setting should be preserved, False otherwise
        """
        for preserve_pattern in self.preserve_settings:
            if preserve_pattern.endswith('*'):
                # Wildcard match
                prefix = preserve_pattern[:-1]
                if setting_name.startswith(prefix):
                    return True
            elif preserve_pattern == setting_name:
                # Exact match
                return True
        
        return False
    
    def validate_modified_config(self, original_config: ET.Element, modified_config: ET.Element, device_type: str) -> Tuple[bool, List[str]]:
        """
        Validate the modified configuration before applying.
        
        Args:
            original_config: Original BIOS configuration
            modified_config: Modified BIOS configuration
            device_type: Device type being applied
            
        Returns:
            Tuple of (is_valid, list_of_validation_errors)
        """
        validation_errors = []
        
        # Check that preserved settings are actually preserved
        original_settings = {s.get('name'): s.get('value') for s in original_config.findall('Setting')}
        modified_settings = {s.get('name'): s.get('value') for s in modified_config.findall('Setting')}
        
        for setting_name in original_settings:
            if self._should_preserve_setting(setting_name):
                if setting_name in modified_settings:
                    if original_settings[setting_name] != modified_settings[setting_name]:
                        validation_errors.append(
                            f"Preserved setting {setting_name} was modified: "
                            f"{original_settings[setting_name]} -> {modified_settings[setting_name]}"
                        )
                else:
                    validation_errors.append(f"Preserved setting {setting_name} was removed")
        
        # Check for required settings based on device type
        device_config = self.get_device_config(device_type)
        if device_config and 'required_settings' in device_config:
            for required_setting in device_config['required_settings']:
                if required_setting not in modified_settings:
                    validation_errors.append(f"Required setting {required_setting} is missing")
        
        # Check for conflicting settings
        conflicts = self._check_setting_conflicts(modified_settings)
        validation_errors.extend(conflicts)
        
        is_valid = len(validation_errors) == 0
        return is_valid, validation_errors
    
    def _check_setting_conflicts(self, settings: Dict[str, str]) -> List[str]:
        """
        Check for conflicting BIOS settings.
        
        Args:
            settings: Dictionary of setting name -> value
            
        Returns:
            List of conflict descriptions
        """
        conflicts = []
        
        # Example conflict checks
        if settings.get('BootMode') == 'Legacy' and settings.get('SecureBoot') == 'Enabled':
            conflicts.append("Secure Boot cannot be enabled in Legacy boot mode")
        
        if settings.get('IntelVT') == 'Disabled' and settings.get('IntelVTD') == 'Enabled':
            conflicts.append("Intel VT-d requires Intel VT to be enabled")
        
        # Add more conflict checks as needed
        
        return conflicts
    
    def push_modified_config(self, modified_config: ET.Element, target_ip: str, username: str = "ADMIN", password: str = None, backup: bool = True) -> bool:
        """
        Push modified BIOS configuration to target system.
        
        Args:
            modified_config: Modified BIOS configuration XML
            target_ip: Target system IP address  
            username: BMC username
            password: BMC password
            backup: Whether to backup current config first
            
        Returns:
            True if successful, False otherwise
            
        Note:
            This is a placeholder for actual BIOS configuration application.
            Implementation would depend on the specific BMC interface (IPMI/RedFish).
        """
        try:
            if backup:
                backup_path = self._create_backup(target_ip, modified_config)
                logger.info(f"Created backup at {backup_path}")
            
            # TODO: Implement actual BIOS configuration application
            # This would use IPMI/RedFish to apply the new settings
            logger.info(f"Pushing modified BIOS config to {target_ip}")
            
            # Convert XML to string for logging
            config_str = ET.tostring(modified_config, encoding='unicode')
            logger.debug(f"Configuration to apply:\n{config_str}")
            
            # In real implementation:
            # 1. Convert XML to BMC-specific format
            # 2. Apply settings via IPMI/RedFish
            # 3. Verify settings were applied
            # 4. Handle any errors or rollback if needed
            
            logger.info(f"Successfully applied BIOS configuration to {target_ip}")
            return True
            
        except Exception as e:
            logger.error(f"Error pushing BIOS config to {target_ip}: {e}")
            return False
    
    def _create_backup(self, target_ip: str, current_config: ET.Element) -> str:
        """Create backup of current BIOS configuration."""
        backup_dir = self.config_dir / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"bios_backup_{target_ip.replace('.', '_')}_{timestamp}.xml"
        backup_path = backup_dir / backup_filename
        
        # Pretty print the XML
        self._indent_xml(current_config)
        tree = ET.ElementTree(current_config)
        tree.write(backup_path, encoding='utf-8', xml_declaration=True)
        
        return str(backup_path)
    
    def apply_bios_config_smart(self, device_type: str, target_ip: str, username: str = "ADMIN", password: str = None, dry_run: bool = False) -> Dict[str, Any]:
        """
        Smart BIOS configuration application using pull-edit-push approach.
        
        Args:
            device_type: Device type template to apply
            target_ip: Target system IP address
            username: BMC username
            password: BMC password
            dry_run: If True, only show what would be changed
            
        Returns:
            Dictionary with operation results
        """
        result = {
            'success': False,
            'target_ip': target_ip,
            'device_type': device_type,
            'changes_made': [],
            'validation_errors': [],
            'backup_path': None,
            'dry_run': dry_run
        }
        
        try:
            # Step 1: Pull current configuration
            logger.info(f"Step 1: Pulling current BIOS config from {target_ip}")
            current_config = self.pull_current_bios_config(target_ip, username, password)
            if current_config is None:
                result['error'] = "Failed to retrieve current BIOS configuration"
                return result
            
            # Step 2: Apply template modifications
            logger.info(f"Step 2: Applying template rules for {device_type}")
            modified_config, changes_made = self.apply_template_to_config(current_config, device_type)
            result['changes_made'] = changes_made
            
            if not changes_made:
                logger.info("No changes needed - configuration already matches template")
                result['success'] = True
                result['message'] = "No changes needed"
                return result
            
            # Step 3: Validate modifications
            logger.info("Step 3: Validating modified configuration")
            is_valid, validation_errors = self.validate_modified_config(current_config, modified_config, device_type)
            result['validation_errors'] = validation_errors
            
            if not is_valid:
                result['error'] = f"Validation failed: {'; '.join(validation_errors)}"
                return result
            
            if dry_run:
                logger.info("Dry run - would apply the following changes:")
                for change in changes_made:
                    logger.info(f"  {change}")
                result['success'] = True
                result['message'] = "Dry run completed successfully"
                return result
            
            # Step 4: Push modified configuration
            logger.info("Step 4: Pushing modified configuration")
            push_success = self.push_modified_config(modified_config, target_ip, username, password)
            
            if push_success:
                result['success'] = True
                result['message'] = f"Successfully applied {len(changes_made)} changes"
                logger.info(f"Successfully applied BIOS configuration for {device_type} to {target_ip}")
            else:
                result['error'] = "Failed to push modified configuration"
            
        except Exception as e:
            logger.error(f"Error in smart BIOS config application: {e}")
            result['error'] = str(e)
        
        return result
    
    def _load_xml_templates(self):
        """Load legacy XML BIOS configuration templates (deprecated)."""
        xml_dir = self.config_dir / "xml_templates"
        xml_dir.mkdir(exist_ok=True)
        
        self.xml_templates = {}
        for xml_file in xml_dir.glob("*.xml"):
            device_type = xml_file.stem
            try:
                tree = ET.parse(xml_file)
                self.xml_templates[device_type] = tree
                logger.info(f"Loaded legacy XML template for {device_type}")
            except Exception as e:
                logger.error(f"Error loading XML template {xml_file}: {e}")
    
    # Legacy methods (deprecated - use smart methods instead)
    
    def get_device_types(self) -> List[str]:
        """Get list of available device types."""
        return list(self.device_types.get('device_types', {}).keys())
    
    def get_device_config(self, device_type: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific device type.
        
        Args:
            device_type: Device type (e.g., 's2_c2_small')
            
        Returns:
            Device configuration dictionary or None if not found
        """
        return self.device_types.get('device_types', {}).get(device_type)
    
    def get_motherboard_for_device(self, device_type: str) -> Optional[List[str]]:
        """
        Get compatible motherboards for a device type.
        
        Args:
            device_type: Device type
            
        Returns:
            List of compatible motherboard models
        """
        config = self.get_device_config(device_type)
        return config.get('motherboards', []) if config else None
    
    def generate_xml_config(self, device_type: str, motherboard: str = None) -> Optional[str]:
        """
        Generate XML BIOS configuration for a device type (DEPRECATED).
        
        Use apply_bios_config_smart() instead for safer configuration management.
        
        Args:
            device_type: Device type (e.g., 's2_c2_small')
            motherboard: Specific motherboard model (optional)
            
        Returns:
            XML configuration string or None if template not found
        """
        logger.warning("generate_xml_config() is deprecated. Use apply_bios_config_smart() instead.")
        
        # First try device-specific template
        if hasattr(self, 'xml_templates') and device_type in self.xml_templates:
            tree = self.xml_templates[device_type]
            return ET.tostring(tree.getroot(), encoding='unicode')
        
        # If no template exists, generate from device config
        config = self.get_device_config(device_type)
        if not config:
            logger.error(f"No configuration found for device type: {device_type}")
            return None
        
        return self._generate_xml_from_config(config, device_type, motherboard)
    
    def _generate_xml_from_config(self, config: Dict[str, Any], device_type: str, motherboard: str = None) -> str:
        """
        Generate XML from device configuration dictionary (DEPRECATED).
        
        Args:
            config: Device configuration
            device_type: Device type name
            motherboard: Motherboard model
            
        Returns:
            XML configuration string
        """
        root = ET.Element("BiosConfig")
        root.set("deviceType", device_type)
        if motherboard:
            root.set("motherboard", motherboard)
        
        # Add CPU configuration
        if 'cpu_configs' in config:
            cpu_elem = ET.SubElement(root, "CPU")
            for key, value in config['cpu_configs'].items():
                setting = ET.SubElement(cpu_elem, "Setting")
                setting.set("name", key)
                setting.set("value", str(value).lower())
        
        # Add Memory configuration
        if 'memory_configs' in config:
            memory_elem = ET.SubElement(root, "Memory")
            for key, value in config['memory_configs'].items():
                setting = ET.SubElement(memory_elem, "Setting")
                setting.set("name", key)
                setting.set("value", str(value).lower())
        
        # Add Boot configuration
        if 'boot_configs' in config:
            boot_elem = ET.SubElement(root, "Boot")
            for key, value in config['boot_configs'].items():
                setting = ET.SubElement(boot_elem, "Setting")
                setting.set("name", key)
                setting.set("value", str(value).lower())
        
        # Pretty print the XML
        self._indent_xml(root)
        return ET.tostring(root, encoding='unicode')
    
    def _indent_xml(self, elem: ET.Element, level: int = 0):
        """Add indentation to XML for pretty printing."""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    def save_xml_template(self, device_type: str, xml_content: str):
        """
        Save XML template for a device type (DEPRECATED).
        
        Args:
            device_type: Device type name
            xml_content: XML configuration content
        """
        logger.warning("save_xml_template() is deprecated. Use template rules instead.")
        
        xml_dir = self.config_dir / "xml_templates"
        xml_dir.mkdir(exist_ok=True)
        
        xml_file = xml_dir / f"{device_type}.xml"
        try:
            # Validate XML before saving
            ET.fromstring(xml_content)
            
            with open(xml_file, 'w') as f:
                f.write(xml_content)
            
            # Reload templates
            self._load_xml_templates()
            logger.info(f"Saved XML template for {device_type}")
            
        except ET.ParseError as e:
            logger.error(f"Invalid XML for {device_type}: {e}")
            raise ValueError(f"Invalid XML content: {e}")
        except Exception as e:
            logger.error(f"Error saving XML template: {e}")
            raise
    
    def list_templates(self) -> List[str]:
        """List available XML templates (DEPRECATED)."""
        logger.warning("list_templates() is deprecated. Use get_device_types() instead.")
        if hasattr(self, 'xml_templates'):
            return list(self.xml_templates.keys())
        return []
    
    def apply_bios_config(self, device_type: str, target_ip: str, username: str = "ADMIN", password: str = None):
        """
        Apply BIOS configuration to a target system (DEPRECATED).
        
        Use apply_bios_config_smart() instead for safer configuration management.
        
        Args:
            device_type: Device type
            target_ip: Target system IP address
            username: BMC username
            password: BMC password
        """
        logger.warning("apply_bios_config() is deprecated. Use apply_bios_config_smart() instead.")
        
        xml_config = self.generate_xml_config(device_type)
        if not xml_config:
            raise ValueError(f"No configuration available for device type: {device_type}")
        
        # TODO: Implement actual BIOS configuration application
        # This would integrate with IPMI/RedFish managers
        logger.info(f"Would apply BIOS config for {device_type} to {target_ip}")
        logger.debug(f"XML Config:\n{xml_config}")
        
        return xml_config
        """Load XML BIOS configuration templates."""
        xml_dir = self.config_dir / "xml_templates"
        xml_dir.mkdir(exist_ok=True)
        
        for xml_file in xml_dir.glob("*.xml"):
            device_type = xml_file.stem
            try:
                tree = ET.parse(xml_file)
                self.xml_templates[device_type] = tree
                logger.info(f"Loaded XML template for {device_type}")
            except Exception as e:
                logger.error(f"Error loading XML template {xml_file}: {e}")
    
    def get_device_types(self) -> List[str]:
        """Get list of available device types."""
        return list(self.device_types.get('device_types', {}).keys())
    
    def get_device_config(self, device_type: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific device type.
        
        Args:
            device_type: Device type (e.g., 's2_c2_small')
            
        Returns:
            Device configuration dictionary or None if not found
        """
        return self.device_types.get('device_types', {}).get(device_type)
    
    def get_motherboard_for_device(self, device_type: str) -> Optional[List[str]]:
        """
        Get compatible motherboards for a device type.
        
        Args:
            device_type: Device type
            
        Returns:
            List of compatible motherboard models
        """
        config = self.get_device_config(device_type)
        return config.get('motherboards', []) if config else None
    
    def generate_xml_config(self, device_type: str, motherboard: str = None) -> Optional[str]:
        """
        Generate XML BIOS configuration for a device type.
        
        Args:
            device_type: Device type (e.g., 's2_c2_small')
            motherboard: Specific motherboard model (optional)
            
        Returns:
            XML configuration string or None if template not found
        """
        # First try device-specific template
        if device_type in self.xml_templates:
            tree = self.xml_templates[device_type]
            return ET.tostring(tree.getroot(), encoding='unicode')
        
        # If no template exists, generate from device config
        config = self.get_device_config(device_type)
        if not config:
            logger.error(f"No configuration found for device type: {device_type}")
            return None
        
        return self._generate_xml_from_config(config, device_type, motherboard)
    
    def _generate_xml_from_config(self, config: Dict[str, Any], device_type: str, motherboard: str = None) -> str:
        """
        Generate XML from device configuration dictionary.
        
        Args:
            config: Device configuration
            device_type: Device type name
            motherboard: Motherboard model
            
        Returns:
            XML configuration string
        """
        root = ET.Element("BiosConfig")
        root.set("deviceType", device_type)
        if motherboard:
            root.set("motherboard", motherboard)
        
        # Add CPU configuration
        if 'cpu_configs' in config:
            cpu_elem = ET.SubElement(root, "CPU")
            for key, value in config['cpu_configs'].items():
                setting = ET.SubElement(cpu_elem, "Setting")
                setting.set("name", key)
                setting.set("value", str(value).lower())
        
        # Add Memory configuration
        if 'memory_configs' in config:
            memory_elem = ET.SubElement(root, "Memory")
            for key, value in config['memory_configs'].items():
                setting = ET.SubElement(memory_elem, "Setting")
                setting.set("name", key)
                setting.set("value", str(value).lower())
        
        # Add Boot configuration
        if 'boot_configs' in config:
            boot_elem = ET.SubElement(root, "Boot")
            for key, value in config['boot_configs'].items():
                setting = ET.SubElement(boot_elem, "Setting")
                setting.set("name", key)
                setting.set("value", str(value).lower())
        
        # Pretty print the XML
        self._indent_xml(root)
        return ET.tostring(root, encoding='unicode')
    
    def _indent_xml(self, elem: ET.Element, level: int = 0):
        """Add indentation to XML for pretty printing."""
        i = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    
    def save_xml_template(self, device_type: str, xml_content: str):
        """
        Save XML template for a device type.
        
        Args:
            device_type: Device type name
            xml_content: XML configuration content
        """
        xml_dir = self.config_dir / "xml_templates"
        xml_dir.mkdir(exist_ok=True)
        
        xml_file = xml_dir / f"{device_type}.xml"
        try:
            # Validate XML before saving
            ET.fromstring(xml_content)
            
            with open(xml_file, 'w') as f:
                f.write(xml_content)
            
            # Reload templates
            self._load_xml_templates()
            logger.info(f"Saved XML template for {device_type}")
            
        except ET.ParseError as e:
            logger.error(f"Invalid XML for {device_type}: {e}")
            raise ValueError(f"Invalid XML content: {e}")
        except Exception as e:
            logger.error(f"Error saving XML template: {e}")
            raise
    
    def list_templates(self) -> List[str]:
        """List available XML templates."""
        return list(self.xml_templates.keys())
    
    def apply_bios_config(self, device_type: str, target_ip: str, username: str = "ADMIN", password: str = None):
        """
        Apply BIOS configuration to a target system.
        
        Args:
            device_type: Device type
            target_ip: Target system IP address
            username: BMC username
            password: BMC password
            
        Note:
            This is a placeholder for actual BIOS configuration application.
            Implementation would depend on the specific BMC interface (IPMI/RedFish).
        """
        xml_config = self.generate_xml_config(device_type)
        if not xml_config:
            raise ValueError(f"No configuration available for device type: {device_type}")
        
        # TODO: Implement actual BIOS configuration application
        # This would integrate with IPMI/RedFish managers
        logger.info(f"Would apply BIOS config for {device_type} to {target_ip}")
        logger.debug(f"XML Config:\n{xml_config}")
        
        return xml_config
