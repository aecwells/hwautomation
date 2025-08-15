"""BIOS configuration workflow steps.

This module provides steps for BIOS configuration operations,
including pulling current settings, modifying configurations,
and pushing updated settings to servers.
"""

import json
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

from hwautomation.logging import get_logger

from ...hardware.bios import BiosConfigManager
from ...utils.network import SSHClient
from ..workflows.base import (
    BaseWorkflowStep,
    ConditionalWorkflowStep,
    RetryableWorkflowStep,
    StepContext,
    StepExecutionResult,
)

logger = get_logger(__name__)


class PullBiosConfigStep(BaseWorkflowStep):
    """Step to pull current BIOS configuration from the server."""

    def __init__(self):
        super().__init__(
            name="pull_bios_config",
            description="Pull current BIOS configuration from server",
        )
        self.bios_manager = None

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate required information is available."""
        if not context.server_ip:
            context.add_error("Server IP required for BIOS configuration")
            return False

        if not context.manufacturer:
            context.add_error("Server manufacturer required for BIOS configuration")
            return False

        return True

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Pull BIOS configuration from the server."""
        try:
            context.add_sub_task("Initializing BIOS configuration manager")

            # Initialize BIOS manager
            self.bios_manager = BiosConfigManager()

            context.add_sub_task(
                f"Pulling BIOS configuration from {context.manufacturer} server"
            )

            # Pull BIOS configuration based on vendor
            if context.manufacturer.lower() == "supermicro":
                config_result = self._pull_supermicro_config(context)
            elif context.manufacturer.lower() in ["hp", "hpe"]:
                config_result = self._pull_hp_config(context)
            elif context.manufacturer.lower() == "dell":
                config_result = self._pull_dell_config(context)
            else:
                return StepExecutionResult.failure(
                    f"BIOS configuration not supported for vendor: {context.manufacturer}"
                )

            if not config_result["success"]:
                return StepExecutionResult.failure(
                    f"Failed to pull BIOS configuration: {config_result.get('error', 'Unknown error')}"
                )

            # Store configuration in context
            context.set_data("current_bios_config", config_result["config"])
            context.set_data("bios_config_format", config_result["format"])
            context.set_data("bios_config_path", config_result.get("config_path"))

            context.add_sub_task("BIOS configuration retrieved successfully")

            return StepExecutionResult.success(
                "BIOS configuration pulled successfully", {"bios_config": config_result}
            )

        except Exception as e:
            return StepExecutionResult.failure(
                f"Failed to pull BIOS configuration: {e}"
            )

    def _pull_supermicro_config(self, context: StepContext) -> Dict[str, Any]:
        """Pull BIOS configuration from Supermicro server."""
        try:
            ssh_client = SSHClient(
                hostname=context.server_ip,
                username=context.get_data("ssh_username", "ubuntu"),
            )

            # Check if SUM tool is available
            check_result = ssh_client.execute_command("which sum")
            if not check_result["success"]:
                # Install SUM tool
                install_result = self._install_sum_tool(ssh_client)
                if not install_result:
                    return {"success": False, "error": "Failed to install SUM tool"}

            # Pull BIOS configuration using SUM
            config_path = "/tmp/current_bios_config.xml"
            sum_command = f"sum -c GetCurrentBiosCfg -o {config_path}"

            result = ssh_client.execute_command(sum_command)
            if not result["success"]:
                return {
                    "success": False,
                    "error": f"SUM command failed: {result.get('stderr', 'Unknown error')}",
                }

            # Download the configuration file
            local_config_path = tempfile.mktemp(suffix=".xml")
            download_result = ssh_client.download_file(config_path, local_config_path)

            if not download_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to download BIOS configuration",
                }

            # Read and parse configuration
            with open(local_config_path, "r") as f:
                config_content = f.read()

            return {
                "success": True,
                "config": config_content,
                "format": "xml",
                "config_path": local_config_path,
                "vendor": "supermicro",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _pull_hp_config(self, context: StepContext) -> Dict[str, Any]:
        """Pull BIOS configuration from HP/HPE server."""
        try:
            # HP servers typically use iLO or conrep
            # For now, return a placeholder
            return {
                "success": True,
                "config": "# HP BIOS configuration placeholder",
                "format": "text",
                "vendor": "hp",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _pull_dell_config(self, context: StepContext) -> Dict[str, Any]:
        """Pull BIOS configuration from Dell server."""
        try:
            # Dell servers typically use racadm or syscfg
            # For now, return a placeholder
            return {
                "success": True,
                "config": "# Dell BIOS configuration placeholder",
                "format": "text",
                "vendor": "dell",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _install_sum_tool(self, ssh_client: SSHClient) -> bool:
        """Install Supermicro SUM tool on the server."""
        try:
            # Download and install SUM tool
            commands = [
                "cd /tmp",
                "wget -q https://www.supermicro.com/SwDownload/UserInfo/SUM/SUM_2.3.0_Linux_x86_64_20200220.tar.gz",
                "tar -xzf SUM_2.3.0_Linux_x86_64_20200220.tar.gz",
                "cd SUM_2.3.0_Linux_x86_64",
                "chmod +x sum",
                "sudo cp sum /usr/local/bin/",
                "sudo chmod +x /usr/local/bin/sum",
            ]

            for command in commands:
                result = ssh_client.execute_command(command)
                if not result["success"]:
                    logger.warning(f"SUM installation command failed: {command}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Failed to install SUM tool: {e}")
            return False


class ModifyBiosConfigStep(BaseWorkflowStep):
    """Step to modify BIOS configuration based on device type."""

    def __init__(self):
        super().__init__(
            name="modify_bios_config",
            description="Modify BIOS configuration for device type",
        )
        self.bios_manager = None

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate required information is available."""
        if not context.device_type:
            context.add_error("Device type required for BIOS modification")
            return False

        current_config = context.get_data("current_bios_config")
        if not current_config:
            context.add_error("Current BIOS configuration required for modification")
            return False

        return True

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Modify BIOS configuration for the specified device type."""
        try:
            context.add_sub_task(
                f"Modifying BIOS configuration for device type: {context.device_type}"
            )

            # Initialize BIOS manager if needed
            if not self.bios_manager:
                self.bios_manager = BiosConfigManager()

            # Apply BIOS configuration for device type
            result = self.bios_manager.apply_bios_config_smart(
                device_type=context.device_type,
                target_ip=context.server_ip,
                username=context.get_data("ssh_username", "ubuntu"),
                password="",  # Using SSH key authentication
                dry_run=True,  # First run as dry run to get modified config
            )

            if not result.success:
                return StepExecutionResult.failure(
                    f"Failed to modify BIOS configuration: {result.error_message}"
                )

            # Store modified configuration
            context.set_data("modified_bios_config", result.config_data)
            context.set_data("bios_changes", result.changes_made)
            context.set_data("bios_modification_result", result)

            context.add_sub_task(
                f"BIOS configuration modified with {len(result.changes_made)} changes"
            )

            return StepExecutionResult.success(
                f"BIOS configuration modified for {context.device_type}",
                {
                    "modified_config": result.config_data,
                    "changes_made": result.changes_made,
                    "modification_result": result,
                },
            )

        except Exception as e:
            return StepExecutionResult.failure(
                f"Failed to modify BIOS configuration: {e}"
            )


class PushBiosConfigStep(RetryableWorkflowStep):
    """Step to push modified BIOS configuration to the server."""

    def __init__(self):
        super().__init__(
            name="push_bios_config",
            description="Push modified BIOS configuration to server",
            max_retries=2,
            retry_delay=5.0,
        )
        self.bios_manager = None

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate modified configuration is available."""
        modified_config = context.get_data("modified_bios_config")
        if not modified_config:
            context.add_error("Modified BIOS configuration required for pushing")
            return False

        return True

    def _execute_with_retry(self, context: StepContext) -> StepExecutionResult:
        """Push BIOS configuration with retry logic."""
        try:
            context.add_sub_task("Pushing modified BIOS configuration to server")

            # Initialize BIOS manager if needed
            if not self.bios_manager:
                self.bios_manager = BiosConfigManager()

            # Apply BIOS configuration (actual push)
            result = self.bios_manager.apply_bios_config_smart(
                device_type=context.device_type,
                target_ip=context.server_ip,
                username=context.get_data("ssh_username", "ubuntu"),
                password="",  # Using SSH key authentication
                dry_run=False,  # Actual configuration push
            )

            if not result.success:
                return StepExecutionResult.retry(
                    f"Failed to push BIOS configuration: {result.error_message}"
                )

            context.set_data("bios_push_result", result)
            context.add_sub_task("BIOS configuration pushed successfully")

            return StepExecutionResult.success(
                "BIOS configuration pushed successfully", {"push_result": result}
            )

        except Exception as e:
            return StepExecutionResult.retry(
                f"Exception pushing BIOS configuration: {e}"
            )


class VerifyBiosConfigStep(BaseWorkflowStep):
    """Step to verify BIOS configuration was applied correctly."""

    def __init__(self):
        super().__init__(
            name="verify_bios_config",
            description="Verify BIOS configuration was applied correctly",
        )

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate push result is available."""
        push_result = context.get_data("bios_push_result")
        if not push_result:
            context.add_error("BIOS push result required for verification")
            return False

        return True

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Verify BIOS configuration application."""
        try:
            context.add_sub_task("Verifying BIOS configuration application")

            push_result = context.get_data("bios_push_result")
            changes_made = context.get_data("bios_changes", [])

            # Check if changes were successfully applied
            if push_result.success and push_result.config_applied:
                context.add_sub_task(
                    f"BIOS configuration verified - {len(changes_made)} changes applied"
                )

                return StepExecutionResult.success(
                    "BIOS configuration verified successfully",
                    {
                        "verified": True,
                        "changes_applied": len(changes_made),
                        "verification_result": push_result,
                    },
                )
            else:
                return StepExecutionResult.failure(
                    f"BIOS configuration verification failed: {push_result.error_message}"
                )

        except Exception as e:
            return StepExecutionResult.failure(
                f"BIOS configuration verification failed: {e}"
            )


class RecordBiosConfigStep(BaseWorkflowStep):
    """Step to record BIOS configuration results in the database."""

    def __init__(self):
        super().__init__(
            name="record_bios_config",
            description="Record BIOS configuration results in database",
        )

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Record BIOS configuration information in the database."""
        try:
            import os
            from ...database.helper import DbHelper

            context.add_sub_task("Recording BIOS configuration results in database")

            # Use DATABASE_PATH from environment, defaulting to data/hw_automation.db
            db_path = os.getenv("DATABASE_PATH", "data/hw_automation.db")
            db_helper = DbHelper(db_path)

            # Record BIOS configuration status
            db_helper.updateserverinfo(context.server_id, "bios_configured", "true")
            db_helper.updateserverinfo(
                context.server_id, "device_type", context.device_type
            )

            # Record configuration details
            changes_made = context.get_data("bios_changes", [])
            if changes_made:
                db_helper.updateserverinfo(
                    context.server_id, "bios_changes_count", str(len(changes_made))
                )
                db_helper.updateserverinfo(
                    context.server_id, "bios_changes", json.dumps(changes_made)
                )

            # Record push result
            push_result = context.get_data("bios_push_result")
            if push_result:
                db_helper.updateserverinfo(
                    context.server_id, "bios_config_status", "applied"
                )
                if hasattr(push_result, "applied_at"):
                    db_helper.updateserverinfo(
                        context.server_id,
                        "bios_config_applied_at",
                        str(push_result.applied_at),
                    )

            return StepExecutionResult.success(
                f"BIOS configuration results recorded for server {context.server_id}",
                {"database_updated": True},
            )

        except Exception as e:
            return StepExecutionResult.failure(
                f"Failed to record BIOS configuration results: {e}"
            )
