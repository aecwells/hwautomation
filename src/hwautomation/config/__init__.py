"""
Configuration management for HWAutomation.

This module provides unified configuration loading and management,
including backward compatibility adapters for existing systems.
"""

from .adapters import BiosConfigAdapter, ConfigurationManager, FirmwareConfigAdapter
from .unified_loader import UnifiedConfigLoader

__all__ = [
    "UnifiedConfigLoader",
    "BiosConfigAdapter",
    "FirmwareConfigAdapter",
    "ConfigurationManager",
]
