"""
Main Workflow Manager

Central orchestration manager that coordinates workflow creation, execution, and lifecycle management
with enhanced device classification and intelligent provisioning through unified configuration integration.
"""

import logging
from typing import Any, Dict, List, Optional

from ...config.adapters import ConfigurationManager
from ...config.unified_loader import UnifiedConfigLoader
from ...database.helper import DbHelper
from ...logging import get_logger
from ...maas.client import MaasClient
from .base import WorkflowContext, WorkflowStatus
from .engine import Workflow
from .firmware import FirmwareWorkflowHandler

logger = get_logger(__name__)


class WorkflowManager:
    """
    Main workflow orchestration manager

    Coordinates the entire server provisioning process from commissioning
    through BIOS configuration to IPMI setup with enhanced device classification
    and intelligent provisioning through unified configuration integration.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.workflows: Dict[str, Workflow] = {}
        self.logger = get_logger(__name__)

        # Initialize unified configuration system
        self.config_manager = ConfigurationManager()
        self.unified_loader = self.config_manager.get_unified_loader()

        # Initialize database helper
        db_config = config.get("database", {})
        self.db_helper = DbHelper(
            tablename=db_config.get("table_name", "servers"),
            db_path=db_config.get("path", "hw_automation.db"),
            auto_migrate=db_config.get("auto_migrate", True),
        )

        # Initialize clients
        maas_config = config.get("maas", {})
        self.maas_client = MaasClient(
            host=maas_config.get("host", ""),
            consumer_key=maas_config.get("consumer_key", ""),
            consumer_token=maas_config.get("consumer_token", ""),
            secret=maas_config.get("secret", ""),
        )

        # Initialize firmware workflow handler
        self.firmware_handler = FirmwareWorkflowHandler(config)

        # Check which configuration system we're using
        config_source = "unified" if self.unified_loader else "legacy"
        logger.info(f"WorkflowManager initialized with {config_source} configuration")

    def create_workflow(self, workflow_id: str) -> Workflow:
        """Create a new workflow instance."""
        workflow = Workflow(workflow_id, self)
        self.workflows[workflow_id] = workflow
        return workflow

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get an existing workflow by ID."""
        return self.workflows.get(workflow_id)

    def list_workflows(self) -> List[str]:
        """List all workflow IDs."""
        return list(self.workflows.keys())

    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get all active (running or pending) workflows."""
        active_workflows = []
        for workflow in self.workflows.values():
            if workflow.status in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]:
                active_workflows.append(workflow.get_status())
        return active_workflows

    def get_all_workflows(self) -> List[Dict[str, Any]]:
        """Get status of all workflows."""
        return [workflow.get_status() for workflow in self.workflows.values()]

    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow."""
        workflow = self.workflows.get(workflow_id)
        if workflow:
            workflow.cancel()
            return True
        return False

    def cleanup_workflow(self, workflow_id: str):
        """Remove a completed or failed workflow from memory."""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]

    def create_firmware_first_workflow(
        self,
        workflow_id: str,
        server_id: str,
        device_type: str,
        target_ip: str,
        credentials: Dict[str, str],
        firmware_policy: Optional[str] = None,
        skip_firmware_check: bool = False,
        skip_bios_config: bool = False,
    ) -> Workflow:
        """
        Create a firmware-first provisioning workflow.

        Args:
            workflow_id: Unique identifier for the workflow
            server_id: Server identifier
            device_type: Type of device being provisioned
            target_ip: Target IP address for the server
            credentials: Authentication credentials
            firmware_policy: Firmware update policy
            skip_firmware_check: Whether to skip firmware checks
            skip_bios_config: Whether to skip BIOS configuration

        Returns:
            Configured Workflow instance
        """
        return self.firmware_handler.create_firmware_first_workflow(
            workflow_id=workflow_id,
            server_id=server_id,
            device_type=device_type,
            target_ip=target_ip,
            credentials=credentials,
            firmware_policy=firmware_policy,
            skip_firmware_check=skip_firmware_check,
            skip_bios_config=skip_bios_config,
            manager=self,
        )

    def create_context(
        self,
        server_id: str,
        device_type: str,
        target_ipmi_ip: Optional[str] = None,
        rack_location: Optional[str] = None,
        gateway: Optional[str] = None,
        subnet_mask: Optional[str] = None,
    ) -> WorkflowContext:
        """
        Create a workflow context with initialized clients.

        Args:
            server_id: Server identifier
            device_type: Type of device being provisioned
            target_ipmi_ip: Target IPMI IP address
            rack_location: Physical rack location
            gateway: Network gateway
            subnet_mask: Network subnet mask

        Returns:
            Configured WorkflowContext instance
        """
        return WorkflowContext(
            server_id=server_id,
            device_type=device_type,
            target_ipmi_ip=target_ipmi_ip,
            rack_location=rack_location,
            maas_client=self.maas_client,
            db_helper=self.db_helper,
            gateway=gateway,
            subnet_mask=subnet_mask,
        )

    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration."""
        return self.config.copy()

    def is_firmware_available(self) -> bool:
        """Check if firmware workflow components are available."""
        return self.firmware_handler.is_firmware_available()

    def shutdown(self):
        """Shutdown the workflow manager and cleanup resources."""
        # Cancel all running workflows
        for workflow_id, workflow in self.workflows.items():
            if workflow.status in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]:
                logger.info(f"Cancelling workflow {workflow_id} during shutdown")
                workflow.cancel()

        # Clear workflows
        self.workflows.clear()
        logger.info("WorkflowManager shutdown complete")

    # Enhanced methods using unified configuration

    def create_intelligent_commissioning_workflow(
        self,
        workflow_id: str,
        server_id: str,
        target_ip: str,
        credentials: Dict[str, str],
        options: Optional[Dict[str, Any]] = None,
    ) -> Workflow:
        """
        Create an intelligent commissioning workflow with enhanced discovery and classification.

        Args:
            workflow_id: Unique workflow identifier
            server_id: Server identifier
            target_ip: Target server IP address
            credentials: SSH/IPMI credentials
            options: Additional workflow options

        Returns:
            Configured workflow instance
        """
        workflow = self.create_workflow(workflow_id)

        # Enhanced context with unified configuration capabilities
        context = WorkflowContext(
            server_id=server_id,
            device_type="unknown",  # Will be determined by discovery
            target_ipmi_ip=target_ip,
            rack_location=options.get("rack_location") if options else None,
            maas_client=self.maas_client,
            db_helper=self.db_helper,
            gateway=options.get("gateway") if options else None,
            subnet_mask=options.get("subnet_mask") if options else None,
        )

        # Set additional context data
        context.workflow_id = workflow_id
        context.server_ip = target_ip
        context.metadata.update(
            {
                "credentials": credentials,
                "config_manager": self.config_manager,
                "enhanced_discovery": self.unified_loader is not None,
                "unified_loader": self.unified_loader,
            }
        )

        workflow.context = context

        # Add intelligent commissioning steps
        workflow.add_step("enhanced_hardware_discovery")
        workflow.add_step("device_classification")
        workflow.add_step("intelligent_configuration_planning")
        workflow.add_step("device_specific_bios_configuration")
        workflow.add_step("vendor_specific_ipmi_configuration")
        workflow.add_step("maas_commissioning_with_device_type")

        self.logger.info(
            f"Created intelligent commissioning workflow {workflow_id} for server {server_id}"
        )
        return workflow

    def get_device_type_from_discovery(
        self, discovery_result: Dict[str, Any]
    ) -> Optional[str]:
        """
        Get device type from hardware discovery results using unified configuration.

        Args:
            discovery_result: Hardware discovery results

        Returns:
            Classified device type or None
        """
        if not self.unified_loader:
            return None

        try:
            # Extract system info from discovery
            system_info = discovery_result.get("system_info", {})

            # Use enhanced discovery manager for classification
            from ...hardware.discovery.base import SystemInfo
            from ...hardware.discovery.manager import HardwareDiscoveryManager
            from ...utils.network import SSHManager

            ssh_manager = SSHManager()
            discovery_manager = HardwareDiscoveryManager(ssh_manager)

            # Create SystemInfo object from discovery results
            sys_info = SystemInfo(
                manufacturer=system_info.get("manufacturer"),
                product_name=system_info.get("product_name"),
                cpu_model=system_info.get("cpu_model"),
                cpu_cores=system_info.get("cpu_cores"),
                memory_total=system_info.get("memory_total"),
            )

            # Classify device type
            classification = discovery_manager.classify_device_type(sys_info)

            self.logger.info(
                f"Device classified as '{classification['device_type']}' "
                f"with {classification['confidence']} confidence"
            )

            return classification.get("device_type")

        except Exception as e:
            self.logger.error(f"Device type classification failed: {e}")
            return None

    def get_device_specific_configuration(self, device_type: str) -> Dict[str, Any]:
        """
        Get device-specific configuration templates and settings.

        Args:
            device_type: Classified device type

        Returns:
            Device-specific configuration
        """
        if not self.unified_loader or not device_type:
            return {}

        try:
            device_info = self.unified_loader.get_device_by_type(device_type)
            if not device_info:
                return {}

            # Get BIOS configuration through adapter
            bios_adapter = self.config_manager.get_bios_adapter()
            device_mappings = bios_adapter.load_device_mappings()
            bios_config = device_mappings.get(device_type, {})

            # Get firmware configuration through adapter
            firmware_adapter = self.config_manager.get_firmware_adapter()
            firmware_config = firmware_adapter.get_firmware_config()

            return {
                "device_type": device_type,
                "vendor": device_info.vendor,
                "motherboard": device_info.motherboard,
                "bios_config": bios_config,
                "firmware_config": firmware_config.get(device_info.motherboard, {}),
                "hardware_specs": device_info.device_config,
            }

        except Exception as e:
            self.logger.error(
                f"Failed to get device-specific configuration for {device_type}: {e}"
            )
            return {}

    def get_supported_device_types(self) -> List[str]:
        """Get list of all supported device types."""
        if self.unified_loader:
            return self.unified_loader.list_all_device_types()
        else:
            # Fallback to legacy device types
            return ["a1.c5.large", "s2.c2.small", "s2.c2.medium", "s2.c2.large"]

    def validate_device_type(self, device_type: str) -> bool:
        """Validate if a device type is supported."""
        if self.unified_loader:
            return self.unified_loader.get_device_by_type(device_type) is not None
        else:
            # Legacy validation
            return device_type in self.get_supported_device_types()

    def get_vendor_specific_procedures(self, vendor: str) -> Dict[str, Any]:
        """Get vendor-specific provisioning procedures."""
        if not self.unified_loader:
            return {}

        try:
            vendor_info = self.unified_loader.get_vendor_info(vendor)
            if vendor_info:
                return vendor_info.get("vendor_info", {}).get(
                    "provisioning_procedures", {}
                )
            return {}
        except Exception as e:
            self.logger.error(f"Failed to get vendor procedures for {vendor}: {e}")
            return {}

    def get_configuration_status(self) -> Dict[str, Any]:
        """Get orchestration configuration system status."""
        return {
            "unified_config_available": self.unified_loader is not None,
            "config_source": "unified" if self.unified_loader else "legacy",
            "enhanced_discovery": self.unified_loader is not None,
            "supported_device_count": len(self.get_supported_device_types()),
            "vendor_count": (
                len(self.unified_loader.list_vendors()) if self.unified_loader else 2
            ),
            "intelligent_workflows": self.unified_loader is not None,
            "adapters_status": (
                self.config_manager.get_status() if self.unified_loader else None
            ),
        }
