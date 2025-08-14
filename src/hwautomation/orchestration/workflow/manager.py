"""
Main Workflow Manager

Central orchestration manager that coordinates workflow creation, execution, and lifecycle management.
"""

import logging
from typing import Any, Dict, List, Optional

from ...database.helper import DbHelper
from ...logging import get_logger
from ...maas.client import MaasClient
from .base import WorkflowContext, WorkflowStatus
from .engine import Workflow
from .firmware import FirmwareWorkflowHandler

logger = get_logger(__name__)


class WorkflowManager:
    """
    Main workflow orchestration manager

    Coordinates the entire server provisioning process from commissioning
    through BIOS configuration to IPMI setup.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.workflows: Dict[str, Workflow] = {}
        self.logger = get_logger(__name__)

        # Initialize database helper
        db_config = config.get("database", {})
        self.db_helper = DbHelper(
            tablename=db_config.get("table_name", "servers"),
            db_path=db_config.get("path", "hw_automation.db"),
            auto_migrate=db_config.get("auto_migrate", True),
        )

        # Initialize clients
        maas_config = config.get("maas", {})
        self.maas_client = MaasClient(
            host=maas_config.get("host", ""),
            consumer_key=maas_config.get("consumer_key", ""),
            consumer_token=maas_config.get("consumer_token", ""),
            secret=maas_config.get("secret", ""),
        )

        # Initialize firmware workflow handler
        self.firmware_handler = FirmwareWorkflowHandler(config)

        logger.info("WorkflowManager initialized successfully")

    def create_workflow(self, workflow_id: str) -> Workflow:
        """Create a new workflow instance."""
        workflow = Workflow(workflow_id, self)
        self.workflows[workflow_id] = workflow
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get an existing workflow by ID."""
        return self.workflows.get(workflow_id)

    def list_workflows(self) -> List[str]:
        """List all workflow IDs."""
        return list(self.workflows.keys())

    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get all active (running or pending) workflows."""
        active_workflows = []
        for workflow in self.workflows.values():
            if workflow.status in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]:
                active_workflows.append(workflow.get_status())
        return active_workflows

    def get_all_workflows(self) -> List[Dict[str, Any]]:
        """Get status of all workflows."""
        return [workflow.get_status() for workflow in self.workflows.values()]

    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow."""
        workflow = self.workflows.get(workflow_id)
        if workflow:
            workflow.cancel()
            return True
        return False

    def cleanup_workflow(self, workflow_id: str):
        """Remove a completed or failed workflow from memory."""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]

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

        Returns:
            Configured Workflow instance
        """
        return self.firmware_handler.create_firmware_first_workflow(
            workflow_id=workflow_id,
            server_id=server_id,
            device_type=device_type,
            target_ip=target_ip,
            credentials=credentials,
            firmware_policy=firmware_policy,
            skip_firmware_check=skip_firmware_check,
            skip_bios_config=skip_bios_config,
            manager=self,
        )

    def create_context(
        self,
        server_id: str,
        device_type: str,
        target_ipmi_ip: Optional[str] = None,
        rack_location: Optional[str] = None,
        gateway: Optional[str] = None,
        subnet_mask: Optional[str] = None,
    ) -> WorkflowContext:
        """
        Create a workflow context with initialized clients.

        Args:
            server_id: Server identifier
            device_type: Type of device being provisioned
            target_ipmi_ip: Target IPMI IP address
            rack_location: Physical rack location
            gateway: Network gateway
            subnet_mask: Network subnet mask

        Returns:
            Configured WorkflowContext instance
        """
        return WorkflowContext(
            server_id=server_id,
            device_type=device_type,
            target_ipmi_ip=target_ipmi_ip,
            rack_location=rack_location,
            maas_client=self.maas_client,
            db_helper=self.db_helper,
            gateway=gateway,
            subnet_mask=subnet_mask,
        )

    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        return self.config.copy()

    def is_firmware_available(self) -> bool:
        """Check if firmware workflow components are available."""
        return self.firmware_handler.is_firmware_available()

    def shutdown(self):
        """Shutdown the workflow manager and cleanup resources."""
        # Cancel all running workflows
        for workflow_id, workflow in self.workflows.items():
            if workflow.status in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]:
                logger.info(f"Cancelling workflow {workflow_id} during shutdown")
                workflow.cancel()

        # Clear workflow references
        self.workflows.clear()

        logger.info("WorkflowManager shutdown completed")
