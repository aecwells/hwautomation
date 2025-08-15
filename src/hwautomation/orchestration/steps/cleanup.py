"""Cleanup workflow steps.

This module provides steps for cleanup operations after workflow completion,
including temporary file cleanup, connection cleanup, and resource cleanup.
"""

import os
import tempfile
from pathlib import Path
from typing import List

from hwautomation.logging import get_logger

from ..workflows.base import (
    BaseWorkflowStep,
    StepContext,
    StepExecutionResult,
)

logger = get_logger(__name__)


class CleanupTempFilesStep(BaseWorkflowStep):
    """Step to clean up temporary files created during workflow."""

    def __init__(self):
        super().__init__(
            name="cleanup_temp_files",
            description="Clean up temporary files and directories",
        )

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Clean up temporary files."""
        try:
            context.add_sub_task("Cleaning up temporary files")

            cleaned_files = []

            # Clean up firmware files if they exist
            firmware_files = context.get_data("firmware_files", [])
            for file_path in firmware_files:
                if os.path.exists(file_path) and "/tmp/" in file_path:
                    try:
                        os.remove(file_path)
                        cleaned_files.append(file_path)
                        logger.debug(f"Removed temporary file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove {file_path}: {e}")

            # Clean up BIOS config files if they exist
            bios_files = context.get_data("temp_bios_files", [])
            for file_path in bios_files:
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        cleaned_files.append(file_path)
                        logger.debug(f"Removed temporary BIOS file: {file_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove {file_path}: {e}")

            # Clean up any temporary directories
            temp_dirs = context.get_data("temp_directories", [])
            for dir_path in temp_dirs:
                if os.path.exists(dir_path):
                    try:
                        os.rmdir(dir_path)
                        cleaned_files.append(dir_path)
                        logger.debug(f"Removed temporary directory: {dir_path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove directory {dir_path}: {e}")

            if cleaned_files:
                context.add_sub_task(
                    f"Cleaned up {len(cleaned_files)} temporary files/directories"
                )
            else:
                context.add_sub_task("No temporary files to clean up")

            return StepExecutionResult.success(
                "Temporary file cleanup completed", {"cleaned_files": cleaned_files}
            )

        except Exception as e:
            # Don't fail the workflow for cleanup issues
            logger.warning(f"Cleanup failed: {e}")
            return StepExecutionResult.success(
                f"Cleanup completed with warnings: {e}", {"warnings": [str(e)]}
            )


class CleanupConnectionsStep(BaseWorkflowStep):
    """Step to clean up network connections and sessions."""

    def __init__(self):
        super().__init__(
            name="cleanup_connections",
            description="Clean up network connections and sessions",
        )

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Clean up connections."""
        try:
            context.add_sub_task("Cleaning up network connections")

            cleaned_connections = []

            # Close SSH connections if they exist
            ssh_clients = context.get_data("ssh_clients", [])
            for client in ssh_clients:
                try:
                    if hasattr(client, "close"):
                        client.close()
                        cleaned_connections.append("SSH connection")
                except Exception as e:
                    logger.warning(f"Failed to close SSH connection: {e}")

            # Close IPMI sessions if they exist
            ipmi_sessions = context.get_data("ipmi_sessions", [])
            for session in ipmi_sessions:
                try:
                    if hasattr(session, "close"):
                        session.close()
                        cleaned_connections.append("IPMI session")
                except Exception as e:
                    logger.warning(f"Failed to close IPMI session: {e}")

            # Close Redfish sessions if they exist
            redfish_sessions = context.get_data("redfish_sessions", [])
            for session in redfish_sessions:
                try:
                    if hasattr(session, "logout"):
                        session.logout()
                        cleaned_connections.append("Redfish session")
                except Exception as e:
                    logger.warning(f"Failed to close Redfish session: {e}")

            if cleaned_connections:
                context.add_sub_task(f"Closed {len(cleaned_connections)} connections")
            else:
                context.add_sub_task("No active connections to clean up")

            return StepExecutionResult.success(
                "Connection cleanup completed",
                {"cleaned_connections": cleaned_connections},
            )

        except Exception as e:
            # Don't fail the workflow for cleanup issues
            logger.warning(f"Connection cleanup failed: {e}")
            return StepExecutionResult.success(
                f"Connection cleanup completed with warnings: {e}",
                {"warnings": [str(e)]},
            )


class RecordWorkflowCompletionStep(BaseWorkflowStep):
    """Step to record workflow completion in database."""

    def __init__(self):
        super().__init__(
            name="record_workflow_completion",
            description="Record workflow completion status in database",
        )

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Record workflow completion."""
        try:
            import os
            from datetime import datetime

            from ...database.helper import DbHelper

            context.add_sub_task("Recording workflow completion")

            # Use DATABASE_PATH from environment, defaulting to data/hw_automation.db
            db_path = os.getenv("DATABASE_PATH", "data/hw_automation.db")
            db_helper = DbHelper(db_path)

            # Record workflow completion time
            db_helper.updateserverinfo(
                context.server_id, "workflow_completed_at", datetime.now().isoformat()
            )

            # Record workflow status
            db_helper.updateserverinfo(
                context.server_id, "workflow_status", "completed"
            )

            # Record any errors that occurred
            if context.errors:
                db_helper.updateserverinfo(
                    context.server_id, "workflow_errors", "; ".join(context.errors)
                )

            # Record sub-tasks completed
            if context.sub_tasks:
                db_helper.updateserverinfo(
                    context.server_id,
                    "workflow_subtasks_completed",
                    str(len(context.sub_tasks)),
                )

            return StepExecutionResult.success(
                "Workflow completion recorded", {"database_updated": True}
            )

        except Exception as e:
            # Don't fail the workflow for database recording issues
            logger.warning(f"Failed to record workflow completion: {e}")
            return StepExecutionResult.success(
                f"Workflow completion recording failed: {e}", {"warnings": [str(e)]}
            )
