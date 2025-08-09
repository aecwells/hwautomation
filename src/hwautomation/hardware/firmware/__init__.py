"""Firmware management module.

This module provides a modular firmware management system that replaces
the legacy firmware_manager.py with a structured approach to handling
different firmware types, vendors, and update operations.
"""

from .manager import FirmwareManager
from .base import (
    FirmwareInfo,
    FirmwareType,
    FirmwareUpdateResult,
    FirmwareUpdateException,
    Priority,
    UpdatePolicy,
    BaseFirmwareHandler,
    BaseFirmwareRepository,
)
from .repositories.local import FirmwareRepository

__all__ = [
    "FirmwareManager",
    "FirmwareInfo",
    "FirmwareType",
    "FirmwareUpdateResult",
    "FirmwareUpdateException",
    "FirmwareRepository",
    "Priority",
    "UpdatePolicy",
    "BaseFirmwareHandler",
    "BaseFirmwareRepository",
]
