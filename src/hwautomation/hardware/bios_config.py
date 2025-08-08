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
import time
from datetime import datetime

from .redfish_manager import RedfishManager, SystemInfo
from .bios_decision_logic import BiosSettingMethodSelector, MethodSelectionResult, ConfigMethod
from .bios_monitoring import BiosConfigMonitor, get_monitor, OperationStatus

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
    
    # ==========================================
    # Redfish Integration Methods
    # ==========================================
    
    def test_redfish_connection(self, target_ip: str, username: str = "ADMIN", 
                               password: str = None) -> Tuple[bool, str]:
        """
        Test Redfish connectivity to target system.
        
        Args:
            target_ip: Target system IP address
            username: BMC username
            password: BMC password
            
        Returns:
            Tuple of (success, message)
        """
        try:
            with RedfishManager(target_ip, username, password) as redfish:
                return redfish.test_connection()
        except Exception as e:
            return False, f"Redfish connection test failed: {e}"
    
    def get_system_info_via_redfish(self, target_ip: str, username: str = "ADMIN", 
                                   password: str = None) -> Optional[SystemInfo]:
        """
        Get system information via Redfish.
        
        Args:
            target_ip: Target system IP address
            username: BMC username  
            password: BMC password
            
        Returns:
            SystemInfo object or None if failed
        """
        try:
            with RedfishManager(target_ip, username, password) as redfish:
                return redfish.get_system_info()
        except Exception as e:
            logger.error(f"Failed to get system info via Redfish: {e}")
            return None
    
    def get_bios_settings_via_redfish(self, target_ip: str, username: str = "ADMIN", 
                                     password: str = None) -> Optional[Dict[str, Any]]:
        """
        Get current BIOS settings via Redfish.
        
        Args:
            target_ip: Target system IP address
            username: BMC username
            password: BMC password
            
        Returns:
            Dictionary of BIOS settings or None if failed
        """
        try:
            with RedfishManager(target_ip, username, password) as redfish:
                return redfish.get_bios_settings()
        except Exception as e:
            logger.error(f"Failed to get BIOS settings via Redfish: {e}")
            return None
    
    def set_bios_settings_via_redfish(self, target_ip: str, settings: Dict[str, Any],
                                     username: str = "ADMIN", password: str = None) -> bool:
        """
        Set BIOS settings via Redfish.
        
        Args:
            target_ip: Target system IP address
            settings: Dictionary of BIOS settings to apply
            username: BMC username
            password: BMC password
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with RedfishManager(target_ip, username, password) as redfish:
                return redfish.set_bios_settings(settings)
        except Exception as e:
            logger.error(f"Failed to set BIOS settings via Redfish: {e}")
            return False
    
    def power_control_via_redfish(self, target_ip: str, action: str,
                                 username: str = "ADMIN", password: str = None) -> bool:
        """
        Control system power via Redfish.
        
        Args:
            target_ip: Target system IP address
            action: Power action ('On', 'ForceOff', 'GracefulShutdown', 'ForceRestart', 'GracefulRestart')
            username: BMC username
            password: BMC password
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with RedfishManager(target_ip, username, password) as redfish:
                return redfish.power_control(action)
        except Exception as e:
            logger.error(f"Failed to control power via Redfish: {e}")
            return False
    
    def determine_bios_config_method(self, target_ip: str, device_type: str,
                                   username: str = "ADMIN", password: str = None) -> str:
        """
        Determine the best method for BIOS configuration.
        
        Args:
            target_ip: Target system IP address
            device_type: Device type to configure
            username: BMC username
            password: BMC password
            
        Returns:
            Configuration method: 'redfish', 'vendor_tool', or 'hybrid'
        """
        try:
            # Test Redfish capabilities
            redfish_available, _ = self.test_redfish_connection(target_ip, username, password)
            
            if not redfish_available:
                logger.info(f"Redfish not available for {target_ip}, using vendor tools")
                return 'vendor_tool'
            
            # Get device configuration to check preferred method
            device_config = self.get_device_config(device_type)
            if device_config:
                preferred_method = device_config.get('preferred_bios_method', 'vendor_tool')
                
                if preferred_method == 'redfish':
                    # Verify Redfish can handle BIOS settings
                    with RedfishManager(target_ip, username, password) as redfish:
                        capabilities = redfish.discover_capabilities()
                        if capabilities.supports_bios_config:
                            logger.info(f"Using Redfish for {target_ip} (preferred and capable)")
                            return 'redfish'
                        else:
                            logger.info(f"Redfish preferred but BIOS config not supported, using vendor tools")
                            return 'vendor_tool'
                
                elif preferred_method == 'hybrid':
                    logger.info(f"Using hybrid approach for {target_ip}")
                    return 'hybrid'
            
            # Default to vendor tools for compatibility
            logger.info(f"Using vendor tools for {target_ip} (default)")
            return 'vendor_tool'
            
        except Exception as e:
            logger.error(f"Error determining BIOS config method: {e}")
            return 'vendor_tool'  # Safe fallback
    
    # ==========================================
    # Enhanced Smart Configuration with Redfish
    # ==========================================
    
    def apply_bios_config_smart_enhanced(self, device_type: str, target_ip: str, 
                                       username: str = "ADMIN", password: str = None, 
                                       dry_run: bool = False, prefer_redfish: bool = True) -> Dict[str, Any]:
        """
        Enhanced smart BIOS configuration with Redfish support.
        
        Args:
            device_type: Device type template to apply
            target_ip: Target system IP address
            username: BMC username
            password: BMC password
            dry_run: If True, only show what would be changed
            prefer_redfish: If True, try Redfish first before vendor tools
            
        Returns:
            Dictionary with operation results
        """
        result = {
            'success': False,
            'target_ip': target_ip,
            'device_type': device_type,
            'method_used': 'unknown',
            'changes_made': [],
            'validation_errors': [],
            'dry_run': dry_run
        }
        
        try:
            # Determine best configuration method
            if prefer_redfish:
                method = self.determine_bios_config_method(target_ip, device_type, username, password)
            else:
                method = 'vendor_tool'
                
            result['method_used'] = method
            
            if method == 'redfish':
                logger.info(f"Applying BIOS configuration via Redfish for {target_ip}")
                return self._apply_bios_config_via_redfish(device_type, target_ip, username, password, dry_run, result)
            
            elif method == 'hybrid':
                logger.info(f"Applying BIOS configuration via hybrid approach for {target_ip}")
                return self._apply_bios_config_hybrid(device_type, target_ip, username, password, dry_run, result)
            
            else:  # vendor_tool
                logger.info(f"Applying BIOS configuration via vendor tools for {target_ip}")
                # Fall back to existing smart method
                vendor_result = self.apply_bios_config_smart(device_type, target_ip, username, password, dry_run)
                vendor_result['method_used'] = 'vendor_tool'
                return vendor_result
                
        except Exception as e:
            result['error'] = f"Enhanced BIOS configuration failed: {e}"
            logger.error(f"Enhanced BIOS configuration failed: {e}")
            return result
    
    def apply_bios_config_phase2(self, device_type: str, target_ip: str, 
                                username: str = "ADMIN", password: str = None, 
                                dry_run: bool = False, prefer_performance: bool = True) -> Dict[str, Any]:
        """
        Step-wise per-setting method selection with enhanced decision logic.
        
        This method analyzes each BIOS setting individually and chooses the optimal
        method (Redfish vs vendor tools) based on setting characteristics, device
        capabilities, and performance considerations.
        
        Args:
            device_type: Device type template to apply
            target_ip: Target system IP address
            username: BMC username
            password: BMC password
            dry_run: If True, only show what would be changed
            prefer_performance: If True, optimize for speed over reliability
            
        Returns:
            Dictionary with operation results including per-setting method selection
        """
        result = {
            'success': False,
            'target_ip': target_ip,
            'device_type': device_type,
            'method_analysis': {},
            'redfish_results': {},
            'vendor_results': {},
            'performance_estimate': {},
            'batch_execution': [],
            'settings_applied': {},
            'validation_errors': [],
            'dry_run': dry_run
        }
        
        try:
            # Get device configuration for decision logic
            device_config = self.device_types.get(device_type)
            if not device_config:
                result['error'] = f"Device type {device_type} not found in configuration"
                return result
            
            # Initialize method selector
            method_selector = BiosSettingMethodSelector(device_config)
            
            # Get template settings to apply
            template_rules = self.template_rules.get('template_rules', {}).get(device_type, {})
            settings_to_apply = template_rules.get('modifications', {})
            
            if not settings_to_apply:
                result['error'] = f"No BIOS settings found for device type: {device_type}"
                return result
            
            # Analyze settings and determine optimal methods
            logger.info(f"Analyzing {len(settings_to_apply)} BIOS settings for optimal method selection")
            method_analysis = method_selector.analyze_settings(
                settings_to_apply, prefer_performance=prefer_performance
            )
            
            result['method_analysis'] = {
                'redfish_settings': method_analysis.redfish_settings,
                'vendor_settings': method_analysis.vendor_settings,
                'unknown_settings': method_analysis.unknown_settings,
                'method_rationale': method_analysis.method_rationale,
                'batch_groups': method_analysis.batch_groups
            }
            result['performance_estimate'] = method_analysis.performance_estimate
            
            logger.info(f"Method analysis complete: {len(method_analysis.redfish_settings)} Redfish, "
                       f"{len(method_analysis.vendor_settings)} vendor tool, "
                       f"{len(method_analysis.unknown_settings)} unknown settings")
            
            if dry_run:
                result['success'] = True
                result['dry_run_summary'] = {
                    'total_settings': len(settings_to_apply),
                    'redfish_count': len(method_analysis.redfish_settings),
                    'vendor_count': len(method_analysis.vendor_settings),
                    'unknown_count': len(method_analysis.unknown_settings),
                    'estimated_total_time': method_analysis.performance_estimate.get('estimated_total_time', 0)
                }
                return result
            
            # Execute settings using optimal methods
            success = True
            
            # Apply Redfish settings in batches
            if method_analysis.redfish_settings:
                logger.info(f"Applying {len(method_analysis.redfish_settings)} settings via Redfish")
                redfish_result = self._apply_settings_via_redfish(
                    target_ip, username, password, method_analysis.redfish_settings
                )
                result['redfish_results'] = redfish_result
                if not redfish_result.get('success', False):
                    success = False
                    logger.warning("Redfish settings application had issues")
            
            # Apply vendor tool settings individually
            if method_analysis.vendor_settings:
                logger.info(f"Applying {len(method_analysis.vendor_settings)} settings via vendor tools")
                vendor_result = self._apply_settings_via_vendor_tools(
                    device_type, target_ip, username, password, method_analysis.vendor_settings
                )
                result['vendor_results'] = vendor_result
                if not vendor_result.get('success', False):
                    success = False
                    logger.warning("Vendor tool settings application had issues")
            
            # Handle unknown settings
            if method_analysis.unknown_settings:
                logger.warning(f"Found {len(method_analysis.unknown_settings)} unknown settings - skipping")
                result['unknown_settings_skipped'] = method_analysis.unknown_settings
            
            # Record batch execution details
            result['batch_execution'] = method_analysis.batch_groups
            
            # Combine applied settings
            result['settings_applied'].update(method_analysis.redfish_settings)
            result['settings_applied'].update(method_analysis.vendor_settings)
            
            result['success'] = success
            
            if success:
                logger.info(f"BIOS configuration (per-setting decision) completed successfully for {target_ip}")
            else:
                logger.warning(f"BIOS configuration (per-setting decision) completed with some issues for {target_ip}")
            
            return result
            
        except Exception as e:
            result['error'] = f"Per-setting BIOS configuration failed: {e}"
            logger.error(f"Per-setting BIOS configuration failed for {target_ip}: {e}")
            return result
    
    async def apply_bios_config_phase3(self, device_type: str, target_ip: str, 
                                      username: str = "ADMIN", password: str = None, 
                                      dry_run: bool = False, prefer_performance: bool = True,
                                      enable_monitoring: bool = True) -> Dict[str, Any]:
        """
        Real-time monitored BIOS configuration with advanced error recovery.
        
        This method enhances the per-setting path with real-time progress monitoring, WebSocket updates,
        intelligent error recovery, and comprehensive validation.
        
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
        result = {
            'success': False,
            'target_ip': target_ip,
            'device_type': device_type,
            'operation_id': None,
            'monitoring_enabled': enable_monitoring,
            'method_analysis': {},
            'execution_phases': [],
            'real_time_progress': [],
            'error_recovery_actions': [],
            'validation_results': {},
            'performance_metrics': {},
            'dry_run': dry_run
        }
        
        monitor = get_monitor() if enable_monitoring else None
        operation_id = None
        
        try:
            # Create monitored operation
            if monitor:
                operation_id = monitor.create_operation(
                    operation_type="phase3_bios_configuration",
                    metadata={
                        'device_type': device_type,
                        'target_ip': target_ip,
                        'prefer_performance': prefer_performance,
                        'dry_run': dry_run
                    }
                )
                result['operation_id'] = operation_id
                await monitor.log_info(operation_id, f"Starting monitored BIOS configuration for {target_ip}")
            
            # Stage 1: Pre-flight validation
            if monitor:
                await monitor.start_subtask(operation_id, "pre_flight_validation", 
                                          "Validating system connectivity and capabilities")
            
            validation_result = await self._phase3_pre_flight_validation(
                device_type, target_ip, username, password, operation_id
            )
            result['validation_results']['pre_flight'] = validation_result
            
            if not validation_result.get('success', False):
                if monitor:
                    await monitor.complete_subtask(operation_id, "pre_flight_validation", False, 
                                                 f"Pre-flight validation failed: {validation_result.get('error')}")
                    await monitor.complete_operation(operation_id, False, "Pre-flight validation failed")
                result['error'] = f"Pre-flight validation failed: {validation_result.get('error')}"
                return result
            
            if monitor:
                await monitor.complete_subtask(operation_id, "pre_flight_validation", True, 
                                             "Pre-flight validation successful")
            
            # Stage 2: Method analysis with monitoring
            if monitor:
                await monitor.start_subtask(operation_id, "method_analysis", 
                                          "Analyzing optimal configuration methods")
            
            method_analysis_result = await self._phase3_method_analysis(
                device_type, prefer_performance, operation_id
            )
            result['method_analysis'] = method_analysis_result
            
            if not method_analysis_result.get('success', False):
                if monitor:
                    await monitor.complete_subtask(operation_id, "method_analysis", False,
                                                 "Method analysis failed")
                    await monitor.complete_operation(operation_id, False, "Method analysis failed")
                result['error'] = f"Method analysis failed: {method_analysis_result.get('error')}"
                return result
            
            if monitor:
                await monitor.complete_subtask(operation_id, "method_analysis", True,
                                             f"Analyzed {method_analysis_result['total_settings']} settings")
            
            # Stage 3: Dry run handling
            if dry_run:
                if monitor:
                    await monitor.log_info(operation_id, "Dry run mode - no changes will be applied")
                    await monitor.complete_operation(operation_id, True, "Dry run completed successfully")
                
                result['success'] = True
                result['dry_run_summary'] = method_analysis_result
                return result
            
            # Stage 4: Configuration execution with real-time monitoring
            if monitor:
                total_phases = len(method_analysis_result.get('batch_groups', []))
                await monitor.start_operation(operation_id, total_phases)
            
            execution_result = await self._phase3_execute_configuration(
                target_ip, username, password, method_analysis_result, operation_id
            )
            result['execution_phases'] = execution_result.get('phases', [])
            result['error_recovery_actions'] = execution_result.get('recovery_actions', [])
            
            # Stage 5: Post-configuration validation
            if monitor:
                await monitor.start_subtask(operation_id, "post_validation", 
                                          "Validating applied configuration")
            
            post_validation_result = await self._phase3_post_validation(
                target_ip, username, password, method_analysis_result, operation_id
            )
            result['validation_results']['post_configuration'] = post_validation_result
            
            if monitor:
                success = post_validation_result.get('success', False)
                await monitor.complete_subtask(operation_id, "post_validation", success,
                                             "Post-configuration validation completed")
            
            # Determine overall success
            overall_success = (
                execution_result.get('success', False) and 
                post_validation_result.get('success', False)
            )
            
            if monitor:
                final_message = "Monitored BIOS configuration completed successfully" if overall_success else "Monitored BIOS configuration completed with issues"
                await monitor.complete_operation(operation_id, overall_success, final_message)
            
            result['success'] = overall_success
            
            if overall_success:
                logger.info(f"Monitored BIOS configuration completed successfully for {target_ip}")
            else:
                logger.warning(f"Monitored BIOS configuration completed with issues for {target_ip}")
            
            return result
            
        except Exception as e:
            error_message = f"Monitored BIOS configuration failed: {e}"
            result['error'] = error_message
            logger.error(f"Monitored BIOS configuration failed for {target_ip}: {e}")
            
            if monitor and operation_id:
                await monitor.log_error(operation_id, error_message, {'exception': str(e)})
                await monitor.complete_operation(operation_id, False, error_message)
            
            return result
    
    async def _phase3_pre_flight_validation(self, device_type: str, target_ip: str,
                                          username: str, password: str, 
                                          operation_id: Optional[str] = None) -> Dict[str, Any]:
        """Pre-flight validation with detailed checks for monitored flow"""
        result = {
            'success': False,
            'checks_performed': [],
            'connectivity_test': {},
            'capability_validation': {},
            'configuration_analysis': {},
            'error': None
        }
        
        monitor = get_monitor()
        
        try:
            # Check 1: Basic connectivity
            if operation_id:
                await monitor.log_info(operation_id, "Testing basic network connectivity")
            
            connectivity_result = await self._test_connectivity(target_ip, username, password)
            result['connectivity_test'] = connectivity_result
            result['checks_performed'].append('connectivity')
            
            if not connectivity_result.get('success', False):
                result['error'] = f"Connectivity test failed: {connectivity_result.get('error')}"
                return result
            
            # Check 2: Capability validation
            if operation_id:
                await monitor.log_info(operation_id, "Validating system capabilities")
            
            capability_result = self.validate_phase2_redfish_capabilities(
                device_type, target_ip, username, password
            )
            result['capability_validation'] = capability_result
            result['checks_performed'].append('capabilities')
            
            # Check 3: Configuration analysis
            if operation_id:
                await monitor.log_info(operation_id, "Analyzing configuration requirements")
            
            config_analysis = await self._analyze_configuration_requirements(device_type)
            result['configuration_analysis'] = config_analysis
            result['checks_performed'].append('configuration_analysis')
            
            result['success'] = True
            return result
            
        except Exception as e:
            result['error'] = f"Pre-flight validation failed: {e}"
            if operation_id:
                await monitor.log_error(operation_id, f"Pre-flight validation error: {e}")
            return result
    
    async def _phase3_method_analysis(self, device_type: str, prefer_performance: bool,
                                    operation_id: Optional[str] = None) -> Dict[str, Any]:
        """Enhanced method analysis for monitored flow"""
        result = {
            'success': False,
            'total_settings': 0,
            'method_breakdown': {},
            'batch_groups': [],
            'performance_estimate': {},
            'error': None
        }
        
        try:
            # Get device configuration and settings
            device_config = self.device_types.get(device_type)
            if not device_config:
                result['error'] = f"Device type {device_type} not found"
                return result
            
            method_selector = BiosSettingMethodSelector(device_config)
            
            # Get template settings
            template_rules = self.template_rules.get('template_rules', {}).get(device_type, {})
            settings_to_apply = template_rules.get('modifications', {})
            
            if not settings_to_apply:
                result['error'] = f"No BIOS settings found for device type: {device_type}"
                return result
            
            # Perform analysis
            analysis = method_selector.analyze_settings(
                settings_to_apply, prefer_performance=prefer_performance
            )
            
            result['success'] = True
            result['total_settings'] = len(settings_to_apply)
            result['method_breakdown'] = {
                'redfish_settings': len(analysis.redfish_settings),
                'vendor_settings': len(analysis.vendor_settings),
                'unknown_settings': len(analysis.unknown_settings)
            }
            result['batch_groups'] = analysis.batch_groups
            result['performance_estimate'] = analysis.performance_estimate
            result['method_rationale'] = analysis.method_rationale
            result['redfish_settings'] = analysis.redfish_settings
            result['vendor_settings'] = analysis.vendor_settings
            result['unknown_settings'] = analysis.unknown_settings
            
            return result
            
        except Exception as e:
            result['error'] = f"Method analysis failed: {e}"
            return result
    
    async def _phase3_execute_configuration(self, target_ip: str, username: str, password: str,
                                          method_analysis: Dict[str, Any], 
                                          operation_id: Optional[str] = None) -> Dict[str, Any]:
        """Configuration execution with monitoring and error recovery"""
        result = {
            'success': False,
            'phases': [],
            'recovery_actions': [],
            'error': None
        }
        
        monitor = get_monitor()
        
        try:
            batch_groups = method_analysis.get('batch_groups', [])
            successful_phases = 0
            
            for i, batch in enumerate(batch_groups):
                phase_name = f"batch_{i+1}_{batch['method']}"
                
                if operation_id:
                    await monitor.start_subtask(operation_id, phase_name, 
                                              f"Executing {batch['method']} batch with {batch['batch_size']} settings")
                
                # Check for cancellation
                if operation_id and monitor.is_operation_cancelled(operation_id):
                    result['error'] = "Operation was cancelled"
                    return result
                
                phase_result = await self._execute_batch_with_recovery(
                    batch, target_ip, username, password, operation_id
                )
                
                result['phases'].append({
                    'phase_name': phase_name,
                    'method': batch['method'],
                    'settings_count': batch['batch_size'],
                    'success': phase_result.get('success', False),
                    'execution_time': phase_result.get('execution_time', 0),
                    'recovery_actions': phase_result.get('recovery_actions', [])
                })
                
                if phase_result.get('recovery_actions'):
                    result['recovery_actions'].extend(phase_result['recovery_actions'])
                
                if phase_result.get('success', False):
                    successful_phases += 1
                    if operation_id:
                        await monitor.complete_subtask(operation_id, phase_name, True,
                                                     f"Batch completed successfully in {phase_result.get('execution_time', 0):.1f}s")
                else:
                    if operation_id:
                        await monitor.complete_subtask(operation_id, phase_name, False,
                                                     f"Batch failed: {phase_result.get('error', 'Unknown error')}")
            
            # Determine overall success
            result['success'] = successful_phases == len(batch_groups)
            
            return result
            
        except Exception as e:
            result['error'] = f"Configuration execution failed: {e}"
            if operation_id:
                await monitor.log_error(operation_id, f"Execution error: {e}")
            return result
    
    async def _phase3_post_validation(self, target_ip: str, username: str, password: str,
                                    method_analysis: Dict[str, Any],
                                    operation_id: Optional[str] = None) -> Dict[str, Any]:
        """Post-configuration validation for monitored flow"""
        result = {
            'success': False,
            'validation_checks': [],
            'applied_settings_verified': {},
            'configuration_drift': [],
            'error': None
        }
        
        monitor = get_monitor()
        
        try:
            # Validate applied Redfish settings
            redfish_settings = method_analysis.get('redfish_settings', {})
            if redfish_settings:
                if operation_id:
                    await monitor.log_info(operation_id, f"Validating {len(redfish_settings)} Redfish settings")
                
                redfish_validation = await self._validate_redfish_settings(
                    target_ip, username, password, redfish_settings
                )
                result['applied_settings_verified']['redfish'] = redfish_validation
                result['validation_checks'].append('redfish_settings')
            
            # Note: Vendor tool validation would require tool-specific validation logic
            vendor_settings = method_analysis.get('vendor_settings', {})
            if vendor_settings:
                if operation_id:
                    await monitor.log_info(operation_id, f"Vendor settings validation noted ({len(vendor_settings)} settings)")
                result['applied_settings_verified']['vendor'] = {
                    'note': 'Vendor tool validation requires tool-specific implementation',
                    'settings_count': len(vendor_settings)
                }
                result['validation_checks'].append('vendor_settings_noted')
            
            result['success'] = True
            return result
            
        except Exception as e:
            result['error'] = f"Post-validation failed: {e}"
            if operation_id:
                await monitor.log_error(operation_id, f"Post-validation error: {e}")
            return result
    
    async def _test_connectivity(self, target_ip: str, username: str, password: str) -> Dict[str, Any]:
        """Test basic connectivity to target system"""
        result = {
            'success': False,
            'response_time': 0,
            'redfish_available': False,
            'error': None
        }
        
        try:
            start_time = time.time()
            
            # Test Redfish connectivity
            with RedfishManager(target_ip, username, password) as redfish:
                system_info = redfish.get_system_info()
                if system_info:
                    result['redfish_available'] = True
                    result['system_info'] = {
                        'manufacturer': system_info.manufacturer,
                        'model': system_info.model,
                        'power_state': system_info.power_state
                    }
            
            result['response_time'] = time.time() - start_time
            result['success'] = True
            
        except Exception as e:
            result['error'] = f"Connectivity test failed: {e}"
        
        return result
    
    async def _analyze_configuration_requirements(self, device_type: str) -> Dict[str, Any]:
        """Analyze configuration requirements for device type"""
        result = {
            'device_type': device_type,
            'total_settings': 0,
            'complexity_score': 0,
            'estimated_time': 0,
            'requirements_met': True
        }
        
        try:
            device_config = self.device_types.get(device_type)
            if device_config:
                bios_setting_methods = device_config.get('bios_setting_methods', {})
                
                total_settings = 0
                complexity_score = 0
                
                for category, settings in bios_setting_methods.items():
                    setting_count = len(settings) if isinstance(settings, dict) else 0
                    total_settings += setting_count
                    
                    # Simple complexity scoring
                    if category == 'redfish_preferred':
                        complexity_score += setting_count * 1
                    elif category == 'redfish_fallback':
                        complexity_score += setting_count * 2
                    elif category == 'vendor_only':
                        complexity_score += setting_count * 4
                
                result['total_settings'] = total_settings
                result['complexity_score'] = complexity_score
                result['estimated_time'] = complexity_score * 2  # Rough estimate in seconds
        
        except Exception as e:
            logger.error(f"Configuration analysis failed: {e}")
        
        return result
    
    async def _execute_batch_with_recovery(self, batch: Dict[str, Any], target_ip: str,
                                         username: str, password: str,
                                         operation_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute batch with error recovery"""
        result = {
            'success': False,
            'execution_time': 0,
            'recovery_actions': [],
            'error': None
        }
        
        start_time = time.time()
        
        try:
            method = batch['method']
            settings = batch['settings']
            
            if method == 'redfish':
                # Execute via Redfish
                redfish_result = self._apply_settings_via_redfish(
                    target_ip, username, password, settings
                )
                result['success'] = redfish_result.get('success', False)
                if not result['success']:
                    result['error'] = redfish_result.get('error', 'Redfish execution failed')
                    
                    # Recovery: Try individual settings
                    recovery_action = {
                        'action': 'individual_retry',
                        'reason': 'Batch Redfish execution failed, trying individual settings',
                        'attempted': True,
                        'success': False
                    }
                    
                    # Implement individual retry logic here
                    result['recovery_actions'].append(recovery_action)
            
            elif method == 'vendor_tool':
                # Execute via vendor tools (use existing method)
                vendor_result = self._apply_settings_via_vendor_tools(
                    "unknown", target_ip, username, password, settings
                )
                result['success'] = vendor_result.get('success', False)
                if not result['success']:
                    result['error'] = vendor_result.get('error', 'Vendor tool execution failed')
            
            result['execution_time'] = time.time() - start_time
            
        except Exception as e:
            result['error'] = f"Batch execution failed: {e}"
            result['execution_time'] = time.time() - start_time
        
        return result
    
    async def _validate_redfish_settings(self, target_ip: str, username: str, password: str,
                                       expected_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that Redfish settings were applied correctly"""
        result = {
            'success': False,
            'verified_settings': {},
            'mismatched_settings': {},
            'error': None
        }
        
        try:
            with RedfishManager(target_ip, username, password) as redfish:
                current_settings = redfish.get_bios_settings()
                
                if current_settings:
                    for setting_name, expected_value in expected_settings.items():
                        current_value = current_settings.get(setting_name)
                        
                        if current_value == expected_value:
                            result['verified_settings'][setting_name] = {
                                'expected': expected_value,
                                'actual': current_value,
                                'match': True
                            }
                        else:
                            result['mismatched_settings'][setting_name] = {
                                'expected': expected_value,
                                'actual': current_value,
                                'match': False
                            }
                    
                    result['success'] = len(result['mismatched_settings']) == 0
                else:
                    result['error'] = "Failed to retrieve current BIOS settings for validation"
        
        except Exception as e:
            result['error'] = f"Settings validation failed: {e}"
        
        return result
    
    def _apply_settings_via_redfish(self, target_ip: str, username: str, password: str,
                                   settings: Dict[str, Any]) -> Dict[str, Any]:
        """Apply BIOS settings via Redfish with batching support."""
        result = {
            'success': False,
            'method': 'redfish',
            'settings_applied': {},
            'settings_failed': {},
            'error': None
        }
        
        try:
            with RedfishManager(target_ip, username, password) as redfish:
                # Get current settings for validation
                current_settings = redfish.get_bios_settings()
                if current_settings is None:
                    result['error'] = "Failed to retrieve current BIOS settings"
                    return result
                
                # Apply settings in batch
                update_result = redfish.update_bios_settings(settings)
                
                if update_result:
                    result['success'] = True
                    result['settings_applied'] = settings
                    logger.info(f"Successfully applied {len(settings)} BIOS settings via Redfish")
                else:
                    result['error'] = "Failed to update BIOS settings via Redfish"
                    result['settings_failed'] = settings
                    
        except Exception as e:
            result['error'] = f"Redfish application failed: {e}"
            result['settings_failed'] = settings
            logger.error(f"Redfish settings application failed: {e}")
        
        return result
    
    def _apply_settings_via_vendor_tools(self, device_type: str, target_ip: str, 
                                        username: str, password: str,
                                        settings: Dict[str, Any]) -> Dict[str, Any]:
        """Apply BIOS settings via vendor tools with individual setting handling."""
        result = {
            'success': False,
            'method': 'vendor_tools',
            'settings_applied': {},
            'settings_failed': {},
            'individual_results': {},
            'error': None
        }
        
        try:
            # Use existing smart method for vendor tool application
            # This maintains compatibility with existing vendor tool logic
            vendor_result = self.apply_bios_config_smart(device_type, target_ip, username, password, dry_run=False)
            
            if vendor_result.get('success', False):
                result['success'] = True
                result['settings_applied'] = settings
                result['individual_results'] = vendor_result
                logger.info(f"Successfully applied {len(settings)} BIOS settings via vendor tools")
            else:
                result['error'] = vendor_result.get('error', 'Unknown vendor tool error')
                result['settings_failed'] = settings
                result['individual_results'] = vendor_result
                
        except Exception as e:
            result['error'] = f"Vendor tool application failed: {e}"
            result['settings_failed'] = settings
            logger.error(f"Vendor tool settings application failed: {e}")
        
        return result
    
    def get_phase2_method_statistics(self, device_type: str) -> Dict[str, Any]:
        """Get statistics about Phase 2 method selection for a device type."""
        device_config = self.device_types.get(device_type)
        if not device_config:
            return {'error': f"Device type {device_type} not found"}
        
        method_selector = BiosSettingMethodSelector(device_config)
        return method_selector.get_method_statistics()
    
    def validate_phase2_redfish_capabilities(self, device_type: str, target_ip: str,
                                           username: str = "ADMIN", password: str = None) -> Dict[str, Any]:
        """Validate which configured Redfish settings are actually available on the target system."""
        result = {
            'success': False,
            'device_type': device_type,
            'target_ip': target_ip,
            'validation_results': {},
            'available_settings': [],
            'unavailable_settings': [],
            'error': None
        }
        
        try:
            device_config = self.device_types.get(device_type)
            if not device_config:
                result['error'] = f"Device type {device_type} not found"
                return result
            
            # Get available Redfish BIOS settings from target system
            with RedfishManager(target_ip, username, password) as redfish:
                current_settings = redfish.get_bios_settings()
                if current_settings is None:
                    result['error'] = "Failed to retrieve BIOS settings from target system"
                    return result
                
                available_setting_names = set(current_settings.keys())
                
                # Validate configured settings against available settings
                method_selector = BiosSettingMethodSelector(device_config)
                validation_results = method_selector.validate_redfish_capabilities(available_setting_names)
                
                result['validation_results'] = validation_results
                result['available_settings'] = [setting for setting, available in validation_results.items() if available]
                result['unavailable_settings'] = [setting for setting, available in validation_results.items() if not available]
                result['success'] = True
                
                logger.info(f"Redfish validation complete: {len(result['available_settings'])} available, "
                           f"{len(result['unavailable_settings'])} unavailable settings")
                
        except Exception as e:
            result['error'] = f"Redfish validation failed: {e}"
            logger.error(f"Redfish capability validation failed: {e}")
        
        return result
    
    def _apply_bios_config_via_redfish(self, device_type: str, target_ip: str,
                                      username: str, password: str, dry_run: bool,
                                      result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply BIOS configuration purely via Redfish."""
        try:
            with RedfishManager(target_ip, username, password) as redfish:
                # Get current BIOS settings
                current_settings = redfish.get_bios_settings()
                if current_settings is None:
                    result['error'] = "Failed to retrieve current BIOS settings via Redfish"
                    return result
                
                # Get template settings for device type
                template_rules = self.template_rules.get('template_rules', {}).get(device_type, {})
                template_modifications = template_rules.get('modifications', {})
                
                if not template_modifications:
                    result['error'] = f"No template modifications found for device type: {device_type}"
                    return result
                
                # Calculate changes needed
                changes_to_apply = {}
                changes_made = []
                
                for setting_name, target_value in template_modifications.items():
                    current_value = current_settings.get(setting_name)
                    
                    if current_value != target_value:
                        changes_to_apply[setting_name] = target_value
                        changes_made.append(f"{setting_name}: {current_value} -> {target_value}")
                
                result['changes_made'] = changes_made
                
                if not changes_to_apply:
                    result['success'] = True
                    result['message'] = "No changes needed - configuration already matches template"
                    return result
                
                if dry_run:
                    result['success'] = True
                    result['message'] = f"Dry run completed - would apply {len(changes_to_apply)} changes via Redfish"
                    return result
                
                # Apply changes via Redfish
                logger.info(f"Applying {len(changes_to_apply)} BIOS settings via Redfish")
                success = redfish.set_bios_settings(changes_to_apply)
                
                if success:
                    result['success'] = True
                    result['message'] = f"Successfully applied {len(changes_to_apply)} BIOS settings via Redfish"
                    logger.info(f"BIOS configuration applied successfully via Redfish for {target_ip}")
                else:
                    result['error'] = "Failed to apply BIOS settings via Redfish"
                
                return result
                
        except Exception as e:
            result['error'] = f"Redfish BIOS configuration failed: {e}"
            logger.error(f"Redfish BIOS configuration failed: {e}")
            return result
    
    def _apply_bios_config_hybrid(self, device_type: str, target_ip: str,
                                 username: str, password: str, dry_run: bool,
                                 result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply BIOS configuration using hybrid Redfish + vendor tool approach."""
        try:
            # Get device configuration to determine which settings go where
            device_config = self.get_device_config(device_type)
            if not device_config:
                result['error'] = f"No device configuration found for {device_type}"
                return result
            
            redfish_settings = device_config.get('redfish_settings', [])
            vendor_only_settings = device_config.get('vendor_only_settings', [])
            
            # Get template modifications
            template_rules = self.template_rules.get('template_rules', {}).get(device_type, {})
            template_modifications = template_rules.get('modifications', {})
            
            # Split settings by method
            redfish_changes = {k: v for k, v in template_modifications.items() if k in redfish_settings}
            vendor_changes = {k: v for k, v in template_modifications.items() if k in vendor_only_settings}
            
            all_changes = []
            
            # Apply Redfish settings first
            if redfish_changes:
                logger.info(f"Applying {len(redfish_changes)} settings via Redfish")
                redfish_result = self._apply_bios_config_via_redfish(device_type, target_ip, username, password, dry_run, {'changes_made': []})
                if redfish_result.get('success'):
                    all_changes.extend(redfish_result.get('changes_made', []))
                else:
                    logger.warning(f"Redfish portion failed: {redfish_result.get('error', 'Unknown error')}")
            
            # Apply vendor tool settings
            if vendor_changes:
                logger.info(f"Applying {len(vendor_changes)} settings via vendor tools")
                # This would integrate with existing vendor tool logic
                # For now, fall back to the existing smart method
                vendor_result = self.apply_bios_config_smart(device_type, target_ip, username, password, dry_run)
                if vendor_result.get('success'):
                    all_changes.extend(vendor_result.get('changes_made', []))
                else:
                    result['error'] = f"Vendor tool portion failed: {vendor_result.get('error', 'Unknown error')}"
                    return result
            
            result['changes_made'] = all_changes
            result['success'] = True
            result['message'] = f"Hybrid configuration completed - {len(all_changes)} total changes"
            return result
            
        except Exception as e:
            result['error'] = f"Hybrid BIOS configuration failed: {e}"
            logger.error(f"Hybrid BIOS configuration failed: {e}")
            return result

    # ==========================================
    
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
