#!/usr/bin/env python3
"""
Script to consolidate device configurations and create a unified approach.
This will eliminate overlap between firmware_repository.yaml and device_mappings.yaml
and make adding new device types much easier.
"""

import os
import sys
from pathlib import Path

import pandas as pd
import yaml


def analyze_current_overlap():
    """Analyze the current overlap between the two config files."""

    print("🔍 ANALYZING CURRENT CONFIGURATION OVERLAP")
    print("=" * 60)

    # Read current configurations
    device_mappings_path = (
        "/home/ubuntu/projects/hwautomation/configs/bios/device_mappings.yaml"
    )
    firmware_repo_path = (
        "/home/ubuntu/projects/hwautomation/configs/firmware/firmware_repository.yaml"
    )

    with open(device_mappings_path, "r") as f:
        device_mappings = yaml.safe_load(f)

    with open(firmware_repo_path, "r") as f:
        firmware_repo = yaml.safe_load(f)

    print(f"\n📊 CURRENT STATE:")
    print(f"   device_mappings.yaml:")
    print(f"   • {len(device_mappings['device_types'])} device types defined")
    print(f"   • Contains: hardware specs, BIOS settings, boot configs, motherboards")
    print(f"   • Focuses on: device configuration and BIOS management")

    print(f"\n   firmware_repository.yaml:")
    vendor_count = len(firmware_repo["firmware_repository"]["vendors"])
    motherboard_count = 0
    for vendor_data in firmware_repo["firmware_repository"]["vendors"].values():
        if "motherboards" in vendor_data:
            motherboard_count += len(vendor_data["motherboards"])

    print(f"   • {vendor_count} vendors defined")
    print(f"   • {motherboard_count} motherboards with firmware tracking")
    print(f"   • Contains: firmware download URLs, update methods, version tracking")
    print(f"   • Focuses on: firmware management and updates")

    print(f"\n🔄 OVERLAP ISSUES:")
    print(f"   • Motherboard information duplicated in both files")
    print(f"   • Vendor information scattered across files")
    print(f"   • Adding new device types requires updating multiple files")
    print(f"   • Firmware and BIOS configs are artificially separated")

    return device_mappings, firmware_repo


def create_unified_approach():
    """Create a unified device configuration approach."""

    print(f"\n💡 PROPOSED UNIFIED APPROACH:")
    print("=" * 60)

    print(f"\n🎯 SINGLE SOURCE OF TRUTH:")
    print(f"   Create: configs/devices/unified_device_config.yaml")
    print(f"   Contains: All device information in one place")
    print(f"   Structure: vendor -> motherboard -> device_types")

    print(f"\n📋 BENEFITS:")
    print(f"   ✅ Single file to add new device types")
    print(f"   ✅ No duplication of motherboard/vendor info")
    print(f"   ✅ Easier maintenance and updates")
    print(f"   ✅ Clear hierarchy: vendor -> motherboard -> devices")
    print(f"   ✅ Automatic firmware-device type mapping")

    unified_config = {
        "device_configuration": {
            "version": "2.0",
            "last_updated": "2025-08-15",
            "vendors": {},
        }
    }

    return unified_config


