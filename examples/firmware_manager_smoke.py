#!/usr/bin/env python3
"""
Firmware Manager smoke test using project-relative paths.

This is a manual/demo script, not part of pytest collection.
Run from repo root:
    python examples/firmware_manager_smoke.py
"""

import asyncio
import os
import sys
import logging

# Add the src directory to the path for imports (relative to repo root)
CURRENT_DIR = os.path.dirname(__file__)
SRC_PATH = os.path.normpath(os.path.join(CURRENT_DIR, "..", "src"))
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def run_smoke():
    from hwautomation.hardware.firmware_manager import FirmwareManager

    print("=" * 80)
    print("Firmware Manager - Smoke Test")
    print("=" * 80)

    try:
        # Initialize firmware manager
        print("\nInitializing Firmware Manager…")
        manager = FirmwareManager()

        print(f"   Repository base path: {manager.repository.base_path}")
        print(f"   Repository exists: {os.path.exists(manager.repository.base_path)}")

        # Test device types
        test_devices = [
            ("a1.c5.large", "192.168.1.100", "HPE server"),
            ("d1.c1.small", "192.168.1.101", "Supermicro server"),
        ]

        for device_type, target_ip, description in test_devices:
            print(f"\nTesting {description} ({device_type}):")
            print(f"   Target IP: {target_ip}")

            try:
                # Check firmware versions
                firmware_info = await manager.check_firmware_versions(
                    device_type=device_type,
                    target_ip=target_ip,
                    username="admin",
                    password="password",
                )

                print("   Firmware analysis completed:")
                for fw_type, fw_info in firmware_info.items():
                    status = (
                        "UPDATE NEEDED" if fw_info.update_required else "UP TO DATE"
                    )
                    priority = (
                        f"({fw_info.priority.value})" if fw_info.update_required else ""
                    )

                    print(
                        f"      {fw_type.value}: {fw_info.current_version} -> {fw_info.latest_version} {status} {priority}"
                    )

                    if fw_info.file_path:
                        file_exists = os.path.exists(fw_info.file_path)
                        print(
                            f"         File: {fw_info.file_path} {'OK' if file_exists else 'MISSING'}"
                        )

                    if fw_info.checksum:
                        print(f"         Checksum: {fw_info.checksum}")

                # Simulate updates if needed
                updates_needed = [
                    fw for fw in firmware_info.values() if fw.update_required
                ]
                if updates_needed:
                    print(
                        f"\nSimulating firmware updates ({len(updates_needed)} components):"
                    )

                    results = await manager.update_firmware_batch(
                        device_type=device_type,
                        target_ip=target_ip,
                        username="admin",
                        password="password",
                        firmware_list=updates_needed,
                    )

                    for result in results:
                        status = "SUCCESS" if result.success else "FAILED"
                        print(
                            f"      {result.firmware_type.value}: {status} - {result.execution_time:.1f}s"
                        )
                        if result.error_message:
                            print(f"         Error: {result.error_message}")
                else:
                    print("   No firmware updates needed")

            except Exception as e:
                print(f"   Test failed: {e}")

        # Repository configuration
        print("\nRepository Configuration:")
        print(f"   Base path: {manager.repository.base_path}")
        print(f"   Download enabled: {manager.repository.download_enabled}")
        print(f"   Auto verify: {manager.repository.auto_verify}")
        print(f"   Cache duration: {manager.repository.cache_duration}s")

        print("\nVendor Configurations:")
        for vendor_name, vendor_config in manager.repository.vendors.items():
            print(f"   {vendor_name}:")
            print(f"      Display name: {vendor_config.get('display_name', 'N/A')}")

        print("\nFirmware Manager smoke test completed!")
        return True

    except Exception as e:
        print(f"\nFirmware Manager smoke test failed: {e}")
        return False


async def _main() -> int:
    success = await run_smoke()
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
