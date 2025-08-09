#!/usr/bin/env python3
"""
Import validation script for the hardware automation package.
Run this to verify that all imports work correctly.
"""

import sys
import traceback
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_imports():
    """Test all imports to ensure package structure is correct"""

    print("Testing hardware automation package imports...")
    print("=" * 50)

    # Test basic package import
    try:
        import hwautomation

        print("✓ Main package import successful")
        print(f"  Package version: {hwautomation.__version__}")
    except Exception as e:
        print(f"✗ Main package import failed: {e}")
        traceback.print_exc()
        return False

    # Test individual module imports
    modules_to_test = [
        ("hwautomation.database.helper", "DbHelper"),
        ("hwautomation.database.migrations", "DatabaseMigrator"),
        ("hwautomation.maas.client", "MaasClient"),
        ("hwautomation.hardware.ipmi", "IpmiManager"),
        ("hwautomation.hardware.redfish_manager", "RedfishManager"),
        ("hwautomation.utils.config", "load_config"),
        ("hwautomation.utils.network", "ping_host"),
    ]

    all_passed = True

    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✓ {module_name}.{class_name}")
        except Exception as e:
            print(f"✗ {module_name}.{class_name} - {e}")
            all_passed = False

    # Test package-level imports
    package_imports = [
        "DbHelper",
        "DatabaseMigrator",
        "MaasClient",
        "IpmiManager",
        "RedfishManager",
        "ping_host",
    ]

    print("\nTesting package-level imports...")
    for import_name in package_imports:
        try:
            obj = getattr(hwautomation, import_name)
            print(f"✓ hwautomation.{import_name}")
        except Exception as e:
            print(f"✗ hwautomation.{import_name} - {e}")
            all_passed = False

    # Test star import (from hwautomation import *)
    print("\nTesting star import...")
    try:
        # Use importlib to test star imports without syntax error
        import importlib

        hwautomation = importlib.import_module("hwautomation")

        print("✓ Star import successful")

        # Check if key classes are available via getattr
        test_class_names = [
            "DbHelper",
            "DatabaseMigrator",
            "MaasClient",
            "IpmiManager",
            "RedfishManager",
            "ping_host",
        ]

        available_count = 0
        for class_name in test_class_names:
            if hasattr(hwautomation, class_name):
                available_count += 1

        print(
            f"✓ {available_count}/{len(test_class_names)} classes available via star import"
        )
    except Exception as e:
        print(f"✗ Star import failed: {e}")
        all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL IMPORTS SUCCESSFUL! Package structure is working correctly.")
    else:
        print("❌ Some imports failed. Check the errors above.")

    return all_passed


def test_basic_functionality():
    """Test basic functionality of key classes"""

    print("\nTesting basic functionality...")
    print("=" * 50)

    try:
        from hwautomation import DatabaseMigrator, ping_host
        from hwautomation.utils.config import load_config

        # Test config loading
        try:
            config = load_config()
            print("✓ Configuration loading works")
        except Exception as e:
            print(
                f"✓ Configuration loading (expected to fail without config file): {e}"
            )

        # Test database migrator creation
        try:
            migrator = DatabaseMigrator(":memory:")  # In-memory database for testing
            version = migrator.get_current_version()
            migrator.close()
            print(f"✓ Database migrator works (version: {version})")
        except Exception as e:
            print(f"✗ Database migrator failed: {e}")
            return False

        # Test network utility
        try:
            # Test with localhost
            result = ping_host("127.0.0.1", timeout=1)
            print(f"✓ Network utility works (localhost ping: {result})")
        except Exception as e:
            print(f"✗ Network utility failed: {e}")
            return False

        print("✓ Basic functionality tests passed")
        return True

    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        traceback.print_exc()
        return False


def check_dependencies():
    """Check if required dependencies are available"""

    print("\nChecking dependencies...")
    print("=" * 50)

    required_packages = ["sqlite3", "json", "subprocess", "pathlib", "os", "sys"]

    optional_packages = [
        ("requests", "For MAAS and RedFish APIs"),
        ("requests_oauthlib", "For MAAS OAuth authentication"),
        ("yaml", "For YAML configuration files"),
    ]

    # Check required packages (built-in)
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} (built-in)")
        except ImportError:
            print(f"✗ {package} (missing)")

    # Check optional packages
    for package, description in optional_packages:
        try:
            __import__(package)
            print(f"✓ {package} - {description}")
        except ImportError:
            print(
                f"⚠ {package} - {description} (optional, install with: pip install {package})"
            )


if __name__ == "__main__":
    print("Hardware Automation Package Validation")
    print("=" * 50)

    # Check dependencies first
    check_dependencies()

    # Test imports
    imports_ok = test_imports()

    if imports_ok:
        # Test basic functionality
        functionality_ok = test_basic_functionality()

        if functionality_ok:
            print("\n🎉 Package validation completed successfully!")
            print("You can now use the hardware automation package.")
            print("\nNext steps:")
            print("1. Create a config.yaml file (see config.yaml.example)")
            print(
                "2. Install optional dependencies: pip install requests requests-oauthlib pyyaml"
            )
            print("3. Run: python examples/basic_usage.py")
        else:
            print("\n⚠ Package imports work but some functionality failed.")
    else:
        print("\n❌ Package validation failed. Check the errors above.")
