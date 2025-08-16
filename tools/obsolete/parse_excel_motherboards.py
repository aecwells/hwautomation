#!/usr/bin/env python3
"""
Script to parse the Excel file with motherboard information and update device mappings.
"""

import os
import sys
from pathlib import Path

import pandas as pd
import yaml


def main():
    # Path to the Excel file
    excel_path = "/home/ubuntu/projects/hwautomation/BMC Server List - Motherboard models added.xlsx"

    # Path to device mappings
    device_mappings_path = (
        "/home/ubuntu/projects/hwautomation/configs/bios/device_mappings.yaml"
    )

    if not os.path.exists(excel_path):
        print(f"Error: Excel file not found at {excel_path}")
        return 1

    try:
        # Read the Excel file
        print(f"Reading Excel file: {excel_path}")
        df = pd.read_excel(excel_path, sheet_name=0)  # "Server Types" sheet

        # Extract device type to motherboard mapping
        device_type_col = "internalServerType"
        motherboard_col = "Mobo model"
        vendor_col = "server_vendor"

        # Filter out rows where device type or motherboard is missing
        valid_data = df.dropna(subset=[device_type_col, motherboard_col])

        # Create mapping dictionary
        device_motherboard_mapping = {}

        for _, row in valid_data.iterrows():
            device_type = row[device_type_col]
            motherboard = row[motherboard_col]
            vendor = row[vendor_col] if pd.notna(row[vendor_col]) else "unknown"

            if device_type not in device_motherboard_mapping:
                device_motherboard_mapping[device_type] = {
                    "motherboard": motherboard,
                    "vendor": vendor,
                }

        print(
            f"\nFound {len(device_motherboard_mapping)} device types with motherboard information:"
        )
        for device_type, info in sorted(device_motherboard_mapping.items()):
            print(f"  {device_type}: {info['motherboard']} ({info['vendor']})")

        # Now update the device_mappings.yaml file
        print(f"\nReading current device mappings from: {device_mappings_path}")

        with open(device_mappings_path, "r") as f:
            device_mappings = yaml.safe_load(f)

        if "device_types" not in device_mappings:
            print("Error: device_types not found in device mappings file")
            return 1

        updates_made = 0
        new_devices_found = 0

        # Update existing device types with motherboard information
        for device_type, mapping_info in device_motherboard_mapping.items():
            motherboard = mapping_info["motherboard"]
            vendor = mapping_info["vendor"]

            if device_type in device_mappings["device_types"]:
                # Update existing device type
                current_motherboards = device_mappings["device_types"][device_type].get(
                    "motherboards", ["Unknown"]
                )

                # Only update if current is Unknown or empty
                if current_motherboards == ["Unknown"] or not current_motherboards:
                    device_mappings["device_types"][device_type]["motherboards"] = [
                        motherboard
                    ]

                    # Also update vendor if it exists in hardware_specs
                    if "hardware_specs" in device_mappings["device_types"][device_type]:
                        device_mappings["device_types"][device_type]["hardware_specs"][
                            "vendor"
                        ] = vendor

                    print(
                        f"  Updated {device_type}: motherboard = {motherboard}, vendor = {vendor}"
                    )
                    updates_made += 1
                else:
                    print(
                        f"  Skipped {device_type}: already has motherboard {current_motherboards}"
                    )
            else:
                print(
                    f"  New device type found in Excel: {device_type} -> {motherboard} ({vendor})"
                )
                new_devices_found += 1

        # Save the updated device mappings
        if updates_made > 0:
            # Create backup
            backup_path = device_mappings_path + ".backup"
            os.rename(device_mappings_path, backup_path)
            print(f"Created backup: {backup_path}")

            # Write updated mappings
            with open(device_mappings_path, "w") as f:
                yaml.dump(
                    device_mappings,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    width=120,
                )

            print(
                f"\nUpdated device mappings file with {updates_made} motherboard updates"
            )
        else:
            print(
                "\nNo updates needed - all device types already have motherboard information"
            )

        if new_devices_found > 0:
            print(
                f"\nFound {new_devices_found} new device types in Excel that are not in device_mappings.yaml"
            )
            print("You may want to add these manually if they should be supported.")

        return 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
