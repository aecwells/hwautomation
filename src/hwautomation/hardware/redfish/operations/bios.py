"""Redfish BIOS configuration operations.

This module provides BIOS settings management through the Redfish API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from hwautomation.logging import get_logger

from ..base import (
    BaseRedfishOperation,
    BiosAttribute,
    RedfishCredentials,
    RedfishOperation,
)
from ..client import RedfishSession

logger = get_logger(__name__)


class RedfishBiosOperation(BaseRedfishOperation):
    """Redfish BIOS configuration operations."""

    def __init__(self, credentials: RedfishCredentials):
        """Initialize BIOS operations.

        Args:
            credentials: Redfish connection credentials
        """
        self.credentials = credentials

    @property
    def operation_name(self) -> str:
        """Get operation name."""
        return "BIOS Configuration"

    def get_bios_attributes(
        self, system_id: str = "1"
    ) -> RedfishOperation[Dict[str, BiosAttribute]]:
        """Get all BIOS attributes.

        Args:
            system_id: System identifier (default: "1")

        Returns:
            Operation result with BIOS attributes
        """
        try:
            with RedfishSession(self.credentials) as session:
                # Get BIOS URI from system
                system_uri = f"/redfish/v1/Systems/{system_id}"
                system_response = session.get(system_uri)

                if not system_response.success:
                    return RedfishOperation(
                        success=False,
                        error_message=f"Failed to get system info: {system_response.error_message}",
                        response=system_response,
                    )

                if not system_response.data:
                    return RedfishOperation(
                        success=False,
                        error_message="No system data received",
                        response=system_response,
                    )

                # Get BIOS URI
                bios_data = system_response.data.get("Bios")
                if not bios_data:
                    return RedfishOperation(
                        success=False,
                        error_message="BIOS information not available",
                        response=system_response,
                    )

                bios_uri = bios_data.get("@odata.id")
                if not bios_uri:
                    return RedfishOperation(
                        success=False,
                        error_message="BIOS URI not found",
                        response=system_response,
                    )

                # Get BIOS attributes
                bios_response = session.get(bios_uri)
                if not bios_response.success:
                    return RedfishOperation(
                        success=False,
                        error_message=f"Failed to get BIOS attributes: {bios_response.error_message}",
                        response=bios_response,
                    )

                if not bios_response.data:
                    return RedfishOperation(
                        success=False,
                        error_message="No BIOS data received",
                        response=bios_response,
                    )

                # Parse BIOS attributes
                attributes_data = bios_response.data.get("Attributes", {})
                attributes = {}

                for name, value in attributes_data.items():
                    attributes[name] = BiosAttribute(
                        name=name,
                        value=value,
                        description=f"BIOS attribute {name}",  # Basic description
                    )

                # Try to get attribute registry for additional metadata
                self._enrich_attributes_from_registry(
                    session, bios_response.data, attributes
                )

                return RedfishOperation(
                    success=True,
                    result=attributes,
                    response=bios_response,
                )

        except Exception as e:
            logger.error(f"Failed to get BIOS attributes: {e}")
            return RedfishOperation(
                success=False,
                error_message=str(e),
            )

    def set_bios_attributes(
        self, attributes: Dict[str, Any], system_id: str = "1"
    ) -> RedfishOperation[bool]:
        """Set BIOS attributes.

        Args:
            attributes: Dictionary of attribute names and values
            system_id: System identifier

        Returns:
            Operation result
        """
        try:
            with RedfishSession(self.credentials) as session:
                # Get BIOS settings URI
                bios_settings_uri = self._get_bios_settings_uri(session, system_id)
                if not bios_settings_uri:
                    return RedfishOperation(
                        success=False,
                        error_message="BIOS settings URI not found",
                    )

                # Prepare BIOS settings data
                settings_data = {"Attributes": attributes}

                # Send PATCH request to update settings
                response = session.patch(bios_settings_uri, settings_data)

                if not response.success:
                    return RedfishOperation(
                        success=False,
                        error_message=f"Failed to set BIOS attributes: {response.error_message}",
                        response=response,
                    )

                logger.info(f"BIOS attributes updated: {list(attributes.keys())}")
                return RedfishOperation(
                    success=True,
                    result=True,
                    response=response,
                )

        except Exception as e:
            logger.error(f"Failed to set BIOS attributes: {e}")
            return RedfishOperation(
                success=False,
                error_message=str(e),
            )

    def get_bios_attribute(
        self, attribute_name: str, system_id: str = "1"
    ) -> RedfishOperation[BiosAttribute]:
        """Get specific BIOS attribute.

        Args:
            attribute_name: Name of the BIOS attribute
            system_id: System identifier

        Returns:
            Operation result with BIOS attribute
        """
        result = self.get_bios_attributes(system_id)

        if not result.success:
            return RedfishOperation(
                success=False,
                error_message=result.error_message,
                response=result.response,
            )

        attributes = result.result or {}
        attribute = attributes.get(attribute_name)

        if not attribute:
            return RedfishOperation(
                success=False,
                error_message=f"BIOS attribute '{attribute_name}' not found",
            )

        return RedfishOperation(
            success=True,
            result=attribute,
            response=result.response,
        )

    def set_bios_attribute(
        self, attribute_name: str, value: Any, system_id: str = "1"
    ) -> RedfishOperation[bool]:
        """Set specific BIOS attribute.

        Args:
            attribute_name: Name of the BIOS attribute
            value: Value to set
            system_id: System identifier

        Returns:
            Operation result
        """
        return self.set_bios_attributes({attribute_name: value}, system_id)

    def reset_bios_to_defaults(self, system_id: str = "1") -> RedfishOperation[bool]:
        """Reset BIOS to default settings.

        Args:
            system_id: System identifier

        Returns:
            Operation result
        """
        try:
            with RedfishSession(self.credentials) as session:
                # Get BIOS URI and check for reset action
                system_uri = f"/redfish/v1/Systems/{system_id}"
                system_response = session.get(system_uri)

                if not system_response.success or not system_response.data:
                    return RedfishOperation(
                        success=False,
                        error_message="Failed to get system information",
                        response=system_response,
                    )

                bios_data = system_response.data.get("Bios")
                if not bios_data:
                    return RedfishOperation(
                        success=False,
                        error_message="BIOS information not available",
                        response=system_response,
                    )

                bios_uri = bios_data.get("@odata.id")
                if not bios_uri:
                    return RedfishOperation(
                        success=False,
                        error_message="BIOS URI not found",
                        response=system_response,
                    )

                # Get BIOS resource to find reset action
                bios_response = session.get(bios_uri)
                if not bios_response.success or not bios_response.data:
                    return RedfishOperation(
                        success=False,
                        error_message="Failed to get BIOS resource",
                        response=bios_response,
                    )

                # Look for reset to defaults action
                actions = bios_response.data.get("Actions", {})
                reset_action = actions.get("#Bios.ResetBios")

                if not reset_action:
                    return RedfishOperation(
                        success=False,
                        error_message="BIOS reset action not supported",
                        response=bios_response,
                    )

                reset_uri = reset_action.get("target")
                if not reset_uri:
                    return RedfishOperation(
                        success=False,
                        error_message="BIOS reset target URI not found",
                        response=bios_response,
                    )

                # Perform reset action
                reset_response = session.post(reset_uri, {})

                if not reset_response.success:
                    return RedfishOperation(
                        success=False,
                        error_message=f"BIOS reset failed: {reset_response.error_message}",
                        response=reset_response,
                    )

                logger.info("BIOS reset to defaults initiated")
                return RedfishOperation(
                    success=True,
                    result=True,
                    response=reset_response,
                )

        except Exception as e:
            logger.error(f"Failed to reset BIOS: {e}")
            return RedfishOperation(
                success=False,
                error_message=str(e),
            )

    def get_pending_bios_settings(
        self, system_id: str = "1"
    ) -> RedfishOperation[Dict[str, Any]]:
        """Get pending BIOS settings that require reboot.

        Args:
            system_id: System identifier

        Returns:
            Operation result with pending settings
        """
        try:
            with RedfishSession(self.credentials) as session:
                bios_settings_uri = self._get_bios_settings_uri(session, system_id)
                if not bios_settings_uri:
                    return RedfishOperation(
                        success=False,
                        error_message="BIOS settings URI not found",
                    )

                response = session.get(bios_settings_uri)
                if not response.success:
                    return RedfishOperation(
                        success=False,
                        error_message=f"Failed to get pending settings: {response.error_message}",
                        response=response,
                    )

                if not response.data:
                    return RedfishOperation(
                        success=False,
                        error_message="No BIOS settings data received",
                        response=response,
                    )

                # Extract pending attributes
                pending_attributes = response.data.get("Attributes", {})

                return RedfishOperation(
                    success=True,
                    result=pending_attributes,
                    response=response,
                )

        except Exception as e:
            logger.error(f"Failed to get pending BIOS settings: {e}")
            return RedfishOperation(
                success=False,
                error_message=str(e),
            )

    def _get_bios_settings_uri(
        self, session: RedfishSession, system_id: str
    ) -> Optional[str]:
        """Get BIOS settings URI for the system.

        Args:
            session: Redfish session
            system_id: System identifier

        Returns:
            BIOS settings URI if found
        """
        try:
            # Get system info
            system_uri = f"/redfish/v1/Systems/{system_id}"
            system_response = session.get(system_uri)

            if not system_response.success or not system_response.data:
                return None

            # Get BIOS URI
            bios_data = system_response.data.get("Bios")
            if not bios_data:
                return None

            bios_uri = bios_data.get("@odata.id")
            if not bios_uri:
                return None

            # Check for BIOS settings URI
            bios_response = session.get(bios_uri)
            if not bios_response.success or not bios_response.data:
                return None

            # Try different possible settings URIs
            settings_data = bios_response.data.get("@Redfish.Settings")
            if settings_data:
                return settings_data.get("SettingsObject", {}).get("@odata.id")

            # Alternative: look for /Settings suffix
            return f"{bios_uri}/Settings"

        except Exception as e:
            logger.warning(f"Failed to get BIOS settings URI: {e}")
            return None

    def _enrich_attributes_from_registry(
        self,
        session: RedfishSession,
        bios_data: Dict,
        attributes: Dict[str, BiosAttribute],
    ) -> None:
        """Enrich attributes with metadata from registry.

        Args:
            session: Redfish session
            bios_data: BIOS resource data
            attributes: Attributes to enrich
        """
        try:
            # Look for attribute registry reference
            registry_data = bios_data.get("AttributeRegistry")
            if not registry_data:
                return

            registry_uri = f"/redfish/v1/Registries/{registry_data}"
            registry_response = session.get(registry_uri)

            if not registry_response.success or not registry_response.data:
                return

            # Get registry entries
            entries = registry_response.data.get("Registry", {}).get("Attributes", [])

            for entry in entries:
                attr_name = entry.get("AttributeName")
                if attr_name in attributes:
                    # Enrich with registry metadata
                    attribute = attributes[attr_name]
                    attribute.description = entry.get("HelpText", attribute.description)
                    attribute.possible_values = entry.get("Value", [])
                    attribute.data_type = entry.get("Type", "Unknown")

        except Exception as e:
            logger.debug(f"Failed to enrich attributes from registry: {e}")
            # Not critical, continue without registry metadata
