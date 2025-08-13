"""
Workflow step registry for HWAutomation modular orchestration.
"""

from typing import List, Type

from .steps.base import BaseWorkflowStep
from .steps.bios_config import BiosConfigStep
from .steps.cleanup import CleanupStep
from .steps.firmware_update import FirmwareUpdateStep
from .steps.hardware_discovery import HardwareDiscoveryStep
from .steps.maas_commission import MaasCommissionStep

# Example: Standard server provisioning workflow
STANDARD_PROVISIONING_WORKFLOW: List[Type[BaseWorkflowStep]] = [
    HardwareDiscoveryStep,
    BiosConfigStep,
    MaasCommissionStep,
    FirmwareUpdateStep,
    CleanupStep,
]

# You can define other workflows by composing steps in different orders
