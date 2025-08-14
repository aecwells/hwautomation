"""
Base classes and interfaces for the provisioning system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from ..workflow_manager import WorkflowContext


class ProvisioningStage(Enum):
    """Stages of the provisioning process."""

    COMMISSIONING = "commissioning"
    NETWORK_SETUP = "network_setup"
    HARDWARE_DISCOVERY = "hardware_discovery"
    BIOS_CONFIGURATION = "bios_configuration"
    IPMI_CONFIGURATION = "ipmi_configuration"
    FINALIZATION = "finalization"


@dataclass
class ProvisioningConfig:
    """Configuration for a provisioning workflow."""

    server_id: str
    device_type: str
    target_ipmi_ip: Optional[str] = None
    rack_location: Optional[str] = None
    subnet_mask: Optional[str] = None
    gateway: Optional[str] = None
    firmware_policy: str = "recommended"
    ssh_username: str = "ubuntu"
    ssh_key_path: Optional[str] = None


@dataclass
class StageResult:
    """Result of a provisioning stage."""

    success: bool
    stage: ProvisioningStage
    data: Dict[str, Any]
    error_message: Optional[str] = None
    next_stage: Optional[ProvisioningStage] = None


class ProvisioningStageHandler(ABC):
    """Abstract base class for provisioning stage handlers."""

    @abstractmethod
    def execute(
        self, context: WorkflowContext, config: ProvisioningConfig
    ) -> StageResult:
        """Execute the provisioning stage."""
        pass

    @abstractmethod
    def get_stage(self) -> ProvisioningStage:
        """Get the stage this handler manages."""
        pass

    @abstractmethod
    def validate_prerequisites(self, context: WorkflowContext) -> bool:
        """Validate that prerequisites for this stage are met."""
        pass


class ProvisioningStrategy(ABC):
    """Abstract base class for different provisioning strategies."""

    @abstractmethod
    def get_stage_order(self) -> list[ProvisioningStage]:
        """Get the order of stages for this strategy."""
        pass

    @abstractmethod
    def should_skip_stage(
        self, stage: ProvisioningStage, context: WorkflowContext
    ) -> bool:
        """Determine if a stage should be skipped."""
        pass
