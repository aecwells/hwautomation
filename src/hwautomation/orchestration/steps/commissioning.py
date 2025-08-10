"""MaaS commissioning workflow steps.

This module provides steps for server commissioning through MaaS,
including machine selection, commissioning, and status monitoring.
"""

import time
from typing import Any, Dict, Optional

from hwautomation.logging import get_logger

from ...maas.client import MaasClient
from ...utils.env_config import load_config
from ..device_selection import DeviceSelectionService, MachineFilter, MachineStatus
from ..workflows.base import (
    BaseWorkflowStep,
    ConditionalWorkflowStep,
    RetryableWorkflowStep,
    StepContext,
    StepExecutionResult,
)

logger = get_logger(__name__)


class SelectMachineStep(BaseWorkflowStep):
    """Step to select a MaaS machine for commissioning."""

    def __init__(self):
        super().__init__(
            name="select_machine", description="Select MaaS machine for commissioning"
        )
        self.maas_client = None
        self.device_service = None

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate MaaS configuration is available."""
        config = load_config()
        required_keys = [
            "MAAS_URL",
            "MAAS_CONSUMER_KEY",
            "MAAS_TOKEN_KEY",
            "MAAS_TOKEN_SECRET",
        ]

        for key in required_keys:
            if not config.get(key):
                context.add_error(f"Missing MaaS configuration: {key}")
                return False

        return True

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Select an appropriate machine for commissioning."""
        try:
            context.add_sub_task("Initializing MaaS client")

            # Initialize MaaS client
            config = load_config()
            self.maas_client = MaasClient(
                url=config["MAAS_URL"],
                consumer_key=config["MAAS_CONSUMER_KEY"],
                token_key=config["MAAS_TOKEN_KEY"],
                token_secret=config["MAAS_TOKEN_SECRET"],
            )

            # Initialize device selection service
            self.device_service = DeviceSelectionService(self.maas_client)

            context.add_sub_task("Selecting available machine")

            # Create filter for available machines
            machine_filter = MachineFilter(
                status=MachineStatus.AVAILABLE,
                min_memory_gb=8,  # Minimum requirements
                min_cpu_cores=2,
            )

            # Get available machines
            machines = self.device_service.filter_machines(machine_filter)

            if not machines:
                return StepExecutionResult.failure(
                    "No available machines found matching criteria"
                )

            # Select the first available machine
            selected_machine = machines[0]

            # Store machine information in context
            context.set_data("machine_id", selected_machine["system_id"])
            context.set_data(
                "machine_hostname", selected_machine.get("hostname", "unknown")
            )
            context.set_data("machine_status", selected_machine.get("status_name"))
            context.set_data(
                "machine_architecture", selected_machine.get("architecture")
            )

            self.logger.info(
                f"Selected machine {selected_machine['system_id']} for commissioning"
            )

            return StepExecutionResult.success(
                f"Selected machine {selected_machine['system_id']}",
                {
                    "machine_id": selected_machine["system_id"],
                    "machine_info": selected_machine,
                },
            )

        except Exception as e:
            return StepExecutionResult.failure(f"Failed to select machine: {e}")


