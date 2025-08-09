#!/usr/bin/env python3
"""
Fix pydocstyle issues by updating docstring format.
Convert "Args:" to "Args\n----" and "Returns:" to "Returns\n-------"
"""

import os
import re
import sys


def fix_docstring_sections(content):
    """Fix docstring section formatting for pydocstyle compliance."""

    # Pattern to match docstring sections that need fixing
    # Look for "Args:" or "Returns:" followed by content
    patterns = [
        # Fix "Args:\n        " to "Args\n        ----\n        "
        (r"(\s+)Args:\n(\s+)", r"\1Args\n\2----\n\2"),
        # Fix "Returns:\n        " to "Returns\n        -------\n        "
        (r"(\s+)Returns:\n(\s+)", r"\1Returns\n\2-------\n\2"),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    return content


def fix_file(filepath):
    """Fix pydocstyle issues in a single file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        content = fix_docstring_sections(content)

        if content != original_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Fixed: {filepath}")
            return True
        else:
            print(f"No changes: {filepath}")
            return False
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False


def main():
    """Main function to fix all Python files."""

    # Files that need fixing based on pydocstyle output
    files_to_fix = [
        "src/hwautomation/hardware/bios/manager.py",
        "src/hwautomation/hardware/bios/operations/validate.py",
        "src/hwautomation/hardware/bios/operations/push.py",
        "src/hwautomation/hardware/bios/operations/pull.py",
        "src/hwautomation/hardware/bios/parsers/redfish_parser.py",
        "src/hwautomation/hardware/bios/devices/supermicro.py",
        "src/hwautomation/hardware/bios/config/validator.py",
        "src/hwautomation/hardware/bios/devices/hpe.py",
        "src/hwautomation/hardware/bios/parsers/xml_parser.py",
        "src/hwautomation/hardware/bios/devices/dell.py",
        "src/hwautomation/hardware/bios/devices/factory.py",
        "src/hwautomation/hardware/bios/parsers/factory.py",
    ]

    fixed_count = 0
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            if fix_file(filepath):
                fixed_count += 1
        else:
            print(f"File not found: {filepath}")

    print(f"\nFixed {fixed_count} out of {len(files_to_fix)} files.")


if __name__ == "__main__":
    main()
