"""Base classes for orchestration workflows and steps.

This module provides the foundational abstractions for building
modular orchestration workflows with composable steps.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from hwautomation.logging import get_logger

logger = get_logger(__name__)


class StepResult(Enum):
    """Result status for workflow steps."""
    
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    SKIP = "skip"


class WorkflowStatus(Enum):
    """Status of workflow execution."""
    
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    RETRY = "retry"


@dataclass
class StepContext:
    """Context passed between workflow steps."""
    
    # Core workflow data
    workflow_id: str
    server_id: str
    device_type: Optional[str] = None
    
    # Server information
    server_ip: Optional[str] = None
    ipmi_ip: Optional[str] = None
    gateway: Optional[str] = None
    
    # Hardware information
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    
    # Workflow state
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    sub_tasks: List[str] = field(default_factory=list)
    
    # Timing
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def add_error(self, error: str) -> None:
        """Add an error to the context."""
        self.errors.append(error)
        logger.error(f"Step error: {error}")
    
    def add_sub_task(self, task: str) -> None:
        """Add a sub-task to the context."""
        self.sub_tasks.append(task)
        logger.info(f"Sub-task: {task}")
    
    def set_data(self, key: str, value: Any) -> None:
        """Set data in the context."""
        self.data[key] = value
    
    def get_data(self, key: str, default: Any = None) -> Any:
        """Get data from the context."""
        return self.data.get(key, default)


@dataclass 
class StepExecutionResult:
    """Result of executing a workflow step."""
    
    status: StepResult
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    should_continue: bool = True
    next_step: Optional[str] = None
    
    @classmethod
    def success(
        cls, 
        message: str = "Step completed successfully", 
        data: Optional[Dict[str, Any]] = None,
        next_step: Optional[str] = None
    ) -> "StepExecutionResult":
        """Create a success result."""
        return cls(
            status=StepResult.SUCCESS,
            message=message,
            data=data or {},
            should_continue=True,
            next_step=next_step
        )
    
    @classmethod
    def failure(
        cls, 
        message: str, 
        should_continue: bool = False,
        data: Optional[Dict[str, Any]] = None
    ) -> "StepExecutionResult":
        """Create a failure result."""
        return cls(
            status=StepResult.FAILURE,
            message=message,
            data=data or {},
            should_continue=should_continue
        )
    
    @classmethod
    def retry(
        cls, 
        message: str = "Step should be retried",
        data: Optional[Dict[str, Any]] = None
    ) -> "StepExecutionResult":
        """Create a retry result."""
        return cls(
            status=StepResult.RETRY,
            message=message,
            data=data or {},
            should_continue=False
        )
    
    @classmethod
    def skip(
        cls, 
        message: str = "Step skipped",
        data: Optional[Dict[str, Any]] = None,
        next_step: Optional[str] = None
    ) -> "StepExecutionResult":
        """Create a skip result."""
        return cls(
            status=StepResult.SKIP,
            message=message,
            data=data or {},
            should_continue=True,
            next_step=next_step
        )


class BaseWorkflowStep(ABC):
    """Abstract base class for workflow steps."""
    
    def __init__(self, name: str, description: str = ""):
        """Initialize the workflow step.
        
        Args:
            name: Step name
            description: Step description
        """
        self.name = name
        self.description = description
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    def execute(self, context: StepContext) -> StepExecutionResult:
        """Execute the workflow step.
        
        Args:
            context: Step execution context
            
        Returns:
            Step execution result
        """
        pass
    
    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate that prerequisites for this step are met.
        
        Args:
            context: Step execution context
            
        Returns:
            True if prerequisites are met
        """
        return True
    
    def cleanup(self, context: StepContext) -> None:
        """Clean up after step execution.
        
        Args:
            context: Step execution context
        """
        pass
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}({self.name})"


class ConditionalWorkflowStep(BaseWorkflowStep):
    """Workflow step that executes conditionally."""
    
    @abstractmethod
    def should_execute(self, context: StepContext) -> bool:
        """Determine if this step should execute.
        
        Args:
            context: Step execution context
            
        Returns:
            True if step should execute
        """
        pass
    
    def execute(self, context: StepContext) -> StepExecutionResult:
        """Execute the step if conditions are met."""
        if not self.should_execute(context):
            return StepExecutionResult.skip(
                f"Skipping {self.name} - conditions not met"
            )
        
        return self._execute_conditional(context)
    
    @abstractmethod
    def _execute_conditional(self, context: StepContext) -> StepExecutionResult:
        """Execute the conditional step logic.
        
        Args:
            context: Step execution context
            
        Returns:
            Step execution result
        """
        pass


