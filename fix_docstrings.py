#!/usr/bin/env python3
"""Script to fix pydocstyle issues in documentation."""

import os
import re
import sys


def fix_docstring_sections(content):
    """Fix docstring section formatting issues."""
    # Pattern to match section headers with colons
    section_pattern = r'(\s+)(Args|Returns|Raises|Yields|Note|Notes)(:)'

    # Replace section headers to add newlines and underlines
    def replace_section(match):
        indent = match.group(1)
        section_name = match.group(2)
        underline = '-' * len(section_name)
        return f'{indent}{section_name}\n{indent}{underline}'

    return re.sub(section_pattern, replace_section, content)

def fix_one_line_docstrings(content):
    """Fix one-line docstrings that span multiple lines."""
    # Pattern for multi-line single docstrings
    pattern = r'(\s+""")(.*?)\n\s+(""")$'

    def replace_oneline(match):
        indent = match.group(1)
        text = match.group(2).strip()
        if '\n' not in text and len(text) < 72:  # Reasonable line length
            return f'{indent}{text}"""'
        return match.group(0)  # Keep original if too long

    return re.sub(pattern, replace_oneline, content, flags=re.MULTILINE)

def add_missing_docstrings(content):
    """Add basic docstrings to methods missing them."""
    # Pattern for methods without docstrings
    method_pattern = r'(\s+def (format|filter|__enter__|__exit__)\([^)]*\).*?:)\n(\s+)(?!""")'

    def add_docstring(match):
        method_def = match.group(1)
        method_name = match.group(2)
        indent = match.group(3)

        docstrings = {
            'format': f'{indent}"""Format the log record."""\n',
            'filter': f'{indent}"""Filter log records."""\n',
            '__enter__': f'{indent}"""Enter the context manager."""\n',
            '__exit__': f'{indent}"""Exit the context manager."""\n'
        }

        return f'{method_def}\n{docstrings.get(method_name, f"{indent}\"\"\"Method implementation.\"\"\"\n")}'

    return re.sub(method_pattern, add_docstring, content, flags=re.MULTILINE | re.DOTALL)

def fix_file(filepath):
    """Fix pydocstyle issues in a single file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Apply fixes
        content = fix_docstring_sections(content)
        content = fix_one_line_docstrings(content)
        content = add_missing_docstrings(content)

        # Only write if content changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {filepath}")
            return True
        else:
            print(f"No changes needed: {filepath}")
            return False

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Main function to fix files."""
    files_to_fix = [
        "src/hwautomation/hardware/bios/operations/pull.py",
        "src/hwautomation/hardware/bios/operations/push.py",
        "src/hwautomation/hardware/bios/operations/validate.py",
        "src/hwautomation/hardware/bios/devices/supermicro.py",
        "src/hwautomation/logging/config.py"
    ]

    changed_files = []

    for filepath in files_to_fix:
        if os.path.exists(filepath):
            if fix_file(filepath):
                changed_files.append(filepath)
        else:
            print(f"File not found: {filepath}")

    print(f"\nProcessed {len(files_to_fix)} files")
    print(f"Changed {len(changed_files)} files")

    if changed_files:
        print("\nChanged files:")
        for f in changed_files:
            print(f"  - {f}")

if __name__ == "__main__":
    main()
