"""
Commissioning stage handler.

Handles server commissioning through MaaS.
"""

import time
from typing import Any, Dict

from ...logging import get_logger
from ..exceptions import CommissioningError
from ..workflow_manager import WorkflowContext
from .base import (
    ProvisioningConfig,
    ProvisioningStage,
    ProvisioningStageHandler,
    StageResult,
)

logger = get_logger(__name__)


class CommissioningStageHandler(ProvisioningStageHandler):
    """Handles server commissioning through MaaS."""

    def get_stage(self) -> ProvisioningStage:
        """Get the stage this handler manages."""
        return ProvisioningStage.COMMISSIONING

    def validate_prerequisites(self, context: WorkflowContext) -> bool:
        """Validate that prerequisites for commissioning are met."""
        return (
            context.maas_client is not None
            and context.server_id is not None
            and context.db_helper is not None
        )

    def execute(
        self, context: WorkflowContext, config: ProvisioningConfig
    ) -> StageResult:
        """Execute server commissioning."""
        logger.info(f"Starting commissioning for server {config.server_id}")

        try:
            # Create database entry if it doesn't exist
            self._ensure_database_entry(context, config)

            # Determine if force commissioning is needed
            should_force_commission = self._should_force_commission(context, config)

            # Start commissioning process
            result = self._start_commissioning(context, config, should_force_commission)

            # Wait for commissioning to complete
            commissioning_result = self._wait_for_commissioning(context, config)

            return StageResult(
                success=True,
                stage=self.get_stage(),
                data={
                    "status": "commissioned",
                    "machine_info": commissioning_result,
                    "forced": should_force_commission,
                },
                next_stage=ProvisioningStage.NETWORK_SETUP,
            )

        except Exception as e:
            logger.error(f"Commissioning failed for {config.server_id}: {e}")
            self._update_error_status(context, config, str(e))
            return StageResult(
                success=False,
                stage=self.get_stage(),
                data={},
                error_message=str(e),
            )

    def _ensure_database_entry(
        self, context: WorkflowContext, config: ProvisioningConfig
    ):
        """Ensure database entry exists for server."""
        context.report_sub_task("Creating database entry")

        if context.db_helper:
            if not context.db_helper.checkifserveridexists(config.server_id)[0]:
                context.db_helper.createrowforserver(config.server_id)
                logger.info(f"Created database entry for server {config.server_id}")

            # Update initial status
            context.db_helper.updateserverinfo(
                config.server_id, "status_name", "Commissioning"
            )
            context.db_helper.updateserverinfo(config.server_id, "is_ready", "FALSE")
            context.db_helper.updateserverinfo(
                config.server_id, "device_type", config.device_type
            )

    def _should_force_commission(
        self, context: WorkflowContext, config: ProvisioningConfig
    ) -> bool:
        """Determine if force commissioning is needed."""
        try:
            # Get current server info from MaaS
            server_info = context.maas_client.get_machine_info(config.server_id)
            if not server_info:
                logger.info(
                    f"Server {config.server_id} not found in MaaS - normal commissioning"
                )
                return False

            current_status = server_info.get("status_name", "Unknown")
            logger.info(f"Server {config.server_id} current status: {current_status}")

            # Check for problematic states that require force recommissioning
            force_states = ["Failed commissioning", "Failed testing", "Broken"]
            return current_status in force_states

        except Exception as e:
            logger.warning(
                f"Could not determine current status for {config.server_id}: {e}"
            )
            return False

    def _start_commissioning(
        self, context: WorkflowContext, config: ProvisioningConfig, force: bool
    ) -> Dict[str, Any]:
        """Start the commissioning process."""
        if force:
            context.report_sub_task("Force commissioning server")
            logger.info(f"Force commissioning server {config.server_id}")
            return context.maas_client.force_commission_machine(config.server_id)
        else:
            context.report_sub_task("Starting normal commissioning")
            logger.info(f"Normal commissioning server {config.server_id}")
            return context.maas_client.commission_machine(config.server_id)

    def _wait_for_commissioning(
        self,
        context: WorkflowContext,
        config: ProvisioningConfig,
        timeout_seconds: int = 1800,  # 30 minutes
    ) -> Dict[str, Any]:
        """Wait for commissioning to complete."""
        context.report_sub_task("Waiting for commissioning to complete")

        timeout = time.time() + timeout_seconds
        while time.time() < timeout:
            status = context.maas_client.get_machine_status(config.server_id)
            context.report_sub_task(f"Commissioning status: {status}")

            if status in ["Commissioned", "Ready"]:
                logger.info(
                    f"Server {config.server_id} commissioned successfully (status: {status})"
                )
                context.report_sub_task("Commissioning completed successfully")

                # Update database with successful commissioning
                if context.db_helper:
                    context.db_helper.updateserverinfo(
                        config.server_id, "status_name", "Commissioned"
                    )
                    context.db_helper.updateserverinfo(
                        config.server_id, "is_ready", "TRUE"
                    )

                # Get machine info for return
                return context.maas_client.get_machine_info(config.server_id)

            elif status == "Failed commissioning":
                self._update_error_status(context, config, "Failed commissioning")
                raise CommissioningError(f"Commissioning failed for {config.server_id}")

            elif status == "Commissioning":
                logger.info(f"Server {config.server_id} still commissioning...")
            else:
                logger.info(
                    f"Server {config.server_id} status: {status} - waiting for completion..."
                )

            time.sleep(30)  # Check every 30 seconds

        # Commissioning timeout
        self._update_error_status(context, config, "Commissioning timeout")
        raise CommissioningError(f"Commissioning timeout for {config.server_id}")

    def _update_error_status(
        self, context: WorkflowContext, config: ProvisioningConfig, error: str
    ):
        """Update database with error status."""
        if context.db_helper:
            context.db_helper.updateserverinfo(
                config.server_id, "status_name", f"Error: {error}"
            )
            context.db_helper.updateserverinfo(config.server_id, "is_ready", "FALSE")
