"""Parser factory for BIOS configuration formats.

This module provides a factory for creating parsers that can handle
different BIOS configuration formats (XML, JSON, vendor-specific).
"""

from typing import Dict, Optional, Type

from ..base import BaseConfigParser
from .xml_parser import XmlConfigParser
from .redfish_parser import RedfishConfigParser
from ....logging import get_logger

logger = get_logger(__name__)


class ParserFactory:
    """Factory for creating configuration format parsers."""
    
    def __init__(self):
        """Initialize parser factory."""
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self._parsers: Dict[str, Type[BaseConfigParser]] = {}
        self._register_default_parsers()

    def _register_default_parsers(self) -> None:
        """Register default configuration parsers."""
        self.register_parser('xml', XmlConfigParser)
        self.register_parser('redfish', RedfishConfigParser)
        logger.info("Registered default configuration parsers")

    def register_parser(self, format_name: str, parser_class: Type[BaseConfigParser]) -> None:
        """Register a parser for a specific configuration format.
        
        Args:
            format_name: Name of the configuration format
            parser_class: Parser class to register
        """
        self._parsers[format_name.lower()] = parser_class
        logger.debug(f"Registered parser {parser_class.__name__} for format: {format_name}")

    def get_parser(self, format_name: str) -> Optional[BaseConfigParser]:
        """Get parser for the specified configuration format.
        
        Args:
            format_name: Configuration format name
            
        Returns:
            Parser instance or None if not found
        """
        format_key = format_name.lower()
        
        if format_key not in self._parsers:
            logger.warning(f"No parser registered for format: {format_name}")
            return None
        
        parser_class = self._parsers[format_key]
        
        try:
            parser = parser_class()
            logger.debug(f"Created parser {parser_class.__name__} for format: {format_name}")
            return parser
            
        except Exception as e:
            logger.error(f"Failed to create parser {parser_class.__name__} for {format_name}: {e}")
            return None

    def get_supported_formats(self) -> list:
        """Get list of supported configuration formats.
        
        Returns:
            List of format names
        """
        return list(self._parsers.keys())

    def detect_format(self, data: str) -> Optional[str]:
        """Detect configuration format from data content.
        
        Args:
            data: Configuration data string
            
        Returns:
            Detected format name or None if unknown
        """
        data_stripped = data.strip()
        
        # Check for XML format
        if data_stripped.startswith('<?xml') or data_stripped.startswith('<'):
            return 'xml'
        
        # Check for JSON/Redfish format
        if data_stripped.startswith('{') or data_stripped.startswith('['):
            return 'redfish'
        
        # Default to XML for unknown formats
        logger.warning(f"Could not detect format, defaulting to XML")
        return 'xml'

    def parse_auto(self, data: str) -> Optional[object]:
        """Automatically detect format and parse configuration data.
        
        Args:
            data: Configuration data string
            
        Returns:
            Parsed configuration object or None if failed
        """
        format_name = self.detect_format(data)
        if not format_name:
            logger.error("Could not detect configuration format")
            return None
        
        parser = self.get_parser(format_name)
        if not parser:
            logger.error(f"No parser available for format: {format_name}")
            return None
        
        try:
            return parser.parse(data)
        except Exception as e:
            logger.error(f"Failed to parse data with {format_name} parser: {e}")
            return None
