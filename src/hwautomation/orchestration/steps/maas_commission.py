"""MaaS commission workflow steps.

This module provides steps for MaaS commissioning operations,
including machine commissioning, status monitoring, and deployment.
"""

import time
from typing import Dict, Optional

from hwautomation.logging import get_logger

from ...maas.client import MaasClient
from ...utils.env_config import load_config
from ..workflows.base import (
    BaseWorkflowStep,
    ConditionalWorkflowStep,
    RetryableWorkflowStep,
    StepContext,
    StepExecutionResult,
)

logger = get_logger(__name__)


class CommissionMachineStep(RetryableWorkflowStep):
    """Step to commission a selected MaaS machine."""

    def __init__(self):
        super().__init__(
            name="commission_machine",
            description="Commission selected MaaS machine",
            max_retries=3,
            retry_delay=30.0,
        )
        self.maas_client = None

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate machine is selected for commissioning."""
        machine_id = context.get_data("selected_machine_id")
        if not machine_id:
            context.add_error("No machine selected for commissioning")
            return False
        return True

    def _execute_with_retry(self, context: StepContext) -> StepExecutionResult:
        """Commission machine with retry logic."""
        try:
            context.add_sub_task("Starting machine commissioning")

            # Initialize MaaS client
            config = load_config()
            maas_config = config.get("maas", {})
            self.maas_client = MaasClient(
                url=maas_config["url"],
                consumer_key=maas_config["consumer_key"],
                token_key=maas_config["token_key"],
                token_secret=maas_config["token_secret"],
            )

            machine_id = context.get_data("selected_machine_id")
            machine_name = context.get_data("selected_machine_name", machine_id)

            context.add_sub_task(f"Commissioning machine: {machine_name}")

            # Start commissioning
            commission_result = self.maas_client.commission_machine(machine_id)

            if not commission_result.success:
                return StepExecutionResult.retry(
                    f"Failed to start commissioning: {commission_result.error_message}"
                )

            context.set_data("commissioning_started", True)
            context.add_sub_task("Machine commissioning started successfully")

            return StepExecutionResult.success(
                f"Machine {machine_name} commissioning started",
                {"commission_result": commission_result},
            )

        except Exception as e:
            return StepExecutionResult.retry(f"Commission operation failed: {e}")


class MonitorCommissioningStep(RetryableWorkflowStep):
    """Step to monitor commissioning progress."""

    def __init__(self):
        super().__init__(
            name="monitor_commissioning",
            description="Monitor machine commissioning progress",
            max_retries=20,  # Allow more retries for long-running commissioning
            retry_delay=60.0,  # Check every minute
        )
        self.maas_client = None

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate commissioning has started."""
        if not context.get_data("commissioning_started"):
            context.add_error("Machine commissioning not started")
            return False
        return True

    def _execute_with_retry(self, context: StepContext) -> StepExecutionResult:
        """Monitor commissioning with retry logic."""
        try:
            # Initialize MaaS client
            config = load_config()
            maas_config = config.get("maas", {})
            self.maas_client = MaasClient(
                url=maas_config["url"],
                consumer_key=maas_config["consumer_key"],
                token_key=maas_config["token_key"],
                token_secret=maas_config["token_secret"],
            )

            machine_id = context.get_data("selected_machine_id")
            machine_name = context.get_data("selected_machine_name", machine_id)

            context.add_sub_task(f"Checking commissioning status for {machine_name}")

            # Get machine status
            machine_status = self.maas_client.get_machine_status(machine_id)

            if not machine_status.success:
                return StepExecutionResult.retry(
                    f"Failed to get machine status: {machine_status.error_message}"
                )

            status = machine_status.status
            context.add_sub_task(f"Machine status: {status}")

            # Check if commissioning is complete
            if status == "Ready":
                context.set_data("commissioning_completed", True)
                context.set_data("machine_status", "Ready")
                context.add_sub_task("Machine commissioning completed successfully")

                return StepExecutionResult.success(
                    f"Machine {machine_name} commissioned successfully",
                    {"final_status": status},
                )

            elif status in ["Failed", "Broken"]:
                return StepExecutionResult.failure(
                    f"Machine commissioning failed with status: {status}"
                )

            elif status in ["Commissioning", "Testing"]:
                # Still in progress, continue monitoring
                return StepExecutionResult.retry(
                    f"Machine commissioning in progress: {status}"
                )

            else:
                # Unexpected status
                return StepExecutionResult.retry(f"Unexpected machine status: {status}")

        except Exception as e:
            return StepExecutionResult.retry(f"Status monitoring failed: {e}")


