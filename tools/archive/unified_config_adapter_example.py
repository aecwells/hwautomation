#!/usr/bin/env python3
"""
Example showing how to create a UnifiedConfigLoader adapter that can replace
the current configuration loading while maintaining backward compatibility.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class UnifiedConfigLoader:
    """
    Adapter to load unified device configuration and provide backward-compatible
    interfaces for existing BIOS and firmware managers.
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize with unified config path."""
        self.config_path = config_path or self._get_default_config_path()
        self._config_cache = None

    def _get_default_config_path(self) -> str:
        """Get default unified config path."""
        return "/home/ubuntu/projects/hwautomation/configs/devices/unified_device_config.yaml"

    def _load_config(self) -> Dict[str, Any]:
        """Load and cache the unified configuration."""
        if self._config_cache is None:
            with open(self.config_path, "r") as f:
                self._config_cache = yaml.safe_load(f)
        return self._config_cache

    def load_device_mappings(self) -> Dict[str, Any]:
        """
        Load device mappings in the old format for backward compatibility.
        This adapter transforms the unified config into the old device_mappings format.
        """
        config = self._load_config()
        device_types = {}

        # Transform unified config back to old device_mappings format
        for vendor_name, vendor_data in config["device_configuration"][
            "vendors"
        ].items():
            for motherboard_name, motherboard_data in vendor_data[
                "motherboards"
            ].items():
                for device_type, device_config in motherboard_data[
                    "device_types"
                ].items():

                    # Create old-style device mapping
                    device_types[device_type] = {
                        "description": device_config.get("description", ""),
                        "hardware_specs": device_config.get("hardware_specs", {}),
                        "boot_configs": device_config.get("boot_configs", {}),
                        "cpu_configs": device_config.get("cpu_configs", {}),
                        "memory_configs": device_config.get("memory_configs", {}),
                        "bios_settings": device_config.get("bios_settings", {}),
                        "redfish_capable": device_config.get("redfish_capable", True),
                        "preferred_bios_method": device_config.get(
                            "preferred_bios_method", "hybrid"
                        ),
                        "motherboards": [motherboard_name],  # Add current motherboard
                        "vendor": vendor_name,
                    }

        return device_types

    def load_firmware_repository(self) -> Dict[str, Any]:
        """
        Load firmware repository in the old format for backward compatibility.
        This adapter transforms the unified config into the old firmware_repository format.
        """
        config = self._load_config()

        # Transform unified config back to old firmware_repository format
        firmware_repo = {
            "firmware_repository": {
                "global_settings": config["device_configuration"]["global_settings"][
                    "firmware"
                ],
                "vendors": {},
            }
        }

        # Extract vendor information
        for vendor_name, vendor_data in config["device_configuration"][
            "vendors"
        ].items():
            firmware_repo["firmware_repository"]["vendors"][vendor_name] = {
                "display_name": vendor_data.get("display_name", vendor_name.title()),
                "support_url": vendor_data.get("support_url", ""),
                "bios": vendor_data["firmware"]["bios"],
                "bmc": vendor_data["firmware"]["bmc"],
                "tools": vendor_data["firmware"]["tools"],
                "motherboards": {},
            }

            # Add motherboard firmware tracking
            for motherboard_name, motherboard_data in vendor_data[
                "motherboards"
            ].items():
                firmware_repo["firmware_repository"]["vendors"][vendor_name][
                    "motherboards"
                ][motherboard_name] = {
                    "model": motherboard_name,
                    "firmware_tracking": motherboard_data["firmware_tracking"],
                }

        return firmware_repo

    def get_device_by_type(self, device_type: str) -> Optional[Dict[str, Any]]:
        """Get complete device information by device type."""
        config = self._load_config()

        for vendor_name, vendor_data in config["device_configuration"][
            "vendors"
        ].items():
            for motherboard_name, motherboard_data in vendor_data[
                "motherboards"
            ].items():
                if device_type in motherboard_data["device_types"]:
                    device_config = motherboard_data["device_types"][device_type]
                    return {
                        "device_type": device_type,
                        "vendor": vendor_name,
                        "motherboard": motherboard_name,
                        "vendor_info": vendor_data,
                        "motherboard_info": motherboard_data,
                        "device_config": device_config,
                    }
        return None

    def get_motherboard_info(self, motherboard: str) -> Optional[Dict[str, Any]]:
        """Get motherboard information including all device types."""
        config = self._load_config()

        for vendor_name, vendor_data in config["device_configuration"][
            "vendors"
        ].items():
            if motherboard in vendor_data["motherboards"]:
                motherboard_data = vendor_data["motherboards"][motherboard]
                return {
                    "motherboard": motherboard,
                    "vendor": vendor_name,
                    "vendor_info": vendor_data,
                    "motherboard_info": motherboard_data,
                    "device_types": list(motherboard_data["device_types"].keys()),
                }
        return None

    def get_vendor_info(self, vendor: str) -> Optional[Dict[str, Any]]:
        """Get complete vendor information."""
        config = self._load_config()

        if vendor in config["device_configuration"]["vendors"]:
            vendor_data = config["device_configuration"]["vendors"][vendor]
            return {
                "vendor": vendor,
                "vendor_info": vendor_data,
                "motherboards": list(vendor_data["motherboards"].keys()),
                "total_device_types": sum(
                    len(mb["device_types"])
                    for mb in vendor_data["motherboards"].values()
                ),
            }
        return None

    def list_all_device_types(self) -> List[str]:
        """Get list of all device types in the system."""
        config = self._load_config()
        device_types = []

        for vendor_data in config["device_configuration"]["vendors"].values():
            for motherboard_data in vendor_data["motherboards"].values():
                device_types.extend(motherboard_data["device_types"].keys())

        return sorted(device_types)

    def get_stats(self) -> Dict[str, int]:
        """Get configuration statistics."""
        config = self._load_config()

        vendors = config["device_configuration"]["vendors"]
        total_motherboards = sum(len(v["motherboards"]) for v in vendors.values())
        total_device_types = sum(
            len(mb["device_types"])
            for v in vendors.values()
            for mb in v["motherboards"].values()
        )

        return {
            "vendors": len(vendors),
            "motherboards": total_motherboards,
            "device_types": total_device_types,
        }


def demonstrate_backward_compatibility():
    """Demonstrate how the adapter maintains backward compatibility."""

    print("🔄 UNIFIED CONFIG ADAPTER DEMONSTRATION")
    print("=" * 60)

    # Create adapter
    loader = UnifiedConfigLoader()

    print("\n📊 Configuration Statistics:")
    stats = loader.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")

    print("\n🔧 Backward Compatible Device Mappings:")
    device_mappings = loader.load_device_mappings()
    print(f"   Loaded {len(device_mappings)} device types")

    # Show example device
    example_device = next(iter(device_mappings.keys()))
    print(f"   Example - {example_device}:")
    print(f"     Vendor: {device_mappings[example_device].get('vendor')}")
    print(f"     Motherboards: {device_mappings[example_device].get('motherboards')}")
    print(
        f"     CPU: {device_mappings[example_device].get('hardware_specs', {}).get('cpu_name')}"
    )

    print("\n📦 Backward Compatible Firmware Repository:")
    firmware_repo = loader.load_firmware_repository()
    vendors = firmware_repo["firmware_repository"]["vendors"]
    print(f"   Loaded {len(vendors)} vendors")

    for vendor_name in vendors:
        motherboard_count = len(vendors[vendor_name].get("motherboards", {}))
        print(f"     {vendor_name}: {motherboard_count} motherboards")

    print("\n🎯 New Unified Methods:")

    # Demonstrate enhanced methods
    device_info = loader.get_device_by_type("a1.c5.large")
    if device_info:
        print(f"   Device: {device_info['device_type']}")
        print(f"   Vendor: {device_info['vendor']}")
        print(f"   Motherboard: {device_info['motherboard']}")
        print(f"   CPU: {device_info['device_config']['hardware_specs']['cpu_name']}")

    print(f"\n✅ All device types: {len(loader.list_all_device_types())} total")


def show_migration_example():
    """Show how existing code can be updated to use the adapter."""

    print("\n\n🔄 CODE MIGRATION EXAMPLE")
    print("=" * 60)

    print("\n❌ OLD CODE (before unified config):")
    print(
        """
    # Old way - multiple file loading
    from hwautomation.hardware.bios.config.loader import ConfigurationLoader
    from hwautomation.hardware.firmware.manager import FirmwareManager

    # Load device mappings
    bios_loader = ConfigurationLoader("configs/bios/")
    device_mappings = bios_loader.load_device_mappings()

    # Load firmware repository separately
    firmware_manager = FirmwareManager("configs/firmware/firmware_repository.yaml")

    # Complex lookup across files
    device_config = device_mappings.get(device_type)
    motherboards = device_config.get('motherboards', [])
    # Then need to cross-reference with firmware config...
    """
    )

    print("\n✅ NEW CODE (with unified config adapter):")
    print(
        """
    # New way - unified loading with backward compatibility
    from hwautomation.config.unified_loader import UnifiedConfigLoader

    # Single loader for everything
    loader = UnifiedConfigLoader()

    # Backward compatible methods still work
    device_mappings = loader.load_device_mappings()
    firmware_repo = loader.load_firmware_repository()

    # OR use new enhanced methods
    device_info = loader.get_device_by_type(device_type)
    # device_info contains: vendor, motherboard, device_config, vendor_info, etc.

    # Much simpler!
    """
    )

    print("\n🚀 ENHANCED METHODS (new capabilities):")
    print(
        """
    # New methods enabled by unified structure
    motherboard_info = loader.get_motherboard_info("X11SCE-F")
    vendor_info = loader.get_vendor_info("supermicro")
    all_devices = loader.list_all_device_types()
    stats = loader.get_stats()

    # Single method gets complete device information
    device_info = loader.get_device_by_type("a1.c5.large")
    # Returns: vendor, motherboard, device config, firmware info, etc.
    """
    )


if __name__ == "__main__":
    demonstrate_backward_compatibility()
    show_migration_example()
