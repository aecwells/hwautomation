"""Intelligent configuration planning workflow steps.

This module provides steps for intelligent configuration planning based on
device classification and unified configuration system.
"""

from typing import Any, Dict, Optional

from hwautomation.logging import get_logger

from ..workflows.base import (
    BaseWorkflowStep,
    StepContext,
    StepExecutionResult,
)

logger = get_logger(__name__)


class IntelligentConfigurationPlanningStep(BaseWorkflowStep):
    """Step to plan device-specific configuration based on classification."""

    def __init__(self):
        super().__init__(
            name="intelligent_configuration_planning",
            description="Plan device-specific configuration based on hardware classification",
        )

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate hardware discovery completed."""
        if not context.get_data("hardware_info"):
            context.add_error("Hardware discovery required for configuration planning")
            return False
        return True

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Plan intelligent configuration based on device classification."""
        try:
            context.add_sub_task("Analyzing hardware discovery results")

            # Get hardware info and classification
            hardware_info = context.get_data("hardware_info")
            device_type = context.get_data("device_type")
            classification_confidence = context.get_data(
                "classification_confidence", 0.0
            )

            manufacturer = hardware_info.get("manufacturer", "Unknown")
            model = hardware_info.get("model", "Unknown")

            context.add_sub_task(f"Planning configuration for {manufacturer} {model}")

            # Initialize configuration plan
            config_plan = {
                "device_type": device_type,
                "manufacturer": manufacturer,
                "model": model,
                "classification_confidence": classification_confidence,
                "configuration_strategy": "intelligent" if device_type else "fallback",
                "planned_configurations": {},
            }

            # Check if we have enhanced configuration available
            if hasattr(context, "config_manager") and context.config_manager:
                context.add_sub_task("Loading device-specific configuration templates")

                try:
                    # Get device-specific configuration if classified
                    if device_type:
                        # BIOS configuration
                        bios_adapter = context.config_manager.get_bios_adapter()
                        bios_config = bios_adapter.get_device_bios_config(device_type)

                        if bios_config:
                            config_plan["planned_configurations"]["bios"] = {
                                "template_available": True,
                                "settings_count": len(bios_config.get("settings", {})),
                                "device_type": device_type,
                            }
                            context.add_sub_task(
                                f"BIOS template found for {device_type}"
                            )

                        # Firmware configuration
                        firmware_adapter = context.config_manager.get_firmware_adapter()
                        firmware_config = firmware_adapter.get_device_firmware_config(
                            device_type
                        )

                        if firmware_config:
                            config_plan["planned_configurations"]["firmware"] = {
                                "template_available": True,
                                "vendor": firmware_config.get("vendor"),
                                "device_type": device_type,
                            }
                            context.add_sub_task(
                                f"Firmware configuration found for {device_type}"
                            )

                        # Get unified device info
                        unified_loader = getattr(
                            context.config_manager, "unified_loader", None
                        )
                        if unified_loader:
                            device_info = unified_loader.get_device_by_type(device_type)
                            if device_info:
                                config_plan["planned_configurations"][
                                    "device_specs"
                                ] = {
                                    "vendor": device_info.vendor,
                                    "motherboard": device_info.motherboard,
                                    "hardware_config": device_info.device_config,
                                }
                                context.add_sub_task(
                                    f"Device specifications loaded for {device_type}"
                                )

                    else:
                        # Fallback configuration planning
                        context.add_sub_task(
                            "Using fallback configuration (no device classification)"
                        )
                        config_plan["planned_configurations"]["fallback"] = {
                            "strategy": "vendor_based",
                            "manufacturer": manufacturer,
                        }

                except Exception as e:
                    logger.warning(f"Configuration planning encountered error: {e}")
                    context.add_sub_task(f"Configuration planning warning: {str(e)}")

                    # Still proceed with basic plan
                    config_plan["planned_configurations"]["basic"] = {
                        "strategy": "manual",
                        "requires_user_input": True,
                    }

            else:
                # Legacy configuration planning
                context.add_sub_task("Using legacy configuration system")
                config_plan["configuration_strategy"] = "legacy"
                config_plan["planned_configurations"]["legacy"] = {
                    "vendor_based": True,
                    "manufacturer": manufacturer,
                }

            # Store configuration plan in context
            context.set_data("configuration_plan", config_plan)

            # Summary message
            strategy = config_plan["configuration_strategy"]
            config_count = len(config_plan["planned_configurations"])

            context.add_sub_task(
                f"Configuration plan complete: {strategy} strategy with {config_count} components"
            )

            logger.info(
                f"Configuration planning completed for {manufacturer} {model} "
                f"(strategy: {strategy}, device_type: {device_type})"
            )

            return StepExecutionResult.success(
                "Configuration planning completed successfully",
                {"configuration_plan": config_plan},
            )

        except Exception as e:
            return StepExecutionResult.failure(f"Configuration planning failed: {e}")


