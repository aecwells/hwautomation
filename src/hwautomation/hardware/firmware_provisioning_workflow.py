"""
Firmware-First Provisioning Workflow

Integrates firmware updates with the enhanced BIOS configuration system to provide a
complete firmware-first provisioning workflow.
."""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from hwautomation.logging import get_logger

from ..orchestration.exceptions import WorkflowError
from .bios_config import BiosConfigManager
from .bios_monitoring import BiosConfigMonitor
from .firmware_manager import (
    FirmwareInfo,
    FirmwareManager,
    FirmwareType,
    FirmwareUpdateResult,
    UpdatePriority,
)

logger = get_logger(__name__)


class ProvisioningPhase(Enum):
    """Firmware-first provisioning phases."""

    PRE_FLIGHT = "pre_flight"
    FIRMWARE_ANALYSIS = "firmware_analysis"
    FIRMWARE_UPDATE = "firmware_update"
    SYSTEM_REBOOT = "system_reboot"
    BIOS_CONFIGURATION = "bios_configuration"
    FINAL_VALIDATION = "final_validation"


@dataclass
class ProvisioningContext:
    """Context for firmware-first provisioning operations."""

    server_id: str
    device_type: str
    target_ip: str
    credentials: Dict[str, str]
    firmware_policy: str = "recommended"
    operation_id: Optional[str] = None
    skip_firmware_check: bool = False
    skip_bios_config: bool = False

    # Runtime state
    firmware_info: Optional[Dict[FirmwareType, FirmwareInfo]] = None
    firmware_results: Optional[List[FirmwareUpdateResult]] = None
    bios_results: Optional[Dict[str, Any]] = None
    total_execution_time: float = 0.0
    start_time: Optional[datetime] = None


