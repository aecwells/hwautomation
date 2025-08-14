"""
Firmware Workflow Handler

Handles firmware-specific workflow operations and provisioning logic.
"""

import logging
from typing import Any, Dict, Optional

from ...database.helper import DbHelper
from ...logging import get_logger
from .base import WorkflowContext, WorkflowExecutionError, WorkflowStep
from .engine import Workflow

logger = get_logger(__name__)


class FirmwareWorkflowHandler:
    """Handles firmware-specific workflow operations."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)

        # Type annotations for fields that will be set
        self.firmware_manager: Optional[Any] = None  # FirmwareManager
        self.firmware_workflow: Optional[Any] = None  # FirmwareProvisioningWorkflow

    def initialize_firmware_components(self):
        """Initialize firmware manager and workflow components."""
        try:
            # Lazy import to avoid circular dependency
            from ...hardware.firmware_manager import FirmwareManager
            from ...hardware.firmware_provisioning_workflow import (
                FirmwareProvisioningWorkflow,
                ProvisioningContext,
            )

            self.firmware_manager = FirmwareManager(self.config)
            self.firmware_workflow = FirmwareProvisioningWorkflow(self.config)

            logger.info("Firmware components initialized successfully")

        except ImportError as e:
            logger.warning(f"Firmware components not available: {e}")
            self.firmware_manager = None
            self.firmware_workflow = None

    def create_firmware_first_workflow(
        self,
        workflow_id: str,
        server_id: str,
        device_type: str,
        target_ip: str,
        credentials: Dict[str, str],
        firmware_policy: Optional[str] = None,
        skip_firmware_check: bool = False,
        skip_bios_config: bool = False,
        manager: Any = None,  # WorkflowManager
    ) -> Workflow:
        """
        Create a firmware-first provisioning workflow.

        Args:
            workflow_id: Unique identifier for the workflow
            server_id: Server identifier
            device_type: Type of device being provisioned
            target_ip: Target IP address for the server
            credentials: Authentication credentials
            firmware_policy: Firmware update policy
            skip_firmware_check: Whether to skip firmware checks
            skip_bios_config: Whether to skip BIOS configuration
            manager: Reference to the workflow manager

        Returns:
            Configured Workflow instance
        """
        # Initialize firmware components if not already done
        if self.firmware_manager is None or self.firmware_workflow is None:
            self.initialize_firmware_components()

        workflow = Workflow(workflow_id, manager)

        # Create provisioning context
        # Note: Using dict for context since ProvisioningContext was in legacy firmware_provisioning_workflow
        context = {
            "server_id": server_id,
            "device_type": device_type,
            "target_ip": target_ip,
            "credentials": credentials,
            "firmware_policy": firmware_policy,
            "operation_id": workflow_id,
            "skip_firmware_check": skip_firmware_check,
            "skip_bios_config": skip_bios_config,
        }

        # Add firmware-first provisioning step
        workflow.add_step(
            WorkflowStep(
                name="firmware_first_provisioning",
                description="Execute complete firmware-first provisioning workflow",
                function=lambda ctx: self._execute_firmware_first_provisioning(
                    ctx, context
                ),
                timeout=3600,  # 1 hour
                retry_count=1,
            )
        )

        return workflow

    async def _execute_firmware_first_provisioning(
        self,
        workflow_context: WorkflowContext,
        provisioning_context: Any,  # ProvisioningContext
    ) -> bool:
        """Execute the firmware-first provisioning workflow."""
        try:
            workflow_context.report_sub_task("Starting firmware-first provisioning...")

            # Execute the firmware provisioning workflow
            if not self.firmware_workflow:
                raise WorkflowExecutionError("Firmware workflow not available")

            result = await self.firmware_workflow.execute_firmware_first_provisioning(
                provisioning_context
            )

            if result.success:
                workflow_context.report_sub_task(
                    f"Firmware-first provisioning completed successfully"
                )
                logger.info(
                    f"Firmware-first provisioning successful for {provisioning_context.server_id}"
                )

                # Update database with results
                self._update_firmware_provisioning_results(
                    provisioning_context.server_id, result
                )

                return True

            else:
                error_msg = f"Firmware-first provisioning failed: {result.error}"
                workflow_context.report_sub_task(error_msg)
                logger.error(error_msg)
                raise WorkflowExecutionError(error_msg)

        except Exception as e:
            error_msg = f"Firmware-first provisioning error: {e}"
            workflow_context.report_sub_task(error_msg)
            logger.error(error_msg)
            raise WorkflowExecutionError(error_msg)

    def _update_firmware_provisioning_results(self, server_id: str, result):
        """Update database with firmware provisioning results."""
        try:
            # Get database helper from config
            db_config = self.config.get("database", {})
            db_helper = DbHelper(
                tablename=db_config.get("table_name", "servers"),
                db_path=db_config.get("path", "hw_automation.db"),
                auto_migrate=db_config.get("auto_migrate", True),
            )

            # Update server status
            db_helper.updateserverinfo(server_id, "status_name", "firmware_provisioned")

            # Store firmware information if available
            if hasattr(result, "firmware_info") and result.firmware_info:
                firmware_info = result.firmware_info
                db_helper.updateserverinfo(
                    server_id, "firmware_version", firmware_info.get("version", "")
                )
                db_helper.updateserverinfo(
                    server_id, "firmware_build", firmware_info.get("build", "")
                )

            # Store any errors or warnings
            if hasattr(result, "warnings") and result.warnings:
                warnings_str = "; ".join(result.warnings)
                db_helper.updateserverinfo(server_id, "firmware_warnings", warnings_str)

            logger.info(
                f"Updated database with firmware provisioning results for {server_id}"
            )

        except Exception as e:
            logger.warning(f"Failed to update database with firmware results: {e}")

    def is_firmware_available(self) -> bool:
        """Check if firmware components are available."""
        return self.firmware_manager is not None and self.firmware_workflow is not None