class DeployMachineStep(ConditionalWorkflowStep):
    """Step to deploy the commissioned machine (optional)."""

    def __init__(self):
        super().__init__(
            name="deploy_machine",
            description="Deploy commissioned machine if requested",
        )
        self.maas_client = None

    def should_execute(self, context: StepContext) -> bool:
        """Check if machine deployment is requested."""
        return context.get_data("auto_deploy", False)

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate machine is ready for deployment."""
        if not context.get_data("commissioning_completed"):
            context.add_error("Machine commissioning not completed")
            return False
        return True

    def _execute_conditional(self, context: StepContext) -> StepExecutionResult:
        """Deploy the machine."""
        try:
            context.add_sub_task("Starting machine deployment")

            # Initialize MaaS client
            config = load_config()
            maas_config = config.get("maas", {})
            self.maas_client = MaasClient(
                url=maas_config["url"],
                consumer_key=maas_config["consumer_key"],
                token_key=maas_config["token_key"],
                token_secret=maas_config["token_secret"],
            )

            machine_id = context.get_data("selected_machine_id")
            machine_name = context.get_data("selected_machine_name", machine_id)

            context.add_sub_task(f"Deploying machine: {machine_name}")

            # Start deployment
            deploy_result = self.maas_client.deploy_machine(
                machine_id, distro_series=context.get_data("deploy_os", "focal")
            )

            if not deploy_result.success:
                return StepExecutionResult.failure(
                    f"Failed to deploy machine: {deploy_result.error_message}"
                )

            context.set_data("deployment_started", True)
            context.add_sub_task("Machine deployment started successfully")

            return StepExecutionResult.success(
                f"Machine {machine_name} deployment started",
                {"deploy_result": deploy_result},
            )

        except Exception as e:
            return StepExecutionResult.failure(f"Machine deployment failed: {e}")


class RecordMaasInfoStep(BaseWorkflowStep):
    """Step to record MaaS machine information in database."""

    def __init__(self):
        super().__init__(
            name="record_maas_info",
            description="Record MaaS machine information in database",
        )

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Record MaaS information."""
        try:
            import os

            from ...database.helper import DbHelper

            context.add_sub_task("Recording MaaS machine information")

            # Use DATABASE_PATH from environment, defaulting to data/hw_automation.db
            db_path = os.getenv("DATABASE_PATH", "data/hw_automation.db")
            db_helper = DbHelper(db_path)

            # Record MaaS machine ID
            machine_id = context.get_data("selected_machine_id")
            if machine_id:
                db_helper.updateserverinfo(
                    context.server_id, "maas_machine_id", machine_id
                )

            # Record machine name
            machine_name = context.get_data("selected_machine_name")
            if machine_name:
                db_helper.updateserverinfo(
                    context.server_id, "maas_machine_name", machine_name
                )

            # Record commissioning status
            if context.get_data("commissioning_completed"):
                db_helper.updateserverinfo(
                    context.server_id, "maas_commissioning_status", "completed"
                )

            # Record deployment status if applicable
            if context.get_data("deployment_started"):
                db_helper.updateserverinfo(
                    context.server_id, "maas_deployment_status", "started"
                )

            return StepExecutionResult.success(
                "MaaS information recorded", {"database_updated": True}
            )

        except Exception as e:
            return StepExecutionResult.failure(
                f"Failed to record MaaS information: {e}"
            )
