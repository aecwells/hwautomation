#!/usr/bin/env python3
"""
Deprecated legacy example.

Use these maintained, neutral examples instead:
- examples/bios_config_example.py
- examples/redfish_example.py

Use the unified runner to list and run examples:
  python -m examples.run --list
  python -m examples.run bios_config_example
"""
import sys

msg = (
    "This legacy example (phase2_standalone_example.py) is deprecated.\n"
    "Please use 'examples/bios_config_example.py' or 'examples/redfish_example.py'.\n"
    "See 'examples/README.md' for details."
)
print(msg)
sys.exit(0)
