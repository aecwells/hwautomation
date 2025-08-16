"""Intelligent commissioning workflows.

This module provides enhanced commissioning workflows that leverage
device classification and unified configuration.
"""

from typing import Any, Dict, Optional

from hwautomation.logging import get_logger

from ..steps.hardware_discovery import DiscoverHardwareStep, EstablishSSHConnectionStep
from ..steps.intelligent_configuration import (
    DeviceSpecificConfigurationStep,
    IntelligentConfigurationPlanningStep,
)
from ..workflow.base import WorkflowContext, WorkflowStatus
from ..workflow.engine import Workflow
from ..workflow.manager import WorkflowManager

logger = get_logger(__name__)


class IntelligentCommissioningWorkflow:
    """Enhanced commissioning workflow with intelligent device classification."""

    def __init__(self, workflow_manager: WorkflowManager):
        """Initialize intelligent commissioning workflow."""
        self.workflow_manager = workflow_manager
        self.logger = logger

    def create_intelligent_commissioning_workflow(
        self,
        workflow_id: str,
        server_id: str,
        target_ip: str,
        credentials: Dict[str, str],
        options: Optional[Dict[str, Any]] = None,
    ) -> Workflow:
        """
        Create an intelligent commissioning workflow.

        Args:
            workflow_id: Unique workflow identifier
            server_id: Server identifier
            target_ip: Target server IP address
            credentials: SSH/IPMI credentials
            options: Additional workflow options

        Returns:
            Configured workflow instance
        """
        # Use workflow manager's intelligent commissioning method
        return self.workflow_manager.create_intelligent_commissioning_workflow(
            workflow_id, server_id, target_ip, credentials, options
        )

    def create_device_specific_provisioning_workflow(
        self,
        workflow_id: str,
        server_id: str,
        device_type: str,
        target_ip: str,
        credentials: Dict[str, str],
        options: Optional[Dict[str, Any]] = None,
    ) -> Workflow:
        """
        Create a device-specific provisioning workflow.

        Args:
            workflow_id: Unique workflow identifier
            server_id: Server identifier
            device_type: Known device type for targeted provisioning
            target_ip: Target server IP address
            credentials: SSH/IPMI credentials
            options: Additional workflow options

        Returns:
            Configured workflow instance
        """
        workflow = self.workflow_manager.create_workflow(workflow_id)

        # Enhanced context with device type pre-specified
        context = WorkflowContext(
            workflow_id=workflow_id,
            server_id=server_id,
            target_ip=target_ip,
            credentials=credentials,
            db_helper=self.workflow_manager.db_helper,
            maas_client=self.workflow_manager.maas_client,
            config_manager=getattr(self.workflow_manager, "config_manager", None),
            enhanced_discovery=getattr(self.workflow_manager, "unified_loader", None)
            is not None,
        )

        # Pre-set device type in context
        context.set_data("device_type", device_type)
        context.set_data(
            "classification_confidence", 1.0
        )  # High confidence since pre-specified

        workflow.context = context

        # Add device-specific provisioning steps
        workflow.add_step("establish_ssh_connection")
        workflow.add_step("verify_device_type")
        workflow.add_step("device_specific_configuration_planning")
        workflow.add_step("apply_device_specific_bios_config")
        workflow.add_step("apply_device_specific_firmware_config")
        workflow.add_step("validate_configuration")
        workflow.add_step("maas_commissioning_with_device_metadata")

        self.logger.info(
            f"Created device-specific provisioning workflow {workflow_id} "
            f"for {device_type} server {server_id}"
        )
        return workflow

    def create_batch_intelligent_commissioning_workflow(
        self,
        workflow_id: str,
        server_list: list,
        base_ip_range: Optional[str] = None,
        gateway: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Workflow:
        """
        Create a batch intelligent commissioning workflow.

        Args:
            workflow_id: Unique workflow identifier
            server_list: List of server identifiers
            base_ip_range: Optional IPMI IP range for assignment
            gateway: Optional gateway for network configuration
            options: Additional workflow options

        Returns:
            Configured batch workflow instance
        """
        workflow = self.workflow_manager.create_workflow(workflow_id)

        # Enhanced context for batch operations
        context = WorkflowContext(
            workflow_id=workflow_id,
            server_id=None,  # Will be set per server
            target_ip=None,  # Will be set per server
            credentials={},  # Will be populated per server
            db_helper=self.workflow_manager.db_helper,
            maas_client=self.workflow_manager.maas_client,
            config_manager=getattr(self.workflow_manager, "config_manager", None),
            enhanced_discovery=getattr(self.workflow_manager, "unified_loader", None)
            is not None,
        )

        # Store batch-specific data
        context.set_data("server_list", server_list)
        context.set_data("base_ip_range", base_ip_range)
        context.set_data("gateway", gateway)
        context.set_data("batch_results", {})

        workflow.context = context

        # Add batch commissioning steps
        workflow.add_step("initialize_batch_commissioning")
        workflow.add_step("assign_ipmi_addresses")  # If IP range provided
        workflow.add_step("batch_hardware_discovery")
        workflow.add_step("batch_device_classification")
        workflow.add_step("batch_configuration_planning")
        workflow.add_step("batch_device_specific_configuration")
        workflow.add_step("batch_maas_commissioning")
        workflow.add_step("batch_results_summary")

        self.logger.info(
            f"Created batch intelligent commissioning workflow {workflow_id} "
            f"for {len(server_list)} servers"
        )
        return workflow

    def get_workflow_recommendations(
        self,
        hardware_info: Dict[str, Any],
        available_device_types: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        Get workflow recommendations based on hardware information.

        Args:
            hardware_info: Hardware discovery results
            available_device_types: List of available device types

        Returns:
            Workflow recommendations
        """
        recommendations = {
            "recommended_workflow": "standard",
            "confidence": 0.5,
            "reasons": [],
            "available_workflows": [],
        }

        try:
            # Check if enhanced discovery is available
            if (
                hasattr(self.workflow_manager, "unified_loader")
                and self.workflow_manager.unified_loader
            ):
                recommendations["available_workflows"].extend(
                    [
                        "intelligent_commissioning",
                        "device_specific_provisioning",
                        "batch_intelligent_commissioning",
                    ]
                )

                # Analyze hardware info for recommendations
                manufacturer = hardware_info.get("manufacturer", "").lower()
                model = hardware_info.get("model", "").lower()

                if "hpe" in manufacturer or "hewlett" in manufacturer:
                    recommendations["recommended_workflow"] = (
                        "intelligent_commissioning"
                    )
                    recommendations["confidence"] = 0.8
                    recommendations["reasons"].append(
                        "HPE hardware detected - enhanced support available"
                    )

                elif "supermicro" in manufacturer or "super micro" in manufacturer:
                    recommendations["recommended_workflow"] = (
                        "intelligent_commissioning"
                    )
                    recommendations["confidence"] = 0.8
                    recommendations["reasons"].append(
                        "Supermicro hardware detected - enhanced support available"
                    )

                else:
                    recommendations["recommended_workflow"] = (
                        "intelligent_commissioning"
                    )
                    recommendations["confidence"] = 0.6
                    recommendations["reasons"].append(
                        "Unknown hardware - intelligent discovery recommended"
                    )

            else:
                # Legacy workflow recommendations
                recommendations["available_workflows"].extend(
                    ["standard_commissioning", "legacy_provisioning"]
                )
                recommendations["reasons"].append("Using legacy workflow system")

        except Exception as e:
            self.logger.error(f"Error generating workflow recommendations: {e}")
            recommendations["reasons"].append(f"Error: {str(e)}")

        return recommendations

    def get_supported_device_types(self) -> list:
        """Get list of supported device types for intelligent workflows."""
        return self.workflow_manager.get_supported_device_types()

    def validate_device_type(self, device_type: str) -> bool:
        """Validate if a device type is supported."""
        return self.workflow_manager.validate_device_type(device_type)

    def get_workflow_status_summary(self) -> Dict[str, Any]:
        """Get summary of workflow system capabilities."""
        return {
            "intelligent_workflows_available": hasattr(
                self.workflow_manager, "unified_loader"
            ),
            "enhanced_discovery": getattr(self.workflow_manager, "unified_loader", None)
            is not None,
            "supported_vendors": (
                self.workflow_manager.unified_loader.list_vendors()
                if hasattr(self.workflow_manager, "unified_loader")
                and self.workflow_manager.unified_loader
                else ["HPE", "Supermicro"]
            ),
            "supported_device_count": len(self.get_supported_device_types()),
            "configuration_adapters": (
                self.workflow_manager.config_manager.get_status()
                if hasattr(self.workflow_manager, "config_manager")
                and self.workflow_manager.config_manager
                else None
            ),
        }
