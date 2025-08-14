"""
Redfish BIOS Management

Specialized manager for BIOS configuration operations.
"""

from typing import Any, Dict, List, Optional

from hwautomation.logging import get_logger

from ..base import BiosAttribute, RedfishCredentials
from ..operations import RedfishBiosOperation
from .base import BaseRedfishManager, RedfishManagerError

logger = get_logger(__name__)


class RedfishBiosManager(BaseRedfishManager):
    """Specialized manager for BIOS operations."""

    def __init__(self, credentials: RedfishCredentials):
        super().__init__(credentials)
        self.bios_ops = RedfishBiosOperation(credentials)

    def get_supported_operations(self) -> Dict[str, bool]:
        """Get supported BIOS operations."""
        return {
            "get_bios_attributes": True,
            "get_bios_attribute": True,
            "set_bios_attributes": True,
            "set_bios_attribute": True,
            "reset_bios_to_defaults": True,
            "get_pending_bios_settings": True,
            "apply_pending_settings": True,
            "get_bios_registry": False,  # Implementation dependent
        }

    def get_bios_attributes(
        self, system_id: str = "1"
    ) -> Optional[Dict[str, BiosAttribute]]:
        """Get all BIOS attributes.

        Args:
            system_id: System identifier

        Returns:
            Dictionary of BIOS attributes
        """
        try:
            result = self.bios_ops.get_bios_attributes(system_id)
            if result.success:
                return result.result
            else:
                self.logger.error(
                    f"Failed to get BIOS attributes: {result.error_message}"
                )
                return None
        except Exception as e:
            self.logger.error(f"Error getting BIOS attributes: {e}")
            return None

    def get_bios_attribute(
        self, attribute_name: str, system_id: str = "1"
    ) -> Optional[BiosAttribute]:
        """Get specific BIOS attribute.

        Args:
            attribute_name: Name of the BIOS attribute
            system_id: System identifier

        Returns:
            BIOS attribute if found
        """
        try:
            with self.create_session() as session:
                result = self.bios_ops.get_bios_attribute(
                    session, attribute_name, system_id
                )
                if result.success:
                    return result.result
                else:
                    self.logger.error(
                        f"Failed to get BIOS attribute {attribute_name}: {result.error_message}"
                    )
                    return None
        except Exception as e:
            self.logger.error(f"Error getting BIOS attribute {attribute_name}: {e}")
            return None

    def set_bios_attributes(
        self, attributes: Dict[str, Any], system_id: str = "1"
    ) -> bool:
        """Set multiple BIOS attributes.

        Args:
            attributes: Dictionary of attribute names and values
            system_id: System identifier

        Returns:
            True if successful
        """
        try:
            with self.create_session() as session:
                result = self.bios_ops.set_bios_attributes(
                    session, attributes, system_id
                )
                if not result.success:
                    self.logger.error(
                        f"Failed to set BIOS attributes: {result.error_message}"
                    )
                return result.success
        except Exception as e:
            self.logger.error(f"Error setting BIOS attributes: {e}")
            return False

    def set_bios_attribute(
        self, attribute_name: str, value: Any, system_id: str = "1"
    ) -> bool:
        """Set specific BIOS attribute.

        Args:
            attribute_name: Name of the BIOS attribute
            value: Value to set
            system_id: System identifier

        Returns:
            True if successful
        """
        return self.set_bios_attributes({attribute_name: value}, system_id)

    def reset_bios_to_defaults(self, system_id: str = "1") -> bool:
        """Reset BIOS to default settings.

        Args:
            system_id: System identifier

        Returns:
            True if successful
        """
        try:
            with self.create_session() as session:
                result = self.bios_ops.reset_bios_to_defaults(session, system_id)
                if not result.success:
                    self.logger.error(
                        f"Failed to reset BIOS to defaults: {result.error_message}"
                    )
                return result.success
        except Exception as e:
            self.logger.error(f"Error resetting BIOS to defaults: {e}")
            return False

    def get_pending_bios_settings(
        self, system_id: str = "1"
    ) -> Optional[Dict[str, Any]]:
        """Get pending BIOS settings.

        Args:
            system_id: System identifier

        Returns:
            Dictionary of pending BIOS settings
        """
        try:
            with self.create_session() as session:
                result = self.bios_ops.get_pending_bios_settings(session, system_id)
                if result.success:
                    return result.result
                else:
                    self.logger.error(
                        f"Failed to get pending BIOS settings: {result.error_message}"
                    )
                    return None
        except Exception as e:
            self.logger.error(f"Error getting pending BIOS settings: {e}")
            return None

    def get_bios_settings(self, system_id: str = "1") -> Optional[Dict[str, Any]]:
        """Get current BIOS settings (legacy compatibility).

        Args:
            system_id: System identifier

        Returns:
            Dictionary of current BIOS settings
        """
        attributes = self.get_bios_attributes(system_id)
        if attributes:
            # Convert BiosAttribute objects to simple dictionary
            return {name: attr.value for name, attr in attributes.items()}
        return None

    def validate_bios_attribute(
        self, attribute_name: str, value: Any, system_id: str = "1"
    ) -> bool:
        """Validate that a BIOS attribute value is acceptable.

        Args:
            attribute_name: Name of the BIOS attribute
            value: Value to validate
            system_id: System identifier

        Returns:
            True if value is valid
        """
        attribute = self.get_bios_attribute(attribute_name, system_id)
        if not attribute:
            self.logger.error(f"BIOS attribute {attribute_name} not found")
            return False

        # Check if value is in allowed values (if specified)
        if attribute.allowable_values and value not in attribute.allowable_values:
            self.logger.error(
                f"Value {value} not in allowed values for {attribute_name}: "
                f"{attribute.allowable_values}"
            )
            return False

        # Check data type compatibility
        if attribute.attribute_type and not self._is_compatible_type(
            value, attribute.attribute_type
        ):
            self.logger.error(
                f"Value {value} is not compatible with type {attribute.attribute_type} "
                f"for attribute {attribute_name}"
            )
            return False

        return True

    def get_bios_attribute_info(
        self, attribute_name: str, system_id: str = "1"
    ) -> Optional[Dict[str, Any]]:
        """Get detailed information about a BIOS attribute.

        Args:
            attribute_name: Name of the BIOS attribute
            system_id: System identifier

        Returns:
            Dictionary with attribute information
        """
        attribute = self.get_bios_attribute(attribute_name, system_id)
        if not attribute:
            return None

        return {
            "name": attribute.name,
            "current_value": attribute.current_value,
            "pending_value": attribute.pending_value,
            "default_value": attribute.default_value,
            "attribute_type": attribute.attribute_type,
            "allowable_values": attribute.allowable_values,
            "read_only": attribute.read_only,
            "description": getattr(attribute, "description", None),
        }

    def compare_bios_settings(
        self, desired_settings: Dict[str, Any], system_id: str = "1"
    ) -> Dict[str, Dict[str, Any]]:
        """Compare desired settings with current BIOS settings.

        Args:
            desired_settings: Dictionary of desired attribute values
            system_id: System identifier

        Returns:
            Dictionary with comparison results
        """
        current_attributes = self.get_bios_attributes(system_id)
        if not current_attributes:
            return {}

        comparison = {}
        for attr_name, desired_value in desired_settings.items():
            current_attr = current_attributes.get(attr_name)
            if current_attr:
                comparison[attr_name] = {
                    "current_value": current_attr.current_value,
                    "desired_value": desired_value,
                    "needs_change": current_attr.current_value != desired_value,
                    "read_only": current_attr.read_only,
                }
            else:
                comparison[attr_name] = {
                    "current_value": None,
                    "desired_value": desired_value,
                    "needs_change": True,
                    "attribute_exists": False,
                }

        return comparison

    def _is_compatible_type(self, value: Any, expected_type: str) -> bool:
        """Check if value is compatible with expected type.

        Args:
            value: Value to check
            expected_type: Expected type string

        Returns:
            True if compatible
        """
        type_mapping = {
            "string": str,
            "integer": (int, float),
            "boolean": bool,
            "enumeration": str,  # Enums are typically strings
        }

        expected_python_type = type_mapping.get(expected_type.lower())
        if expected_python_type:
            return isinstance(value, expected_python_type)

        # Default to True for unknown types
        return True
