#!/usr/bin/env python3
"""
Routes package for HWAutomation Web Interface

Organized Flask blueprints for different functional areas:
- core: Dashboard, health checks, basic pages
- database: Database management APIs
- orchestration: Workflow & orchestration APIs
- maas: MaaS integration APIs
- logs: Log management APIs
- firmware: Firmware management APIs
"""

# Import blueprints and initialization functions
try:
    from .core import core_bp, init_core_routes
except ImportError:
    core_bp = None
    init_core_routes = None

try:
    from .database import database_bp, init_database_routes
except ImportError:
    database_bp = None
    init_database_routes = None

try:
    from .orchestration import init_orchestration_routes, orchestration_bp
except ImportError:
    orchestration_bp = None
    init_orchestration_routes = None

try:
    from .maas import init_maas_routes, maas_bp
except ImportError:
    maas_bp = None
    init_maas_routes = None

try:
    from .logs import init_logs_routes, logs_bp
except ImportError:
    logs_bp = None
    init_logs_routes = None

try:
    from .firmware import firmware_bp, init_firmware_routes
except ImportError:
    firmware_bp = None
    init_firmware_routes = None

__all__ = [
    "core_bp",
    "init_core_routes",
    "database_bp",
    "init_database_routes",
    "orchestration_bp",
    "init_orchestration_routes",
    "maas_bp",
    "init_maas_routes",
    "logs_bp",
    "init_logs_routes",
    "firmware_bp",
    "init_firmware_routes",
]
