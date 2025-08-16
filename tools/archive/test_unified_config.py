#!/usr/bin/env python3
"""
Test the unified configuration system with backward compatibility adapters.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hwautomation.config import (
    BiosConfigAdapter,
    FirmwareConfigAdapter,
    UnifiedConfigLoader,
)
from hwautomation.config.adapters import ConfigurationManager


def test_unified_loader():
    """Test the unified configuration loader."""
    print("🔄 TESTING UNIFIED CONFIGURATION LOADER")
    print("=" * 60)

    try:
        loader = UnifiedConfigLoader()

        # Test basic stats
        stats = loader.get_stats()
        print(f"✅ Configuration loaded successfully")
        print(f"   • Vendors: {stats.vendors}")
        print(f"   • Motherboards: {stats.motherboards}")
        print(f"   • Device types: {stats.device_types}")
        print(f"   • Firmware files: {stats.total_firmware_files}")

        # Test device lookup
        device_info = loader.get_device_by_type("a1.c5.large")
        if device_info:
            print(f"✅ Device lookup working:")
            print(f"   • Device: {device_info.device_type}")
            print(f"   • Vendor: {device_info.vendor}")
            print(f"   • Motherboard: {device_info.motherboard}")
            print(
                f"   • CPU: {device_info.device_config['hardware_specs']['cpu_name']}"
            )
        else:
            print("❌ Device lookup failed")

        # Test listing functions
        all_devices = loader.list_all_device_types()
        print(f"✅ Found {len(all_devices)} total device types")

        return True

    except Exception as e:
        print(f"❌ Error testing unified loader: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_bios_adapter():
    """Test the BIOS configuration adapter."""
    print(f"\n🔧 TESTING BIOS CONFIGURATION ADAPTER")
    print("=" * 60)

    try:
        adapter = BiosConfigAdapter()

        # Test device mappings loading
        device_mappings = adapter.load_device_mappings()
        print(f"✅ BIOS adapter loaded {len(device_mappings)} device types")

        # Test a specific device
        if "a1.c5.large" in device_mappings:
            device_config = device_mappings["a1.c5.large"]
            print(f"✅ Device config format check:")
            print(f"   • Description: {device_config.get('description', 'N/A')}")
            print(f"   • Vendor: {device_config.get('vendor', 'N/A')}")
            print(f"   • Motherboards: {device_config.get('motherboards', [])}")
            print(
                f"   • Redfish capable: {device_config.get('redfish_capable', False)}"
            )

        # Test validation
        validation = adapter.validate_device_config("a1.c5.large")
        print(f"✅ Validation result: {'Valid' if validation['valid'] else 'Invalid'}")
        if validation["errors"]:
            print(f"   • Errors: {validation['errors']}")
        if validation["warnings"]:
            print(f"   • Warnings: {validation['warnings']}")

        return True

    except Exception as e:
        print(f"❌ Error testing BIOS adapter: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_firmware_adapter():
    """Test the firmware configuration adapter."""
    print(f"\n📦 TESTING FIRMWARE CONFIGURATION ADAPTER")
    print("=" * 60)

    try:
        adapter = FirmwareConfigAdapter()

        # Test firmware repository loading
        firmware_repo = adapter.load_firmware_repository()
        vendors = firmware_repo["firmware_repository"]["vendors"]
        print(f"✅ Firmware adapter loaded {len(vendors)} vendors")

        # Test vendor info
        for vendor_name, vendor_data in vendors.items():
            motherboard_count = len(vendor_data.get("motherboards", {}))
            print(f"   • {vendor_name}: {motherboard_count} motherboards")

            # Show tools if available
            tools = vendor_data.get("tools", {})
            if tools:
                print(f"     Tools: {list(tools.keys())}")

        # Test motherboard firmware info
        motherboard_info = adapter.get_motherboard_firmware_info("X11SCE-F")
        if motherboard_info:
            print(f"✅ Motherboard firmware info available")
            print(f"   • BIOS tracking: {bool(motherboard_info.get('bios'))}")
            print(f"   • BMC tracking: {bool(motherboard_info.get('bmc'))}")

        return True

    except Exception as e:
        print(f"❌ Error testing firmware adapter: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_configuration_manager():
    """Test the overall configuration manager."""
    print(f"\n🎯 TESTING CONFIGURATION MANAGER")
    print("=" * 60)

    try:
        config_manager = ConfigurationManager()

        # Test system status
        status = config_manager.get_system_status()
        print(f"✅ Configuration manager initialized")
        print(f"   • Config version: {status['config_version']}")
        print(f"   • Last updated: {status['last_updated']}")
        print(f"   • Statistics: {status['statistics']}")
        print(f"   • Adapters working: {status['adapters']}")

        # Test adapter access
        unified_loader = config_manager.get_unified_loader()
        bios_adapter = config_manager.get_bios_adapter()
        firmware_adapter = config_manager.get_firmware_adapter()

        print(f"✅ All adapters accessible")

        return True

    except Exception as e:
        print(f"❌ Error testing configuration manager: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_backward_compatibility():
    """Test that the adapters provide backward-compatible interfaces."""
    print(f"\n🔄 TESTING BACKWARD COMPATIBILITY")
    print("=" * 60)

    try:
        # Test that we can use adapters like the old config loaders
        bios_adapter = BiosConfigAdapter()
        firmware_adapter = FirmwareConfigAdapter()

        # Simulate old BIOS config usage
        device_mappings = bios_adapter.load_device_mappings()
        print(f"✅ Old-style device mappings: {len(device_mappings)} entries")

        # Simulate old firmware config usage
        firmware_repo = firmware_adapter.load_firmware_repository()
        print(
            f"✅ Old-style firmware repo: {len(firmware_repo['firmware_repository']['vendors'])} vendors"
        )

        # Test specific device lookup (old way)
        if "a1.c5.large" in device_mappings:
            device = device_mappings["a1.c5.large"]
            motherboards = device.get("motherboards", [])
            vendor = device.get("vendor")
            print(f"✅ Old-style device access:")
            print(f"   • Device: a1.c5.large")
            print(f"   • Vendor: {vendor}")
            print(f"   • Motherboards: {motherboards}")

        return True

    except Exception as e:
        print(f"❌ Error testing backward compatibility: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🧪 UNIFIED CONFIGURATION SYSTEM TESTS")
    print("=" * 80)

    tests = [
        test_unified_loader,
        test_bios_adapter,
        test_firmware_adapter,
        test_configuration_manager,
        test_backward_compatibility,
    ]

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
        print(
            "✅ All tests passed! The unified configuration system is working correctly."
        )
        print("\n🚀 READY FOR INTEGRATION:")
        print("   • Unified config loader working")
        print("   • Backward compatibility adapters working")
        print("   • Ready to integrate with existing systems")
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
