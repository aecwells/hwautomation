"""
Hardware Automation Package

A Python package for automating server hardware management through MAAS API,
IPMI, and RedFish interfaces.
."""

__version__ = "1.0.0"
__author__ = "Hardware Automation Team"

# Make key classes available at package level
from .database.helper import DbHelper
from .database.migrations import DatabaseMigrator
from .hardware.bios import BiosConfigManager
from .hardware.ipmi import IpmiManager
from .hardware.redfish import RedfishManager
from .maas.client import MaasClient
from .utils.network import ping_host

__all__ = [
    "DbHelper",
    "DatabaseMigrator",
    "MaasClient",
    "IpmiManager",
    "RedfishManager",
    "ping_host",
]
