#!/usr/bin/env python3
"""
Redfish Integration Example for HWAutomation

This example demonstrates Redfish integration:
- Basic hardware discovery via Redfish
- Power control operations
- Simple BIOS configuration
- Comparison with vendor tools

Usage:
    python examples/redfish_example.py --target <ip> --username <user> --password <pass>
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hwautomation.hardware.bios import BiosConfigManager
from hwautomation.hardware.redfish import RedfishManager

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_redfish_connection(target_ip: str, username: str, password: str):
    """Test basic Redfish connectivity."""
    print(f"\n🔍 Testing Redfish connection to {target_ip}")
    print("=" * 50)

    try:
        with RedfishManager(target_ip, username, password) as redfish:
            success, message = redfish.test_connection()

            if success:
                print(f"✅ {message}")
                return True
            else:
                print(f"❌ {message}")
                return False

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


def discover_system_info(target_ip: str, username: str, password: str):
    """Discover system information via Redfish."""
    print(f"\n🖥️  Discovering system information")
    print("=" * 50)

    try:
        with RedfishManager(target_ip, username, password) as redfish:
            # Get service root info
            service_root = redfish.discover_service_root()
            print(f"Redfish Version: {service_root.get('RedfishVersion', 'Unknown')}")
            print(f"Service ID: {service_root.get('Id', 'Unknown')}")

            # Get capabilities
            capabilities = redfish.discover_capabilities()
            print(f"\nCapabilities:")
            print(
                f"  System Info: {'✅' if capabilities.supports_system_info else '❌'}"
            )
            print(
                f"  Power Control: {'✅' if capabilities.supports_power_control else '❌'}"
            )
            print(
                f"  BIOS Config: {'✅' if capabilities.supports_bios_config else '❌'}"
            )

            # Get detailed system info
            system_info = redfish.get_system_info()
            if system_info:
                print(f"\nSystem Information:")
                print(f"  Manufacturer: {system_info.manufacturer}")
                print(f"  Model: {system_info.model}")
                print(f"  Serial Number: {system_info.serial_number}")
                print(f"  BIOS Version: {system_info.bios_version}")
                print(f"  Power State: {system_info.power_state}")
                print(f"  Health Status: {system_info.health_status}")
                print(f"  Processors: {system_info.processor_count}")
                print(f"  Memory: {system_info.memory_total_gb} GB")
            else:
                print("❌ Could not retrieve system information")

            return capabilities

    except Exception as e:
        print(f"❌ System discovery failed: {e}")
        return None


def test_power_operations(target_ip: str, username: str, password: str):
    """Test power control operations (read-only for safety)."""
    print(f"\n⚡ Testing power operations")
    print("=" * 50)

    try:
        with RedfishManager(target_ip, username, password) as redfish:
            # Get current power state
            power_state = redfish.get_power_state()
            print(f"Current Power State: {power_state}")

            # Note: We don't actually change power state in this example
            print("\n⚠️  Power control commands available (not executed in this demo):")
            print("   - On: Turn system on")
            print("   - ForceOff: Force immediate shutdown")
            print("   - GracefulShutdown: Graceful shutdown")
            print("   - ForceRestart: Force restart")
            print("   - GracefulRestart: Graceful restart")

    except Exception as e:
        print(f"❌ Power operations test failed: {e}")


def test_bios_operations(target_ip: str, username: str, password: str):
    """Test BIOS configuration operations."""
    print(f"\n⚙️  Testing BIOS operations")
    print("=" * 50)

    try:
        with RedfishManager(target_ip, username, password) as redfish:
            capabilities = redfish.discover_capabilities()

            if not capabilities.supports_bios_config:
                print("❌ BIOS configuration not supported via Redfish")
                return

            # Get current BIOS settings
            bios_settings = redfish.get_bios_settings()
            if bios_settings:
                print(f"✅ Retrieved {len(bios_settings)} BIOS settings")

                # Show a sample of settings
                print("\n📋 Sample BIOS Settings:")
                count = 0
                for key, value in sorted(bios_settings.items()):
                    if count < 10:  # Show first 10 settings
                        print(f"  {key}: {value}")
                        count += 1
                    else:
                        print(f"  ... and {len(bios_settings) - 10} more settings")
                        break

                # Note: We don't modify settings in this example
                print("\n⚠️  BIOS modification available but not executed in this demo")
                print(
                    "   Use --modify-bios flag to test setting changes (with caution!)"
                )

            else:
                print("❌ Could not retrieve BIOS settings")

    except Exception as e:
        print(f"❌ BIOS operations test failed: {e}")


def compare_with_bios_manager(target_ip: str, username: str, password: str):
    """Compare Redfish capabilities with BiosConfigManager."""
    print(f"\n🔄 Comparing Redfish with BIOS Config Manager")
    print("=" * 50)

    try:
        bios_manager = BiosConfigManager()

        # Test Redfish connection via BIOS manager
        redfish_success, redfish_msg = bios_manager.test_redfish_connection(
            target_ip, username, password
        )
        print(
            f"Redfish via BiosConfigManager: {'✅' if redfish_success else '❌'} {redfish_msg}"
        )

        # Test method determination
        device_type = "a1.c5.large"  # Example device type
        method = bios_manager.determine_bios_config_method(
            target_ip, device_type, username, password
        )
        print(f"Recommended BIOS config method for {device_type}: {method}")

        # Get system info via BIOS manager
        system_info = bios_manager.get_system_info_via_redfish(
            target_ip, username, password
        )
        if system_info:
            print(
                f"System info via BiosConfigManager: {system_info.manufacturer} {system_info.model}"
            )
        else:
            print("❌ Could not get system info via BiosConfigManager")

    except Exception as e:
        print(f"❌ BIOS manager comparison failed: {e}")


def test_enhanced_bios_config(
    target_ip: str, username: str, password: str, device_type: str, dry_run: bool = True
):
    """Test enhanced BIOS configuration with Redfish support."""
    print(f"\n🚀 Testing Enhanced BIOS Configuration")
    print("=" * 50)

    try:
        bios_manager = BiosConfigManager()

        # Test enhanced smart configuration
        result = bios_manager.apply_bios_config_smart_enhanced(
            device_type=device_type,
            target_ip=target_ip,
            username=username,
            password=password,
            dry_run=dry_run,
            prefer_redfish=True,
        )

        print(f"Configuration Method Used: {result.get('method_used', 'unknown')}")
        print(f"Success: {'✅' if result.get('success') else '❌'}")
        print(f"Message: {result.get('message', 'No message')}")

        if result.get("error"):
            print(f"Error: {result['error']}")

        changes = result.get("changes_made", [])
        if changes:
            print(f"\n📝 Changes {'(would be made)' if dry_run else 'made'}:")
            for change in changes[:10]:  # Show first 10 changes
                print(f"  {change}")
            if len(changes) > 10:
                print(f"  ... and {len(changes) - 10} more changes")
        else:
            print("📝 No changes needed")

    except Exception as e:
        print(f"❌ Enhanced BIOS configuration test failed: {e}")


def main():
    """Main example function."""
    parser = argparse.ArgumentParser(description="Redfish Integration Example")
    parser.add_argument("--target", required=True, help="Target BMC IP address")
    parser.add_argument(
        "--username", default="ADMIN", help="BMC username (default: ADMIN)"
    )
    parser.add_argument("--password", required=True, help="BMC password")
    parser.add_argument(
        "--device-type", default="a1.c5.large", help="Device type for BIOS config test"
    )
    parser.add_argument(
        "--modify-bios",
        action="store_true",
        help="Actually modify BIOS settings (use with caution!)",
    )
    parser.add_argument(
        "--power-control", help="Power control action (On, ForceOff, etc.)"
    )

    args = parser.parse_args()

    print("🔧 HWAutomation Redfish Integration Example")
    print("=" * 50)
    print(f"Target: {args.target}")
    print(f"Username: {args.username}")
    print(f"Device Type: {args.device_type}")

    # Test connection
    if not test_redfish_connection(args.target, args.username, args.password):
        print("\n❌ Cannot proceed - Redfish connection failed")
        sys.exit(1)

    # Discover system
    capabilities = discover_system_info(args.target, args.username, args.password)

    # Test power operations
    test_power_operations(args.target, args.username, args.password)

    # Execute power control if requested
    if args.power_control:
        print(f"\n⚡ Executing power control: {args.power_control}")
        try:
            with RedfishManager(args.target, args.username, args.password) as redfish:
                success = redfish.power_control(args.power_control)
                print(
                    f"Power control result: {'✅ Success' if success else '❌ Failed'}"
                )
        except Exception as e:
            print(f"❌ Power control failed: {e}")

    # Test BIOS operations
    test_bios_operations(args.target, args.username, args.password)

    # Compare with BIOS manager
    compare_with_bios_manager(args.target, args.username, args.password)

    # Test enhanced BIOS configuration
    dry_run = not args.modify_bios
    test_enhanced_bios_config(
        args.target, args.username, args.password, args.device_type, dry_run
    )

    print(f"\n🎉 Redfish example completed!")
    print("\nNext steps:")
    print("1. Review the discovered capabilities")
    print("2. Configure device_mappings.yaml with Redfish preferences")
    print("3. Test with your specific hardware vendor")
    print("4. Integrate into your automation workflows")


if __name__ == "__main__":
    main()