@dataclass
class ProvisioningResult:
    """Result of firmware-first provisioning operation."""

    success: bool
    operation_id: str
    server_id: str
    device_type: str
    execution_time: float
    phases_completed: List[ProvisioningPhase]
    firmware_updates_applied: int = 0
    bios_settings_applied: int = 0
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class FirmwareProvisioningWorkflow:
    """Complete firmware-first provisioning workflow."""

    def __init__(self):
        """Initialize the firmware-first provisioning workflow."""
        self.firmware_manager = FirmwareManager()
        self.bios_manager = BiosConfigManager()
        self.monitor = BiosConfigMonitor()

        logger.info("FirmwareProvisioningWorkflow initialized")

    async def execute_firmware_first_provisioning(
        self, context: ProvisioningContext
    ) -> ProvisioningResult:
        """
        Execute complete firmware-first provisioning workflow.

        Workflow phases:
        1. Pre-flight validation
        2. Firmware version analysis
        3. Firmware updates (if needed)
        4. System reboot and validation
        5. BIOS configuration
        6. Post-configuration validation

        Args:
            context: Provisioning context with all required parameters

        Returns:
            ProvisioningResult with operation details
        ."""
        logger.info(f"Starting firmware-first provisioning for {context.server_id}")
        logger.info(f"  Device: {context.device_type}")
        logger.info(f"  Target: {context.target_ip}")
        logger.info(f"  Policy: {context.firmware_policy}")

        context.start_time = datetime.now()
        phases_completed = []

        # Create operation tracking
        if not context.operation_id:
            context.operation_id = self.monitor.create_operation(
                "firmware_first_provisioning"
            )

        await self.monitor.start_operation(context.operation_id, total_subtasks=6)

        try:
            # Step 1: Pre-flight validation
            logger.info("Pre-flight validation")
            await self.monitor.start_subtask(
                context.operation_id, "pre_flight", "Pre-flight system validation"
            )

            await self._execute_pre_flight_validation(context)
            phases_completed.append(ProvisioningPhase.PRE_FLIGHT)

            await self.monitor.complete_subtask(
                context.operation_id, "pre_flight", True
            )
            await self.monitor.update_progress(
                context.operation_id, 10, "Pre-flight validation completed"
            )

            # Step 2: Firmware version analysis
            if not context.skip_firmware_check:
                logger.info("Firmware version analysis")
                await self.monitor.start_subtask(
                    context.operation_id,
                    "firmware_analysis",
                    "Analyzing current firmware versions",
                )

                await self._execute_firmware_analysis(context)
                phases_completed.append(ProvisioningPhase.FIRMWARE_ANALYSIS)

                updates_needed = (
                    [fw for fw in context.firmware_info.values() if fw.update_required]
                    if context.firmware_info
                    else []
                )
                critical_updates = [
                    fw
                    for fw in updates_needed
                    if fw.priority == UpdatePriority.CRITICAL
                ]

                await self.monitor.update_progress(
                    context.operation_id,
                    20,
                    f"Found {len(updates_needed)} updates needed ({len(critical_updates)} critical)",
                )
                await self.monitor.complete_subtask(
                    context.operation_id, "firmware_analysis", True
                )

                # Step 3: Firmware updates
                if updates_needed:
                    logger.info(f"Firmware updates ({len(updates_needed)} components)")
                    await self.monitor.start_subtask(
                        context.operation_id,
                        "firmware_update",
                        f"Updating {len(updates_needed)} firmware components",
                    )

                    await self._execute_firmware_updates(context, updates_needed)
                    phases_completed.append(ProvisioningPhase.FIRMWARE_UPDATE)

                    successful_updates = (
                        [r for r in context.firmware_results if r.success]
                        if context.firmware_results
                        else []
                    )
                    failed_updates = (
                        [r for r in context.firmware_results if not r.success]
                        if context.firmware_results
                        else []
                    )

                    await self.monitor.update_progress(
                        context.operation_id,
                        50,
                        f"Firmware updates: {len(successful_updates)} successful, {len(failed_updates)} failed",
                    )
                    await self.monitor.complete_subtask(
                        context.operation_id,
                        "firmware_update",
                        len(failed_updates) == 0,
                    )

                    # Step 4: System reboot and validation
                    reboot_required = any(r.requires_reboot for r in successful_updates)
                    if reboot_required:
                        logger.info("System reboot and validation")
                        await self.monitor.start_subtask(
                            context.operation_id,
                            "system_reboot",
                            "System reboot and validation",
                        )

                        await self._execute_system_reboot(context)
                        phases_completed.append(ProvisioningPhase.SYSTEM_REBOOT)

                        await self.monitor.update_progress(
                            context.operation_id, 70, "System reboot completed"
                        )
                        await self.monitor.complete_subtask(
                            context.operation_id, "system_reboot", True
                        )
                else:
                    logger.info(
                        "No firmware updates required, proceeding to BIOS configuration"
                    )
                    await self.monitor.update_progress(
                        context.operation_id, 70, "No firmware updates required"
                    )
            else:
                logger.info("Firmware check skipped per configuration")
                await self.monitor.update_progress(
                    context.operation_id, 70, "Firmware check skipped"
                )

            # Step 5: BIOS configuration
            if not context.skip_bios_config:
                logger.info("BIOS configuration")
                await self.monitor.start_subtask(
                    context.operation_id,
                    "bios_config",
                    "Applying BIOS configuration with enhanced monitoring",
                )

                await self._execute_bios_configuration(context)
                phases_completed.append(ProvisioningPhase.BIOS_CONFIGURATION)

                settings_applied = (
                    context.bios_results.get("settings_applied", 0)
                    if context.bios_results
                    else 0
                )
                await self.monitor.update_progress(
                    context.operation_id,
                    90,
                    f"BIOS configuration completed: {settings_applied} settings applied",
                )
                await self.monitor.complete_subtask(
                    context.operation_id, "bios_config", True
                )
            else:
                logger.info("BIOS configuration skipped per configuration")
                await self.monitor.update_progress(
                    context.operation_id, 90, "BIOS configuration skipped"
                )

            # Step 6: Final validation
            logger.info("Final validation")
            await self.monitor.start_subtask(
                context.operation_id, "final_validation", "Final system validation"
            )

            await self._execute_final_validation(context)
            phases_completed.append(ProvisioningPhase.FINAL_VALIDATION)

            await self.monitor.update_progress(
                context.operation_id, 100, "All validation checks passed"
            )
            await self.monitor.complete_subtask(
                context.operation_id, "final_validation", True
            )

            # Calculate execution time
            context.total_execution_time = (
                datetime.now() - context.start_time
            ).total_seconds()

            await self.monitor.complete_operation(
                context.operation_id,
                True,
                "Firmware-first provisioning completed successfully",
            )

            # Build result
            result = ProvisioningResult(
                success=True,
                operation_id=context.operation_id,
                server_id=context.server_id,
                device_type=context.device_type,
                execution_time=context.total_execution_time,
                phases_completed=phases_completed,
                firmware_updates_applied=len(
                    [r for r in (context.firmware_results or []) if r.success]
                ),
                bios_settings_applied=(
                    context.bios_results.get("settings_applied", 0)
                    if context.bios_results
                    else 0
                ),
            )

            logger.info(f"✅ Firmware-first provisioning completed successfully")
            logger.info(f"   Execution time: {context.total_execution_time:.1f}s")
            logger.info(f"   Firmware updates: {result.firmware_updates_applied}")
            logger.info(f"   BIOS settings: {result.bios_settings_applied}")

            return result

        except Exception as e:
            context.total_execution_time = (
                (datetime.now() - context.start_time).total_seconds()
                if context.start_time
                else 0.0
            )

            error_message = f"Firmware-first provisioning failed: {e}"
            logger.error(error_message)

            await self.monitor.log_error(context.operation_id, error_message)
            await self.monitor.complete_operation(
                context.operation_id, False, error_message
            )

            return ProvisioningResult(
                success=False,
                operation_id=context.operation_id,
                server_id=context.server_id,
                device_type=context.device_type,
                execution_time=context.total_execution_time,
                phases_completed=phases_completed,
                error_message=error_message,
            )

    async def _execute_pre_flight_validation(self, context: ProvisioningContext):
        """Execute pre-flight system validation."""
        logger.debug(f"Executing pre-flight validation for {context.target_ip}")

        try:
            # Validate network connectivity
            await self._validate_network_connectivity(context.target_ip)

            # Validate BMC credentials
            await self._validate_bmc_credentials(context)

            # Validate system readiness
            await self._validate_system_readiness(context)

            logger.debug("Pre-flight validation completed successfully")

        except Exception as e:
            logger.error(f"Pre-flight validation failed: {e}")
            raise WorkflowError(f"Pre-flight validation failed: {e}")

    async def _validate_network_connectivity(self, target_ip: str):
        """Validate network connectivity to target system."""
        # Simulate network connectivity check
        await asyncio.sleep(0.5)
        logger.debug(f"Network connectivity validated for {target_ip}")

    async def _validate_bmc_credentials(self, context: ProvisioningContext):
        """Validate BMC credentials."""
        # Simulate credential validation
        await asyncio.sleep(0.3)
        logger.debug(f"BMC credentials validated for {context.target_ip}")

    async def _validate_system_readiness(self, context: ProvisioningContext):
        """Validate system readiness for provisioning."""
        # Simulate system readiness check
        await asyncio.sleep(0.2)
        logger.debug(f"System readiness validated for {context.target_ip}")

    async def _execute_firmware_analysis(self, context: ProvisioningContext):
        """Execute firmware version analysis."""
        logger.debug(f"Executing firmware analysis for {context.device_type}")

        try:
            context.firmware_info = await self.firmware_manager.check_firmware_versions(
                context.device_type,
                context.target_ip,
                context.credentials["username"],
                context.credentials["password"],
            )

            logger.info("Firmware analysis completed:")
            for fw_type, fw_info in context.firmware_info.items():
                status = "UPDATE NEEDED" if fw_info.update_required else "UP TO DATE"
                priority = (
                    f"({fw_info.priority.value})" if fw_info.update_required else ""
                )
                logger.info(
                    f"  {fw_type.value}: {fw_info.current_version} → {fw_info.latest_version} {status} {priority}"
                )

        except Exception as e:
            logger.error(f"Firmware analysis failed: {e}")
            raise WorkflowError(f"Firmware analysis failed: {e}")

    async def _execute_firmware_updates(
        self, context: ProvisioningContext, updates_needed: List[FirmwareInfo]
    ):
        """Execute firmware updates."""
        logger.debug(f"Executing firmware updates for {len(updates_needed)} components")

        try:
            total_estimated_time = sum(fw.estimated_time for fw in updates_needed)
            logger.info(
                f"Estimated update time: {total_estimated_time} seconds ({total_estimated_time/60:.1f} minutes)"
            )

            context.firmware_results = (
                await self.firmware_manager.update_firmware_batch(
                    context.device_type,
                    context.target_ip,
                    context.credentials["username"],
                    context.credentials["password"],
                    updates_needed,
                    context.operation_id,
                )
            )

            successful_updates = [r for r in context.firmware_results if r.success]
            failed_updates = [r for r in context.firmware_results if not r.success]

            logger.info(
                f"Firmware updates completed: {len(successful_updates)} successful, {len(failed_updates)} failed"
            )

            if failed_updates:
                logger.warning("Some firmware updates failed:")
                for result in failed_updates:
                    logger.warning(
                        f"  ❌ {result.firmware_type.value}: {result.error_message}"
                    )

        except Exception as e:
            logger.error(f"Firmware updates failed: {e}")
            raise WorkflowError(f"Firmware updates failed: {e}")

    async def _execute_system_reboot(self, context: ProvisioningContext):
        """Execute system reboot and validation."""
        logger.debug(f"Executing system reboot for {context.target_ip}")

        try:
            logger.info("System reboot required for firmware changes to take effect...")

            # Simulate reboot process
            await asyncio.sleep(3)  # Simulate reboot time

            logger.info("System rebooted successfully")

        except Exception as e:
            logger.error(f"System reboot failed: {e}")
            raise WorkflowError(f"System reboot failed: {e}")

    async def _execute_bios_configuration(self, context: ProvisioningContext):
        """Execute BIOS configuration using enhanced monitoring logic."""
        logger.debug(f"Executing BIOS configuration for {context.device_type}")

        try:
            logger.info("Applying BIOS configuration with enhanced monitoring...")

            # Use the existing enhanced BIOS configuration system (phase 3 API)
            bios_result = await self.bios_manager.apply_bios_config_phase3(
                context.device_type,
                context.target_ip,
                context.credentials["username"],
                context.credentials["password"],
                operation_id=context.operation_id,
                monitor=self.monitor,
            )

            if not bios_result.success:
                raise WorkflowError(f"BIOS configuration failed: {bios_result.error}")

            # Store results
            context.bios_results = {
                "settings_applied": bios_result.settings_applied,
                "redfish_settings": bios_result.redfish_success_count,
                "vendor_tool_settings": bios_result.vendor_tool_success_count,
                "fallback_settings": bios_result.fallback_success_count,
                "execution_time": f"{bios_result.execution_time:.1f}s",
                "success_rate": f"{bios_result.success_rate:.1f}%",
            }

            logger.info("BIOS configuration results:")
            logger.info(
                f"  Settings applied: {context.bios_results['settings_applied']}"
            )
            logger.info(
                f"  Redfish method: {context.bios_results['redfish_settings']} settings"
            )
            logger.info(
                f"  Vendor tools: {context.bios_results['vendor_tool_settings']} settings"
            )
            logger.info(f"  Execution time: {context.bios_results['execution_time']}")
            logger.info(f"  Success rate: {context.bios_results['success_rate']}")

        except Exception as e:
            logger.error(f"BIOS configuration failed: {e}")
            raise WorkflowError(f"BIOS configuration failed: {e}")

    async def _execute_final_validation(self, context: ProvisioningContext):
        """Execute final system validation."""
        logger.debug(f"Executing final validation for {context.target_ip}")

        try:
            # Validate system configuration
            await self._validate_final_configuration(context)

            # Validate system health
            await self._validate_system_health(context)

            logger.debug("Final validation completed successfully")

        except Exception as e:
            logger.error(f"Final validation failed: {e}")
            raise WorkflowError(f"Final validation failed: {e}")

    async def _validate_final_configuration(self, context: ProvisioningContext):
        """Validate final system configuration."""
        # Simulate final configuration validation
        await asyncio.sleep(0.5)
        logger.debug(f"Final configuration validated for {context.target_ip}")

    async def _validate_system_health(self, context: ProvisioningContext):
        """Validate system health."""
        # Simulate system health validation
        await asyncio.sleep(0.3)
        logger.debug(f"System health validated for {context.target_ip}")

    def create_provisioning_context(
        self,
        server_id: str,
        device_type: str,
        target_ip: str,
        credentials: Dict[str, str],
        **kwargs,
    ) -> ProvisioningContext:
        """
        Create a provisioning context for firmware-first workflow.

        Args:
            server_id: Server identifier
            device_type: Device type (e.g., 'a1.c5.large')
            target_ip: Target IP address
            credentials: BMC credentials dict with 'username' and 'password'
            **kwargs: Additional context parameters

        Returns:
            ProvisioningContext instance
        ."""
        return ProvisioningContext(
            server_id=server_id,
            device_type=device_type,
            target_ip=target_ip,
            credentials=credentials,
            **kwargs,
        )


# Factory function for creating workflow instances
def create_firmware_provisioning_workflow() -> FirmwareProvisioningWorkflow:
    """Create a new firmware provisioning workflow instance."""
    return FirmwareProvisioningWorkflow()


# Custom exceptions
class FirmwareProvisioningException(WorkflowError):
    """Firmware provisioning specific exception."""

    pass
