"""
Backward compatibility module for the legacy server_provisioning.py file.

This module provides a compatibility layer to ensure existing code continues
to work while using the new modular provisioning system.
"""

import warnings
from typing import Any, Callable, Dict, Optional

from ..logging import get_logger
from .provisioning import (
    create_provisioning_workflow as new_create_provisioning_workflow,
)
from .workflow_manager import Workflow, WorkflowContext, WorkflowManager

logger = get_logger(__name__)


class ServerProvisioningWorkflow:
    """
    Backward compatibility wrapper for the legacy ServerProvisioningWorkflow class.

    This class provides the same interface as the original monolithic class
    but delegates to the new modular system.
    """

    def __init__(self, workflow_manager: WorkflowManager):
        self.manager = workflow_manager
        self.logger = get_logger(__name__)

        # Issue deprecation warning
        warnings.warn(
            "ServerProvisioningWorkflow is deprecated. "
            "Use hwautomation.orchestration.provisioning.create_provisioning_workflow instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    def create_provisioning_workflow(
        self,
        server_id: str,
        device_type: str,
        target_ipmi_ip: Optional[str] = None,
        rack_location: Optional[str] = None,
        subnet_mask: Optional[str] = None,
        gateway: Optional[str] = None,
        **kwargs,
    ) -> Workflow:
        """
        Create a provisioning workflow (legacy interface).

        This method provides backward compatibility for the original interface.
        """
        logger.info(
            f"Creating provisioning workflow via legacy interface for {server_id}"
        )

        return new_create_provisioning_workflow(
            workflow_manager=self.manager,
            server_id=server_id,
            device_type=device_type,
            target_ipmi_ip=target_ipmi_ip,
            rack_location=rack_location,
            subnet_mask=subnet_mask,
            gateway=gateway,
            workflow_type="standard",
            **kwargs,
        )

    def create_firmware_first_provisioning_workflow(
        self,
        server_id: str,
        device_type: str,
        target_ipmi_ip: Optional[str] = None,
        rack_location: Optional[str] = None,
        subnet_mask: Optional[str] = None,
        gateway: Optional[str] = None,
        firmware_policy: str = "recommended",
        **kwargs,
    ) -> Workflow:
        """
        Create a firmware-first provisioning workflow (legacy interface).
        """
        logger.info(
            f"Creating firmware-first workflow via legacy interface for {server_id}"
        )

        return new_create_provisioning_workflow(
            workflow_manager=self.manager,
            server_id=server_id,
            device_type=device_type,
            target_ipmi_ip=target_ipmi_ip,
            rack_location=rack_location,
            subnet_mask=subnet_mask,
            gateway=gateway,
            workflow_type="firmware_first",
            firmware_policy=firmware_policy,
            **kwargs,
        )

    def provision_server(
        self,
        server_id: str,
        device_type: str,
        target_ipmi_ip: Optional[str] = None,
        rack_location: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        Provision a server (legacy interface).

        This method provides backward compatibility for direct provisioning.
        """
        logger.info(f"Provisioning server via legacy interface: {server_id}")

        # Create workflow
        workflow = self.create_provisioning_workflow(
            server_id=server_id,
            device_type=device_type,
            target_ipmi_ip=target_ipmi_ip,
            rack_location=rack_location,
        )

        # Set progress callback if provided
        if progress_callback:
            workflow.set_progress_callback(progress_callback)

        # Create context
        context = WorkflowContext(
            server_id=server_id,
            device_type=device_type,
            target_ipmi_ip=target_ipmi_ip,
            rack_location=rack_location,
            maas_client=self.manager.maas_client,
            db_helper=self.manager.db_helper,
            workflow_id=workflow.id,
        )

        # Execute workflow
        success = workflow.execute(context)

        # Return results in legacy format
        status = workflow.get_status()
        status["success"] = success
        status["workflow_id"] = workflow.id
        status["context"] = {
            "server_id": context.server_id,
            "device_type": context.device_type,
            "target_ipmi_ip": context.target_ipmi_ip,
            "server_ip": getattr(context, "server_ip", None),
            "metadata": getattr(context, "metadata", {}),
        }

        return status
