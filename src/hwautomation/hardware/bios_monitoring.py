"""
Real-time progress monitoring for BIOS configuration operations.

Provides WebSocket support, detailed sub-task reporting, and cancellation capabilities.
."""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class OperationStatus(Enum):
    """BIOS configuration operation status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ProgressEventType(Enum):
    """Types of progress events."""

    OPERATION_STARTED = "operation_started"
    OPERATION_COMPLETED = "operation_completed"
    OPERATION_FAILED = "operation_failed"
    OPERATION_CANCELLED = "operation_cancelled"
    SUBTASK_STARTED = "subtask_started"
    SUBTASK_COMPLETED = "subtask_completed"
    SUBTASK_FAILED = "subtask_failed"
    PROGRESS_UPDATE = "progress_update"
    ERROR_OCCURRED = "error_occurred"
    WARNING_OCCURRED = "warning_occurred"
    INFO_MESSAGE = "info_message"


@dataclass
class ProgressEvent:
    """Progress event data structure."""

    event_type: ProgressEventType
    operation_id: str
    timestamp: datetime
    message: str
    progress_percentage: float = 0.0
    subtask_name: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_type": self.event_type.value,
            "operation_id": self.operation_id,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
            "progress_percentage": self.progress_percentage,
            "subtask_name": self.subtask_name,
            "error_details": self.error_details,
            "metadata": self.metadata,
        }


@dataclass
class OperationProgress:
    """Overall operation progress tracking."""

    operation_id: str
    status: OperationStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    progress_percentage: float = 0.0
    current_subtask: Optional[str] = None
    completed_subtasks: List[str] = field(default_factory=list)
    failed_subtasks: List[str] = field(default_factory=list)
    total_subtasks: int = 0
    error_count: int = 0
    warning_count: int = 0
    cancellation_requested: bool = False

    @property
    def duration(self) -> Optional[timedelta]:
        """Calculate operation duration."""
        if self.start_time:
            end = self.end_time or datetime.now()
            return end - self.start_time
        return None

    @property
    def estimated_completion(self) -> Optional[datetime]:
        """Estimate completion time based on current progress."""
        if self.progress_percentage > 0 and self.status == OperationStatus.RUNNING:
            duration = self.duration
            if duration:
                total_estimated = duration.total_seconds() / (
                    self.progress_percentage / 100.0
                )
                return self.start_time + timedelta(seconds=total_estimated)
        return None


class ProgressCallback:
    """Interface for progress callbacks."""

    async def on_progress_event(self, event: ProgressEvent):
        """Handle progress event."""
        pass

    async def on_operation_status_change(
        self, operation_id: str, status: OperationStatus
    ):
        """Handle operation status change."""
        pass


class WebSocketProgressCallback(ProgressCallback):
    """WebSocket-based progress callback for real-time updates."""

    def __init__(self, websocket_handler=None):
        self.websocket_handler = websocket_handler
        self.connected_clients = set()

    async def on_progress_event(self, event: ProgressEvent):
        """Send progress event via WebSocket."""
        if self.websocket_handler and self.connected_clients:
            message = {"type": "progress_event", "data": event.to_dict()}
            await self._broadcast_message(message)

    async def on_operation_status_change(
        self, operation_id: str, status: OperationStatus
    ):
        """Send status change via WebSocket."""
        if self.websocket_handler and self.connected_clients:
            message = {
                "type": "status_change",
                "data": {
                    "operation_id": operation_id,
                    "status": status.value,
                    "timestamp": datetime.now().isoformat(),
                },
            }
            await self._broadcast_message(message)

    async def _broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        if self.websocket_handler:
            disconnected_clients = set()
            for client in self.connected_clients:
                try:
                    await client.send(json.dumps(message))
                except Exception as e:
                    logger.warning(f"Failed to send message to WebSocket client: {e}")
                    disconnected_clients.add(client)

            # Remove disconnected clients
            self.connected_clients -= disconnected_clients

    def add_client(self, websocket):
        """Add WebSocket client."""
        self.connected_clients.add(websocket)

    def remove_client(self, websocket):
        """Remove WebSocket client."""
        self.connected_clients.discard(websocket)


class BiosConfigMonitor:
    """
    Real-time monitoring for BIOS configuration operations.

    Provides comprehensive progress tracking, error monitoring, and real-time
    updates for BIOS configuration operations with WebSocket support.
    ."""

    def __init__(self):
        self.operations: Dict[str, OperationProgress] = {}
        self.progress_callbacks: List[ProgressCallback] = []
        self.event_history: List[ProgressEvent] = []
        self.max_history_size = 1000

    def add_progress_callback(self, callback: ProgressCallback):
        """Add progress callback for real-time updates."""
        self.progress_callbacks.append(callback)

    def remove_progress_callback(self, callback: ProgressCallback):
        """Remove progress callback."""
        if callback in self.progress_callbacks:
            self.progress_callbacks.remove(callback)

    def create_operation(
        self,
        operation_type: str = "bios_configuration",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create new monitored operation."""
        operation_id = str(uuid.uuid4())

        self.operations[operation_id] = OperationProgress(
            operation_id=operation_id,
            status=OperationStatus.PENDING,
            start_time=datetime.now(),
        )

        # Create operation started event
        event = ProgressEvent(
            event_type=ProgressEventType.OPERATION_STARTED,
            operation_id=operation_id,
            timestamp=datetime.now(),
            message=f"Started {operation_type} operation",
            metadata=metadata or {},
        )

        asyncio.create_task(self._emit_event(event))

        return operation_id

    async def start_operation(self, operation_id: str, total_subtasks: int = 0):
        """Start monitoring an operation."""
        if operation_id not in self.operations:
            raise ValueError(f"Operation {operation_id} not found")

        operation = self.operations[operation_id]
        operation.status = OperationStatus.RUNNING
        operation.start_time = datetime.now()
        operation.total_subtasks = total_subtasks

        await self._emit_status_change(operation_id, OperationStatus.RUNNING)

    async def complete_operation(
        self,
        operation_id: str,
        success: bool = True,
        final_message: str = "Operation completed",
    ):
        """Complete an operation."""
        if operation_id not in self.operations:
            raise ValueError(f"Operation {operation_id} not found")

        operation = self.operations[operation_id]
        operation.end_time = datetime.now()
        operation.progress_percentage = 100.0

        if success:
            operation.status = OperationStatus.COMPLETED
            event_type = ProgressEventType.OPERATION_COMPLETED
        else:
            operation.status = OperationStatus.FAILED
            event_type = ProgressEventType.OPERATION_FAILED

        event = ProgressEvent(
            event_type=event_type,
            operation_id=operation_id,
            timestamp=datetime.now(),
            message=final_message,
            progress_percentage=100.0,
        )

        await self._emit_event(event)
        await self._emit_status_change(operation_id, operation.status)

    async def cancel_operation(
        self, operation_id: str, reason: str = "Operation cancelled"
    ):
        """Cancel an operation."""
        if operation_id not in self.operations:
            raise ValueError(f"Operation {operation_id} not found")

        operation = self.operations[operation_id]
        operation.status = OperationStatus.CANCELLED
        operation.end_time = datetime.now()
        operation.cancellation_requested = True

        event = ProgressEvent(
            event_type=ProgressEventType.OPERATION_CANCELLED,
            operation_id=operation_id,
            timestamp=datetime.now(),
            message=reason,
        )

        await self._emit_event(event)
        await self._emit_status_change(operation_id, OperationStatus.CANCELLED)

    async def start_subtask(
        self, operation_id: str, subtask_name: str, description: str = ""
    ):
        """Start a subtask within an operation."""
        if operation_id not in self.operations:
            raise ValueError(f"Operation {operation_id} not found")

        operation = self.operations[operation_id]
        operation.current_subtask = subtask_name

        event = ProgressEvent(
            event_type=ProgressEventType.SUBTASK_STARTED,
            operation_id=operation_id,
            timestamp=datetime.now(),
            message=f"Started subtask: {subtask_name}",
            subtask_name=subtask_name,
            metadata={"description": description},
        )

        await self._emit_event(event)

    async def complete_subtask(
        self,
        operation_id: str,
        subtask_name: str,
        success: bool = True,
        message: str = "",
    ):
        """Complete a subtask."""
        if operation_id not in self.operations:
            raise ValueError(f"Operation {operation_id} not found")

        operation = self.operations[operation_id]

        if success:
            operation.completed_subtasks.append(subtask_name)
            event_type = ProgressEventType.SUBTASK_COMPLETED
            event_message = message or f"Completed subtask: {subtask_name}"
        else:
            operation.failed_subtasks.append(subtask_name)
            operation.error_count += 1
            event_type = ProgressEventType.SUBTASK_FAILED
            event_message = message or f"Failed subtask: {subtask_name}"

        # Update overall progress
        if operation.total_subtasks > 0:
            completed_count = len(operation.completed_subtasks) + len(
                operation.failed_subtasks
            )
            operation.progress_percentage = (
                completed_count / operation.total_subtasks
            ) * 100

        operation.current_subtask = None

        event = ProgressEvent(
            event_type=event_type,
            operation_id=operation_id,
            timestamp=datetime.now(),
            message=event_message,
            progress_percentage=operation.progress_percentage,
            subtask_name=subtask_name,
        )

        await self._emit_event(event)

    async def update_progress(
        self,
        operation_id: str,
        percentage: float,
        message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Update operation progress."""
        if operation_id not in self.operations:
            raise ValueError(f"Operation {operation_id} not found")

        operation = self.operations[operation_id]
        operation.progress_percentage = min(100.0, max(0.0, percentage))

        event = ProgressEvent(
            event_type=ProgressEventType.PROGRESS_UPDATE,
            operation_id=operation_id,
            timestamp=datetime.now(),
            message=message,
            progress_percentage=operation.progress_percentage,
            metadata=metadata or {},
        )

        await self._emit_event(event)

    async def log_error(
        self,
        operation_id: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
    ):
        """Log an error during operation."""
        if operation_id not in self.operations:
            raise ValueError(f"Operation {operation_id} not found")

        operation = self.operations[operation_id]
        operation.error_count += 1

        event = ProgressEvent(
            event_type=ProgressEventType.ERROR_OCCURRED,
            operation_id=operation_id,
            timestamp=datetime.now(),
            message=error_message,
            error_details=error_details,
        )

        await self._emit_event(event)

    async def log_warning(self, operation_id: str, warning_message: str):
        """Log a warning during operation."""
        if operation_id not in self.operations:
            raise ValueError(f"Operation {operation_id} not found")

        operation = self.operations[operation_id]
        operation.warning_count += 1

        event = ProgressEvent(
            event_type=ProgressEventType.WARNING_OCCURRED,
            operation_id=operation_id,
            timestamp=datetime.now(),
            message=warning_message,
        )

        await self._emit_event(event)

    async def log_info(
        self,
        operation_id: str,
        info_message: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log an info message during operation."""
        event = ProgressEvent(
            event_type=ProgressEventType.INFO_MESSAGE,
            operation_id=operation_id,
            timestamp=datetime.now(),
            message=info_message,
            metadata=metadata or {},
        )

        await self._emit_event(event)

    def get_operation_status(self, operation_id: str) -> Optional[OperationProgress]:
        """Get current operation status."""
        return self.operations.get(operation_id)

    def is_operation_cancelled(self, operation_id: str) -> bool:
        """Check if operation is cancelled."""
        operation = self.operations.get(operation_id)
        return operation.cancellation_requested if operation else False

    def get_active_operations(self) -> List[OperationProgress]:
        """Get all active operations."""
        return [
            op
            for op in self.operations.values()
            if op.status in [OperationStatus.PENDING, OperationStatus.RUNNING]
        ]

    def get_operation_history(self, operation_id: str) -> List[ProgressEvent]:
        """Get event history for an operation."""
        return [
            event for event in self.event_history if event.operation_id == operation_id
        ]

    async def _emit_event(self, event: ProgressEvent):
        """Emit progress event to all callbacks."""
        # Add to history
        self.event_history.append(event)

        # Trim history if needed
        if len(self.event_history) > self.max_history_size:
            self.event_history = self.event_history[-self.max_history_size :]

        # Notify callbacks
        for callback in self.progress_callbacks:
            try:
                await callback.on_progress_event(event)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

    async def _emit_status_change(self, operation_id: str, status: OperationStatus):
        """Emit status change to all callbacks."""
        for callback in self.progress_callbacks:
            try:
                await callback.on_operation_status_change(operation_id, status)
            except Exception as e:
                logger.error(f"Error in status change callback: {e}")


# Global monitor instance
global_monitor = BiosConfigMonitor()


def get_monitor() -> BiosConfigMonitor:
    """Get the global monitor instance."""
    return global_monitor


async def create_monitored_operation(
    operation_type: str = "bios_configuration",
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a new monitored operation."""
    return global_monitor.create_operation(operation_type, metadata)
