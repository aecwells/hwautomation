#!/usr/bin/env python3
"""
Test cases for BIOS Configuration Manager.
"""

import sys
import unittest
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

from hwautomation.hardware.bios_config import BiosConfigManager


class TestBiosConfigManager(unittest.TestCase):
    """Test cases for BiosConfigManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = BiosConfigManager()
    
    def test_initialization(self):
        """Test that BiosConfigManager initializes correctly."""
        self.assertIsNotNone(self.manager)
        self.assertIsNotNone(self.manager.config_dir)
        self.assertIsNotNone(self.manager.device_types)
        self.assertIsNotNone(self.manager.template_rules)
        self.assertIsNotNone(self.manager.preserve_settings)
    
    def test_get_device_types(self):
        """Test getting available device types."""
        device_types = self.manager.get_device_types()
        self.assertIsInstance(device_types, list)
        self.assertIn('a1.c5.large', device_types)
        self.assertIn('d1.c1.small', device_types)
        self.assertIn('d1.c2.medium', device_types)
    
    def test_get_device_config(self):
        """Test getting device configuration."""
        # Use a device type that exists in device_mappings.yaml
        config = self.manager.get_device_config('a1.c5.large')
        self.assertIsNotNone(config)
        self.assertIn('description', config)
        self.assertIn('motherboards', config)
        
        # Test non-existent device type
        config = self.manager.get_device_config('non_existent')
        self.assertIsNone(config)
    
    def test_get_motherboard_for_device(self):
        """Test getting motherboards for device type."""
        # Use a device type that exists in device_mappings.yaml
        motherboards = self.manager.get_motherboard_for_device('a1.c5.large')
        self.assertIsNotNone(motherboards)
        self.assertIsInstance(motherboards, list)
        self.assertGreater(len(motherboards), 0)
        
        # Test non-existent device type
        motherboards = self.manager.get_motherboard_for_device('non_existent')
        self.assertIsNone(motherboards)
    
    def test_preserve_settings(self):
        """Test preserve settings functionality."""
        # Test some settings that should be preserved
        self.assertTrue(self.manager._should_preserve_setting('mac_address_lan1'))
        self.assertTrue(self.manager._should_preserve_setting('system_serial_number'))
        self.assertTrue(self.manager._should_preserve_setting('mac_address_ipmi'))
        
        # Test wildcard matching
        self.assertTrue(self.manager._should_preserve_setting('mac_address_whatever'))
        self.assertTrue(self.manager._should_preserve_setting('memory_size_dimm0'))
        
        # Test settings that should not be preserved
        self.assertFalse(self.manager._should_preserve_setting('IntelHyperThreadingTech'))
        self.assertFalse(self.manager._should_preserve_setting('BootMode'))
    
    def test_smart_config_dry_run(self):
        """Test smart configuration in dry run mode."""
        result = self.manager.apply_bios_config_smart(
            device_type='s2_c2_small',
            target_ip='192.168.1.100',
            username='ADMIN',
            password='test_password',
            dry_run=True
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('target_ip', result)
        self.assertIn('device_type', result)
        self.assertIn('changes_made', result)
        self.assertIn('validation_errors', result)
        self.assertIn('dry_run', result)
        self.assertTrue(result['dry_run'])
        
        # Should succeed in dry run mode
        self.assertTrue(result['success'])
    
    def test_template_rules_loading(self):
        """Test that template rules are loaded correctly."""
        template_rules = self.manager.template_rules
        self.assertIn('template_rules', template_rules)
        
        rules = template_rules['template_rules']
        # Check that the expected template rule device types exist
        expected_types = ['s2_c2_small', 's2_c2_medium', 's2_c2_large']
        for device_type in expected_types:
            self.assertIn(device_type, rules)
        
        # Check structure of rules using s2_c2_small
        small_rules = rules['s2_c2_small']
        self.assertIn('description', small_rules)
        self.assertIn('modifications', small_rules)
        
        modifications = small_rules['modifications']
        self.assertIsInstance(modifications, dict)
        self.assertGreater(len(modifications), 0)


class TestBiosConfigValidation(unittest.TestCase):
    """Test validation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = BiosConfigManager()
    
    def test_setting_conflicts(self):
        """Test setting conflict detection."""
        # Test conflicting settings
        conflicting_settings = {
            'BootMode': 'Legacy',
            'SecureBoot': 'Enabled'
        }
        conflicts = self.manager._check_setting_conflicts(conflicting_settings)
        self.assertGreater(len(conflicts), 0)
        
        # Test non-conflicting settings
        good_settings = {
            'BootMode': 'UEFI',
            'SecureBoot': 'Enabled'
        }
        conflicts = self.manager._check_setting_conflicts(good_settings)
        self.assertEqual(len(conflicts), 0)


if __name__ == '__main__':
    unittest.main()
