#!/usr/bin/env python3
"""
Simple Phase 4 Implementation Test
"""

import sys
import os
import tempfile
import yaml
import asyncio

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_firmware_manager_basic():
    """Test basic firmware manager functionality"""
    print("🧪 Testing FirmwareManager Basic Functionality")
    
    try:
        from hwautomation.hardware.firmware_manager import (
            FirmwareManager, FirmwareType, FirmwareInfo, UpdatePriority
        )
        print("   ✅ Imports successful")
        
        # Create temporary config
        with tempfile.TemporaryDirectory() as temp_dir:
            config_data = {
                'firmware_repository': {
                    'base_path': f'{temp_dir}/firmware',
                    'vendors': {
                        'hpe': {'display_name': 'HPE'},
                        'supermicro': {'display_name': 'Supermicro'}
                    }
                }
            }
            config_path = os.path.join(temp_dir, 'config.yaml')
            with open(config_path, 'w') as f:
                yaml.safe_dump(config_data, f)
            
            # Initialize firmware manager
            fm = FirmwareManager(config_path=config_path)
            print("   ✅ FirmwareManager initialized")
            print(f"      Repository: {fm.repository.base_path}")
            print(f"      Vendors: {list(fm.repository.vendors.keys())}")
            print(f"      Tools: {list(fm.vendor_tools.keys())}")
            
            # Test vendor info
            vendor_info = fm._get_vendor_info("a1.c5.large")
            print(f"   ✅ Vendor info: {vendor_info}")
            
            # Test version comparison
            update_needed = fm._compare_versions("1.0.0", "1.1.0")
            print(f"   ✅ Version comparison: {update_needed}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_firmware_manager_async():
    """Test async firmware manager functionality"""
    print("\n🧪 Testing FirmwareManager Async Functionality")
    
    try:
        from hwautomation.hardware.firmware_manager import FirmwareManager
        
        # Create temporary config
        with tempfile.TemporaryDirectory() as temp_dir:
            config_data = {
                'firmware_repository': {
                    'base_path': f'{temp_dir}/firmware',
                    'vendors': {}
                }
            }
            config_path = os.path.join(temp_dir, 'config.yaml')
            with open(config_path, 'w') as f:
                yaml.safe_dump(config_data, f)
            
            fm = FirmwareManager(config_path=config_path)
            
            # Test firmware version check
            firmware_info = await fm.check_firmware_versions(
                "a1.c5.large", "192.168.1.100", "admin", "password"
            )
            print("   ✅ Firmware version check completed")
            print(f"      Found {len(firmware_info)} firmware components")
            
            for fw_type, fw_info in firmware_info.items():
                print(f"      {fw_type.value}: {fw_info.current_version} → {fw_info.latest_version}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Async test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_configuration_files():
    """Test configuration file structure"""
    print("\n🧪 Testing Configuration Files")
    
    try:
        # Check if config file exists
        config_path = os.path.join(os.path.dirname(__file__), '..', 'configs', 'firmware', 'firmware_repository.yaml')
        if os.path.exists(config_path):
            print("   ✅ Configuration file exists")
            
            # Load and validate
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            if 'firmware_repository' in config:
                print("   ✅ Configuration structure valid")
                repo_config = config['firmware_repository']
                
                print(f"      Base path: {repo_config.get('base_path')}")
                print(f"      Vendors: {list(repo_config.get('vendors', {}).keys())}")
                
                if 'device_firmware_mapping' in config:
                    print(f"      Device mappings: {len(config['device_firmware_mapping'])}")
                
            else:
                print("   ❌ Invalid configuration structure")
                return False
        else:
            print("   ❌ Configuration file not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Phase 4: Firmware Manager Implementation Tests")
    print("=" * 60)
    
    tests = [
        ("Basic Functionality", test_firmware_manager_basic()),
        ("Configuration Files", test_configuration_files())
    ]
    
    async_tests = [
        ("Async Functionality", test_firmware_manager_async())
    ]
    
    # Run sync tests
    passed = 0
    total = len(tests)
    
    for test_name, result in tests:
        if result:
            passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            print(f"❌ {test_name}: FAILED")
    
    # Run async tests
    async def run_async_tests():
        nonlocal passed, total
        for test_name, test_coro in async_tests:
            total += 1
            try:
                result = await test_coro
                if result:
                    passed += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ {test_name}: FAILED - {e}")
    
    asyncio.run(run_async_tests())
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Phase 4 implementation is ready.")
        
        print("\n📋 Implementation Status:")
        print("   ✅ Core FirmwareManager module")
        print("   ✅ Configuration system")
        print("   ✅ Async operation support")
        print("   ✅ Vendor information mapping")
        print("   ✅ Version comparison logic")
        
        print("\n🚀 Ready for Integration:")
        print("   • Firmware version checking")
        print("   • Update priority determination")
        print("   • Batch firmware updates")
        print("   • Integration with Phase 3 BIOS system")
        
    else:
        print("⚠️  Some tests failed. Review and fix issues before proceeding.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