class RetryableWorkflowStep(BaseWorkflowStep):
    """Workflow step that supports retries."""
    
    def __init__(
        self, 
        name: str, 
        description: str = "", 
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize retryable step.
        
        Args:
            name: Step name
            description: Step description
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
        """
        super().__init__(name, description)
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def execute(self, context: StepContext) -> StepExecutionResult:
        """Execute step with retry logic."""
        import time
        
        last_result = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.info(f"Executing {self.name}, attempt {attempt + 1}")
                result = self._execute_with_retry(context)
                
                if result.status == StepResult.SUCCESS:
                    if attempt > 0:
                        self.logger.info(f"Step {self.name} succeeded after {attempt + 1} attempts")
                    return result
                elif result.status != StepResult.RETRY:
                    # Non-retryable failure
                    return result
                
                last_result = result
                
                if attempt < self.max_retries:
                    self.logger.warning(f"Step {self.name} failed, retrying in {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                
            except Exception as e:
                self.logger.error(f"Step {self.name} failed with exception: {e}")
                last_result = StepExecutionResult.failure(f"Exception in {self.name}: {e}")
                
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
        
        # All retries exhausted
        self.logger.error(f"Step {self.name} failed after {self.max_retries + 1} attempts")
        return last_result or StepExecutionResult.failure(f"Step {self.name} failed after retries")
    
    @abstractmethod
    def _execute_with_retry(self, context: StepContext) -> StepExecutionResult:
        """Execute the retryable step logic.
        
        Args:
            context: Step execution context
            
        Returns:
            Step execution result
        """
        pass


class BaseWorkflow(ABC):
    """Abstract base class for workflows."""
    
    def __init__(self, name: str, description: str = ""):
        """Initialize the workflow.
        
        Args:
            name: Workflow name
            description: Workflow description
        """
        self.name = name
        self.description = description
        self.steps: List[BaseWorkflowStep] = []
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
    
    def add_step(self, step: BaseWorkflowStep) -> None:
        """Add a step to the workflow.
        
        Args:
            step: Workflow step to add
        """
        self.steps.append(step)
        self.logger.debug(f"Added step {step.name} to workflow {self.name}")
    
    def execute(self, context: StepContext) -> StepExecutionResult:
        """Execute the workflow.
        
        Args:
            context: Workflow execution context
            
        Returns:
            Final execution result
        """
        self.logger.info(f"Starting workflow {self.name}")
        context.started_at = datetime.now()
        
        try:
            return self._execute_steps(context)
        finally:
            context.completed_at = datetime.now()
            duration = context.completed_at - context.started_at if context.started_at else None
            self.logger.info(f"Workflow {self.name} completed in {duration}")
    
    def _execute_steps(self, context: StepContext) -> StepExecutionResult:
        """Execute workflow steps sequentially.
        
        Args:
            context: Workflow execution context
            
        Returns:
            Final execution result
        """
        for i, step in enumerate(self.steps):
            self.logger.info(f"Executing step {i+1}/{len(self.steps)}: {step.name}")
            
            # Validate prerequisites
            if not step.validate_prerequisites(context):
                error_msg = f"Prerequisites not met for step {step.name}"
                context.add_error(error_msg)
                return StepExecutionResult.failure(error_msg)
            
            # Execute step
            try:
                result = step.execute(context)
                
                # Update context with step result data
                context.data.update(result.data)
                
                # Handle step result
                if result.status == StepResult.FAILURE:
                    context.add_error(result.message)
                    if not result.should_continue:
                        return result
                elif result.status == StepResult.SUCCESS:
                    self.logger.info(f"Step {step.name} completed: {result.message}")
                
                # Handle step skipping or jumping
                if result.next_step:
                    next_step_index = self._find_step_index(result.next_step)
                    if next_step_index is not None and next_step_index > i:
                        self.logger.info(f"Jumping to step {result.next_step}")
                        # Continue from the specified step
                        remaining_steps = self.steps[next_step_index:]
                        for remaining_step in remaining_steps:
                            sub_result = remaining_step.execute(context)
                            context.data.update(sub_result.data)
                            if sub_result.status == StepResult.FAILURE and not sub_result.should_continue:
                                return sub_result
                        break
                
            except Exception as e:
                error_msg = f"Step {step.name} failed with exception: {e}"
                self.logger.error(error_msg)
                context.add_error(error_msg)
                return StepExecutionResult.failure(error_msg)
            
            finally:
                # Always run cleanup
                try:
                    step.cleanup(context)
                except Exception as e:
                    self.logger.warning(f"Cleanup failed for step {step.name}: {e}")
        
        return StepExecutionResult.success("Workflow completed successfully")
    
    def _find_step_index(self, step_name: str) -> Optional[int]:
        """Find the index of a step by name.
        
        Args:
            step_name: Name of the step to find
            
        Returns:
            Step index if found, None otherwise
        """
        for i, step in enumerate(self.steps):
            if step.name == step_name:
                return i
        return None
    
    @abstractmethod
    def build_steps(self) -> List[BaseWorkflowStep]:
        """Build the list of steps for this workflow.
        
        Returns:
            List of workflow steps
        """
        pass
