#!/usr/bin/env python3
"""
Deprecated legacy example.

This script has been replaced by neutral, maintained demos:
- examples/firmware_provisioning_demo.py
- examples/firmware_manager_demo.py

Use the unified runner to list and run examples:
  python -m examples.run --list
  python -m examples.run firmware_provisioning_demo
"""
import sys

msg = (
    "This legacy example (phase4_firmware_demo.py) is deprecated.\n"
    "Please use 'examples/firmware_provisioning_demo.py' or 'examples/firmware_manager_demo.py'.\n"
    "See 'examples/README.md' for details."
)
print(msg)
sys.exit(0)
