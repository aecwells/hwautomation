"""
Provisioning coordinator.

Orchestrates the complete server provisioning process using modular stage handlers.
"""

from typing import Any, Dict, List, Optional

from ...logging import get_logger
from ..workflow_manager import Workflow, WorkflowContext, WorkflowManager, WorkflowStep
from .base import (
    ProvisioningConfig,
    ProvisioningStage,
    ProvisioningStageHandler,
    ProvisioningStrategy,
)
from .commissioning import CommissioningStageHandler
from .hardware_discovery import HardwareDiscoveryStageHandler
from .network_setup import NetworkSetupStageHandler

logger = get_logger(__name__)


class StandardProvisioningStrategy(ProvisioningStrategy):
    """Standard provisioning strategy."""

    def get_stage_order(self) -> List[ProvisioningStage]:
        """Get the standard order of provisioning stages."""
        return [
            ProvisioningStage.COMMISSIONING,
            ProvisioningStage.NETWORK_SETUP,
            ProvisioningStage.HARDWARE_DISCOVERY,
            ProvisioningStage.BIOS_CONFIGURATION,
            ProvisioningStage.IPMI_CONFIGURATION,
            ProvisioningStage.FINALIZATION,
        ]

    def should_skip_stage(
        self, stage: ProvisioningStage, context: WorkflowContext
    ) -> bool:
        """Determine if a stage should be skipped."""
        # Skip IPMI configuration if no target IP is provided
        if stage == ProvisioningStage.IPMI_CONFIGURATION:
            return (
                not hasattr(context, "target_ipmi_ip") or context.target_ipmi_ip is None
            )
        return False


class ProvisioningCoordinator:
    """Coordinates the complete server provisioning process."""

    def __init__(self, workflow_manager: WorkflowManager):
        self.workflow_manager = workflow_manager
        self.logger = get_logger(__name__)

        # Initialize stage handlers
        self.stage_handlers: Dict[ProvisioningStage, ProvisioningStageHandler] = {
            ProvisioningStage.COMMISSIONING: CommissioningStageHandler(),
            ProvisioningStage.NETWORK_SETUP: NetworkSetupStageHandler(),
            ProvisioningStage.HARDWARE_DISCOVERY: HardwareDiscoveryStageHandler(),
            # TODO: Add remaining stage handlers
            # ProvisioningStage.BIOS_CONFIGURATION: BiosConfigurationStageHandler(),
            # ProvisioningStage.IPMI_CONFIGURATION: IpmiConfigurationStageHandler(),
            # ProvisioningStage.FINALIZATION: FinalizationStageHandler(),
        }

    def create_provisioning_workflow(
        self,
        server_id: str,
        device_type: str,
        target_ipmi_ip: Optional[str] = None,
        rack_location: Optional[str] = None,
        subnet_mask: Optional[str] = None,
        gateway: Optional[str] = None,
        strategy: Optional[ProvisioningStrategy] = None,
        **kwargs,
    ) -> Workflow:
        """Create a provisioning workflow using the modular system."""

        # Create provisioning configuration
        config = ProvisioningConfig(
            server_id=server_id,
            device_type=device_type,
            target_ipmi_ip=target_ipmi_ip,
            rack_location=rack_location,
            subnet_mask=subnet_mask,
            gateway=gateway,
            **kwargs,
        )

        # Use default strategy if none provided
        if strategy is None:
            strategy = StandardProvisioningStrategy()

        # Create workflow
        workflow_id = f"provision_{server_id}"
        workflow = self.workflow_manager.create_workflow(workflow_id)

        # Add stages based on strategy
        stage_order = strategy.get_stage_order()

        for stage in stage_order:
            # Skip stages that should be skipped
            # Create a minimal context for stage decision making
            context = WorkflowContext(
                server_id=server_id,
                device_type=config.device_type,
                target_ipmi_ip=config.target_ipmi_ip,
                rack_location=config.rack_location,
                maas_client=None,  # Will be set during execution
                db_helper=None,  # Will be set during execution
                gateway=config.gateway,
                subnet_mask=config.subnet_mask,
            )
            if strategy.should_skip_stage(stage, context):
                continue

            # Get stage handler
            handler = self.stage_handlers.get(stage)
            if handler is None:
                logger.warning(
                    f"No handler available for stage {stage.value}, skipping"
                )
                continue

            # Create workflow step
            step = WorkflowStep(
                name=stage.value,
                description=f"Execute {stage.value} stage",
                function=lambda ctx, h=handler, c=config: self._execute_stage(
                    ctx, h, c
                ),
                timeout=self._get_stage_timeout(stage),
                retry_count=self._get_stage_retry_count(stage),
            )

            workflow.add_step(step)

        return workflow

    def _execute_stage(
        self,
        context: WorkflowContext,
        handler: ProvisioningStageHandler,
        config: ProvisioningConfig,
    ) -> Dict[str, Any]:
        """Execute a provisioning stage."""
        stage = handler.get_stage()
        logger.info(f"Executing stage {stage.value} for server {config.server_id}")

        # Validate prerequisites
        if not handler.validate_prerequisites(context):
            raise ValueError(f"Prerequisites not met for stage {stage.value}")

        # Execute the stage
        result = handler.execute(context, config)

        # Handle result
        if not result.success:
            raise Exception(f"Stage {stage.value} failed: {result.error_message}")

        logger.info(
            f"Stage {stage.value} completed successfully for server {config.server_id}"
        )
        return result.data

    def _get_stage_timeout(self, stage: ProvisioningStage) -> int:
        """Get timeout for a specific stage."""
        timeouts = {
            ProvisioningStage.COMMISSIONING: 1800,  # 30 minutes
            ProvisioningStage.NETWORK_SETUP: 300,  # 5 minutes
            ProvisioningStage.HARDWARE_DISCOVERY: 600,  # 10 minutes
            ProvisioningStage.BIOS_CONFIGURATION: 600,  # 10 minutes
            ProvisioningStage.IPMI_CONFIGURATION: 300,  # 5 minutes
            ProvisioningStage.FINALIZATION: 180,  # 3 minutes
        }
        return timeouts.get(stage, 300)  # Default 5 minutes

    def _get_stage_retry_count(self, stage: ProvisioningStage) -> int:
        """Get retry count for a specific stage."""
        retry_counts = {
            ProvisioningStage.COMMISSIONING: 2,
            ProvisioningStage.NETWORK_SETUP: 3,
            ProvisioningStage.HARDWARE_DISCOVERY: 2,
            ProvisioningStage.BIOS_CONFIGURATION: 2,
            ProvisioningStage.IPMI_CONFIGURATION: 3,
            ProvisioningStage.FINALIZATION: 1,
        }
        return retry_counts.get(stage, 1)  # Default 1 retry
