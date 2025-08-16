#!/usr/bin/env python3
"""
Simple syntax and import checker for the BIOS configuration system.
Run this to verify the code works without needing actual hardware.
"""

import os
import sys
from pathlib import Path


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    # Add src to path (from tests directory, go up one level then to src)
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    sys.path.insert(0, str(src_path))

    tests = [
        (
            "BiosConfigManager",
            "from hwautomation.hardware.bios_config import BiosConfigManager",
        ),
        (
            "Hardware package",
            "from hwautomation.hardware import BiosConfigManager, IpmiManager, RedFishManager",
        ),
        ("Main package", "import hwautomation"),
        ("YAML parsing", "import yaml"),
        ("XML parsing", "import xml.etree.ElementTree as ET"),
    ]

    results = []
    for test_name, import_statement in tests:
        try:
            exec(import_statement)
            print(f"✓ {test_name}")
            results.append(True)
        except ImportError as e:
            print(f"✗ {test_name}: {e}")
            results.append(False)
        except Exception as e:
            print(f"? {test_name}: {e}")
            results.append(False)

    return all(results)


def test_basic_functionality():
    """Test basic functionality without hardware."""
    print("\nTesting basic functionality...")

    try:
        from hwautomation.hardware.bios_config import BiosConfigManager

        # Initialize manager
        manager = BiosConfigManager()
        print("✓ BiosConfigManager initialization")

        # Test device types
        device_types = manager.get_device_types()
        print(f"✓ Device types loaded: {device_types}")

        # Test configuration retrieval
        if "s2_c2_small" in device_types:
            config = manager.get_device_config("s2_c2_small")
            print(f"✓ Device config loaded: {config is not None}")

        # Test preserve settings
        preserve_count = len(manager.preserve_settings)
        print(f"✓ Preserve settings loaded: {preserve_count} patterns")

        # Test template rules
        template_rules = manager.template_rules
        print(
            f"✓ Template rules loaded: {len(template_rules.get('template_rules', {}))}"
        )

        return True

    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_mock_smart_config():
    """Test the smart configuration with mock data."""
    print("\nTesting smart configuration (mock)...")

    try:
        from hwautomation.hardware.bios_config import BiosConfigManager

        manager = BiosConfigManager()

        # Test dry run
        result = manager.apply_bios_config_smart(
            device_type="s2_c2_small",
            target_ip="192.168.1.100",  # Mock IP
            username="ADMIN",
            password="mock_password",
            dry_run=True,
        )

        print(f"✓ Smart config dry run completed: {result['success']}")
        print(f"  Changes identified: {len(result.get('changes_made', []))}")
        print(f"  Validation errors: {len(result.get('validation_errors', []))}")

        # Show some sample changes
        changes = result.get("changes_made", [])
        if changes:
            print("  Sample changes:")
            for change in changes[:3]:
                print(f"    - {change}")

        return result["success"]

    except Exception as e:
        print(f"✗ Smart config test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_config_files():
    """Test that configuration files exist and are valid."""
    print("\nTesting configuration files...")

    # Config dir is one level up from tests directory
    config_dir = Path(__file__).parent.parent / "configs" / "bios"

    files_to_check = [
        "device_mappings.yaml",
        "preserve_settings.yaml",
        "template_rules.yaml",
    ]

    results = []
    for filename in files_to_check:
        filepath = config_dir / filename
        if filepath.exists():
            try:
                import yaml

                with open(filepath, "r") as f:
                    data = yaml.safe_load(f)
                print(f"✓ {filename}: Valid YAML with {len(data)} top-level keys")
                results.append(True)
            except Exception as e:
                print(f"✗ {filename}: Invalid YAML - {e}")
                results.append(False)
        else:
            print(f"? {filename}: File not found")
            results.append(False)

    return all(results)


def main():
    """Run all tests."""
    print("BIOS Configuration System Test Suite")
    print("=" * 40)

    tests = [
        ("Import Tests", test_imports),
        ("Basic Functionality", test_basic_functionality),
        ("Configuration Files", test_config_files),
        ("Smart Configuration Mock", test_mock_smart_config),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * len(test_name) + ":")
        result = test_func()
        results.append(result)
        print(f"Result: {'PASS' if result else 'FAIL'}")

    print("\n" + "=" * 40)
    print(f"Overall Results: {sum(results)}/{len(results)} tests passed")

    if all(results):
        print("🎉 All tests passed! The BIOS configuration system is ready to use.")
        print("\nNext steps:")
        print("1. Install a real BMC client (ipmitool, redfish libraries)")
        print("2. Configure actual BMC connection details")
        print("3. Test with real hardware")
    else:
        print("❌ Some tests failed. Check the output above for details.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
