"""Provisioning workflow implementation.

This module provides the main server provisioning workflow that composes
all the individual step modules into a complete workflow.
"""

from typing import Any, Dict, List, Optional

from hwautomation.logging import get_logger

from ..steps.commissioning import (
    SelectMachineStep,
    CommissionMachineStep,
    WaitForCommissioningStep,
    RecordCommissioningStep,
)
from ..steps.hardware_discovery import (
    EstablishSSHConnectionStep,
    DiscoverHardwareStep,
    DetectServerVendorStep,
    GatherSystemInfoStep,
    RecordHardwareInfoStep,
)
from ..steps.bios_config import (
    PullBiosConfigStep,
    ModifyBiosConfigStep,
    PushBiosConfigStep,
    VerifyBiosConfigStep,
    RecordBiosConfigStep,
)
from ..steps.ipmi_config import (
    ConfigureIpmiStep,
    TestIpmiConnectivityStep,
    RecordIpmiConfigStep,
    AssignIpmiIpStep,
)
from ..steps.network_config import (
    EstablishSSHConnectionStep as NetworkSSHStep,
    TestNetworkConnectivityStep,
    ConfigureNetworkSettingsStep,
    ValidateNetworkConfigurationStep,
    GatherNetworkInventoryStep,
    PingTestStep,
    RecordNetworkInfoStep,
)
from ..workflows.base import (
    BaseWorkflow,
    BaseWorkflowStep,
    StepContext,
    StepExecutionResult,
    WorkflowStatus,
)

logger = get_logger(__name__)


