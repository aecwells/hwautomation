"""Base classes for orchestration workflows and steps.

This module provides the foundational abstractions for building
modular orchestration workflows with composable steps.
"""

import json
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
        next_step: Optional[str] = None,
    ) -> "StepExecutionResult":
        """Create a success result."""
        return cls(
            status=StepResult.SUCCESS,
            message=message,
            data=data or {},
            should_continue=True,
            next_step=next_step,
        )

    @classmethod
    def failure(
        cls,
        message: str,
        should_continue: bool = False,
        data: Optional[Dict[str, Any]] = None,
    ) -> "StepExecutionResult":
        """Create a failure result."""
        return cls(
            status=StepResult.FAILURE,
            message=message,
            data=data or {},
            should_continue=should_continue,
        )

    @classmethod
    def retry(
        cls,
        message: str = "Step should be retried",
        data: Optional[Dict[str, Any]] = None,
    ) -> "StepExecutionResult":
        """Create a retry result."""
        return cls(
            status=StepResult.RETRY,
            message=message,
            data=data or {},
            should_continue=False,
        )

    @classmethod
    def skip(
        cls,
        message: str = "Step skipped",
        data: Optional[Dict[str, Any]] = None,
        next_step: Optional[str] = None,
    ) -> "StepExecutionResult":
        """Create a skip result."""
        return cls(
            status=StepResult.SKIP,
            message=message,
            data=data or {},
            should_continue=True,
            next_step=next_step,
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
        retry_delay: float = 1.0,
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
                        self.logger.info(
                            f"Step {self.name} succeeded after {attempt + 1} attempts"
                        )
                    return result
                elif result.status != StepResult.RETRY:
                    # Non-retryable failure
                    return result

                last_result = result

                if attempt < self.max_retries:
                    self.logger.warning(
                        f"Step {self.name} failed, retrying in {self.retry_delay}s..."
                    )
                    time.sleep(self.retry_delay)

            except Exception as e:
                self.logger.error(f"Step {self.name} failed with exception: {e}")
                last_result = StepExecutionResult.failure(
                    f"Exception in {self.name}: {e}"
                )

                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)

        # All retries exhausted
        self.logger.error(
            f"Step {self.name} failed after {self.max_retries + 1} attempts"
        )
        return last_result or StepExecutionResult.failure(
            f"Step {self.name} failed after retries"
        )

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
        self.status = WorkflowStatus.PENDING
        self.current_step_index = 0
        self.current_step_name = ""
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def _record_workflow_start(self, context: "StepContext") -> None:
        """Record workflow start in database."""
        try:
            # Get database helper from context
            db_helper = context.data.get("db_helper")
            if not db_helper:
                self.logger.warning(
                    "No database helper available for workflow recording"
                )
                return

            # Get workflow ID from context or use name as fallback
            workflow_id = getattr(context, "workflow_id", self.name)

            with db_helper.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO workflow_history (
                        workflow_id, server_id, device_type, status,
                        started_at, total_steps, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        workflow_id,
                        getattr(context, "server_id", None),
                        getattr(context, "device_type", None),
                        self.status.value,
                        self.start_time.isoformat() if self.start_time else None,
                        len(self.steps),
                        self._get_metadata_json(context),
                    ),
                )
                conn.commit()
                self.logger.info(f"Recorded workflow start for {workflow_id}")

        except Exception as e:
            self.logger.error(f"Failed to record workflow start: {e}")

    def _update_workflow_status(self, context: "StepContext") -> None:
        """Update workflow status in database."""
        try:
            # Get database helper from context
            db_helper = context.data.get("db_helper")
            if not db_helper:
                return

            # Get workflow ID from context or use name as fallback
            workflow_id = getattr(context, "workflow_id", self.name)

            with db_helper.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE workflow_history
                    SET status = ?, completed_at = ?, metadata = ?
                    WHERE workflow_id = ?
                """,
                    (
                        self.status.value,
                        self.end_time.isoformat() if self.end_time else None,
                        self._get_metadata_json(context),
                        workflow_id,
                    ),
                )
                conn.commit()
                self.logger.info(
                    f"Updated workflow status to {self.status.value} for {workflow_id}"
                )

        except Exception as e:
            self.logger.error(f"Failed to update workflow status: {e}")

    def _update_workflow_progress(self, context: "StepContext") -> None:
        """Update workflow progress in database."""
        try:
            # Get database helper from context
            db_helper = context.data.get("db_helper")
            if not db_helper:
                return

            # Get workflow ID from context or use name as fallback
            workflow_id = getattr(context, "workflow_id", self.name)

            with db_helper.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    UPDATE workflow_history
                    SET steps_completed = ?, metadata = ?
                    WHERE workflow_id = ?
                """,
                    (
                        self.current_step_index,
                        self._get_metadata_json(context),
                        workflow_id,
                    ),
                )
                conn.commit()
                self.logger.debug(
                    f"Updated workflow progress: {self.current_step_index}/{len(self.steps)} for {workflow_id}"
                )

        except Exception as e:
            self.logger.error(f"Failed to update workflow progress: {e}")

    def _get_metadata_json(self, context: "StepContext") -> str:
        """Get workflow metadata as JSON string."""
        try:
            metadata = {
                "workflow_name": self.name,
                "description": self.description,
                "current_step_name": self.current_step_name,
                "current_step_index": self.current_step_index,
                "total_steps": len(self.steps),
                "steps": [
                    {
                        "name": step.name,
                        "description": step.description,
                        "status": (
                            "completed" if i < self.current_step_index else "pending"
                        ),
                    }
                    for i, step in enumerate(self.steps)
                ],
                "context_data": {
                    "server_ip": getattr(context, "server_ip", None),
                    "ipmi_ip": getattr(context, "ipmi_ip", None),
                    "gateway": getattr(context, "gateway", None),
                },
                "timestamps": {
                    "start_time": (
                        self.start_time.isoformat() if self.start_time else None
                    ),
                    "end_time": self.end_time.isoformat() if self.end_time else None,
                    "started_at": (
                        context.started_at.isoformat()
                        if getattr(context, "started_at", None)
                        else None
                    ),
                    "completed_at": (
                        context.completed_at.isoformat()
                        if getattr(context, "completed_at", None)
                        else None
                    ),
                },
                "errors": getattr(context, "errors", []),
            }
            return json.dumps(metadata, default=str)
        except Exception as e:
            self.logger.error(f"Failed to serialize metadata: {e}")
            return "{}"

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
        self.start_time = datetime.now()
        context.started_at = self.start_time

        # Record workflow start in database
        self._record_workflow_start(context)

        try:
            result = self._execute_steps(context)

            # Update final status
            if result.status == StepResult.SUCCESS:
                self.status = WorkflowStatus.COMPLETED
            else:
                self.status = WorkflowStatus.FAILED

            return result
        except Exception as e:
            self.status = WorkflowStatus.FAILED
            self.logger.error(f"Workflow {self.name} failed with exception: {e}")
            raise
        finally:
            self.end_time = datetime.now()
            context.completed_at = self.end_time
            duration = (
                context.completed_at - context.started_at
                if context.started_at
                else None
            )
            self.logger.info(f"Workflow {self.name} completed in {duration}")

            # Update final status in database
            self._update_workflow_status(context)

    def _execute_steps(self, context: StepContext) -> StepExecutionResult:
        """Execute workflow steps sequentially.

        Args:
            context: Workflow execution context

        Returns:
            Final execution result
        """
        self.status = WorkflowStatus.RUNNING

        for i, step in enumerate(self.steps):
            self.current_step_index = i + 1
            self.current_step_name = step.name
            self.logger.info(f"Executing step {i+1}/{len(self.steps)}: {step.name}")

            # Validate prerequisites
            if not step.validate_prerequisites(context):
                error_msg = f"Prerequisites not met for step {step.name}"
                context.add_error(error_msg)
                self.status = WorkflowStatus.FAILED
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
                    # Update workflow progress in database
                    self._update_workflow_progress(context)

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
                            if (
                                sub_result.status == StepResult.FAILURE
                                and not sub_result.should_continue
                            ):
                                return sub_result
                        break

            except Exception as e:
                error_msg = f"Step {step.name} failed with exception: {e}"
                self.logger.error(error_msg)
                context.add_error(error_msg)
                self.status = WorkflowStatus.FAILED
                return StepExecutionResult.failure(error_msg)

            finally:
                # Always run cleanup
                try:
                    step.cleanup(context)
                except Exception as e:
                    self.logger.warning(f"Cleanup failed for step {step.name}: {e}")

        # All steps completed successfully
        self.status = WorkflowStatus.SUCCESS
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

    def get_status(self) -> Dict[str, Any]:
        """Get workflow status for API consumption.

        Returns:
            Dictionary containing workflow status information
        """
        return {
            "id": getattr(self, "workflow_id", self.name),
            "name": self.name,
            "description": self.description,
            "status": (
                self.status.value if hasattr(self.status, "value") else str(self.status)
            ),
            "current_step_index": self.current_step_index,
            "current_step_name": self.current_step_name,
            "total_steps": len(self.steps),
            "progress": (
                (self.current_step_index / len(self.steps) * 100) if self.steps else 0
            ),
        }

    @abstractmethod
    def build_steps(self) -> List[BaseWorkflowStep]:
        """Build the list of steps for this workflow.

        Returns:
            List of workflow steps
        """
        pass
