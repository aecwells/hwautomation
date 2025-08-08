#!/usr/bin/env python3
"""
Vendor Discovery Test Script

This script demonstrates the vendor-specific hardware discovery capabilities
for HPE and Supermicro devices. It tests the installation and usage of vendor
tools like sumtool (Supermicro) and hpssacli (HPE).

Usage:
    python vendor_discovery_test.py --host <hostname> [--user <username>]
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add the source directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging

from hwautomation.hardware.discovery import HardwareDiscoveryManager
from hwautomation.utils.config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def main():
    parser = argparse.ArgumentParser(
        description="Test vendor-specific hardware discovery"
    )
    parser.add_argument("--host", required=True, help="Target hostname or IP address")
    parser.add_argument(
        "--user", default="ubuntu", help="SSH username (default: ubuntu)"
    )
    parser.add_argument("--ssh-key", help="Path to SSH private key file")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--manufacturer",
        help="Force specific manufacturer detection (supermicro, hpe, dell)",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"Warning: Could not load config: {e}")
        config = {}

    # Initialize discovery manager
    discovery_manager = HardwareDiscoveryManager(config)

    print(f"Testing vendor-specific discovery on {args.host}...")
    print("=" * 60)

    try:
        # Perform hardware discovery
        result = discovery_manager.discover_hardware(
            hostname=args.host, username=args.user, ssh_key_path=args.ssh_key
        )

        if result.success:
            print("✅ Hardware discovery completed successfully!")
            print()

            # Display system information
            system_info = result.system_info
            print("System Information:")
            print(f"  Manufacturer: {system_info.manufacturer}")
            print(f"  Product Name: {system_info.product_name}")
            print(f"  Serial Number: {system_info.serial_number}")
            print(f"  UUID: {system_info.uuid}")
            print()

            # Display BIOS information
            print("BIOS Information:")
            print(f"  Vendor: {system_info.bios_vendor}")
            print(f"  Version: {system_info.bios_version}")
            print(f"  Release Date: {system_info.bios_release_date}")
            print()

            # Display IPMI information
            if result.ipmi_info:
                print("IPMI/BMC Information:")
                print(f"  IP Address: {result.ipmi_info.ip_address}")
                print(f"  MAC Address: {result.ipmi_info.mac_address}")
                print(f"  Channel: {result.ipmi_info.channel}")
                print()

            # Display vendor-specific information
            vendor_info = getattr(result, "vendor_info", {})
            if vendor_info:
                print("Vendor-Specific Information:")
                print(json.dumps(vendor_info, indent=2))
                print()

            # Test specific vendor functionality
            manufacturer = args.manufacturer or system_info.manufacturer.lower()

            if "supermicro" in manufacturer:
                print(
                    "🔧 Supermicro Device Detected - Testing sumtool functionality..."
                )
                test_supermicro_tools(
                    discovery_manager, args.host, args.user, args.ssh_key
                )
            elif "hewlett" in manufacturer or "hpe" in manufacturer:
                print("🔧 HPE Device Detected - Testing HPE tools functionality...")
                test_hpe_tools(discovery_manager, args.host, args.user, args.ssh_key)
            elif "dell" in manufacturer:
                print(
                    "🔧 Dell Device Detected - Testing Dell OpenManage functionality..."
                )
                test_dell_tools(discovery_manager, args.host, args.user, args.ssh_key)
            else:
                print(f"ℹ️  Unknown or unsupported manufacturer: {manufacturer}")
                print("   Supported vendors: Supermicro, HPE, Dell")

        else:
            print("❌ Hardware discovery failed!")
            print("Errors:")
            for error in result.errors:
                print(f"  - {error}")

    except KeyboardInterrupt:
        print("\n⚠️  Discovery interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error during discovery: {e}")
        sys.exit(1)


def test_supermicro_tools(discovery_manager, hostname, username, ssh_key_path):
    """Test Supermicro sumtool functionality"""
    print("  • Testing sumtool installation and commands...")

    ssh_manager = discovery_manager.ssh_manager

    try:
        with ssh_manager.get_client(hostname, username, ssh_key_path) as ssh_client:
            # Test sumtool availability
            result = ssh_client.execute_command("which sum")
            if result.exit_code == 0:
                print("    ✅ sumtool is available")

                # Test basic sumtool commands
                commands = [
                    ("sum -c GetSystemInfo", "System Information"),
                    ("sum -c GetBiosInfo", "BIOS Information"),
                    ("sum -c GetBmcInfo", "BMC Information"),
                ]

                for cmd, desc in commands:
                    result = ssh_client.execute_command(f"sudo {cmd}")
                    if result.exit_code == 0:
                        print(f"    ✅ {desc} - Command executed successfully")
                        # Show first few lines of output
                        lines = result.stdout.split("\n")[:3]
                        for line in lines:
                            if line.strip():
                                print(f"      {line.strip()}")
                    else:
                        print(f"    ❌ {desc} - Command failed: {result.stderr}")
            else:
                print(
                    "    ⚠️  sumtool not available - would be installed during discovery"
                )

    except Exception as e:
        print(f"    ❌ Error testing Supermicro tools: {e}")


def test_hpe_tools(discovery_manager, hostname, username, ssh_key_path):
    """Test HPE tools functionality"""
    print("  • Testing HPE management tools...")

    ssh_manager = discovery_manager.ssh_manager

    try:
        with ssh_manager.get_client(hostname, username, ssh_key_path) as ssh_client:
            # Test HPE tools availability
            hpe_tools = ["hpssacli", "ssacli"]
            available_tool = None

            for tool in hpe_tools:
                result = ssh_client.execute_command(f"which {tool}")
                if result.exit_code == 0:
                    available_tool = tool
                    print(f"    ✅ {tool} is available")
                    break

            if available_tool:
                # Test controller discovery
                result = ssh_client.execute_command(
                    f"sudo {available_tool} ctrl all show config"
                )
                if result.exit_code == 0:
                    print(
                        "    ✅ Controller Information - Command executed successfully"
                    )
                    # Show first few lines
                    lines = result.stdout.split("\n")[:5]
                    for line in lines:
                        if line.strip():
                            print(f"      {line.strip()}")
                else:
                    print(
                        f"    ⚠️  Controller query failed (may be normal if no controllers present)"
                    )
            else:
                print(
                    "    ⚠️  HPE tools not available - would be installed during discovery"
                )

            # Test iLO detection
            result = ssh_client.execute_command("sudo dmidecode -t 38 | grep -i ilo")
            if result.exit_code == 0 and result.stdout.strip():
                print("    ✅ iLO detected")
            else:
                print("    ℹ️  iLO not detected via dmidecode")

    except Exception as e:
        print(f"    ❌ Error testing HPE tools: {e}")


def test_dell_tools(discovery_manager, hostname, username, ssh_key_path):
    """Test Dell OpenManage tools functionality"""
    print("  • Testing Dell OpenManage tools...")

    ssh_manager = discovery_manager.ssh_manager

    try:
        with ssh_manager.get_client(hostname, username, ssh_key_path) as ssh_client:
            # Test OpenManage availability
            result = ssh_client.execute_command("which omreport")
            if result.exit_code == 0:
                print("    ✅ omreport is available")

                # Test chassis information
                result = ssh_client.execute_command("sudo omreport chassis info")
                if result.exit_code == 0:
                    print("    ✅ Chassis Information - Command executed successfully")
                    # Show first few lines
                    lines = result.stdout.split("\n")[:5]
                    for line in lines:
                        if line.strip():
                            print(f"      {line.strip()}")
                else:
                    print(f"    ❌ Chassis query failed: {result.stderr}")
            else:
                print(
                    "    ⚠️  Dell OpenManage tools not available - would be installed during discovery"
                )

    except Exception as e:
        print(f"    ❌ Error testing Dell tools: {e}")


if __name__ == "__main__":
    main()
