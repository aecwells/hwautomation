#!/usr/bin/env python3
"""Test Flask app imports step by step."""

import sys
import os
import logging
from pathlib import Path

print("✓ Basic Python imports successful")

try:
    from flask import Flask, render_template, request, jsonify, flash, redirect, url_for
    from flask_socketio import SocketIO, emit
    print("✓ Flask imports successful")
except Exception as e:
    print(f"✗ Flask import error: {e}")
    import traceback
    traceback.print_exc()

try:
    import json
    import xml.etree.ElementTree as ET
    from datetime import datetime
    from typing import Dict, List, Any
    print("✓ Standard library imports successful")
except Exception as e:
    print(f"✗ Standard library import error: {e}")

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

print(f"✓ Path setup: {src_path}")

try:
    from hwautomation.hardware.bios_config import BiosConfigManager
    from hwautomation.database.helper import DbHelper
    from hwautomation.utils.config import load_config
    print("✓ HWAutomation basic imports successful")
except Exception as e:
    print(f"✗ HWAutomation basic import error: {e}")
    import traceback
    traceback.print_exc()

try:
    from hwautomation.hardware.ipmi import IpmiManager
    from hwautomation.hardware.redfish import RedFishManager
    from hwautomation.maas.client import create_maas_client
    print("✓ HWAutomation hardware/maas imports successful")
except Exception as e:
    print(f"✗ HWAutomation hardware/maas import error: {e}")
    import traceback
    traceback.print_exc()

try:
    from hwautomation.orchestration.workflow_manager import WorkflowManager
    from hwautomation.orchestration.server_provisioning import ServerProvisioningWorkflow
    from hwautomation.orchestration.device_selection import DeviceSelectionService, MachineFilter, MachineStatus
    print("✓ HWAutomation orchestration imports successful")
except Exception as e:
    print(f"✗ HWAutomation orchestration import error: {e}")
    import traceback
    traceback.print_exc()

try:
    # Initialize Flask app
    app = Flask(__name__)
    app.secret_key = 'test-key'
    socketio = SocketIO(app, cors_allowed_origins="*")
    print("✓ Flask app initialization successful")
except Exception as e:
    print(f"✗ Flask app initialization error: {e}")
    import traceback
    traceback.print_exc()

print("All tests completed")
