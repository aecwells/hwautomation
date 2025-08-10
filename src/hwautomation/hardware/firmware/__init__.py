"""Firmware management module.

This module provides a modular firmware management system that replaces
the legacy firmware_manager.py with a structured approach to handling
different firmware types, vendors, and update operations.
"""

from .base import (
    BaseFirmwareHandler,
    BaseFirmwareRepository,
    FirmwareInfo,
    FirmwareType,
    FirmwareUpdateException,
    FirmwareUpdateResult,
    Priority,
    UpdatePolicy,
)
from .manager import FirmwareManager
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
