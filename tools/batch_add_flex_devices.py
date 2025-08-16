#!/usr/bin/env python3
"""
Batch script to add all remaining flex device types from Excel data.
"""

import subprocess
import sys

import pandas as pd


def add_flex_devices():
    """Add all flex device types from Excel data."""

    print("🚀 ADDING ALL FLEX DEVICE TYPES")
    print("=" * 50)

    # Read Excel data
    df = pd.read_excel("BMC Server List - Motherboard models added.xlsx", sheet_name=0)
    flex_devices = df[
        df["internalServerType"].str.contains("flex", na=False, case=False)
    ]

    # Remove duplicates based on device type
    flex_devices = flex_devices.drop_duplicates(subset=["internalServerType"])

    added_count = 0

    for _, row in flex_devices.iterrows():
        device_type = row["internalServerType"]
        motherboard = row["Mobo model"]
        vendor = row["server_vendor"]
        cpu_name = row["cpuName"]
        ram_gb = int(row["ramInGb"]) if pd.notna(row["ramInGb"]) else 0
        cpu_cores = int(row["total cores"]) if pd.notna(row["total cores"]) else 0

        # Create description
        description = f"Flex server - {cpu_name}"

        # Convert all values to strings and handle NaN values
        device_type = str(device_type) if pd.notna(device_type) else "unknown"
        motherboard = str(motherboard) if pd.notna(motherboard) else "unknown"
        vendor = str(vendor) if pd.notna(vendor) else "unknown"
        cpu_name = str(cpu_name) if pd.notna(cpu_name) else "unknown"

        # Run add script
        cmd = [
            "python",
            "tools/add_device_type.py",
            "--device-type",
            device_type,
            "--vendor",
            vendor,
            "--motherboard",
            motherboard,
            "--description",
            description,
            "--cpu-name",
            cpu_name,
            "--ram-gb",
            str(ram_gb),
            "--cpu-cores",
            str(cpu_cores),
            "--network",
            "2x 10Gbps",
            "--storage",
            "2x 1TB NVMe",
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"✅ {device_type}")
            added_count += 1
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to add {device_type}: {e}")
            print(f"   Error output: {e.stderr}")

    print(f"\n📊 SUMMARY:")
    print(f"   • Added {added_count} flex device types")
    print(f"   • Total flex devices in Excel: {len(flex_devices)}")

    return added_count


if __name__ == "__main__":
    added_count = add_flex_devices()
    print(f"\n🎉 Successfully added {added_count} flex device types!")
