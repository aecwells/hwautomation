#!/usr/bin/env python3
"""
Easy script to add new device types to the unified configuration.
Usage: python add_device_type.py --device-type s1.c3.large --vendor supermicro --motherboard X11SCE-F
"""

import argparse
import sys
from pathlib import Path

import yaml


def add_device_type(device_type, vendor, motherboard, **kwargs):
    """Add a new device type to the unified configuration."""

    config_path = "configs/devices/unified_device_config.yaml"

    # Load existing config
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Initialize vendor if needed
    if vendor not in config["device_configuration"]["vendors"]:
        print(f"Vendor '{vendor}' not found. Please add vendor configuration first.")
        return False

    # Initialize motherboard if needed
    if (
        motherboard
        not in config["device_configuration"]["vendors"][vendor]["motherboards"]
    ):
        config["device_configuration"]["vendors"][vendor]["motherboards"][
            motherboard
        ] = {
            "model": motherboard,
            "firmware_tracking": {
                "bios": {
                    "current_version": "unknown",
                    "latest_version": "unknown",
                    "update_available": False,
                    "files": [],
                },
                "bmc": {
                    "current_version": "unknown",
                    "latest_version": "unknown",
                    "update_available": False,
                    "files": [],
                },
            },
            "device_types": {},
        }
        print(f"Added new motherboard: {motherboard}")

    # Add device type
    device_config = {
        "description": kwargs.get("description", f"{device_type} server"),
        "hardware_specs": {
            "cpu_name": kwargs.get("cpu_name", "Unknown"),
            "ram_gb": kwargs.get("ram_gb", 0),
            "cpu_cores": kwargs.get("cpu_cores", 0),
            "cpu_frequency": kwargs.get("cpu_frequency", 0),
            "network": kwargs.get("network", ""),
            "storage": kwargs.get("storage", ""),
            "vendor": vendor,
        },
        "boot_configs": {
            "boot_mode": kwargs.get("boot_mode", "legacy"),
            "pxe_boot": kwargs.get("pxe_boot", True),
            "secure_boot": kwargs.get("secure_boot", False),
        },
        "cpu_configs": {
            "hyperthreading": kwargs.get("hyperthreading", True),
            "power_profile": kwargs.get("power_profile", "performance"),
            "turbo_boost": kwargs.get("turbo_boost", True),
        },
        "memory_configs": {
            "ecc_enabled": kwargs.get("ecc_enabled", True),
            "memory_speed": kwargs.get("memory_speed", "auto"),
        },
        "redfish_capable": kwargs.get("redfish_capable", True),
        "preferred_bios_method": kwargs.get("preferred_bios_method", "hybrid"),
    }

    config["device_configuration"]["vendors"][vendor]["motherboards"][motherboard][
        "device_types"
    ][device_type] = device_config

    # Save updated config
    with open(config_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, width=120)

    print(f"✅ Added device type: {device_type}")
    print(f"   Vendor: {vendor}")
    print(f"   Motherboard: {motherboard}")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Add new device type to unified configuration"
    )
    parser.add_argument(
        "--device-type", required=True, help="Device type (e.g., s1.c3.large)"
    )
    parser.add_argument(
        "--vendor", required=True, help="Vendor (e.g., supermicro, hpe)"
    )
    parser.add_argument(
        "--motherboard", required=True, help="Motherboard model (e.g., X11SCE-F)"
    )
    parser.add_argument("--description", help="Device description")
    parser.add_argument("--cpu-name", help="CPU name")
    parser.add_argument("--ram-gb", type=int, help="RAM in GB")
    parser.add_argument("--cpu-cores", type=int, help="Number of CPU cores")
    parser.add_argument("--cpu-frequency", type=float, help="CPU frequency in GHz")
    parser.add_argument("--network", help="Network specification")
    parser.add_argument("--storage", help="Storage specification")

    args = parser.parse_args()

    success = add_device_type(
        args.device_type,
        args.vendor,
        args.motherboard,
        description=args.description,
        cpu_name=args.cpu_name,
        ram_gb=args.ram_gb,
        cpu_cores=args.cpu_cores,
        cpu_frequency=args.cpu_frequency,
        network=args.network,
        storage=args.storage,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
