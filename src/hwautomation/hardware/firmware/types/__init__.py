"""Firmware type handlers."""

from .bios import BiosFirmwareHandler
from .bmc import BmcFirmwareHandler

__all__ = [
    "BiosFirmwareHandler",
    "BmcFirmwareHandler",
]
