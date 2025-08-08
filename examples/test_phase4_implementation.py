#!/usr/bin/env python3
"""
Deprecated legacy example test.

Use the maintained firmware tests instead:
- tests/test_firmware_manager.py
- tests/test_firmware_integration.py
"""

import sys

msg = (
    "This legacy example test (examples/test_phase4_implementation.py) is deprecated.\n"
    "Please run 'tests/test_firmware_manager.py' or 'tests/test_firmware_integration.py'.\n"
)
print(msg)
sys.exit(0)