class ServerProvisioningWorkflow(BaseWorkflow):
    """Complete server provisioning workflow."""

    def __init__(self, server_id: str, device_type: str, 
                 target_ipmi_ip: Optional[str] = None,
                 gateway: Optional[str] = None,
                 ipmi_range_start: Optional[str] = None,
                 ipmi_range_end: Optional[str] = None,
                 ssh_username: str = "ubuntu",
                 ssh_key_path: Optional[str] = None):
        """Initialize provisioning workflow."""
        super().__init__(
            name=f"Server Provisioning: {server_id}",
            description=f"Complete provisioning workflow for server {server_id} as {device_type}"
        )
        
        self.workflow_id = f"provision_{server_id}"
        self.server_id = server_id
        self.device_type = device_type
        self.target_ipmi_ip = target_ipmi_ip
        self.gateway = gateway
        self.ipmi_range_start = ipmi_range_start
        self.ipmi_range_end = ipmi_range_end
        self.ssh_username = ssh_username
        self.ssh_key_path = ssh_key_path
        
        # Build workflow steps
        self.steps = self.build_steps()

    def build_steps(self) -> List[BaseWorkflowStep]:
        """Build the complete workflow step sequence."""
        steps = []
        
        # Phase 1: MaaS Commissioning
        steps.append(SelectMachineStep())
        steps.append(CommissionMachineStep())
        steps.append(WaitForCommissioningStep())
        steps.append(RecordCommissioningStep())
        
        # Phase 2: Network Setup and SSH Connection
        steps.append(NetworkSSHStep(
            ssh_username=self.ssh_username,
            ssh_key_path=self.ssh_key_path
        ))
        steps.append(TestNetworkConnectivityStep())
        steps.append(ConfigureNetworkSettingsStep(target_gateway=self.gateway))
        steps.append(ValidateNetworkConfigurationStep())
        
        # Phase 3: Hardware Discovery
        steps.append(DiscoverHardwareStep())
        steps.append(DetectServerVendorStep())
        steps.append(GatherSystemInfoStep())
        steps.append(GatherNetworkInventoryStep())
        steps.append(RecordHardwareInfoStep())
        
        # Phase 4: IPMI Configuration (conditional)
        if self.ipmi_range_start and self.ipmi_range_end:
            steps.append(AssignIpmiIpStep(
                ip_range_start=self.ipmi_range_start,
                ip_range_end=self.ipmi_range_end
            ))
        
        steps.append(ConfigureIpmiStep())
        steps.append(TestIpmiConnectivityStep())
        steps.append(RecordIpmiConfigStep())
        
        # Phase 5: BIOS Configuration
        steps.append(PullBiosConfigStep())
        steps.append(ModifyBiosConfigStep())
        steps.append(PushBiosConfigStep())
        steps.append(VerifyBiosConfigStep())
        steps.append(RecordBiosConfigStep())
        
        # Phase 6: Final Validation and Recording
        steps.append(PingTestStep())
        steps.append(RecordNetworkInfoStep())
        
        return steps

    def create_initial_context(self) -> StepContext:
        """Create initial context for the workflow."""
        context = StepContext(
            workflow_id=self.workflow_id,
            server_id=self.server_id,
            device_type=self.device_type
        )
        
        # Set optional parameters
        if self.target_ipmi_ip:
            context.ipmi_ip = self.target_ipmi_ip
        
        if self.gateway:
            context.gateway = self.gateway
        
        # Set SSH parameters
        context.set_data("ssh_username", self.ssh_username)
        if self.ssh_key_path:
            context.set_data("ssh_key_path", self.ssh_key_path)
        
        return context

    def get_workflow_summary(self) -> Dict[str, Any]:
        """Get a summary of the workflow configuration."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "server_id": self.server_id,
            "device_type": self.device_type,
            "target_ipmi_ip": self.target_ipmi_ip,
            "gateway": self.gateway,
            "ipmi_range": f"{self.ipmi_range_start} - {self.ipmi_range_end}" if self.ipmi_range_start else None,
            "ssh_username": self.ssh_username,
            "total_steps": len(self.steps),
            "phases": [
                "MaaS Commissioning",
                "Network Setup",
                "Hardware Discovery", 
                "IPMI Configuration",
                "BIOS Configuration",
                "Final Validation"
            ]
        }


class FirmwareFirstProvisioningWorkflow(BaseWorkflow):
    """Alternative workflow that prioritizes firmware updates before BIOS configuration."""

    def __init__(self, server_id: str, device_type: str,
                 firmware_version: Optional[str] = None,
                 target_ipmi_ip: Optional[str] = None,
                 gateway: Optional[str] = None,
                 ssh_username: str = "ubuntu",
                 ssh_key_path: Optional[str] = None):
        """Initialize firmware-first provisioning workflow."""
        super().__init__(
            name=f"Firmware-First Provisioning: {server_id}",
            description=f"Firmware-priority provisioning workflow for server {server_id}"
        )
        
        self.workflow_id = f"firmware_provision_{server_id}"
        self.server_id = server_id
        self.device_type = device_type
        self.firmware_version = firmware_version
        self.target_ipmi_ip = target_ipmi_ip
        self.gateway = gateway
        self.ssh_username = ssh_username
        self.ssh_key_path = ssh_key_path
        
        # Build workflow steps
        self.steps = self.build_steps()

    def build_steps(self) -> List[BaseWorkflowStep]:
        """Build the firmware-first workflow step sequence."""
        steps = []
        
        # Phase 1: MaaS Commissioning
        steps.append(SelectMachineStep())
        steps.append(CommissionMachineStep())
        steps.append(WaitForCommissioningStep())
        steps.append(RecordCommissioningStep())
        
        # Phase 2: Network and SSH Setup
        steps.append(NetworkSSHStep(
            ssh_username=self.ssh_username,
            ssh_key_path=self.ssh_key_path
        ))
        steps.append(TestNetworkConnectivityStep())
        
        # Phase 3: Hardware Discovery
        steps.append(DiscoverHardwareStep())
        steps.append(DetectServerVendorStep())
        steps.append(GatherSystemInfoStep())
        
        # Phase 4: IPMI Configuration (early for firmware management)
        steps.append(ConfigureIpmiStep())
        steps.append(TestIpmiConnectivityStep())
        
        # Phase 5: Firmware Management (before BIOS)
        # Note: These would be implemented in firmware workflow steps
        # For now, we'll use placeholders
        
        # Phase 6: BIOS Configuration (after firmware)
        steps.append(PullBiosConfigStep())
        steps.append(ModifyBiosConfigStep())
        steps.append(PushBiosConfigStep())
        steps.append(VerifyBiosConfigStep())
        
        # Phase 7: Final Steps
        steps.append(GatherNetworkInventoryStep())
        steps.append(RecordHardwareInfoStep())
        steps.append(RecordIpmiConfigStep())
        steps.append(RecordBiosConfigStep())
        
        return steps

    def create_initial_context(self) -> StepContext:
        """Create initial context for the firmware workflow."""
        context = StepContext(
            workflow_id=self.workflow_id,
            server_id=self.server_id,
            device_type=self.device_type
        )
        
        # Set optional parameters
        if self.target_ipmi_ip:
            context.ipmi_ip = self.target_ipmi_ip
        
        if self.gateway:
            context.gateway = self.gateway
        
        if self.firmware_version:
            context.set_data("target_firmware_version", self.firmware_version)
        
        # Set SSH parameters
        context.set_data("ssh_username", self.ssh_username)
        if self.ssh_key_path:
            context.set_data("ssh_key_path", self.ssh_key_path)
        
        return context


def create_provisioning_workflow(server_id: str, device_type: str,
                                target_ipmi_ip: Optional[str] = None,
                                gateway: Optional[str] = None,
                                ipmi_range_start: Optional[str] = None,
                                ipmi_range_end: Optional[str] = None,
                                workflow_type: str = "standard",
                                **kwargs) -> BaseWorkflow:
    """Factory function to create provisioning workflows."""
    
    if workflow_type == "firmware_first":
        return FirmwareFirstProvisioningWorkflow(
            server_id=server_id,
            device_type=device_type,
            target_ipmi_ip=target_ipmi_ip,
            gateway=gateway,
            **kwargs
        )
    else:
        return ServerProvisioningWorkflow(
            server_id=server_id,
            device_type=device_type,
            target_ipmi_ip=target_ipmi_ip,
            gateway=gateway,
            ipmi_range_start=ipmi_range_start,
            ipmi_range_end=ipmi_range_end,
            **kwargs
        )


def get_available_workflow_types() -> List[Dict[str, str]]:
    """Get list of available workflow types."""
    return [
        {
            "type": "standard",
            "name": "Standard Provisioning",
            "description": "Standard server provisioning with BIOS configuration"
        },
        {
            "type": "firmware_first", 
            "name": "Firmware-First Provisioning",
            "description": "Prioritizes firmware updates before BIOS configuration"
        }
    ]
