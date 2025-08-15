"""Firmware update workflow steps.

This module provides steps for firmware update operations,
including firmware validation, downloading, and updating.
"""

import os
from typing import Dict, Optional

from hwautomation.logging import get_logger

from ...hardware.firmware import FirmwareManager
from ...utils.network import SSHClient
from ..workflows.base import (
    BaseWorkflowStep,
    ConditionalWorkflowStep,
    RetryableWorkflowStep,
    StepContext,
    StepExecutionResult,
)

logger = get_logger(__name__)


class ValidateFirmwareStep(BaseWorkflowStep):
    """Step to validate firmware requirements and availability."""

    def __init__(self):
        super().__init__(
            name="validate_firmware",
            description="Validate firmware requirements and availability",
        )

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate required information is available."""
        if not context.manufacturer:
            context.add_error("Server manufacturer required for firmware validation")
            return False

        if not context.model:
            context.add_error("Server model required for firmware validation")
            return False

        return True

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Validate firmware requirements."""
        try:
            context.add_sub_task("Validating firmware requirements")

            firmware_manager = FirmwareManager()

            # Check if firmware is available for this server
            available_firmware = firmware_manager.get_available_firmware(
                manufacturer=context.manufacturer, model=context.model
            )

            if not available_firmware:
                return StepExecutionResult.skip(
                    f"No firmware available for {context.manufacturer} {context.model}"
                )

            context.set_data("available_firmware", available_firmware)
            context.add_sub_task(f"Found {len(available_firmware)} firmware packages")

            return StepExecutionResult.success(
                "Firmware validation completed",
                {"available_firmware": len(available_firmware)},
            )

        except Exception as e:
            return StepExecutionResult.failure(f"Firmware validation failed: {e}")


class DownloadFirmwareStep(RetryableWorkflowStep):
    """Step to download required firmware packages."""

    def __init__(self):
        super().__init__(
            name="download_firmware",
            description="Download required firmware packages",
            max_retries=3,
            retry_delay=5.0,
        )

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate firmware is available for download."""
        available_firmware = context.get_data("available_firmware", [])
        if not available_firmware:
            context.add_error("No firmware available for download")
            return False
        return True

    def _execute_with_retry(self, context: StepContext) -> StepExecutionResult:
        """Download firmware with retry logic."""
        try:
            context.add_sub_task("Downloading firmware packages")

            firmware_manager = FirmwareManager()
            available_firmware = context.get_data("available_firmware", [])

            downloaded_files = []
            for firmware_info in available_firmware:
                context.add_sub_task(f"Downloading {firmware_info['name']}")

                download_result = firmware_manager.download_firmware(firmware_info)

                if not download_result.success:
                    return StepExecutionResult.retry(
                        f"Failed to download {firmware_info['name']}: {download_result.error}"
                    )

                downloaded_files.append(download_result.file_path)

            context.set_data("firmware_files", downloaded_files)
            context.add_sub_task(f"Downloaded {len(downloaded_files)} firmware files")

            return StepExecutionResult.success(
                "Firmware download completed", {"downloaded_files": downloaded_files}
            )

        except Exception as e:
            return StepExecutionResult.retry(f"Firmware download failed: {e}")


class UpdateFirmwareStep(RetryableWorkflowStep):
    """Step to update server firmware."""

    def __init__(self):
        super().__init__(
            name="update_firmware",
            description="Update server firmware",
            max_retries=2,
            retry_delay=30.0,
        )

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate firmware files are available."""
        firmware_files = context.get_data("firmware_files", [])
        if not firmware_files:
            context.add_error("No firmware files available for update")
            return False

        if not context.server_ip:
            context.add_error("Server IP required for firmware update")
            return False

        return True

    def _execute_with_retry(self, context: StepContext) -> StepExecutionResult:
        """Update firmware with retry logic."""
        try:
            context.add_sub_task("Starting firmware update process")

            firmware_manager = FirmwareManager()
            firmware_files = context.get_data("firmware_files", [])

            update_results = []
            for firmware_file in firmware_files:
                context.add_sub_task(
                    f"Updating firmware: {os.path.basename(firmware_file)}"
                )

                update_result = firmware_manager.update_firmware(
                    target_ip=context.server_ip,
                    ipmi_ip=context.ipmi_ip,
                    firmware_file=firmware_file,
                    manufacturer=context.manufacturer,
                )

                if not update_result.success:
                    return StepExecutionResult.retry(
                        f"Firmware update failed: {update_result.error}"
                    )

                update_results.append(update_result)
                context.add_sub_task(
                    f"Successfully updated: {os.path.basename(firmware_file)}"
                )

            context.set_data("firmware_update_results", update_results)

            return StepExecutionResult.success(
                "Firmware update completed successfully",
                {"updated_files": len(firmware_files)},
            )

        except Exception as e:
            return StepExecutionResult.retry(f"Firmware update failed: {e}")


class VerifyFirmwareStep(BaseWorkflowStep):
    """Step to verify firmware update success."""

    def __init__(self):
        super().__init__(
            name="verify_firmware",
            description="Verify firmware update success",
        )

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate firmware update results are available."""
        update_results = context.get_data("firmware_update_results", [])
        if not update_results:
            context.add_error("No firmware update results to verify")
            return False
        return True

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Verify firmware update."""
        try:
            context.add_sub_task("Verifying firmware update")

            firmware_manager = FirmwareManager()

            # Get current firmware versions
            current_versions = firmware_manager.get_firmware_versions(
                target_ip=context.server_ip,
                ipmi_ip=context.ipmi_ip,
                manufacturer=context.manufacturer,
            )

            if not current_versions.success:
                return StepExecutionResult.failure(
                    f"Failed to verify firmware versions: {current_versions.error}"
                )

            context.set_data("current_firmware_versions", current_versions.versions)
            context.add_sub_task("Firmware verification completed")

            return StepExecutionResult.success(
                "Firmware verification completed",
                {"firmware_versions": current_versions.versions},
            )

        except Exception as e:
            return StepExecutionResult.failure(f"Firmware verification failed: {e}")


class RecordFirmwareUpdateStep(BaseWorkflowStep):
    """Step to record firmware update results in database."""

    def __init__(self):
        super().__init__(
            name="record_firmware_update",
            description="Record firmware update results in database",
        )

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Record firmware update results."""
        try:
            import os

            from ...database.helper import DbHelper

            context.add_sub_task("Recording firmware update results")

            # Use DATABASE_PATH from environment, defaulting to data/hw_automation.db
            db_path = os.getenv("DATABASE_PATH", "data/hw_automation.db")
            db_helper = DbHelper(db_path)

            # Record firmware update completion
            db_helper.updateserverinfo(
                context.server_id, "firmware_update_status", "completed"
            )

            # Record current firmware versions
            firmware_versions = context.get_data("current_firmware_versions", {})
            if firmware_versions:
                for component, version in firmware_versions.items():
                    db_helper.updateserverinfo(
                        context.server_id, f"firmware_{component}_version", version
                    )

            # Record update timestamp
            from datetime import datetime

            db_helper.updateserverinfo(
                context.server_id, "firmware_last_updated", datetime.now().isoformat()
            )

            return StepExecutionResult.success(
                "Firmware update results recorded", {"database_updated": True}
            )

        except Exception as e:
            return StepExecutionResult.failure(
                f"Failed to record firmware update results: {e}"
            )
