"""
Redfish Firmware Management

Specialized manager for firmware operations (inventory, updates).
"""

from typing import Any, Dict, List, Optional

from hwautomation.logging import get_logger

from ..base import FirmwareComponent, RedfishCredentials
from ..operations import RedfishFirmwareOperation
from .base import BaseRedfishManager, RedfishManagerError

logger = get_logger(__name__)


class RedfishFirmwareManager(BaseRedfishManager):
    """Specialized manager for firmware operations."""

    def __init__(self, credentials: RedfishCredentials):
        super().__init__(credentials)
        self.firmware_ops = RedfishFirmwareOperation(credentials)

    def get_supported_operations(self) -> Dict[str, bool]:
        """Get supported firmware operations."""
        return {
            "get_firmware_inventory": True,
            "get_firmware_component": True,
            "update_firmware": True,
            "get_update_status": True,
            "wait_for_update_completion": True,
            "schedule_firmware_update": False,  # Implementation dependent
            "verify_firmware_image": False,  # Implementation dependent
        }

    def get_firmware_inventory(self, system_id: str = "1") -> List[FirmwareComponent]:
        """Get firmware inventory.

        Args:
            system_id: System identifier

        Returns:
            List of firmware components
        """
        try:
            result = self.firmware_ops.get_firmware_inventory(system_id)
            if result.success:
                return result.result
            else:
                self.logger.error(
                    f"Failed to get firmware inventory: {result.error_message}"
                )
                return []
        except Exception as e:
            self.logger.error(f"Error getting firmware inventory: {e}")
            return []

    def get_firmware_component(self, component_id: str) -> Optional[FirmwareComponent]:
        """Get specific firmware component information.

        Args:
            component_id: Firmware component identifier

        Returns:
            Firmware component if found
        """
        try:
            with self.create_session() as session:
                result = self.firmware_ops.get_firmware_component(session, component_id)
                if result.success:
                    return result.result
                else:
                    self.logger.error(
                        f"Failed to get firmware component {component_id}: {result.error_message}"
                    )
                    return None
        except Exception as e:
            self.logger.error(f"Error getting firmware component {component_id}: {e}")
            return None

    def update_firmware(
        self,
        image_uri: str,
        component_id: Optional[str] = None,
        system_id: str = "1",
        transfer_protocol: str = "HTTP",
    ) -> Optional[str]:
        """Update firmware component.

        Args:
            image_uri: URI of firmware image
            component_id: Specific component to update (optional)
            system_id: System identifier
            transfer_protocol: Transfer protocol for image

        Returns:
            Task URI for monitoring update progress
        """
        try:
            with self.create_session() as session:
                result = self.firmware_ops.update_firmware(
                    session, image_uri, component_id, system_id, transfer_protocol
                )
                if result.success:
                    return result.result  # Task URI
                else:
                    self.logger.error(
                        f"Failed to start firmware update: {result.error_message}"
                    )
                    return None
        except Exception as e:
            self.logger.error(f"Error starting firmware update: {e}")
            return None

    def get_update_status(self, task_uri: str) -> Optional[Dict[str, str]]:
        """Get firmware update status.

        Args:
            task_uri: Task URI from update operation

        Returns:
            Update status information
        """
        try:
            with self.create_session() as session:
                result = self.firmware_ops.get_update_status(session, task_uri)
                if result.success:
                    return result.result
                else:
                    self.logger.error(
                        f"Failed to get update status: {result.error_message}"
                    )
                    return None
        except Exception as e:
            self.logger.error(f"Error getting update status: {e}")
            return None

    def wait_for_update_completion(self, task_uri: str, timeout: int = 1800) -> bool:
        """Wait for firmware update to complete.

        Args:
            task_uri: Task URI from update operation
            timeout: Maximum wait time in seconds

        Returns:
            True if update completed successfully
        """
        try:
            with self.create_session() as session:
                result = self.firmware_ops.wait_for_update_completion(
                    session, task_uri, timeout
                )
                if not result.success:
                    self.logger.error(
                        f"Firmware update failed or timed out: {result.error_message}"
                    )
                return result.success
        except Exception as e:
            self.logger.error(f"Error waiting for update completion: {e}")
            return False

    def get_firmware_summary(self, system_id: str = "1") -> Dict[str, Any]:
        """Get summary of firmware components.

        Args:
            system_id: System identifier

        Returns:
            Firmware summary dictionary
        """
        summary = {
            "total_components": 0,
            "updateable_components": 0,
            "components_by_type": {},
            "components": [],
        }

        try:
            components = self.get_firmware_inventory(system_id)
            summary["total_components"] = len(components)

            for component in components:
                # Count updateable components
                if getattr(component, "updateable", False):
                    summary["updateable_components"] += 1

                # Group by component type
                component_type = getattr(component, "component_type", "Unknown")
                if component_type not in summary["components_by_type"]:
                    summary["components_by_type"][component_type] = 0
                summary["components_by_type"][component_type] += 1

                # Add to components list
                component_info = {
                    "id": component.id,
                    "name": component.name,
                    "version": component.version,
                    "component_type": component_type,
                    "updateable": getattr(component, "updateable", False),
                    "status": getattr(component, "status", "Unknown"),
                }
                summary["components"].append(component_info)

        except Exception as e:
            self.logger.error(f"Error getting firmware summary: {e}")

        return summary

    def find_firmware_component(
        self,
        name: Optional[str] = None,
        component_type: Optional[str] = None,
        system_id: str = "1",
    ) -> List[FirmwareComponent]:
        """Find firmware components by name or type.

        Args:
            name: Component name to search for
            component_type: Component type to filter by
            system_id: System identifier

        Returns:
            List of matching firmware components
        """
        matching_components = []

        try:
            components = self.get_firmware_inventory(system_id)

            for component in components:
                matches = True

                if name and name.lower() not in component.name.lower():
                    matches = False

                if (
                    component_type
                    and getattr(component, "component_type", "").lower()
                    != component_type.lower()
                ):
                    matches = False

                if matches:
                    matching_components.append(component)

        except Exception as e:
            self.logger.error(f"Error finding firmware components: {e}")

        return matching_components

    def get_updateable_components(
        self, system_id: str = "1"
    ) -> List[FirmwareComponent]:
        """Get list of updateable firmware components.

        Args:
            system_id: System identifier

        Returns:
            List of updateable firmware components
        """
        updateable_components = []

        try:
            components = self.get_firmware_inventory(system_id)

            for component in components:
                if getattr(component, "updateable", False):
                    updateable_components.append(component)

        except Exception as e:
            self.logger.error(f"Error getting updateable components: {e}")

        return updateable_components

    def validate_firmware_image(self, image_uri: str) -> bool:
        """Validate firmware image (basic checks).

        Args:
            image_uri: URI of firmware image to validate

        Returns:
            True if image appears valid
        """
        try:
            # Basic validation - check if URI is accessible
            import requests

            response = requests.head(image_uri, timeout=10)

            if response.status_code != 200:
                self.logger.error(
                    f"Firmware image not accessible: {response.status_code}"
                )
                return False

            # Check content length
            content_length = response.headers.get("content-length")
            if content_length and int(content_length) == 0:
                self.logger.error("Firmware image appears to be empty")
                return False

            # Check content type (if available)
            content_type = response.headers.get("content-type", "")
            valid_types = [
                "application/octet-stream",
                "application/binary",
                "application/zip",
            ]

            if content_type and not any(vt in content_type for vt in valid_types):
                self.logger.warning(
                    f"Unexpected content type for firmware image: {content_type}"
                )

            return True

        except Exception as e:
            self.logger.error(f"Error validating firmware image: {e}")
            return False

    def schedule_firmware_update(
        self,
        image_uri: str,
        component_id: Optional[str] = None,
        system_id: str = "1",
        scheduled_time: Optional[str] = None,
    ) -> Optional[str]:
        """Schedule firmware update for later execution.

        Args:
            image_uri: URI of firmware image
            component_id: Specific component to update
            system_id: System identifier
            scheduled_time: When to perform update (ISO format)

        Returns:
            Task URI for monitoring scheduled update
        """
        # This is a placeholder for advanced scheduling functionality
        # Most Redfish implementations don't support scheduling
        self.logger.warning(
            "Scheduled firmware updates not supported by most implementations"
        )

        if scheduled_time:
            self.logger.info(
                f"Ignoring scheduled time {scheduled_time}, executing immediately"
            )

        # Fall back to immediate update
        return self.update_firmware(image_uri, component_id, system_id)
