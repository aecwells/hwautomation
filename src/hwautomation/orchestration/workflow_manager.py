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
from ..hardware.firmware_manager import FirmwareManager
from ..hardware.firmware_provisioning_workflow import FirmwareProvisioningWorkflow, ProvisioningContext
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
    """Shared context for workflow execution"""
    server_id: str
    device_type: str
    target_ipmi_ip: Optional[str]
    rack_location: Optional[str]
    maas_client: Any
    db_helper: Any
    gateway: Optional[str] = None
    
    # Runtime context data
    workflow_id: Optional[str] = None
    server_ip: Optional[str] = None
    ssh_connectivity_verified: bool = False
    hardware_discovery_result: Optional[Dict[str, Any]] = None
    original_bios_config: Optional[Dict[str, Any]] = None
    modified_bios_config: Optional[Dict[str, Any]] = None
    bios_config_path: Optional[str] = None
    discovered_ipmi_ip: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    # Sub-task progress reporting
    sub_task_callback: Optional[Callable] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def report_sub_task(self, sub_task_description: str):
        """Report a sub-task being executed"""
        if self.sub_task_callback:
            self.sub_task_callback(sub_task_description)

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
        
        # Initialize firmware management (Phase 4)
        try:
            self.firmware_manager = FirmwareManager()
            self.firmware_workflow = FirmwareProvisioningWorkflow()
            logger.info("Firmware management initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize firmware management: {e}")
            self.firmware_manager = None
            self.firmware_workflow = None
    
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
    
    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get all active workflows with their status"""
        active_workflows = []
        for workflow_id, workflow in self.workflows.items():
            if workflow.status in [WorkflowStatus.RUNNING, WorkflowStatus.PENDING]:
                active_workflows.append(workflow.get_status())
        return active_workflows
    
    def get_all_workflows(self) -> List[Dict[str, Any]]:
        """Get all workflows with their status"""
        return [workflow.get_status() for workflow in self.workflows.values()]
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        workflow = self.get_workflow(workflow_id)
        if workflow:
            workflow.cancel()
            return True
        return False
    
    def cleanup_workflow(self, workflow_id: str):
        """Clean up completed or failed workflow"""
        if workflow_id in self.workflows:
            del self.workflows[workflow_id]
    
    def create_firmware_first_workflow(self, 
                                     server_id: str, 
                                     device_type: str, 
                                     target_ip: str,
                                     credentials: Dict[str, str],
                                     firmware_policy: str = "recommended",
                                     skip_firmware_check: bool = False,
                                     skip_bios_config: bool = False) -> Optional['Workflow']:
        """
        Create a firmware-first provisioning workflow (Phase 4).
        
        Args:
            server_id: Unique identifier for the server
            device_type: Device type (e.g., 's2.c2.small')
            target_ip: Target server IP address
            credentials: Authentication credentials
            firmware_policy: Firmware update policy ('recommended', 'latest', 'security_only')
            skip_firmware_check: Skip firmware update phase
            skip_bios_config: Skip BIOS configuration phase
            
        Returns:
            Workflow: Configured firmware-first workflow or None if firmware not available
        """
        if not self.firmware_workflow or not self.firmware_manager:
            logger.warning("Firmware management not available - cannot create firmware-first workflow")
            return None
        
        workflow_id = f"firmware_first_{server_id}_{int(time.time())}"
        workflow = self.create_workflow(workflow_id)
        
        # Create provisioning context
        context = ProvisioningContext(
            server_id=server_id,
            device_type=device_type,
            target_ip=target_ip,
            credentials=credentials,
            firmware_policy=firmware_policy,
            operation_id=workflow_id,
            skip_firmware_check=skip_firmware_check,
            skip_bios_config=skip_bios_config
        )
        
        # Add firmware-first provisioning step
        workflow.add_step(WorkflowStep(
            name="firmware_first_provisioning",
            description="Execute complete firmware-first provisioning workflow",
            function=lambda ctx: self._execute_firmware_first_provisioning(ctx, context),
            timeout=3600,  # 1 hour
            retry_count=1
        ))
        
        return workflow
    
    async def _execute_firmware_first_provisioning(self, workflow_context: 'WorkflowContext', 
                                                  provisioning_context: ProvisioningContext) -> bool:
        """Execute the firmware-first provisioning workflow"""
        try:
            workflow_context.report_sub_task("Starting firmware-first provisioning...")
            
            # Execute the firmware provisioning workflow
            result = await self.firmware_workflow.execute_firmware_first_provisioning(provisioning_context)
            
            if result.success:
                workflow_context.report_sub_task(f"Firmware-first provisioning completed successfully")
                logger.info(f"Firmware-first provisioning successful for {provisioning_context.server_id}")
                logger.info(f"  - Firmware updates applied: {result.firmware_updates_applied}")
                logger.info(f"  - BIOS settings applied: {result.bios_settings_applied}")
                logger.info(f"  - Execution time: {result.execution_time:.2f}s")
                
                # Update database with results
                self._update_firmware_provisioning_results(provisioning_context.server_id, result)
                
                return True
            else:
                workflow_context.report_sub_task(f"Firmware-first provisioning failed: {result.error_message}")
                logger.error(f"Firmware-first provisioning failed for {provisioning_context.server_id}: {result.error_message}")
                return False
                
        except Exception as e:
            workflow_context.report_sub_task(f"Firmware-first provisioning error: {str(e)}")
            logger.error(f"Firmware-first provisioning exception for {provisioning_context.server_id}: {e}")
            return False
    
    def _update_firmware_provisioning_results(self, server_id: str, result):
        """Update database with firmware provisioning results"""
        try:
            # Update server record with firmware provisioning information
            updates = {
                'firmware_version': f"Updated-{datetime.now().strftime('%Y%m%d')}",
                'bios_config_applied': 'Yes' if result.bios_settings_applied > 0 else 'No',
                'bios_config_version': f"FW-First-{datetime.now().strftime('%Y%m%d')}",
                'last_workflow_run': datetime.now().isoformat(),
                'notes': f"Firmware-first provisioning: {result.firmware_updates_applied} firmware updates, {result.bios_settings_applied} BIOS settings"
            }
            
            for field, value in updates.items():
                self.db_helper.updateserverinfo(server_id, field, value)
                
            logger.info(f"Updated database with firmware provisioning results for {server_id}")
            
        except Exception as e:
            logger.warning(f"Failed to update database with firmware results: {e}")

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
        self.current_sub_task: Optional[str] = None  # Track current sub-task
    
    def add_step(self, step: WorkflowStep):
        """Add a step to the workflow"""
        self.steps.append(step)
    
    def set_progress_callback(self, callback: Callable):
        """Set callback for progress updates"""
        self.progress_callback = callback
    
    def _report_sub_task(self, sub_task_description: str):
        """Report a sub-task being executed"""
        self.current_sub_task = sub_task_description
        logger.info(f"Sub-task: {sub_task_description}")
        
        if self.progress_callback:
            self.progress_callback({
                'workflow_id': self.id,
                'step': self.current_step_index + 1 if self.current_step_index is not None else None,
                'total_steps': len(self.steps),
                'step_name': self.steps[self.current_step_index].name if self.current_step_index is not None else None,
                'status': 'running',
                'sub_task': sub_task_description
            })
    
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
        
        # Set up sub-task callback
        context.sub_task_callback = self._report_sub_task
        
        try:
            logger.info(f"Starting workflow {self.id}")
            
            for i, step in enumerate(self.steps):
                if self.status == WorkflowStatus.CANCELLED:
                    break
                
                # Update current step index
                self.current_step_index = i
                self.current_sub_task = None  # Clear previous sub-task
                
                success = self._execute_step(step, i + 1, len(self.steps))
                if not success:
                    self.status = WorkflowStatus.FAILED
                    self.error = f"Step '{step.name}' failed: {step.error}"
                    return False
            
            # Clear current step when completed
            self.current_step_index = None
            self.current_sub_task = None
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
                'status': 'running',
                'sub_task': None
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
                        'status': 'completed',
                        'sub_task': None
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
                            'error': str(e),
                            'sub_task': None
                        })
                    
                    return False
                
                # Wait before retry
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return False
    
    def cancel(self):
        """Cancel the workflow execution"""
        self.status = WorkflowStatus.CANCELLED
        self.end_time = datetime.now()
        logger.info(f"Workflow {self.id} cancelled")
        
        # Notify via progress callback if available
        if self.progress_callback:
            self.progress_callback({
                'workflow_id': self.id,
                'step': self.current_step_index + 1 if self.current_step_index is not None else None,
                'total_steps': len(self.steps),
                'step_name': self.steps[self.current_step_index].name if self.current_step_index is not None else None,
                'status': 'cancelled',
                'sub_task': None
            })
    
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
            'current_sub_task': self.current_sub_task,  # Add current sub-task
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
