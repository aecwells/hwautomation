#!/usr/bin/env python3
"""
Debug the unified config path detection.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def debug_config_paths():
    """Debug configuration path detection."""
    print("🔍 DEBUGGING CONFIGURATION PATH DETECTION")
    print("=" * 60)

    # Test the path detection logic
    current_file = os.path.abspath(__file__)
    print(f"Current file: {current_file}")

    # Simulate the path detection from the BIOS loader
    bios_loader_file = "/home/ubuntu/projects/hwautomation/src/hwautomation/hardware/bios/config/loader.py"
    project_root = os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(bios_loader_file)))
        )
    )
    unified_config_path = os.path.join(
        project_root, "configs", "devices", "unified_device_config.yaml"
    )

    print(f"BIOS loader file: {bios_loader_file}")
    print(f"Calculated project root: {project_root}")
    print(f"Unified config path: {unified_config_path}")
    print(f"Unified config exists: {os.path.exists(unified_config_path)}")

    # Check actual unified config location
    actual_unified_path = (
        "/home/ubuntu/projects/hwautomation/configs/devices/unified_device_config.yaml"
    )
    print(f"Actual unified config path: {actual_unified_path}")
    print(f"Actual unified config exists: {os.path.exists(actual_unified_path)}")

    # Test direct import and initialization
    try:
        from hwautomation.config import UnifiedConfigLoader

        loader = UnifiedConfigLoader()
        stats = loader.get_stats()
        print(f"✅ Direct unified loader works: {stats.device_types} devices")
    except Exception as e:
        print(f"❌ Direct unified loader failed: {e}")

    # Test the BIOS loader detection method
    try:
        from hwautomation.hardware.bios.config.loader import ConfigurationLoader

        # Create a test instance to check path detection
        test_loader = ConfigurationLoader(
            "/home/ubuntu/projects/hwautomation/configs/bios"
        )
        print(f"BIOS loader unified check: {test_loader._use_unified}")

        if hasattr(test_loader, "_get_unified_config_path"):
            detected_path = test_loader._get_unified_config_path()
            print(f"Detected unified path: {detected_path}")
            print(f"Detected path exists: {os.path.exists(detected_path)}")

    except Exception as e:
        print(f"❌ BIOS loader test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_config_paths()
