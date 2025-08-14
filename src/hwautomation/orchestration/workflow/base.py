"""
Workflow Base Definitions

Contains enums, data classes, and base interfaces for the workflow system.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class WorkflowStatus(Enum):
    """Workflow execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(Enum):
    """Individual step status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Represents a single workflow step."""

    name: str
    description: str
    function: Callable
    timeout: int = 300  # 5 minutes default
    retry_count: int = 3
    status: StepStatus = StepStatus.PENDING
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Any = None


@dataclass
class WorkflowContext:
    """Shared context for workflow execution."""

    server_id: str
    device_type: str
    target_ipmi_ip: Optional[str]
    rack_location: Optional[str]
    maas_client: Any
    db_helper: Any
    gateway: Optional[str] = None
    subnet_mask: Optional[str] = None

    # Runtime context data
    workflow_id: Optional[str] = None
    server_ip: Optional[str] = None
    ssh_connectivity_verified: bool = False
    hardware_discovery_result: Optional[Dict[str, Any]] = None
    hardware_info: Optional[Dict[str, Any]] = None
    server_data: Optional[Dict[str, Any]] = None
    original_bios_config: Optional[Any] = None  # xml.etree.ElementTree.Element
    modified_bios_config: Optional[Any] = None  # xml.etree.ElementTree.Element
    bios_config_path: Optional[str] = None
    discovered_ipmi_ip: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Sub-task progress reporting
    sub_task_callback: Optional[Callable] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.server_data is None:
            self.server_data = {}
        if self.hardware_info is None:
            self.hardware_info = {}

    def report_sub_task(self, sub_task_description: str):
        """Report a sub-task being executed."""
        if self.sub_task_callback:
            self.sub_task_callback(sub_task_description)


class WorkflowExecutionError(Exception):
    """Base exception for workflow execution errors."""

    pass


class WorkflowTimeoutError(WorkflowExecutionError):
    """Raised when a workflow step times out."""

    pass


class WorkflowCancellationError(WorkflowExecutionError):
    """Raised when a workflow is cancelled."""

    pass
