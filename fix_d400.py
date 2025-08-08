#!/usr/bin/env python3
"""
Script to fix D400 pydocstyle errors (missing periods in docstrings).
"""

import os
import re
import sys

def fix_d400_errors(file_path):
    """Fix D400 errors in a Python file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern to match docstrings that don't end with a period
    # Matches: """Some text""" or '''Some text'''
    # But excludes ones that already end with period, question mark, or exclamation
    
    # Single line docstrings
    pattern1 = r'("""[^"]*[^."?!])(""")' 
    pattern2 = r"('''[^']*[^.'?!])(''')"
    
    # Multi-line docstrings (first line)
    pattern3 = r'("""\s*\n?\s*[A-Z][^"]*[^."?!\n])\s*\n'
    pattern4 = r"('''\s*\n?\s*[A-Z][^']*[^.'?!\n])\s*\n"
    
    # Simple single-line patterns
    simple_pattern1 = r'(""")([^"]+[^."?!])(""")'
    simple_pattern2 = r"(''')([^']+[^.'?!])(''')"
    
    def add_period(match):
        """Add period to docstring if it doesn't have proper ending."""
        groups = match.groups()
        if len(groups) == 3:
            return groups[0] + groups[1] + '.' + groups[2]
        else:
            return match.group(1) + '.\n'
    
    # Apply fixes
    content = re.sub(simple_pattern1, add_period, content)
    content = re.sub(simple_pattern2, add_period, content)
    
    # More sophisticated pattern for module docstrings and class docstrings
    lines = content.split('\n')
    in_docstring = False
    docstring_quote = None
    modified_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Detect start of docstring
        if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
            docstring_quote = stripped[:3]
            
            # Check if it's a single-line docstring
            if stripped.endswith(docstring_quote) and len(stripped) > 6:
                # Single line docstring
                content_part = stripped[3:-3].strip()
                if content_part and not content_part.endswith(('.', '?', '!')):
                    line = line.replace(stripped, f'{docstring_quote}{content_part}.{docstring_quote}')
            elif stripped == docstring_quote:
                # Multi-line docstring starts on next line
                in_docstring = True
            else:
                # Multi-line docstring starts on same line
                content_part = stripped[3:].strip()
                if content_part and not content_part.endswith(('.', '?', '!')):
                    line = line.replace(stripped, f'{docstring_quote}{content_part}.')
                in_docstring = True
        
        elif in_docstring and stripped.endswith(docstring_quote):
            # End of multi-line docstring
            in_docstring = False
            docstring_quote = None
        
        modified_lines.append(line)
    
    content = '\n'.join(modified_lines)
    
    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Fix D400 errors in all Python files under src/."""
    src_dir = 'src'
    fixed_files = 0
    
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if fix_d400_errors(file_path):
                    print(f"Fixed: {file_path}")
                    fixed_files += 1
    
    print(f"\nFixed {fixed_files} files")

if __name__ == '__main__':
    main()
