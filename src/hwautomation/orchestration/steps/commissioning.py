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

        # Check if we're in development/mock mode
        dev_config = config.get("development", {})
        mock_mode = (
            dev_config.get("mock_services", False)
            or config.get("DEVELOPMENT_MODE", False)
            or config.get("MOCK_MAAS", False)
        )

        if mock_mode:
            context.add_sub_task("Running in development/mock mode")
            return True

        # Check MaaS configuration in nested structure
        maas_config = config.get("maas", {})
        required_maas_keys = ["url", "consumer_key", "token_key", "token_secret"]

        for key in required_maas_keys:
            if not maas_config.get(key):
                context.add_error(f"Missing MaaS configuration: maas.{key}")
                return False

        return True

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Select an appropriate machine for commissioning."""
        try:
            config = load_config()

            # Check if we're in development/mock mode
            dev_config = config.get("development", {})
            mock_mode = dev_config.get("mock_services", False) or config.get(
                "MOCK_MAAS", False
            )

            if mock_mode:
                import time

                context.add_sub_task("Running in development/mock mode")
                time.sleep(2)  # Small delay for debugging visibility

                # Generate mock machine data
                server_id = context.get_data("server_id", "mock-server")
                mock_machine = {
                    "system_id": f"mock-{server_id}",
                    "hostname": f"mock-host-{server_id}",
                    "status_name": "Available",
                    "architecture": "amd64",
                    "memory": 16384,
                    "cpu_count": 4,
                }

                # Store machine information in context
                context.set_data("machine_id", mock_machine["system_id"])
                context.set_data("machine_hostname", mock_machine["hostname"])
                context.set_data("machine_status", mock_machine["status_name"])
                context.set_data("machine_architecture", mock_machine["architecture"])
                context.set_data("selected_machine_id", mock_machine["system_id"])
                context.set_data("selected_machine_name", mock_machine["hostname"])

                self.logger.info(
                    f"Mock mode: Selected machine {mock_machine['system_id']} for commissioning"
                )

                return StepExecutionResult.success(
                    f"Mock mode: Selected machine {mock_machine['system_id']}",
                    {
                        "machine_id": mock_machine["system_id"],
                        "machine_info": mock_machine,
                    },
                )

            context.add_sub_task("Initializing MaaS client")

            # Initialize MaaS client
            maas_config = config.get("maas", {})
            self.maas_client = MaasClient(
                host=maas_config["url"],
                consumer_key=maas_config["consumer_key"],
                consumer_token=maas_config["token_key"],
                secret=maas_config["token_secret"],
            )

            # Initialize device selection service
            self.device_service = DeviceSelectionService(self.maas_client)

            context.add_sub_task("Selecting available machine")

            # Create filter for available machines
            machine_filter = MachineFilter(
                status_category=MachineStatus.AVAILABLE,
                min_memory_gb=8,  # Minimum requirements
                min_cpu_count=2,
            )

            # Get available machines
            machines = self.device_service.list_available_machines(machine_filter)

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
                maas_config = config["maas"]
                self.maas_client = MaasClient(
                    host=maas_config["url"],
                    consumer_key=maas_config["consumer_key"],
                    consumer_token=maas_config["token_key"],
                    secret=maas_config["token_secret"],
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
                maas_config = config["maas"]
                self.maas_client = MaasClient(
                    host=maas_config["url"],
                    consumer_key=maas_config["consumer_key"],
                    consumer_token=maas_config["token_key"],
                    secret=maas_config["token_secret"],
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
            elif status in [
                "Failed commissioning",
                "Failed deployment",
                "Failed testing",
                "Broken",
            ]:
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
            # Use DATABASE_PATH from environment, defaulting to data/hw_automation.db
            import os
            db_path = os.getenv("DATABASE_PATH", "data/hw_automation.db")
            db_helper = DbHelper(db_path)

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
