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
."""

from typing import Any, Callable, Optional

from flask import Blueprint

# Import blueprints and initialization functions with proper typing
core_bp: Optional[Blueprint] = None
init_core_routes: Optional[Callable[[Any, Any, Any, Any], Any]] = None
try:
    from .core import core_bp, init_core_routes
except ImportError:
    pass

database_bp: Optional[Blueprint] = None
init_database_routes: Optional[Callable[[Any, Any], Any]] = None
try:
    from .database import database_bp, init_database_routes
except ImportError:
    pass

orchestration_bp: Optional[Blueprint] = None
init_orchestration_routes: Optional[Callable[[Any, Any, Any], Any]] = None
try:
    from .orchestration import init_orchestration_routes, orchestration_bp
except ImportError:
    pass

maas_bp: Optional[Blueprint] = None
init_maas_routes: Optional[Callable[[Any, Any, Any], Any]] = None
try:
    from .maas import init_maas_routes, maas_bp
except ImportError:
    pass

logs_bp: Optional[Blueprint] = None
init_logs_routes: Optional[Callable[[Any], Any]] = None
try:
    from .logs import init_logs_routes, logs_bp
except ImportError:
    pass

firmware_bp: Optional[Blueprint] = None
init_firmware_routes: Optional[Callable[[Any, Any, Any, Any], Any]] = None
try:
    from .firmware import firmware_bp, init_firmware_routes
except ImportError:
    pass

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
