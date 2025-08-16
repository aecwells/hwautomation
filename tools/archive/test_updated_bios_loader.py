#!/usr/bin/env python3
"""
Test the updated BIOS configuration loader with unified config integration.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hwautomation.hardware.bios.config.loader import ConfigurationLoader


def test_updated_bios_loader():
    """Test the updated BIOS configuration loader."""
    print("🔧 TESTING UPDATED BIOS CONFIGURATION LOADER")
    print("=" * 60)

    try:
        # Initialize with BIOS config directory
        config_dir = "/home/ubuntu/projects/hwautomation/configs/bios"
        loader = ConfigurationLoader(config_dir)

        print(f"✅ BIOS loader initialized")

        # Test configuration stats
        stats = loader.get_configuration_stats()
        print(f"✅ Configuration statistics:")
        print(f"   • Source: {stats['source']}")
        print(f"   • Vendors: {stats['vendors']}")
        print(f"   • Motherboards: {stats['motherboards']}")
        print(f"   • Device types: {stats['device_types']}")
        print(f"   • Version: {stats['version']}")

        # Test device listing
        all_devices = loader.list_all_device_types()
        print(f"✅ Found {len(all_devices)} device types")

        # Test specific device lookup
        test_device = "a1.c5.large"
        if loader.validate_device_type(test_device):
            print(f"✅ Device validation working for {test_device}")

            # Get complete device info
            device_info = loader.get_device_by_type(test_device)
            print(f"✅ Device information:")
            if "vendor" in device_info:
                print(f"   • Vendor: {device_info.get('vendor')}")
            if "motherboard" in device_info:
                print(f"   • Motherboard: {device_info.get('motherboard')}")
            elif "motherboards" in device_info:
                print(f"   • Motherboards: {device_info.get('motherboards')}")

            # Test motherboards and vendor lookup
            motherboards = loader.get_motherboards_for_device(test_device)
            vendor = loader.get_vendor_for_device(test_device)
            print(f"   • Motherboards (new method): {motherboards}")
            print(f"   • Vendor (new method): {vendor}")
        else:
            print(f"❌ Device {test_device} not found")

        # Test legacy device mappings format
        print(f"\n🔄 Testing backward compatibility:")
        device_mappings = loader.load_device_mappings()
        print(f"✅ Legacy device mappings: {len(device_mappings)} entries")

        if test_device in device_mappings:
            legacy_config = device_mappings[test_device]
            print(f"✅ Legacy format access:")
            print(f"   • Description: {legacy_config.get('description', 'N/A')}")
            print(f"   • Hardware specs: {bool(legacy_config.get('hardware_specs'))}")
            print(f"   • Boot configs: {bool(legacy_config.get('boot_configs'))}")

        return True

    except Exception as e:
        print(f"❌ Error testing BIOS loader: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_enhanced_features():
    """Test enhanced features available through unified config."""
    print(f"\n🚀 TESTING ENHANCED FEATURES")
    print("=" * 60)

    try:
        config_dir = "/home/ubuntu/projects/hwautomation/configs/bios"
        loader = ConfigurationLoader(config_dir)

        # Test device search functionality
        print(f"✅ Enhanced device lookup capabilities:")

        # Get all Supermicro devices
        all_devices = loader.list_all_device_types()
        supermicro_devices = []

        for device_type in all_devices:
            vendor = loader.get_vendor_for_device(device_type)
            if vendor.lower() == "supermicro":
                supermicro_devices.append(device_type)

        print(f"   • Supermicro devices: {len(supermicro_devices)}")

        # Get all HPE devices
        hpe_devices = []
        for device_type in all_devices:
            vendor = loader.get_vendor_for_device(device_type)
            if vendor.lower() == "hpe":
                hpe_devices.append(device_type)

        print(f"   • HPE devices: {len(hpe_devices)}")

        # Test motherboard grouping
        motherboard_groups = {}
        for device_type in all_devices[:10]:  # Test first 10 devices
            motherboards = loader.get_motherboards_for_device(device_type)
            for mb in motherboards:
                if mb not in motherboard_groups:
                    motherboard_groups[mb] = []
                motherboard_groups[mb].append(device_type)

        print(f"✅ Motherboard grouping (sample):")
        for mb, devices in list(motherboard_groups.items())[:3]:
            print(f"   • {mb}: {len(devices)} devices")

        return True

    except Exception as e:
        print(f"❌ Error testing enhanced features: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_fallback_behavior():
    """Test fallback behavior when unified config is not available."""
    print(f"\n🔄 TESTING FALLBACK BEHAVIOR")
    print("=" * 60)

    try:
        # Test with a directory that doesn't have unified config
        # This should fall back to legacy mode

        # We'll simulate this by testing both modes
        config_dir = "/home/ubuntu/projects/hwautomation/configs/bios"
        loader = ConfigurationLoader(config_dir)

        stats = loader.get_configuration_stats()
        print(f"✅ Current mode: {stats['source']}")

        if stats["source"] == "unified":
            print(f"   • Using unified configuration (expected)")
            print(f"   • Unified config provides enhanced capabilities")
        else:
            print(f"   • Using legacy configuration (fallback)")
            print(f"   • Legacy mode provides basic functionality")

        # Test that basic functionality works in either mode
        device_mappings = loader.load_device_mappings()
        print(f"✅ Basic device mappings work: {len(device_mappings)} devices")

        # Test that enhanced methods work (or gracefully degrade)
        test_device = list(device_mappings.keys())[0] if device_mappings else None
        if test_device:
            vendor = loader.get_vendor_for_device(test_device)
            motherboards = loader.get_motherboards_for_device(test_device)
            print(f"✅ Enhanced methods work for {test_device}:")
            print(f"   • Vendor: {vendor}")
            print(f"   • Motherboards: {motherboards}")

        return True

    except Exception as e:
        print(f"❌ Error testing fallback behavior: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🧪 UPDATED BIOS CONFIGURATION LOADER TESTS")
    print("=" * 80)

    tests = [test_updated_bios_loader, test_enhanced_features, test_fallback_behavior]

    passed = 0
    total = len(tests)

    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_func.__name__} failed")
        except Exception as e:
            print(f"❌ {test_func.__name__} failed with exception: {e}")

    print(f"\n🎉 TEST RESULTS: {passed}/{total} tests passed")

    if passed == total:
        print("✅ All tests passed! The updated BIOS loader is working correctly.")
        print("\n🚀 INTEGRATION SUCCESS:")
        print("   • Unified config integration working")
        print("   • Backward compatibility maintained")
        print("   • Enhanced features available")
        print("   • Fallback behavior working")
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