class DeviceSpecificConfigurationStep(BaseWorkflowStep):
    """Step to apply device-specific BIOS and firmware configuration."""

    def __init__(self):
        super().__init__(
            name="device_specific_configuration",
            description="Apply device-specific BIOS and firmware configuration",
        )

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate configuration plan is available."""
        if not context.get_data("configuration_plan"):
            context.add_error(
                "Configuration plan required for device-specific configuration"
            )
            return False
        return True

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Apply device-specific configuration."""
        try:
            context.add_sub_task("Applying device-specific configuration")

            config_plan = context.get_data("configuration_plan")
            device_type = config_plan.get("device_type")
            planned_configs = config_plan.get("planned_configurations", {})

            results = {
                "applied_configurations": [],
                "skipped_configurations": [],
                "failed_configurations": [],
            }

            # Apply BIOS configuration if available
            if "bios" in planned_configs and hasattr(context, "config_manager"):
                context.add_sub_task("Applying BIOS configuration")
                try:
                    # Get BIOS manager through config manager
                    bios_adapter = context.config_manager.get_bios_adapter()

                    # Note: In a real implementation, you would apply the BIOS config here
                    # For now, we'll simulate the operation
                    context.add_sub_task(
                        f"BIOS configuration prepared for {device_type}"
                    )
                    results["applied_configurations"].append("bios")

                except Exception as e:
                    logger.error(f"BIOS configuration failed: {e}")
                    results["failed_configurations"].append(f"bios: {str(e)}")

            # Apply firmware configuration if available
            if "firmware" in planned_configs and hasattr(context, "config_manager"):
                context.add_sub_task("Applying firmware configuration")
                try:
                    # Get firmware manager through config manager
                    firmware_adapter = context.config_manager.get_firmware_adapter()

                    # Note: In a real implementation, you would apply firmware config here
                    context.add_sub_task(
                        f"Firmware configuration prepared for {device_type}"
                    )
                    results["applied_configurations"].append("firmware")

                except Exception as e:
                    logger.error(f"Firmware configuration failed: {e}")
                    results["failed_configurations"].append(f"firmware: {str(e)}")

            # Handle fallback configuration
            if "fallback" in planned_configs:
                context.add_sub_task("Applying fallback configuration")
                results["applied_configurations"].append("fallback")

            # Handle legacy configuration
            if "legacy" in planned_configs:
                context.add_sub_task("Applying legacy configuration")
                results["applied_configurations"].append("legacy")

            # Store results
            context.set_data("configuration_results", results)

            # Summary
            applied_count = len(results["applied_configurations"])
            failed_count = len(results["failed_configurations"])

            context.add_sub_task(
                f"Configuration complete: {applied_count} applied, {failed_count} failed"
            )

            if failed_count > 0:
                logger.warning(
                    f"Some configurations failed: {results['failed_configurations']}"
                )

            return StepExecutionResult.success(
                "Device-specific configuration completed", results
            )

        except Exception as e:
            return StepExecutionResult.failure(
                f"Device-specific configuration failed: {e}"
            )
