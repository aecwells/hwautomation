"""Vendor handler factory for IPMI operations.

This module provides a factory for creating vendor-specific IPMI handlers.
"""

from typing import Dict, Optional

from hwautomation.logging import get_logger
from ..base import BaseVendorHandler, IPMIVendor

logger = get_logger(__name__)


class VendorHandlerFactory:
    """Factory for creating vendor-specific IPMI handlers."""

    def __init__(self):
        """Initialize vendor handler factory."""
        self._handlers: Dict[IPMIVendor, BaseVendorHandler] = {}

    def get_handler(self, vendor: IPMIVendor) -> Optional[BaseVendorHandler]:
        """Get vendor-specific handler.

        Args:
            vendor: IPMI vendor

        Returns:
            Vendor handler or None if not available
        """
        if vendor not in self._handlers:
            self._handlers[vendor] = self._create_handler(vendor)
            
        return self._handlers.get(vendor)

    def _create_handler(self, vendor: IPMIVendor) -> Optional[BaseVendorHandler]:
        """Create vendor-specific handler.

        Args:
            vendor: IPMI vendor

        Returns:
            Vendor handler or None if not available
        """
        try:
            if vendor == IPMIVendor.SUPERMICRO:
                from ..vendors.supermicro import SupermicroHandler
                return SupermicroHandler(vendor)
            elif vendor == IPMIVendor.HP_ILO:
                from ..vendors.hp_ilo import HPiLOHandler
                return HPiLOHandler(vendor)
            elif vendor == IPMIVendor.DELL_IDRAC:
                from ..vendors.dell_idrac import DellHandler
                return DellHandler(vendor)
            else:
                logger.warning(f"No handler available for vendor: {vendor.value}")
                return None
                
        except ImportError as e:
            logger.warning(f"Failed to load handler for {vendor.value}: {e}")
            return None
