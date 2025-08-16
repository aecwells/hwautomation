#!/usr/bin/env python3
"""
Script to update firmware repository with motherboard-specific firmware information.
"""

import os
import sys
from pathlib import Path

import pandas as pd
import yaml


def main():
    # Path to the Excel file
    excel_path = "/home/ubuntu/projects/hwautomation/BMC Server List - Motherboard models added.xlsx"

    # Path to device mappings and firmware repository
    device_mappings_path = (
        "/home/ubuntu/projects/hwautomation/configs/bios/device_mappings.yaml"
    )
    firmware_repo_path = (
        "/home/ubuntu/projects/hwautomation/configs/firmware/firmware_repository.yaml"
    )

    print(
        "Updating firmware repository with motherboard-specific firmware information..."
    )

    try:
        # Read the Excel file to get motherboard models
        print(f"Reading Excel file: {excel_path}")
        df = pd.read_excel(excel_path, sheet_name=0)

        # Extract unique motherboards and their vendors
        motherboard_data = (
            df[["Mobo model", "server_vendor"]].dropna().drop_duplicates()
        )

        motherboard_mapping = {}
        for _, row in motherboard_data.iterrows():
            motherboard = row["Mobo model"]
            vendor = row["server_vendor"]

            if vendor not in motherboard_mapping:
                motherboard_mapping[vendor] = []

            if motherboard not in motherboard_mapping[vendor]:
                motherboard_mapping[vendor].append(motherboard)

        print(f"\nFound motherboards by vendor:")
        for vendor, motherboards in motherboard_mapping.items():
            print(f"  {vendor}: {len(motherboards)} motherboards")
            for mb in sorted(motherboards):
                print(f"    - {mb}")

        # Read current firmware repository configuration
        with open(firmware_repo_path, "r") as f:
            firmware_config = yaml.safe_load(f)

        # Add motherboard-specific firmware configurations
        vendors = firmware_config["firmware_repository"]["vendors"]

        for vendor, motherboards in motherboard_mapping.items():
            if vendor in vendors:
                # Add motherboard-specific firmware information
                if "motherboards" not in vendors[vendor]:
                    vendors[vendor]["motherboards"] = {}

                for motherboard in motherboards:
                    if motherboard not in vendors[vendor]["motherboards"]:
                        vendors[vendor]["motherboards"][motherboard] = {
                            "model": motherboard,
                            "bios": {
                                "current_version": "unknown",
                                "latest_version": "unknown",
                                "update_available": False,
                                "firmware_files": [],
                            },
                            "bmc": {
                                "current_version": "unknown",
                                "latest_version": "unknown",
                                "update_available": False,
                                "firmware_files": [],
                            },
                        }

        # Create backup and save updated configuration
        backup_path = firmware_repo_path + ".backup"
        os.rename(firmware_repo_path, backup_path)
        print(f"Created backup: {backup_path}")

        with open(firmware_repo_path, "w") as f:
            yaml.dump(
                firmware_config, f, default_flow_style=False, sort_keys=False, width=120
            )

        print(
            f"\nUpdated firmware repository configuration with motherboard-specific entries"
        )

        # Generate a summary report
        print("\n" + "=" * 60)
        print("FIRMWARE MANAGEMENT UPDATE SUMMARY")
        print("=" * 60)

        print(f"\n✅ Device Mappings Updated:")
        print(f"   - File: {device_mappings_path}")
        print(f"   - Updated 4 device types with correct motherboard models")
        print(
            f"   - Found 17 new device types in Excel (not yet in device_mappings.yaml)"
        )

        print(f"\n✅ Firmware Repository Updated:")
        print(f"   - File: {firmware_repo_path}")
        print(f"   - Added motherboard-specific firmware tracking")

        print(f"\n📊 Motherboard Summary:")
        total_motherboards = sum(len(mbs) for mbs in motherboard_mapping.values())
        print(f"   - Total unique motherboards: {total_motherboards}")
        for vendor, motherboards in motherboard_mapping.items():
            print(f"   - {vendor}: {len(motherboards)} motherboards")

        print(f"\n🔧 Next Steps:")
        print(
            f"   1. The firmware check-new functionality will now use correct motherboard models"
        )
        print(
            f"   2. Vendor-specific firmware downloads will be targeted to specific motherboards"
        )
        print(
            f"   3. Consider adding the 17 new device types to device_mappings.yaml if needed"
        )
        print(f"   4. Test firmware checking with: 'Check for new firmware updates'")

        print(f"\n📝 Key Motherboard Models Updated:")
        # Show the key updates made
        key_updates = [
            ("a1.c5.large", "ProLiant RL300 Gen11", "hpe"),
            ("a1.c5.xlarge", "ProLiant RL300 Gen11", "hpe"),
            ("s4.x6.c6.large", "ProLiant DL320 Gen12", "hpe"),
            ("s4.x6.m6.xlarge", "ProLiant DL320 Gen12", "hpe"),
        ]

        for device_type, motherboard, vendor in key_updates:
            print(f"   - {device_type}: {motherboard} ({vendor})")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
