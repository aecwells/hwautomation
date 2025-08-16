#!/usr/bin/env python3
"""
Simple syntax check for the hardware automation package.
This only checks if the Python files have valid syntax and basic imports work.
"""

import ast
import sys
import traceback
from pathlib import Path


def check_python_syntax(file_path):
    """Check if a Python file has valid syntax"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse the AST to check syntax
        ast.parse(content, filename=str(file_path))
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error reading file: {e}"


def find_python_files():
    """Find all Python files in the src directory"""
    src_dir = Path(__file__).parent.parent.parent.parent.parent / "src"
    if not src_dir.exists():
        return []

    python_files = []
    for file_path in src_dir.rglob("*.py"):
        python_files.append(file_path)

    return python_files


def check_package_structure():
    """Check if the package structure is correct"""

    print("Checking package structure...")
    print("=" * 40)

    required_files = [
        "src/hwautomation/__init__.py",
        "src/hwautomation/database/__init__.py",
        "src/hwautomation/database/helper.py",
        "src/hwautomation/database/migrations.py",
        "src/hwautomation/maas/__init__.py",
        "src/hwautomation/maas/client.py",
        "src/hwautomation/hardware/__init__.py",
        "src/hwautomation/hardware/ipmi/__init__.py",
        "src/hwautomation/hardware/redfish/__init__.py",
        "src/hwautomation/utils/__init__.py",
        "src/hwautomation/utils/config.py",
        "src/hwautomation/utils/network.py",
    ]

    base_path = Path(__file__).parent.parent.parent.parent.parent
    all_exist = True

    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} (missing)")
            all_exist = False

    return all_exist


def main():
    """Main syntax checking function"""

    print("Hardware Automation Package - Syntax Check")
    print("=" * 50)

    # Check package structure
    structure_ok = check_package_structure()

    if not structure_ok:
        print("\n❌ Package structure is incomplete.")
        return False

    print(f"\n✓ Package structure is correct")

    # Find and check Python files
    python_files = find_python_files()

    if not python_files:
        print("\n❌ No Python files found in src/ directory")
        return False

    print(f"\nChecking syntax of {len(python_files)} Python files...")
    print("-" * 40)

    all_valid = True

    for file_path in sorted(python_files):
        relative_path = file_path.relative_to(
            Path(__file__).parent.parent.parent.parent.parent
        )
        is_valid, error = check_python_syntax(file_path)

        if is_valid:
            print(f"✓ {relative_path}")
        else:
            print(f"✗ {relative_path}")
            print(f"   {error}")
            all_valid = False

    print("\n" + "=" * 50)

    if all_valid:
        print("🎉 ALL SYNTAX CHECKS PASSED!")
        print(
            "\nThe package structure is correct and all Python files have valid syntax."
        )
        print("\nNext steps:")
        print("1. Run: python validate_package.py (to test imports)")
        print("2. Run: python migration_guide.py (to see how to update old files)")
        print("3. Create config.yaml from config.yaml.example")
        return True
    else:
        print("❌ Some syntax errors found. Fix them before proceeding.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
