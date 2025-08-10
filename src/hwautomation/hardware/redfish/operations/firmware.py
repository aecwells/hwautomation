"""Redfish firmware management operations.

This module provides firmware update and inventory operations
through the Redfish API.
"""

from __future__ import annotations
import time
from typing import Dict, List, Optional

from hwautomation.logging import get_logger
from ..base import (
    BaseRedfishOperation,
    FirmwareComponent,
    RedfishCredentials,
    RedfishOperation,
)
from ..client import RedfishSession

logger = get_logger(__name__)


class RedfishFirmwareOperation(BaseRedfishOperation):
    """Redfish firmware management operations."""

    def __init__(self, credentials: RedfishCredentials):
        """Initialize firmware operations.
        
        Args:
            credentials: Redfish connection credentials
        """
        self.credentials = credentials

    @property
    def operation_name(self) -> str:
        """Get operation name."""
        return "Firmware Management"

    def get_firmware_inventory(self, system_id: str = "1") -> RedfishOperation[List[FirmwareComponent]]:
        """Get firmware inventory for the system.

        Args:
            system_id: System identifier (default: "1")

        Returns:
            Operation result with firmware inventory
        """
        try:
            with RedfishSession(self.credentials) as session:
                # Get update service
                update_service_response = session.get("/redfish/v1/UpdateService")
                if not update_service_response.success:
                    return RedfishOperation(
                        success=False,
                        error_message="Update service not available",
                        response=update_service_response,
                    )

                if not update_service_response.data:
                    return RedfishOperation(
                        success=False,
                        error_message="No update service data received",
                        response=update_service_response,
                    )

                # Get firmware inventory URI
                firmware_inventory_uri = None
                update_data = update_service_response.data
                
                if "FirmwareInventory" in update_data:
                    firmware_inventory_uri = update_data["FirmwareInventory"].get("@odata.id")

                if not firmware_inventory_uri:
                    return RedfishOperation(
                        success=False,
                        error_message="Firmware inventory not available",
                        response=update_service_response,
                    )

                # Get firmware inventory collection
                inventory_response = session.get(firmware_inventory_uri)
                if not inventory_response.success:
                    return RedfishOperation(
                        success=False,
                        error_message=f"Failed to get firmware inventory: {inventory_response.error_message}",
                        response=inventory_response,
                    )

                if not inventory_response.data:
                    return RedfishOperation(
                        success=False,
                        error_message="No firmware inventory data received",
                        response=inventory_response,
                    )

                # Process firmware components
                members = inventory_response.data.get("Members", [])
                firmware_components = []

                for member in members:
                    component_uri = member.get("@odata.id")
                    if not component_uri:
                        continue

                    component = self._get_firmware_component(session, component_uri)
                    if component:
                        firmware_components.append(component)

                return RedfishOperation(
                    success=True,
                    result=firmware_components,
                    response=inventory_response,
                )

        except Exception as e:
            logger.error(f"Failed to get firmware inventory: {e}")
            return RedfishOperation(
                success=False,
                error_message=str(e),
            )

    def get_firmware_component(self, component_id: str) -> RedfishOperation[FirmwareComponent]:
        """Get specific firmware component information.

        Args:
            component_id: Firmware component identifier

        Returns:
            Operation result with firmware component
        """
        try:
            with RedfishSession(self.credentials) as session:
                component_uri = f"/redfish/v1/UpdateService/FirmwareInventory/{component_id}"
                component = self._get_firmware_component(session, component_uri)

                if not component:
                    return RedfishOperation(
                        success=False,
                        error_message=f"Firmware component '{component_id}' not found",
                    )

                return RedfishOperation(
                    success=True,
                    result=component,
                )

        except Exception as e:
            logger.error(f"Failed to get firmware component: {e}")
            return RedfishOperation(
                success=False,
                error_message=str(e),
            )

    def update_firmware(
        self, 
        firmware_uri: str, 
        targets: Optional[List[str]] = None,
        apply_time: str = "Immediate"
    ) -> RedfishOperation[str]:
        """Update firmware using a firmware image URI.

        Args:
            firmware_uri: URI of the firmware image
            targets: List of target URIs to update
            apply_time: When to apply the update ("Immediate", "OnReset", "AtMaintenanceWindowStart")

        Returns:
            Operation result with task URI if async
        """
        try:
            with RedfishSession(self.credentials) as session:
                # Get update service
                update_service_response = session.get("/redfish/v1/UpdateService")
                if not update_service_response.success or not update_service_response.data:
                    return RedfishOperation(
                        success=False,
                        error_message="Update service not available",
                        response=update_service_response,
                    )

                # Check for simple update action
                actions = update_service_response.data.get("Actions", {})
                simple_update = actions.get("#UpdateService.SimpleUpdate")
                
                if not simple_update:
                    return RedfishOperation(
                        success=False,
                        error_message="Simple update action not supported",
                        response=update_service_response,
                    )

                update_uri = simple_update.get("target")
                if not update_uri:
                    return RedfishOperation(
                        success=False,
                        error_message="Update target URI not found",
                        response=update_service_response,
                    )

                # Prepare update data
                update_data = {
                    "ImageURI": firmware_uri,
                    "@Redfish.OperationApplyTime": apply_time,
                }

                if targets:
                    update_data["Targets"] = targets

                # Initiate firmware update
                update_response = session.post(update_uri, update_data)
                
                if not update_response.success:
                    return RedfishOperation(
                        success=False,
                        error_message=f"Firmware update failed: {update_response.error_message}",
                        response=update_response,
                    )

                # Check for task URI in response
                task_uri = None
                if update_response.headers:
                    location = update_response.headers.get("Location")
                    if location:
                        task_uri = location

                logger.info(f"Firmware update initiated from {firmware_uri}")
                
                return RedfishOperation(
                    success=True,
                    result=task_uri or "Update initiated",
                    response=update_response,
                )

        except Exception as e:
            logger.error(f"Failed to update firmware: {e}")
            return RedfishOperation(
                success=False,
                error_message=str(e),
            )

    def get_update_status(self, task_uri: str) -> RedfishOperation[Dict[str, str]]:
        """Get firmware update task status.

        Args:
            task_uri: Task URI from update operation

        Returns:
            Operation result with task status
        """
        try:
            with RedfishSession(self.credentials) as session:
                response = session.get(task_uri)
                
                if not response.success:
                    return RedfishOperation(
                        success=False,
                        error_message=f"Failed to get task status: {response.error_message}",
                        response=response,
                    )

                if not response.data:
                    return RedfishOperation(
                        success=False,
                        error_message="No task data received",
                        response=response,
                    )

                data = response.data
                status = {
                    "task_state": data.get("TaskState", "Unknown"),
                    "task_status": data.get("TaskStatus", "Unknown"),
                    "percent_complete": str(data.get("PercentComplete", 0)),
                    "start_time": data.get("StartTime", ""),
                    "end_time": data.get("EndTime", ""),
                }

                # Add messages if available
                messages = data.get("Messages", [])
                if messages:
                    status["messages"] = [msg.get("Message", "") for msg in messages]

                return RedfishOperation(
                    success=True,
                    result=status,
                    response=response,
                )

        except Exception as e:
            logger.error(f"Failed to get update status: {e}")
            return RedfishOperation(
                success=False,
                error_message=str(e),
            )

    def wait_for_update_completion(
        self, 
        task_uri: str, 
        timeout: int = 1800
    ) -> RedfishOperation[bool]:
        """Wait for firmware update to complete.

        Args:
            task_uri: Task URI from update operation
            timeout: Timeout in seconds

        Returns:
            Operation result with completion status
        """
        start_time = time.time()
        check_interval = 30  # seconds

        logger.info(f"Waiting for firmware update completion (timeout: {timeout}s)")

        while time.time() - start_time < timeout:
            status_result = self.get_update_status(task_uri)
            
            if not status_result.success:
                return RedfishOperation(
                    success=False,
                    error_message=f"Failed to check update status: {status_result.error_message}",
                )

            status = status_result.result or {}
            task_state = status.get("task_state", "Unknown")
            percent = status.get("percent_complete", "0")

            logger.info(f"Update progress: {task_state} ({percent}%)")

            # Check for completion states
            if task_state in ["Completed", "CompletedWithWarnings"]:
                logger.info("Firmware update completed successfully")
                return RedfishOperation(
                    success=True,
                    result=True,
                )
            elif task_state in ["Exception", "Cancelled", "Interrupted"]:
                logger.error(f"Firmware update failed: {task_state}")
                return RedfishOperation(
                    success=False,
                    error_message=f"Update failed with state: {task_state}",
                )

            time.sleep(check_interval)

        logger.warning(f"Firmware update timeout after {timeout}s")
        return RedfishOperation(
            success=False,
            error_message="Update timeout",
        )

    def _get_firmware_component(self, session: RedfishSession, component_uri: str) -> Optional[FirmwareComponent]:
        """Get firmware component details.

        Args:
            session: Redfish session
            component_uri: Component URI

        Returns:
            Firmware component if successful
        """
        try:
            response = session.get(component_uri)
            if not response.success or not response.data:
                return None

            data = response.data
            
            # Determine component type from name/description
            name = data.get("Name", "Unknown")
            description = data.get("Description", "")
            component_type = self._determine_component_type(name, description)

            return FirmwareComponent(
                id=data.get("Id", "Unknown"),
                name=name,
                version=data.get("Version", "Unknown"),
                component_type=component_type,
                description=description,
                updateable=data.get("Updateable", False),
                manufacturer=data.get("Manufacturer"),
                release_date=data.get("ReleaseDate"),
            )

        except Exception as e:
            logger.warning(f"Failed to get firmware component from {component_uri}: {e}")
            return None

    def _determine_component_type(self, name: str, description: str) -> str:
        """Determine component type from name and description.

        Args:
            name: Component name
            description: Component description

        Returns:
            Component type string
        """
        text = f"{name} {description}".lower()
        
        if any(keyword in text for keyword in ["bios", "uefi", "system"]):
            return "BIOS"
        elif any(keyword in text for keyword in ["bmc", "management", "controller"]):
            return "BMC"
        elif any(keyword in text for keyword in ["nic", "network", "ethernet"]):
            return "NIC"
        elif any(keyword in text for keyword in ["storage", "raid", "disk"]):
            return "Storage"
        elif any(keyword in text for keyword in ["cpu", "processor", "microcode"]):
            return "CPU"
        else:
            return "Other"
