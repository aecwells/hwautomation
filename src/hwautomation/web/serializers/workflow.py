"""
Workflow data serializers.

This module provides serialization for workflow and orchestration data
including progress tracking, step information, and timing data.
"""

import json
import time
from typing import Any, Dict, List

from .base import BaseSerializer, SerializationMixin


class WorkflowSerializer(BaseSerializer, SerializationMixin):
    """
    Serializer for workflow data with progress tracking.

    Features:
    - Workflow status formatting
    - Progress calculation
    - Step information
    - Duration tracking
    """

    def serialize_item(self, item: Any) -> Dict[str, Any]:
        """Serialize workflow data with specific formatting."""
        data = super().serialize_item(item)

        if isinstance(item, dict):
            workflow_data = item
        else:
            workflow_data = data

        formatted_data = {}

        # Basic workflow information
        formatted_data["id"] = workflow_data.get("id")
        formatted_data["type"] = workflow_data.get("type", "unknown")
        formatted_data["server_id"] = workflow_data.get("server_id")
        formatted_data["status"] = self._format_workflow_status(
            workflow_data.get("status")
        )

        # Progress information
        formatted_data["progress"] = self._format_progress_info(workflow_data)

        # Steps information
        formatted_data["steps"] = self._format_steps_info(workflow_data)

        # Timing information
        formatted_data["timing"] = self._format_timing_info(workflow_data)

        # Error information if applicable
        if workflow_data.get("error_message"):
            formatted_data["error"] = {
                "message": workflow_data.get("error_message"),
                "code": workflow_data.get("error_code"),
                "details": workflow_data.get("error_details"),
            }

        return formatted_data

    def _format_workflow_status(self, status: Any) -> Dict[str, Any]:
        """Format workflow status."""
        if isinstance(status, str):
            return {
                "name": status,
                "description": status.replace("_", " ").title(),
                "is_terminal": status in ["COMPLETED", "FAILED", "CANCELLED"],
                "is_active": status in ["PENDING", "RUNNING"],
            }

        return {
            "name": "unknown",
            "description": "Unknown status",
            "is_terminal": False,
            "is_active": False,
        }

    def _format_progress_info(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format progress information."""
        progress = {
            "percentage": workflow_data.get("progress_percentage", 0),
            "current_step": workflow_data.get("current_step"),
            "total_steps": workflow_data.get("total_steps"),
            "message": workflow_data.get("progress_message", ""),
        }

        # Calculate step progress if available
        if progress["current_step"] and progress["total_steps"]:
            try:
                current = int(progress["current_step"])
                total = int(progress["total_steps"])
                step_progress = (current / total) * 100
                progress["step_percentage"] = min(100, max(0, step_progress))
            except (ValueError, ZeroDivisionError):
                progress["step_percentage"] = 0

        return progress

    def _format_steps_info(self, workflow_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format workflow steps information."""
        steps_data = workflow_data.get("steps", [])
        if isinstance(steps_data, str):
            try:
                steps_data = json.loads(steps_data)
            except json.JSONDecodeError:
                steps_data = []

        formatted_steps = []
        for step in steps_data:
            if isinstance(step, dict):
                formatted_step = {
                    "name": step.get("name"),
                    "status": step.get("status", "pending"),
                    "message": step.get("message", ""),
                    "started_at": step.get("started_at"),
                    "completed_at": step.get("completed_at"),
                    "error": step.get("error"),
                }

                # Calculate step duration
                if step.get("started_at") and step.get("completed_at"):
                    try:
                        start = float(step["started_at"])
                        end = float(step["completed_at"])
                        formatted_step["duration"] = end - start
                    except (ValueError, TypeError):
                        formatted_step["duration"] = None

                formatted_steps.append(formatted_step)

        return formatted_steps

    def _format_timing_info(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format timing information."""
        timing = {}

        # Start and end times
        if workflow_data.get("started_at"):
            timing["started_at"] = workflow_data["started_at"]

        if workflow_data.get("completed_at"):
            timing["completed_at"] = workflow_data["completed_at"]

        # Calculate duration
        if timing.get("started_at") and timing.get("completed_at"):
            try:
                start = float(timing["started_at"])
                end = float(timing["completed_at"])
                timing["duration"] = end - start
                timing["duration_human"] = self._format_duration(timing["duration"])
            except (ValueError, TypeError):
                timing["duration"] = None

        # Estimated completion time for running workflows
        if (
            workflow_data.get("status") == "RUNNING"
            and timing.get("started_at")
            and workflow_data.get("progress_percentage")
        ):
            try:
                start = float(timing["started_at"])
                current = time.time()
                elapsed = current - start
                progress = float(workflow_data["progress_percentage"])

                if progress > 0:
                    estimated_total = elapsed / (progress / 100)
                    estimated_remaining = estimated_total - elapsed
                    timing["estimated_completion"] = current + estimated_remaining
                    timing["estimated_remaining"] = estimated_remaining
                    timing["estimated_remaining_human"] = self._format_duration(
                        estimated_remaining
                    )
            except (ValueError, TypeError, ZeroDivisionError):
                pass

        return timing


class WorkflowListSerializer(BaseSerializer):
    """Optimized serializer for workflow lists with minimal data."""

    def serialize_item(self, item: Any) -> Dict[str, Any]:
        """Serialize workflow data with minimal fields for lists."""
        data = super().serialize_item(item)

        if isinstance(item, dict):
            workflow_data = item
        else:
            workflow_data = data

        return {
            "id": workflow_data.get("id"),
            "type": workflow_data.get("type"),
            "server_id": workflow_data.get("server_id"),
            "status": workflow_data.get("status"),
            "progress_percentage": workflow_data.get("progress_percentage", 0),
            "started_at": workflow_data.get("started_at"),
            "completed_at": workflow_data.get("completed_at"),
        }