def generate_unified_config():
    """Generate the unified configuration from Excel and existing configs."""

    # Read Excel data
    excel_path = "/home/ubuntu/projects/hwautomation/BMC Server List - Motherboard models added.xlsx"
    df = pd.read_excel(excel_path, sheet_name=0)

    # Read existing configurations
    device_mappings_path = (
        "/home/ubuntu/projects/hwautomation/configs/bios/device_mappings.yaml"
    )
    firmware_repo_path = (
        "/home/ubuntu/projects/hwautomation/configs/firmware/firmware_repository.yaml"
    )

    with open(device_mappings_path, "r") as f:
        device_mappings = yaml.safe_load(f)

    with open(firmware_repo_path, "r") as f:
        firmware_repo = yaml.safe_load(f)

    # Create unified structure
    unified_config = {
        "device_configuration": {
            "version": "2.0",
            "last_updated": "2025-08-15",
            "global_settings": {
                "firmware": firmware_repo["firmware_repository"]["global_settings"],
                "default_bios_method": "hybrid",
                "auto_detect_capabilities": True,
            },
            "vendors": {},
        }
    }

    # Process Excel data to create vendor -> motherboard -> device structure
    excel_data = df[
        [
            "internalServerType",
            "Mobo model",
            "server_vendor",
            "cpuName",
            "ramInGb",
            "total cores",
        ]
    ].dropna(subset=["internalServerType", "Mobo model"])

    for _, row in excel_data.iterrows():
        device_type = row["internalServerType"]
        motherboard = row["Mobo model"]
        vendor = row["server_vendor"]

        # Initialize vendor if not exists
        if vendor not in unified_config["device_configuration"]["vendors"]:
            # Get vendor info from firmware_repo
            vendor_info = firmware_repo["firmware_repository"]["vendors"].get(
                vendor, {}
            )
            unified_config["device_configuration"]["vendors"][vendor] = {
                "display_name": vendor_info.get("display_name", vendor.title()),
                "support_url": vendor_info.get("support_url", ""),
                "firmware": {
                    "bios": vendor_info.get("bios", {}),
                    "bmc": vendor_info.get("bmc", {}),
                    "tools": vendor_info.get("tools", {}),
                },
                "motherboards": {},
            }

        # Initialize motherboard if not exists
        if (
            motherboard
            not in unified_config["device_configuration"]["vendors"][vendor][
                "motherboards"
            ]
        ):
            unified_config["device_configuration"]["vendors"][vendor]["motherboards"][
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

        # Add device type information
        device_config = {}

        # Get existing device config if available
        if device_type in device_mappings["device_types"]:
            existing_config = device_mappings["device_types"][device_type]
            device_config = {
                "description": existing_config.get(
                    "description", f"{device_type} server"
                ),
                "hardware_specs": existing_config.get("hardware_specs", {}),
                "boot_configs": existing_config.get("boot_configs", {}),
                "cpu_configs": existing_config.get("cpu_configs", {}),
                "memory_configs": existing_config.get("memory_configs", {}),
                "bios_settings": existing_config.get("bios_setting_methods", {}),
                "redfish_capable": existing_config.get("redfish_capable", True),
                "preferred_bios_method": existing_config.get(
                    "preferred_bios_method", "hybrid"
                ),
            }
        else:
            # Create basic config from Excel data
            device_config = {
                "description": f"{device_type} server",
                "hardware_specs": {
                    "cpu_name": row.get("cpuName", "Unknown"),
                    "ram_gb": (
                        int(row.get("ramInGb", 0))
                        if pd.notna(row.get("ramInGb"))
                        else 0
                    ),
                    "cpu_cores": (
                        int(row.get("total cores", 0))
                        if pd.notna(row.get("total cores"))
                        else 0
                    ),
                    "vendor": vendor,
                },
                "boot_configs": {
                    "boot_mode": "legacy",
                    "pxe_boot": True,
                    "secure_boot": False,
                },
                "cpu_configs": {
                    "hyperthreading": True,
                    "power_profile": "performance",
                    "turbo_boost": True,
                },
                "memory_configs": {"ecc_enabled": True, "memory_speed": "auto"},
                "redfish_capable": True,
                "preferred_bios_method": "hybrid",
            }

        unified_config["device_configuration"]["vendors"][vendor]["motherboards"][
            motherboard
        ]["device_types"][device_type] = device_config

    return unified_config


def create_easy_add_script():
    """Create a script to easily add new device types."""

    script_content = '''#!/usr/bin/env python3
"""
Easy script to add new device types to the unified configuration.
Usage: python add_device_type.py --device-type s1.c3.large --vendor supermicro --motherboard X11SCE-F
"""

import yaml
import argparse
import sys
from pathlib import Path

def add_device_type(device_type, vendor, motherboard, **kwargs):
    """Add a new device type to the unified configuration."""

    config_path = "configs/devices/unified_device_config.yaml"

    # Load existing config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # Initialize vendor if needed
    if vendor not in config['device_configuration']['vendors']:
        print(f"Vendor '{vendor}' not found. Please add vendor configuration first.")
        return False

    # Initialize motherboard if needed
    if motherboard not in config['device_configuration']['vendors'][vendor]['motherboards']:
        config['device_configuration']['vendors'][vendor]['motherboards'][motherboard] = {
            'model': motherboard,
            'firmware_tracking': {
                'bios': {'current_version': 'unknown', 'latest_version': 'unknown', 'update_available': False, 'files': []},
                'bmc': {'current_version': 'unknown', 'latest_version': 'unknown', 'update_available': False, 'files': []}
            },
            'device_types': {}
        }
        print(f"Added new motherboard: {motherboard}")

    # Add device type
    device_config = {
        'description': kwargs.get('description', f'{device_type} server'),
        'hardware_specs': {
            'cpu_name': kwargs.get('cpu_name', 'Unknown'),
            'ram_gb': kwargs.get('ram_gb', 0),
            'cpu_cores': kwargs.get('cpu_cores', 0),
            'cpu_frequency': kwargs.get('cpu_frequency', 0),
            'network': kwargs.get('network', ''),
            'storage': kwargs.get('storage', ''),
            'vendor': vendor
        },
        'boot_configs': {
            'boot_mode': kwargs.get('boot_mode', 'legacy'),
            'pxe_boot': kwargs.get('pxe_boot', True),
            'secure_boot': kwargs.get('secure_boot', False)
        },
        'cpu_configs': {
            'hyperthreading': kwargs.get('hyperthreading', True),
            'power_profile': kwargs.get('power_profile', 'performance'),
            'turbo_boost': kwargs.get('turbo_boost', True)
        },
        'memory_configs': {
            'ecc_enabled': kwargs.get('ecc_enabled', True),
            'memory_speed': kwargs.get('memory_speed', 'auto')
        },
        'redfish_capable': kwargs.get('redfish_capable', True),
        'preferred_bios_method': kwargs.get('preferred_bios_method', 'hybrid')
    }

    config['device_configuration']['vendors'][vendor]['motherboards'][motherboard]['device_types'][device_type] = device_config

    # Save updated config
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, width=120)

    print(f"✅ Added device type: {device_type}")
    print(f"   Vendor: {vendor}")
    print(f"   Motherboard: {motherboard}")
    return True

def main():
    parser = argparse.ArgumentParser(description='Add new device type to unified configuration')
    parser.add_argument('--device-type', required=True, help='Device type (e.g., s1.c3.large)')
    parser.add_argument('--vendor', required=True, help='Vendor (e.g., supermicro, hpe)')
    parser.add_argument('--motherboard', required=True, help='Motherboard model (e.g., X11SCE-F)')
    parser.add_argument('--description', help='Device description')
    parser.add_argument('--cpu-name', help='CPU name')
    parser.add_argument('--ram-gb', type=int, help='RAM in GB')
    parser.add_argument('--cpu-cores', type=int, help='Number of CPU cores')
    parser.add_argument('--cpu-frequency', type=float, help='CPU frequency in GHz')
    parser.add_argument('--network', help='Network specification')
    parser.add_argument('--storage', help='Storage specification')

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
        storage=args.storage
    )

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
'''

    return script_content


def main():
    print("DEVICE CONFIGURATION CONSOLIDATION ANALYSIS")
    print("=" * 80)

    # Analyze current overlap
    device_mappings, firmware_repo = analyze_current_overlap()

    # Create unified approach
    create_unified_approach()

    print(f"\n🏗️ GENERATING UNIFIED CONFIGURATION:")
    print("=" * 60)

    try:
        unified_config = generate_unified_config()

        # Create directories
        unified_config_dir = Path("/home/ubuntu/projects/hwautomation/configs/devices")
        unified_config_dir.mkdir(exist_ok=True)

        # Write unified config
        unified_config_path = unified_config_dir / "unified_device_config.yaml"
        with open(unified_config_path, "w") as f:
            yaml.dump(
                unified_config, f, default_flow_style=False, sort_keys=False, width=120
            )

        print(f"✅ Created: {unified_config_path}")

        # Create easy add script
        add_script_path = Path(
            "/home/ubuntu/projects/hwautomation/tools/add_device_type.py"
        )
        add_script_content = create_easy_add_script()
        with open(add_script_path, "w") as f:
            f.write(add_script_content)

        print(f"✅ Created: {add_script_path}")

        # Generate summary
        vendor_count = len(unified_config["device_configuration"]["vendors"])
        total_motherboards = sum(
            len(v["motherboards"])
            for v in unified_config["device_configuration"]["vendors"].values()
        )
        total_devices = sum(
            len(mb["device_types"])
            for v in unified_config["device_configuration"]["vendors"].values()
            for mb in v["motherboards"].values()
        )

        print(f"\n📊 UNIFIED CONFIGURATION SUMMARY:")
        print(f"   • {vendor_count} vendors")
        print(f"   • {total_motherboards} motherboards")
        print(f"   • {total_devices} device types")

        print(f"\n🚀 HOW TO ADD NEW DEVICE TYPES:")
        print(f"   1. Using the script:")
        print(f"      python tools/add_device_type.py \\")
        print(f"        --device-type s1.c3.large \\")
        print(f"        --vendor supermicro \\")
        print(f"        --motherboard X11SCE-F \\")
        print(f"        --cpu-name 'Intel Xeon E-2288G' \\")
        print(f"        --ram-gb 128 \\")
        print(f"        --cpu-cores 8")

        print(f"\n   2. Or manually edit: {unified_config_path}")
        print(f"      Follow the existing structure under:")
        print(
            f"      vendors -> [vendor] -> motherboards -> [motherboard] -> device_types"
        )

        print(f"\n🔄 MIGRATION PLAN:")
        print(f"   1. Test the unified config with current firmware functionality")
        print(
            f"   2. Update code to use unified_device_config.yaml instead of separate files"
        )
        print(
            f"   3. Gradually migrate away from device_mappings.yaml and firmware_repository.yaml"
        )
        print(
            f"   4. Update adding the 17 new flex-* device types using the new approach"
        )

        return True

    except Exception as e:
        print(f"❌ Error generating unified configuration: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
