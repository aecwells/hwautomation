"""
Core Workflow Engine

Contains the Workflow class responsible for executing individual workflow instances.
"""

import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ...logging import get_logger
from .base import (
    StepStatus,
    WorkflowContext,
    WorkflowExecutionError,
    WorkflowStatus,
    WorkflowStep,
    WorkflowTimeoutError,
)

logger = get_logger(__name__)


class Workflow:
    """
    Individual workflow instance

    Manages the execution of a sequence of steps with error handling,
    retries, and status tracking.
    """

    def __init__(self, workflow_id: str, manager: Any):  # manager: WorkflowManager
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
        self._cancelled = False

    def add_step(self, step: WorkflowStep):
        """Add a step to the workflow."""
        self.steps.append(step)

    def set_progress_callback(self, callback: Callable):
        """Set callback for progress updates."""
        self.progress_callback = callback

    def _report_sub_task(self, sub_task_description: str):
        """Report a sub-task being executed."""
        self.current_sub_task = sub_task_description
        logger.info(f"Sub-task: {sub_task_description}")

        if self.progress_callback:
            self.progress_callback(
                {
                    "workflow_id": self.id,
                    "step": (
                        self.current_step_index + 1
                        if self.current_step_index is not None
                        else None
                    ),
                    "total_steps": len(self.steps),
                    "step_name": (
                        self.steps[self.current_step_index].name
                        if self.current_step_index is not None
                        else None
                    ),
                    "status": "running",
                    "sub_task": sub_task_description,
                }
            )

    def execute(self, context: WorkflowContext) -> bool:
        """Execute the workflow."""
        if self._cancelled:
            logger.info(f"Workflow {self.id} was cancelled before execution")
            return False

        self.context = context
        self.context.workflow_id = self.id
        self.context.sub_task_callback = self._report_sub_task

        self.status = WorkflowStatus.RUNNING
        self.start_time = datetime.now()

        # Record workflow start in database
        self._record_workflow_start()

        logger.info(f"Starting workflow {self.id} with {len(self.steps)} steps")

        try:
            for i, step in enumerate(self.steps):
                if self._cancelled:
                    logger.info(f"Workflow {self.id} cancelled at step {i + 1}")
                    self.status = WorkflowStatus.CANCELLED
                    self.end_time = datetime.now()
                    # Update database with cancellation
                    self._update_workflow_status()
                    return False

                self.current_step_index = i
                success = self._execute_step(step, i + 1, len(self.steps))

                # Update progress in database
                self._update_workflow_progress()

                if not success:
                    self.status = WorkflowStatus.FAILED
                    self.error = step.error
                    self.end_time = datetime.now()
                    # Update database with failure
                    self._update_workflow_status()
                    logger.error(f"Workflow {self.id} failed at step: {step.name}")
                    return False

            self.status = WorkflowStatus.COMPLETED
            self.end_time = datetime.now()
            # Update database with completion
            self._update_workflow_status()
            logger.info(f"Workflow {self.id} completed successfully")
            return True

        except Exception as e:
            self.status = WorkflowStatus.FAILED
            self.error = str(e)
            self.end_time = datetime.now()
            # Update database with failure
            self._update_workflow_status()
            logger.error(f"Workflow {self.id} failed: {e}")
            return False

    def _execute_step(
        self, step: WorkflowStep, step_num: int, total_steps: int
    ) -> bool:
        """Execute a single workflow step with retry logic."""
        step.status = StepStatus.RUNNING
        step.start_time = datetime.now()

        logger.info(f"Executing step {step_num}/{total_steps}: {step.name}")

        if self.progress_callback:
            self.progress_callback(
                {
                    "workflow_id": self.id,
                    "step": step_num,
                    "total_steps": total_steps,
                    "step_name": step.name,
                    "status": "running",
                    "sub_task": None,
                }
            )

        for attempt in range(step.retry_count):
            if self._cancelled:
                step.status = StepStatus.SKIPPED
                step.error = "Workflow cancelled"
                return False

            try:
                # Execute step with timeout
                start_time = time.time()
                step.result = step.function(self.context)

                # Check timeout
                if time.time() - start_time > step.timeout:
                    raise WorkflowTimeoutError(
                        f"Step timed out after {step.timeout} seconds"
                    )

                step.status = StepStatus.COMPLETED
                step.end_time = datetime.now()

                if self.progress_callback:
                    self.progress_callback(
                        {
                            "workflow_id": self.id,
                            "step": step_num,
                            "total_steps": total_steps,
                            "step_name": step.name,
                            "status": "completed",
                            "sub_task": None,
                        }
                    )

                logger.info(f"Step {step.name} completed successfully")
                return True

            except Exception as e:
                logger.warning(
                    f"Step {step.name} failed (attempt {attempt + 1}/{step.retry_count}): {e}"
                )

                if attempt == step.retry_count - 1:
                    # Final attempt failed
                    step.status = StepStatus.FAILED
                    step.error = str(e)
                    step.end_time = datetime.now()

                    if self.progress_callback:
                        self.progress_callback(
                            {
                                "workflow_id": self.id,
                                "step": step_num,
                                "total_steps": total_steps,
                                "step_name": step.name,
                                "status": "failed",
                                "error": str(e),
                                "sub_task": None,
                            }
                        )

                    logger.error(f"Step {step.name} failed after all retries: {e}")
                    return False

                # Wait before retry (exponential backoff)
                if attempt < step.retry_count - 1:
                    wait_time = 2**attempt  # 1s, 2s, 4s, etc.
                    logger.info(f"Retrying step {step.name} in {wait_time} seconds...")
                    time.sleep(wait_time)

        return False

    def cancel(self):
        """Cancel the workflow execution."""
        self._cancelled = True
        self.status = WorkflowStatus.CANCELLED
        self.end_time = datetime.now()

        # Update database with cancellation
        self._update_workflow_status()

        logger.info(f"Workflow {self.id} marked for cancellation")

        if self.progress_callback:
            self.progress_callback(
                {
                    "workflow_id": self.id,
                    "step": (
                        self.current_step_index + 1
                        if self.current_step_index is not None
                        else None
                    ),
                    "total_steps": len(self.steps),
                    "step_name": (
                        self.steps[self.current_step_index].name
                        if self.current_step_index is not None
                        else None
                    ),
                    "status": "cancelled",
                    "sub_task": None,
                }
            )

    def get_status(self) -> Dict[str, Any]:
        """Get current workflow status."""
        status_data = {
            "id": self.id,
            "status": self.status.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error": self.error,
            "current_step_index": self.current_step_index,
            "current_step_name": None,  # Initialize as None
            "current_sub_task": self.current_sub_task,  # Add current sub-task
            "steps": [
                {
                    "name": step.name,
                    "description": step.description,
                    "status": step.status.value,
                    "error": step.error,
                    "start_time": (
                        step.start_time.isoformat() if step.start_time else None
                    ),
                    "end_time": step.end_time.isoformat() if step.end_time else None,
                }
                for step in self.steps
            ],
        }

        # Add current step name if available
        if self.current_step_index is not None and 0 <= self.current_step_index < len(
            self.steps
        ):
            status_data["current_step_name"] = self.steps[self.current_step_index].name

        return status_data

    def _record_workflow_start(self):
        """Record workflow start in the database."""
        if not self.context or not self.context.db_helper:
            logger.warning(f"No database helper available for workflow {self.id}")
            return

        try:
            with self.context.db_helper.get_connection() as conn:
                cursor = conn.cursor()

                cursor.execute(
                    """
                    INSERT INTO workflow_history
                    (workflow_id, server_id, device_type, status, started_at, total_steps, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        self.id,
                        self.context.server_id,
                        self.context.device_type,
                        self.status.value,
                        self.start_time.isoformat() if self.start_time else None,
                        len(self.steps),
                        self._get_metadata_json(),
                    ),
                )
                conn.commit()
                logger.debug(f"Recorded workflow start for {self.id}")
        except Exception as e:
            logger.error(f"Failed to record workflow start: {e}")

    def _update_workflow_status(self):
        """Update workflow status in the database."""
        if not self.context or not self.context.db_helper:
            return

        try:
            with self.context.db_helper.get_connection() as conn:
                cursor = conn.cursor()

                completed_steps = sum(
                    1
                    for step in self.steps
                    if step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED]
                )

                cursor.execute(
                    """
                    UPDATE workflow_history
                    SET status = ?, completed_at = ?, steps_completed = ?,
                        error_message = ?, metadata = ?
                    WHERE workflow_id = ?
                    """,
                    (
                        self.status.value,
                        self.end_time.isoformat() if self.end_time else None,
                        completed_steps,
                        self.error,
                        self._get_metadata_json(),
                        self.id,
                    ),
                )
                conn.commit()
                logger.debug(f"Updated workflow status for {self.id}")
        except Exception as e:
            logger.error(f"Failed to update workflow status: {e}")

    def _update_workflow_progress(self):
        """Update workflow progress in the database."""
        if not self.context or not self.context.db_helper:
            return

        try:
            with self.context.db_helper.get_connection() as conn:
                cursor = conn.cursor()

                completed_steps = sum(
                    1
                    for step in self.steps
                    if step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED]
                )

                cursor.execute(
                    """
                    UPDATE workflow_history
                    SET steps_completed = ?, metadata = ?
                    WHERE workflow_id = ?
                    """,
                    (
                        completed_steps,
                        self._get_metadata_json(),
                        self.id,
                    ),
                )
                conn.commit()
                logger.debug(
                    f"Updated workflow progress for {self.id}: {completed_steps}/{len(self.steps)} steps"
                )
        except Exception as e:
            logger.error(f"Failed to update workflow progress: {e}")

    def _get_metadata_json(self) -> str:
        """Get workflow metadata as JSON string."""
        import json

        metadata = {
            "steps": [
                {
                    "name": step.name,
                    "status": step.status.value,
                    "start_time": (
                        step.start_time.isoformat() if step.start_time else None
                    ),
                    "end_time": step.end_time.isoformat() if step.end_time else None,
                    "error": step.error,
                }
                for step in self.steps
            ],
            "context": (
                {
                    "target_ipmi_ip": (
                        self.context.target_ipmi_ip if self.context else None
                    ),
                    "gateway": self.context.gateway if self.context else None,
                    "rack_location": (
                        self.context.rack_location if self.context else None
                    ),
                }
                if self.context
                else {}
            ),
        }

        # Add any additional context metadata
        if self.context and hasattr(self.context, "metadata"):
            metadata.update(self.context.metadata)

        return json.dumps(metadata)
