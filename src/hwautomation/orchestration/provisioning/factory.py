"""
Factory functions for creating provisioning workflows.

Provides backward-compatible interface for creating provisioning workflows.
"""

from typing import Optional

from ...logging import get_logger
from ..workflow_manager import Workflow, WorkflowManager
from .base import ProvisioningStrategy
from .coordinator import ProvisioningCoordinator, StandardProvisioningStrategy

logger = get_logger(__name__)


def create_provisioning_workflow(
    workflow_manager: WorkflowManager,
    server_id: str,
    device_type: str,
    target_ipmi_ip: Optional[str] = None,
    rack_location: Optional[str] = None,
    subnet_mask: Optional[str] = None,
    gateway: Optional[str] = None,
    workflow_type: str = "standard",
    **kwargs,
) -> Workflow:
    """
    Factory function to create a provisioning workflow.

    This function provides a backward-compatible interface for creating
    provisioning workflows while using the new modular system.

    Args:
        workflow_manager: The workflow manager instance
        server_id: Unique identifier for the server
        device_type: Device type (e.g., 'a1.c5.large')
        target_ipmi_ip: Optional target IPMI IP address
        rack_location: Optional physical rack location
        subnet_mask: Optional subnet mask for network configuration
        gateway: Optional gateway IP address
        workflow_type: Type of workflow ("standard", "firmware_first")
        **kwargs: Additional configuration parameters

    Returns:
        Workflow: Configured workflow ready for execution
    """
    logger.info(f"Creating {workflow_type} provisioning workflow for {server_id}")

    # Create coordinator
    coordinator = ProvisioningCoordinator(workflow_manager)

    # Select strategy based on workflow type
    strategy = _get_strategy(workflow_type, kwargs)

    # Create workflow
    workflow = coordinator.create_provisioning_workflow(
        server_id=server_id,
        device_type=device_type,
        target_ipmi_ip=target_ipmi_ip,
        rack_location=rack_location,
        subnet_mask=subnet_mask,
        gateway=gateway,
        strategy=strategy,
        **kwargs,
    )

    logger.info(f"Created workflow {workflow.id} with {len(workflow.steps)} steps")
    return workflow


def _get_strategy(workflow_type: str, kwargs: dict) -> ProvisioningStrategy:
    """Get the appropriate provisioning strategy."""
    if workflow_type == "firmware_first":
        # TODO: Implement FirmwareFirstProvisioningStrategy
        logger.warning("Firmware-first strategy not yet implemented, using standard")
        return StandardProvisioningStrategy()
    elif workflow_type == "standard":
        return StandardProvisioningStrategy()
    else:
        logger.warning(f"Unknown workflow type {workflow_type}, using standard")
        return StandardProvisioningStrategy()
