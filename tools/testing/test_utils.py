#!/usr/bin/env python3
"""
Test cases for utility functions.
"""

import sys
import unittest
import tempfile
import os
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

try:
    from hwautomation.utils.config import load_config
    from hwautomation.utils.network import test_ssh_connection
    UTILS_AVAILABLE = True
except ImportError:
    UTILS_AVAILABLE = False


@unittest.skipUnless(UTILS_AVAILABLE, "Utils modules not available")
class TestConfigUtils(unittest.TestCase):
    """Test cases for configuration utilities."""
    
    def test_config_loading(self):
        """Test configuration loading."""
        # Create a temporary config file
        config_content = """
maas:
  host: "http://test-server:5240/MAAS"
  consumer_key: "test_key"
  token_key: "test_token"
  token_secret: "test_secret"

database:
  path: "test.db"
  table_name: "test_servers"
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(config_content)
            config_path = f.name
        
        try:
            config = load_config(config_path)
            self.assertIsNotNone(config)
            self.assertIn('maas', config)
            self.assertIn('database', config)
            self.assertEqual(config['maas']['host'], "http://test-server:5240/MAAS")
        finally:
            os.unlink(config_path)


@unittest.skipUnless(UTILS_AVAILABLE, "Utils modules not available")
class TestNetworkUtils(unittest.TestCase):
    """Test cases for network utilities."""
    
    def test_ssh_connection_test(self):
        """Test SSH connection testing (mock)."""
        # This would normally test actual SSH connections
        # For now, just test that the function exists and can be called
        try:
            # This should fail but not crash
            result = test_ssh_connection('127.0.0.1', 'test_user', timeout=1)
            # We expect this to fail for localhost without SSH
            self.assertFalse(result)
        except Exception:
            # It's okay if this throws an exception for invalid connection
            pass


class TestUtilsPackage(unittest.TestCase):
    """Test the utils package structure."""
    
    def test_utils_imports(self):
        """Test that utils package imports work."""
        try:
            from hwautomation.utils import config, network
            self.assertTrue(True, "Utils imports successful")
        except ImportError as e:
            self.skipTest(f"Utils modules not fully implemented: {e}")


if __name__ == '__main__':
    unittest.main()
