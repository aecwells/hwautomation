#!/usr/bin/env python3
"""
Fix pydocstyle section underline issues.
"""

import os
import re


def fix_section_underlines(content):
    """Fix section underlines in docstrings."""

    # Fix malformed Args sections
    # Pattern: "Args\n\n\n        ----\n        " -> "Args\n        ----\n        "
    content = re.sub(r"(\s+)Args\n\n\n(\s+)----\n(\s+)", r"\1Args\n\2----\n\3", content)

    # Fix malformed Returns sections
    # Pattern: "Returns\n\n\n        -------\n        " -> "Returns\n        -------\n        "
    content = re.sub(
        r"(\s+)Returns\n\n\n(\s+)-------\n(\s+)", r"\1Returns\n\2-------\n\3", content
    )

    # Fix any remaining Args: -> Args with underline
    content = re.sub(r"(\s+)Args:\n(\s+)", r"\1Args\n\2----\n\2", content)

    # Fix any remaining Returns: -> Returns with underline
    content = re.sub(r"(\s+)Returns:\n(\s+)", r"\1Returns\n\2-------\n\2", content)

    return content


def fix_file(filepath):
    """Fix pydocstyle issues in a file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        original_content = content
        content = fix_section_underlines(content)

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
    """Main function."""
    files_to_fix = [
        "src/hwautomation/hardware/bios/devices/dell.py",
        "src/hwautomation/hardware/bios/devices/hpe.py",
        "src/hwautomation/hardware/bios/devices/supermicro.py",
        "src/hwautomation/hardware/bios/devices/factory.py",
        "src/hwautomation/hardware/bios/parsers/factory.py",
        "src/hwautomation/hardware/bios/parsers/xml_parser.py",
        "src/hwautomation/hardware/bios/parsers/redfish_parser.py",
        "src/hwautomation/hardware/bios/operations/validate.py",
        "src/hwautomation/hardware/bios/operations/push.py",
        "src/hwautomation/hardware/bios/operations/pull.py",
        "src/hwautomation/hardware/bios/config/validator.py",
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
