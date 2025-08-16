#!/usr/bin/env python3
"""
Phase 2 Unified Configuration Demo - FirmwareManager Integration
================================================================

This demonstrates Phase 2 integration of the unified configuration system
with the FirmwareManager and web routes, showing enhanced firmware management
capabilities.

Features demonstrated:
- FirmwareManager with unified configuration support
- Enhanced device type discovery and vendor mapping
- Backward compatibility with legacy configuration
- Enhanced web API endpoints
- Real firmware information using unified config
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from hwautomation.config.adapters import ConfigurationManager
from hwautomation.config.unified_loader import UnifiedConfigLoader
from hwautomation.hardware.firmware.manager import FirmwareManager


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'-'*40}")
    print(f"{title}")
    print(f"{'-'*40}")


def demo_firmware_manager_initialization():
    """Demonstrate FirmwareManager initialization with unified config."""
    print_header("PHASE 2 DEMO: FirmwareManager with Unified Configuration")

    print("🔧 Initializing FirmwareManager...")

    # Initialize FirmwareManager (will auto-detect unified config)
    manager = FirmwareManager()

    print(f"✅ FirmwareManager initialized successfully")

    # Check configuration status
    config_status = manager.get_configuration_status()
    print(f"\n📊 Configuration Status:")
    print(f"  • Config Source: {config_status['config_source']}")
    print(f"  • Unified Config Available: {config_status['unified_config_available']}")
    print(f"  • Supported Device Count: {config_status['supported_device_count']}")
    print(f"  • Repository Path: {config_status['repository_path']}")

    if config_status.get("adapters_status"):
        adapters = config_status["adapters_status"]
        print(f"  • BIOS Adapter Compatible: {adapters.get('bios_compatible', False)}")
        print(
            f"  • Firmware Adapter Compatible: {adapters.get('firmware_compatible', False)}"
        )

    return manager


def demo_enhanced_device_discovery(manager: FirmwareManager):
    """Demonstrate enhanced device discovery capabilities."""
    print_section("Enhanced Device Discovery")

    # Get all supported device types
    print("🔍 Getting all supported device types...")
    device_types = manager.get_supported_device_types()
    print(f"✅ Found {len(device_types)} device types")

    # Show first few device types
    print("\n📋 Sample Device Types:")
    for i, device_type in enumerate(device_types[:5]):
        print(f"  {i+1}. {device_type}")
    if len(device_types) > 5:
        print(f"  ... and {len(device_types) - 5} more")

    return device_types


def demo_vendor_analysis(manager: FirmwareManager):
    """Demonstrate vendor statistics and analysis."""
    print_section("Vendor Analysis")

    # Get vendor statistics
    print("📊 Analyzing vendor statistics...")
    stats = manager.get_vendor_statistics()

    print(f"✅ Vendor Statistics:")
    print(f"  • Total Vendors: {stats['total_vendors']}")
    print(f"  • Total Devices: {stats['total_devices']}")

    print(f"\n🏢 Vendor Breakdown:")
    for vendor, info in stats["vendors"].items():
        device_count = info["device_count"]
        motherboards = info["motherboards"]
        print(f"  • {vendor.upper()}:")
        print(f"    - Devices: {device_count}")
        print(
            f"    - Motherboards: {len(motherboards)} ({', '.join(motherboards[:3])}{'...' if len(motherboards) > 3 else ''})"
        )


def demo_device_lookup(manager: FirmwareManager, device_types: list):
    """Demonstrate enhanced device lookup capabilities."""
    print_section("Enhanced Device Lookup")

    # Test a few device types
    test_devices = device_types[:3] if len(device_types) >= 3 else device_types

    print("🔍 Testing device lookup for sample devices...")

    for device_type in test_devices:
        print(f"\n📱 Device: {device_type}")

        # Validate device type
        is_valid = manager.validate_device_type(device_type)
        print(f"  • Valid: {is_valid}")

        if is_valid:
            # Get vendor info using unified config
            vendor_info = manager._get_vendor_info(device_type)
            print(f"  • Vendor: {vendor_info.get('vendor', 'unknown')}")
            print(f"  • Model/Motherboard: {vendor_info.get('model', 'unknown')}")

            # Get device details if available
            device_info = manager.get_device_info(device_type)
            if device_info:
                print(f"  • CPU: {device_info.get('cpu_name', 'Unknown')}")
                print(f"  • RAM: {device_info.get('ram_gb', 0)} GB")
                print(f"  • CPU Cores: {device_info.get('cpu_cores', 0)}")

            # Get devices by vendor
            vendor = vendor_info.get("vendor")
            if vendor and vendor != "unknown":
                vendor_devices = manager.get_devices_by_vendor(vendor)
                print(f"  • Other {vendor} devices: {len(vendor_devices)}")


def demo_device_search(manager: FirmwareManager):
    """Demonstrate device search capabilities."""
    print_section("Device Search Capabilities")

    # Test different search terms
    search_terms = ["Intel", "Xeon", "large", "supermicro"]

    print("🔍 Testing device search functionality...")

    for term in search_terms:
        print(f"\n🔎 Searching for: '{term}'")
        results = manager.search_devices(term)
        print(f"  • Found {len(results)} matches")

        # Show first few results
        for i, result in enumerate(results[:2]):
            device_type = result.get("device_type", "unknown")
            vendor = result.get("vendor", "unknown")
            motherboard = result.get("motherboard", "unknown")
            print(f"    {i+1}. {device_type} ({vendor} {motherboard})")


def demo_firmware_operations(manager: FirmwareManager, device_types: list):
    """Demonstrate firmware operations with enhanced capabilities."""
    print_section("Firmware Operations")

    if not device_types:
        print("❌ No device types available for testing")
        return

    # Use first device type for testing
    test_device = device_types[0]
    print(f"🧪 Testing firmware operations with: {test_device}")

    # Get vendor info
    vendor_info = manager._get_vendor_info(test_device)
    print(f"✅ Vendor Info Retrieved:")
    print(f"  • Vendor: {vendor_info.get('vendor', 'unknown')}")
    print(f"  • Model: {vendor_info.get('model', 'unknown')}")
    print(f"  • Device Type: {vendor_info.get('device_type', 'unknown')}")

    # Check repository info
    repo_info = manager.get_repository_info()
    print(f"\n📁 Repository Info:")
    print(f"  • Base Path: {repo_info['base_path']}")
    print(f"  • Vendor Count: {repo_info['vendor_count']}")
    print(f"  • Download Enabled: {repo_info['download_enabled']}")


def demo_backward_compatibility(manager: FirmwareManager):
    """Demonstrate backward compatibility with legacy configuration."""
    print_section("Backward Compatibility Test")

    print("🔄 Testing backward compatibility...")

    # Test legacy device types
    legacy_devices = ["a1.c5.large", "s2.c2.small", "unknown.device.type"]

    for device in legacy_devices:
        print(f"\n🧪 Testing legacy device: {device}")

        # Test vendor info retrieval
        vendor_info = manager._get_vendor_info(device)
        print(f"  • Vendor: {vendor_info.get('vendor', 'unknown')}")
        print(f"  • Model: {vendor_info.get('model', 'unknown')}")

        # Test validation
        is_valid = manager.validate_device_type(device)
        print(f"  • Valid: {is_valid}")


def demo_comparison_summary(manager: FirmwareManager):
    """Show a comparison summary of capabilities."""
    print_section("Phase 2 Enhancement Summary")

    config_status = manager.get_configuration_status()
    is_unified = config_status["unified_config_available"]

    print(
        f"📈 Configuration System: {'Unified (Enhanced)' if is_unified else 'Legacy'}"
    )

    capabilities = [
        ("Device Type Discovery", "✅ Enhanced" if is_unified else "⚠️  Limited"),
        (
            "Vendor Analysis",
            "✅ Detailed Statistics" if is_unified else "⚠️  Basic Info",
        ),
        (
            "Device Search",
            "✅ Full Text Search" if is_unified else "⚠️  Pattern Matching",
        ),
        (
            "Motherboard Mapping",
            "✅ Accurate from Excel" if is_unified else "⚠️  Hardcoded",
        ),
        ("Backward Compatibility", "✅ Full Support" if is_unified else "✅ Native"),
        (
            "API Enhancements",
            "✅ Enhanced Endpoints" if is_unified else "⚠️  Basic Only",
        ),
    ]

    print("\n🚀 Capability Comparison:")
    for capability, status in capabilities:
        print(f"  • {capability}: {status}")

    # Show device count comparison
    device_count = config_status["supported_device_count"]
    print(f"\n📊 Supported Devices: {device_count} device types")

    if is_unified:
        stats = manager.get_vendor_statistics()
        print(
            f"📊 Vendor Coverage: {stats['total_vendors']} vendors, {stats['total_devices']} devices"
        )


def main():
    """Run the Phase 2 firmware demonstration."""
    try:
        # Initialize FirmwareManager
        manager = demo_firmware_manager_initialization()

        # Demo enhanced capabilities
        device_types = demo_enhanced_device_discovery(manager)
        demo_vendor_analysis(manager)
        demo_device_lookup(manager, device_types)
        demo_device_search(manager)
        demo_firmware_operations(manager, device_types)
        demo_backward_compatibility(manager)
        demo_comparison_summary(manager)

        print_header("Phase 2 Demo Complete")
        print("✅ All Phase 2 firmware enhancements working successfully!")
        print("🚀 Ready for Phase 3: Hardware Discovery Integration")

        return True

    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
