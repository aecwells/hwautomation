"""
Workflow Manager for Hardware Orchestration

This module provides the main orchestration engine that coordinates
MaaS operations, BIOS configuration, and IPMI setup workflows.
"""

import logging
import time
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

from ..maas.client import MaasClient
from ..hardware.bios_config import BiosConfigManager
from ..hardware.ipmi import IpmiManager
from ..hardware.discovery import HardwareDiscoveryManager
from ..utils.network import SSHManager
from ..database.helper import DbHelper
from .exceptions import (
    WorkflowError,
    CommissioningError,
    BiosConfigurationError,
    IPMIConfigurationError,
    SSHConnectionError
)

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepStatus(Enum):
    """Individual step status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class WorkflowStep:
    """Represents a single workflow step"""
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
    """Context object passed between workflow steps"""
    server_id: str
    device_type: str
    target_ipmi_ip: Optional[str] = None
    rack_location: Optional[str] = None
    maas_client: Optional[MaasClient] = None
    db_helper: Optional[DbHelper] = None
    server_ip: Optional[str] = None
    ssh_connectivity_verified: bool = False
    hardware_discovery_result: Optional[Dict] = None
    bios_config_path: Optional[str] = None
    original_bios_config: Optional[Dict] = None
    modified_bios_config: Optional[Dict] = None
    ipmi_credentials: Optional[Dict] = None
    workflow_id: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class WorkflowManager:
    """
    Main workflow orchestration manager
    
    Coordinates the entire server provisioning process from commissioning
    through BIOS configuration to IPMI setup.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.workflows: Dict[str, 'Workflow'] = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize database helper
        db_config = config.get('database', {})
        self.db_helper = DbHelper(
            tablename=db_config.get('table_name', 'servers'),
            db_path=db_config.get('path', 'hw_automation.db'),
            auto_migrate=db_config.get('auto_migrate', True)
        )
        
        # Initialize clients
        maas_config = config.get('maas', {})
        self.maas_client = MaasClient(
            host=maas_config.get('host', ''),
            consumer_key=maas_config.get('consumer_key', ''),
            consumer_token=maas_config.get('token_key', ''),  # Note: token_key in config
            secret=maas_config.get('token_secret', '')
        )
        self.bios_manager = BiosConfigManager(config.get('bios', {}).get('config_dir'))
        self.ipmi_manager = IpmiManager(config.get('ipmi', {}))
        self.ssh_manager = SSHManager(config.get('ssh', {}))
        self.discovery_manager = HardwareDiscoveryManager(self.ssh_manager)
    
    def create_workflow(self, workflow_id: str) -> 'Workflow':
        """Create a new workflow instance"""
        workflow = Workflow(workflow_id, self)
        self.workflows[workflow_id] = workflow
        return workflow
    
    def get_workflow(self, workflow_id: str) -> Optional['Workflow']:
        """Get an existing workflow"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self) -> List[str]:
        """List all workflow IDs"""
        return list(self.workflows.keys())
    
    def cleanup_workflow(self, workflow_id: str):
        """Clean up completed or failed workflow"""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]

class Workflow:
    """
    Individual workflow instance
    
    Manages the execution of a sequence of steps with error handling,
    retries, and status tracking.
    """
    
    def __init__(self, workflow_id: str, manager: WorkflowManager):
        self.id = workflow_id
        self.manager = manager
        self.status = WorkflowStatus.PENDING
        self.steps: List[WorkflowStep] = []
        self.context: Optional[WorkflowContext] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.error: Optional[str] = None
        self.progress_callback: Optional[Callable] = None
        self.current_step_index: Optional[int] = None  # Track current step
    
    def add_step(self, step: WorkflowStep):
        """Add a step to the workflow"""
        self.steps.append(step)
    
    def set_progress_callback(self, callback: Callable):
        """Set callback for progress updates"""
        self.progress_callback = callback
    
    def execute(self, context: WorkflowContext) -> bool:
        """
        Execute the workflow
        
        Args:
            context: WorkflowContext with initial parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.context = context
        self.status = WorkflowStatus.RUNNING
        self.start_time = datetime.now()
        
        try:
            logger.info(f"Starting workflow {self.id}")
            
            for i, step in enumerate(self.steps):
                if self.status == WorkflowStatus.CANCELLED:
                    break
                
                # Update current step index
                self.current_step_index = i
                
                success = self._execute_step(step, i + 1, len(self.steps))
                if not success:
                    self.status = WorkflowStatus.FAILED
                    self.error = f"Step '{step.name}' failed: {step.error}"
                    return False
            
            # Clear current step when completed
            self.current_step_index = None
            self.status = WorkflowStatus.COMPLETED
            self.end_time = datetime.now()
            logger.info(f"Workflow {self.id} completed successfully")
            return True
            
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            self.error = str(e)
            self.end_time = datetime.now()
            logger.error(f"Workflow {self.id} failed: {e}")
            return False
    
    def _execute_step(self, step: WorkflowStep, step_num: int, total_steps: int) -> bool:
        """Execute a single workflow step with retry logic"""
        step.status = StepStatus.RUNNING
        step.start_time = datetime.now()
        
        logger.info(f"Executing step {step_num}/{total_steps}: {step.name}")
        
        if self.progress_callback:
            self.progress_callback({
                'workflow_id': self.id,
                'step': step_num,
                'total_steps': total_steps,
                'step_name': step.name,
                'status': 'running'
            })
        
        for attempt in range(step.retry_count):
            try:
                # Execute step with timeout
                start_time = time.time()
                step.result = step.function(self.context)
                
                # Check timeout
                if time.time() - start_time > step.timeout:
                    raise TimeoutError(f"Step timed out after {step.timeout} seconds")
                
                step.status = StepStatus.COMPLETED
                step.end_time = datetime.now()
                
                if self.progress_callback:
                    self.progress_callback({
                        'workflow_id': self.id,
                        'step': step_num,
                        'total_steps': total_steps,
                        'step_name': step.name,
                        'status': 'completed'
                    })
                
                return True
                
            except Exception as e:
                error_msg = f"Attempt {attempt + 1}/{step.retry_count} failed: {str(e)}"
                logger.warning(error_msg)
                
                if attempt == step.retry_count - 1:
                    step.status = StepStatus.FAILED
                    step.error = str(e)
                    step.end_time = datetime.now()
                    
                    if self.progress_callback:
                        self.progress_callback({
                            'workflow_id': self.id,
                            'step': step_num,
                            'total_steps': total_steps,
                            'step_name': step.name,
                            'status': 'failed',
                            'error': str(e)
                        })
                    
                    return False
                
                # Wait before retry
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return False
    
    def cancel(self):
        """Cancel the workflow execution"""
        self.status = WorkflowStatus.CANCELLED
        logger.info(f"Workflow {self.id} cancelled")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        status_data = {
            'id': self.id,
            'status': self.status.value,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'error': self.error,
            'current_step_index': self.current_step_index,
            'current_step_name': None,  # Initialize as None
            'steps': [
                {
                    'name': step.name,
                    'description': step.description,
                    'status': step.status.value,
                    'error': step.error,
                    'start_time': step.start_time.isoformat() if step.start_time else None,
                    'end_time': step.end_time.isoformat() if step.end_time else None
                }
                for step in self.steps
            ]
        }
        
        # Add current step name if available
        if self.current_step_index is not None and 0 <= self.current_step_index < len(self.steps):
            status_data['current_step_name'] = self.steps[self.current_step_index].name
        
        return status_data
