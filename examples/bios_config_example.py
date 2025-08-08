#!/usr/bin/env python3
"""
BIOS Configuration Example Usage - Smart Pull-Edit-Push Approach

This example demonstrates how to use the BIOS Configuration Manager
with the smart pull-edit-push approach that preserves hardware-specific settings.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hwautomation.hardware.bios_config import BiosConfigManager


def main():
    """Demonstrate smart BIOS configuration management."""
    print("Smart BIOS Configuration Manager Example")
    print("=" * 45)

    # Initialize the BIOS config manager
    manager = BiosConfigManager()

    # List available device types
    print("\n1. Available Device Types:")
    device_types = manager.get_device_types()
    for device_type in device_types:
        config = manager.get_device_config(device_type)
        print(f"   {device_type}: {config.get('description', 'No description')}")

    # Show template rules for s2_c2_small
    print("\n2. Template Rules for s2_c2_small:")
    if "template_rules" in manager.template_rules:
        rules = manager.template_rules["template_rules"].get("s2_c2_small", {})
        modifications = rules.get("modifications", {})
        print(f"   Description: {rules.get('description', 'N/A')}")
        print("   Key Settings:")
        for setting, value in list(modifications.items())[:5]:  # Show first 5
            print(f"     {setting}: {value}")
        if len(modifications) > 5:
            print(f"     ... and {len(modifications) - 5} more settings")

    # Show preserve settings
    print("\n3. Settings That Will Be Preserved:")
    preserve_count = len(manager.preserve_settings)
    print(f"   Total: {preserve_count} setting patterns")
    sample_preserves = list(manager.preserve_settings)[:8]
    for setting in sample_preserves:
        print(f"     {setting}")
    if preserve_count > 8:
        print(f"     ... and {preserve_count - 8} more patterns")

    # Demonstrate smart configuration (dry run)
    print("\n4. Smart Configuration Demo (Dry Run):")
    print("   Target IP: 192.168.1.100 (mock)")
    print("   Device Type: s2_c2_small")

    try:
        # This would normally connect to a real system
        result = manager.apply_bios_config_smart(
            device_type="s2_c2_small",
            target_ip="192.168.1.100",
            username="ADMIN",
            password="mock_password",
            dry_run=True,
        )

        print(f"   Success: {result['success']}")
        if result["success"]:
            print(f"   Changes to be made: {len(result['changes_made'])}")
            for change in result["changes_made"][:3]:  # Show first 3 changes
                print(f"     - {change}")
            if len(result["changes_made"]) > 3:
                print(f"     ... and {len(result['changes_made']) - 3} more changes")
        else:
            print(f"   Error: {result.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"   Error: {e}")

    # Show motherboard compatibility
    print("\n5. Motherboard Compatibility:")
    for device_type in device_types:
        motherboards = manager.get_motherboard_for_device(device_type)
        if motherboards:
            print(f"   {device_type}: {', '.join(motherboards)}")

    print("\n" + "=" * 45)
    print("Smart BIOS Configuration Features:")
    print("✓ Pulls current BIOS settings from target system")
    print("✓ Preserves hardware-specific settings (MAC addresses, serial numbers)")
    print("✓ Applies only necessary changes based on device type templates")
    print("✓ Validates configuration before applying")
    print("✓ Creates automatic backups")
    print("✓ Supports dry-run mode to preview changes")

    print("\nCommand-line usage:")
    print("  # Pull current config")
    print("  python scripts/bios_manager.py pull-config 192.168.1.100")
    print()
    print("  # Dry run to see what would change")
    print(
        "  python scripts/bios_manager.py apply-config s2_c2_small 192.168.1.100 --dry-run"
    )
    print()
    print("  # Apply configuration")
    print("  python scripts/bios_manager.py apply-config s2_c2_small 192.168.1.100")


if __name__ == "__main__":
    main()