class CommissionMachineStep(RetryableWorkflowStep):
    """Step to commission a selected MaaS machine."""

    def __init__(self):
        super().__init__(
            name="commission_machine",
            description="Commission the selected MaaS machine",
            max_retries=2,
            retry_delay=5.0,
        )
        self.maas_client = None

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate machine ID is available."""
        machine_id = context.get_data("machine_id")
        if not machine_id:
            context.add_error("No machine ID available for commissioning")
            return False
        return True

    def _execute_with_retry(self, context: StepContext) -> StepExecutionResult:
        """Commission the machine with retry logic."""
        try:
            # Initialize MaaS client if needed
            if not self.maas_client:
                config = load_config()
                self.maas_client = MaasClient(
                    url=config["MAAS_URL"],
                    consumer_key=config["MAAS_CONSUMER_KEY"],
                    token_key=config["MAAS_TOKEN_KEY"],
                    token_secret=config["MAAS_TOKEN_SECRET"],
                )

            machine_id = context.get_data("machine_id")
            context.add_sub_task(f"Starting commissioning for machine {machine_id}")

            # Start commissioning
            result = self.maas_client.commission_machine(machine_id)

            if not result.get("success", False):
                return StepExecutionResult.retry(
                    f"Commissioning failed: {result.get('error', 'Unknown error')}"
                )

            context.add_sub_task("Commissioning started successfully")

            return StepExecutionResult.success(
                f"Commissioning started for machine {machine_id}",
                {"commissioning_result": result},
            )

        except Exception as e:
            return StepExecutionResult.retry(f"Exception during commissioning: {e}")


class WaitForCommissioningStep(RetryableWorkflowStep):
    """Step to wait for commissioning to complete."""

    def __init__(self, timeout_minutes: int = 30):
        super().__init__(
            name="wait_for_commissioning",
            description="Wait for machine commissioning to complete",
            max_retries=int(timeout_minutes * 60 / 30),  # Check every 30 seconds
            retry_delay=30.0,
        )
        self.maas_client = None
        self.timeout_minutes = timeout_minutes

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate machine ID is available."""
        machine_id = context.get_data("machine_id")
        if not machine_id:
            context.add_error("No machine ID available for status checking")
            return False
        return True

    def _execute_with_retry(self, context: StepContext) -> StepExecutionResult:
        """Check commissioning status with retry logic."""
        try:
            # Initialize MaaS client if needed
            if not self.maas_client:
                config = load_config()
                self.maas_client = MaasClient(
                    url=config["MAAS_URL"],
                    consumer_key=config["MAAS_CONSUMER_KEY"],
                    token_key=config["MAAS_TOKEN_KEY"],
                    token_secret=config["MAAS_TOKEN_SECRET"],
                )

            machine_id = context.get_data("machine_id")
            context.add_sub_task(f"Checking commissioning status for {machine_id}")

            # Get machine status
            machine_info = self.maas_client.get_machine(machine_id)

            if not machine_info:
                return StepExecutionResult.retry("Failed to get machine information")

            status = machine_info.get("status_name", "Unknown")
            status_message = machine_info.get("status_message", "")

            context.add_sub_task(f"Machine status: {status}")

            # Check for completion
            if status in ["Ready", "Commissioned"]:
                context.add_sub_task("Commissioning completed successfully")

                # Update context with commissioned machine info
                context.set_data("machine_status", status)
                context.set_data("commissioned_machine_info", machine_info)

                # Extract IP information if available
                ip_addresses = machine_info.get("ip_addresses", [])
                if ip_addresses:
                    context.server_ip = ip_addresses[0]
                    context.set_data("server_ip", ip_addresses[0])

                return StepExecutionResult.success(
                    f"Machine {machine_id} commissioned successfully",
                    {
                        "final_status": status,
                        "machine_info": machine_info,
                        "ip_addresses": ip_addresses,
                    },
                )

            # Check for failure states
            elif status in ["Failed commissioning", "Failed deployment", "Broken"]:
                return StepExecutionResult.failure(
                    f"Commissioning failed with status: {status} - {status_message}"
                )

            # Still in progress
            elif status in ["Commissioning", "Testing", "Deploying"]:
                return StepExecutionResult.retry(f"Commissioning in progress: {status}")

            # Unknown status - keep waiting
            else:
                return StepExecutionResult.retry(
                    f"Waiting for commissioning, current status: {status}"
                )

        except Exception as e:
            return StepExecutionResult.retry(
                f"Exception checking commissioning status: {e}"
            )


class RecordCommissioningStep(BaseWorkflowStep):
    """Step to record commissioning results in the database."""

    def __init__(self):
        super().__init__(
            name="record_commissioning",
            description="Record commissioning results in database",
        )

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate required data is available."""
        machine_id = context.get_data("machine_id")
        if not machine_id:
            context.add_error("No machine ID available for database recording")
            return False
        return True

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Record commissioning information in the database."""
        try:
            from ...database.helper import DbHelper

            context.add_sub_task("Recording commissioning results in database")

            machine_id = context.get_data("machine_id")
            machine_info = context.get_data("commissioned_machine_info", {})

            # Initialize database helper
            db_helper = DbHelper()

            # Create or update server record
            db_helper.createrowforserver(context.server_id)

            # Update with commissioning information
            db_helper.updateserverinfo(context.server_id, "machine_id", machine_id)
            db_helper.updateserverinfo(context.server_id, "status_name", "Commissioned")

            # Update with hardware information if available
            if machine_info:
                if machine_info.get("hostname"):
                    db_helper.updateserverinfo(
                        context.server_id, "hostname", machine_info["hostname"]
                    )

                if machine_info.get("architecture"):
                    db_helper.updateserverinfo(
                        context.server_id, "architecture", machine_info["architecture"]
                    )

                # Store IP addresses
                ip_addresses = machine_info.get("ip_addresses", [])
                if ip_addresses:
                    db_helper.updateserverinfo(
                        context.server_id, "ip_addresses", ",".join(ip_addresses)
                    )

            return StepExecutionResult.success(
                f"Commissioning results recorded for server {context.server_id}",
                {"database_updated": True},
            )

        except Exception as e:
            return StepExecutionResult.failure(
                f"Failed to record commissioning results: {e}"
            )
