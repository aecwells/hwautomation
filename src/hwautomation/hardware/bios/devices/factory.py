"""Device handler factory for BIOS system.

This module provides a factory for creating device-specific BIOS handlers
based on device type and configuration.
"""

from typing import Dict, List, Optional, Type

from ..base import BaseDeviceHandler, DeviceConfig
from .dell import DellDeviceHandler
from .hpe import HpeDeviceHandler
from .supermicro import SupermicroDeviceHandler
from ....logging import get_logger

logger = get_logger(__name__)


class DeviceHandlerFactory:
    """Factory for creating device-specific BIOS handlers."""
    
    def __init__(self):
        """Initialize device handler factory."""
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._handlers: Dict[str, Type[BaseDeviceHandler]] = {}
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        """Register default device handlers."""
        self.register_handler('Dell', DellDeviceHandler)
        self.register_handler('HPE', HpeDeviceHandler)
        self.register_handler('Supermicro', SupermicroDeviceHandler)
        logger.info("Registered default device handlers")

    def register_handler(self, manufacturer: str, handler_class: Type[BaseDeviceHandler]) -> None:
        """Register a device handler for a specific manufacturer.
        
        Args:
            manufacturer: Manufacturer name
            handler_class: Handler class to register
        """
        self._handlers[manufacturer] = handler_class
        logger.debug(f"Registered handler {handler_class.__name__} for {manufacturer}")

    def get_handler(self, device_type: str, device_config: DeviceConfig) -> Optional[BaseDeviceHandler]:
        """Get appropriate device handler for the given device type.
        
        Args:
            device_type: Target device type
            device_config: Device configuration
            
        Returns:
            Device handler instance or None if not found
        """
        manufacturer = device_config.manufacturer
        
        if manufacturer not in self._handlers:
            logger.warning(f"No handler registered for manufacturer: {manufacturer}")
            return None
        
        handler_class = self._handlers[manufacturer]
        
        try:
            handler = handler_class(device_config)
            
            # Verify the handler can handle this specific device type
            if not handler.can_handle(device_type):
                logger.warning(f"Handler {handler_class.__name__} cannot handle device type: {device_type}")
                return None
            
            logger.debug(f"Created handler {handler_class.__name__} for device type: {device_type}")
            return handler
            
        except Exception as e:
            logger.error(f"Failed to create handler {handler_class.__name__} for {device_type}: {e}")
            return None

    def get_supported_manufacturers(self) -> List[str]:
        """Get list of supported manufacturers.
        
        Returns:
            List of manufacturer names
        """
        return list(self._handlers.keys())

    def get_handler_info(self, manufacturer: str) -> Optional[Dict[str, str]]:
        """Get information about a specific handler.
        
        Args:
            manufacturer: Manufacturer name
            
        Returns:
            Dictionary with handler information
        """
        if manufacturer not in self._handlers:
            return None
        
        handler_class = self._handlers[manufacturer]
        return {
            'manufacturer': manufacturer,
            'class_name': handler_class.__name__,
            'module': handler_class.__module__
        }

    def list_all_handlers(self) -> Dict[str, Dict[str, str]]:
        """List information about all registered handlers.
        
        Returns:
            Dictionary mapping manufacturers to handler info
        """
        return {
            manufacturer: self.get_handler_info(manufacturer)
            for manufacturer in self._handlers.keys()
        }
