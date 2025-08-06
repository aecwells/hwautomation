#!/usr/bin/env python3
"""Simple test to see if basic imports work."""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

print(f"Project root: {project_root}")
print(f"Source path: {src_path}")
print(f"Python path: {sys.path}")

try:
    import hwautomation
    print("✓ hwautomation package imported successfully")
except Exception as e:
    print(f"✗ Error importing hwautomation: {e}")
    import traceback
    traceback.print_exc()

try:
    from hwautomation.hardware.bios_config import BiosConfigManager
    print("✓ BiosConfigManager imported successfully")
except Exception as e:
    print(f"✗ Error importing BiosConfigManager: {e}")
    import traceback
    traceback.print_exc()

try:
    from hwautomation.database.helper import DbHelper
    print("✓ DbHelper imported successfully")
except Exception as e:
    print(f"✗ Error importing DbHelper: {e}")
    import traceback
    traceback.print_exc()

try:
    from hwautomation.orchestration.workflow_manager import WorkflowManager
    print("✓ WorkflowManager imported successfully")
except Exception as e:
    print(f"✗ Error importing WorkflowManager: {e}")
    import traceback
    traceback.print_exc()
    
print("Test completed")
