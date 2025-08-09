"""
WebSocket managers for HWAutomation Web Interface.

This module provides WebSocket functionality for real-time communication
between the web interface and backend services.
"""

import json
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Set

from flask import request
from flask_socketio import SocketIO, disconnect, emit, join_room, leave_room

from hwautomation.logging import get_logger

logger = get_logger(__name__)


class WebSocketManager:
    """
    Base WebSocket manager with connection handling.

    Features:
    - Connection management
    - Room management
    - Message broadcasting
    - Event handling
    """

    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.connections: Dict[str, Dict[str, Any]] = {}
        self.rooms: Dict[str, Set[str]] = {}
        self.event_handlers: Dict[str, Callable] = {}

        # Register default event handlers
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default WebSocket event handlers."""

        @self.socketio.on("connect")
        def handle_connect():
            client_id = self._generate_client_id()
            self.connections[client_id] = {
                "session_id": request.sid,
                "connected_at": time.time(),
                "user_info": {},
                "rooms": set(),
            }

            logger.info(f"WebSocket client connected: {client_id}")

            # Send welcome message
            emit(
                "connected",
                {
                    "client_id": client_id,
                    "message": "Connected to HWAutomation",
                    "timestamp": time.time(),
                },
            )

        @self.socketio.on("disconnect")
        def handle_disconnect():
            client_id = self._get_client_id_by_session(request.sid)
            if client_id:
                # Leave all rooms
                client_rooms = self.connections[client_id].get("rooms", set())
                for room in list(client_rooms):
                    self.leave_room(client_id, room)

                # Remove connection
                del self.connections[client_id]
                logger.info(f"WebSocket client disconnected: {client_id}")

        @self.socketio.on("join_room")
        def handle_join_room(data):
            client_id = self._get_client_id_by_session(request.sid)
            room_name = data.get("room")

            if client_id and room_name:
                self.join_room(client_id, room_name)
                emit(
                    "joined_room",
                    {
                        "room": room_name,
                        "message": f"Joined room: {room_name}",
                        "timestamp": time.time(),
                    },
                )

        @self.socketio.on("leave_room")
        def handle_leave_room(data):
            client_id = self._get_client_id_by_session(request.sid)
            room_name = data.get("room")

            if client_id and room_name:
                self.leave_room(client_id, room_name)
                emit(
                    "left_room",
                    {
                        "room": room_name,
                        "message": f"Left room: {room_name}",
                        "timestamp": time.time(),
                    },
                )

    def _generate_client_id(self) -> str:
        """Generate unique client ID."""
        return f"ws-{uuid.uuid4().hex[:8]}"

    def _get_client_id_by_session(self, session_id: str) -> Optional[str]:
        """Get client ID by session ID."""
        for client_id, info in self.connections.items():
            if info["session_id"] == session_id:
                return client_id
        return None

    def join_room(self, client_id: str, room_name: str) -> bool:
        """Add client to a room."""
        if client_id not in self.connections:
            return False

        try:
            join_room(room_name)

            # Update tracking
            if room_name not in self.rooms:
                self.rooms[room_name] = set()

            self.rooms[room_name].add(client_id)
            self.connections[client_id]["rooms"].add(room_name)

            logger.debug(f"Client {client_id} joined room {room_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to join room {room_name}: {e}")
            return False

    def leave_room(self, client_id: str, room_name: str) -> bool:
        """Remove client from a room."""
        if client_id not in self.connections:
            return False

        try:
            leave_room(room_name)

            # Update tracking
            if room_name in self.rooms:
                self.rooms[room_name].discard(client_id)
                if not self.rooms[room_name]:
                    del self.rooms[room_name]

            self.connections[client_id]["rooms"].discard(room_name)

            logger.debug(f"Client {client_id} left room {room_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to leave room {room_name}: {e}")
            return False

    def broadcast_to_room(self, room_name: str, event: str, data: Any):
        """Broadcast message to all clients in a room."""
        try:
            self.socketio.emit(event, data, room=room_name)
            logger.debug(f"Broadcasted {event} to room {room_name}")
        except Exception as e:
            logger.error(f"Failed to broadcast to room {room_name}: {e}")

    def send_to_client(self, client_id: str, event: str, data: Any):
        """Send message to specific client."""
        if client_id not in self.connections:
            logger.warning(f"Client {client_id} not found")
            return False

        try:
            session_id = self.connections[client_id]["session_id"]
            self.socketio.emit(event, data, room=session_id)
            logger.debug(f"Sent {event} to client {client_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to send to client {client_id}: {e}")
            return False

    def broadcast_to_all(self, event: str, data: Any):
        """Broadcast message to all connected clients."""
        try:
            self.socketio.emit(event, data)
            logger.debug(f"Broadcasted {event} to all clients")
        except Exception as e:
            logger.error(f"Failed to broadcast to all clients: {e}")

    def get_room_clients(self, room_name: str) -> List[str]:
        """Get list of clients in a room."""
        return list(self.rooms.get(room_name, set()))

    def get_client_rooms(self, client_id: str) -> List[str]:
        """Get list of rooms a client is in."""
        if client_id in self.connections:
            return list(self.connections[client_id]["rooms"])
        return []

    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        return {
            "total_connections": len(self.connections),
            "total_rooms": len(self.rooms),
            "rooms": {room: len(clients) for room, clients in self.rooms.items()},
            "uptime_seconds": time.time()
            - min(
                (conn["connected_at"] for conn in self.connections.values()),
                default=time.time(),
            ),
        }


class ServerStatusManager(WebSocketManager):
    """
    WebSocket manager for server status updates.

    Features:
    - Server status broadcasting
    - Hardware monitoring
    - Real-time alerts
    """

    def __init__(self, socketio: SocketIO):
        super().__init__(socketio)
        self._register_server_handlers()

    def _register_server_handlers(self):
        """Register server-specific event handlers."""

        @self.socketio.on("subscribe_server_status")
        def handle_subscribe_server_status(data):
            client_id = self._get_client_id_by_session(request.sid)
            server_id = data.get("server_id")

            if client_id and server_id:
                room_name = f"server_{server_id}"
                self.join_room(client_id, room_name)

                # Send current status if available
                current_status = self._get_current_server_status(server_id)
                if current_status:
                    self.send_to_client(
                        client_id,
                        "server_status_update",
                        {
                            "server_id": server_id,
                            "status": current_status,
                            "timestamp": time.time(),
                        },
                    )

        @self.socketio.on("unsubscribe_server_status")
        def handle_unsubscribe_server_status(data):
            client_id = self._get_client_id_by_session(request.sid)
            server_id = data.get("server_id")

            if client_id and server_id:
                room_name = f"server_{server_id}"
                self.leave_room(client_id, room_name)

    def _get_current_server_status(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get current server status from database."""
        try:
            # This would integrate with your database layer
            # For now, return a placeholder
            return {
                "id": server_id,
                "status": "online",
                "last_seen": time.time(),
                "cpu_usage": 45.2,
                "memory_usage": 68.1,
                "disk_usage": 32.7,
            }
        except Exception as e:
            logger.error(f"Failed to get server status for {server_id}: {e}")
            return None

    def broadcast_server_status(self, server_id: str, status_data: Dict[str, Any]):
        """Broadcast server status update."""
        room_name = f"server_{server_id}"
        self.broadcast_to_room(
            room_name,
            "server_status_update",
            {"server_id": server_id, "status": status_data, "timestamp": time.time()},
        )

    def broadcast_server_alert(self, server_id: str, alert_data: Dict[str, Any]):
        """Broadcast server alert."""
        room_name = f"server_{server_id}"
        self.broadcast_to_room(
            room_name,
            "server_alert",
            {"server_id": server_id, "alert": alert_data, "timestamp": time.time()},
        )


class WorkflowManager(WebSocketManager):
    """
    WebSocket manager for workflow progress updates.

    Features:
    - Workflow progress tracking
    - Step-by-step updates
    - Error notifications
    """

    def __init__(self, socketio: SocketIO):
        super().__init__(socketio)
        self._register_workflow_handlers()

    def _register_workflow_handlers(self):
        """Register workflow-specific event handlers."""

        @self.socketio.on("subscribe_workflow")
        def handle_subscribe_workflow(data):
            client_id = self._get_client_id_by_session(request.sid)
            workflow_id = data.get("workflow_id")

            if client_id and workflow_id:
                room_name = f"workflow_{workflow_id}"
                self.join_room(client_id, room_name)

                # Send current workflow status
                current_status = self._get_current_workflow_status(workflow_id)
                if current_status:
                    self.send_to_client(
                        client_id,
                        "workflow_status_update",
                        {
                            "workflow_id": workflow_id,
                            "status": current_status,
                            "timestamp": time.time(),
                        },
                    )

        @self.socketio.on("unsubscribe_workflow")
        def handle_unsubscribe_workflow(data):
            client_id = self._get_client_id_by_session(request.sid)
            workflow_id = data.get("workflow_id")

            if client_id and workflow_id:
                room_name = f"workflow_{workflow_id}"
                self.leave_room(client_id, room_name)

    def _get_current_workflow_status(
        self, workflow_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get current workflow status from database."""
        try:
            # This would integrate with your workflow system
            # For now, return a placeholder
            return {
                "id": workflow_id,
                "status": "running",
                "progress": 65,
                "current_step": "Installing BIOS configuration",
                "total_steps": 5,
                "started_at": time.time() - 300,  # 5 minutes ago
            }
        except Exception as e:
            logger.error(f"Failed to get workflow status for {workflow_id}: {e}")
            return None

    def broadcast_workflow_progress(
        self, workflow_id: str, progress_data: Dict[str, Any]
    ):
        """Broadcast workflow progress update."""
        room_name = f"workflow_{workflow_id}"
        self.broadcast_to_room(
            room_name,
            "workflow_progress_update",
            {
                "workflow_id": workflow_id,
                "progress": progress_data,
                "timestamp": time.time(),
            },
        )

    def broadcast_workflow_step(self, workflow_id: str, step_data: Dict[str, Any]):
        """Broadcast workflow step update."""
        room_name = f"workflow_{workflow_id}"
        self.broadcast_to_room(
            room_name,
            "workflow_step_update",
            {"workflow_id": workflow_id, "step": step_data, "timestamp": time.time()},
        )

    def broadcast_workflow_completion(
        self, workflow_id: str, result_data: Dict[str, Any]
    ):
        """Broadcast workflow completion."""
        room_name = f"workflow_{workflow_id}"
        self.broadcast_to_room(
            room_name,
            "workflow_completed",
            {
                "workflow_id": workflow_id,
                "result": result_data,
                "timestamp": time.time(),
            },
        )

    def broadcast_workflow_error(self, workflow_id: str, error_data: Dict[str, Any]):
        """Broadcast workflow error."""
        room_name = f"workflow_{workflow_id}"
        self.broadcast_to_room(
            room_name,
            "workflow_error",
            {"workflow_id": workflow_id, "error": error_data, "timestamp": time.time()},
        )


class LogStreamManager(WebSocketManager):
    """
    WebSocket manager for real-time log streaming.

    Features:
    - Log level filtering
    - Component filtering
    - Real-time updates
    """

    def __init__(self, socketio: SocketIO):
        super().__init__(socketio)
        self._register_log_handlers()

    def _register_log_handlers(self):
        """Register log streaming event handlers."""

        @self.socketio.on("subscribe_logs")
        def handle_subscribe_logs(data):
            client_id = self._get_client_id_by_session(request.sid)
            log_level = data.get("level", "INFO")
            component = data.get("component", "all")

            if client_id:
                room_name = f"logs_{log_level}_{component}"
                self.join_room(client_id, room_name)

        @self.socketio.on("unsubscribe_logs")
        def handle_unsubscribe_logs(data):
            client_id = self._get_client_id_by_session(request.sid)
            log_level = data.get("level", "INFO")
            component = data.get("component", "all")

            if client_id:
                room_name = f"logs_{log_level}_{component}"
                self.leave_room(client_id, room_name)

    def broadcast_log_entry(self, log_entry: Dict[str, Any]):
        """Broadcast log entry to appropriate subscribers."""
        log_level = log_entry.get("level", "INFO")
        component = log_entry.get("component", "unknown")

        # Broadcast to level-specific rooms
        level_room = f"logs_{log_level}_all"
        self.broadcast_to_room(
            level_room, "log_entry", {"entry": log_entry, "timestamp": time.time()}
        )

        # Broadcast to component-specific rooms
        component_room = f"logs_INFO_{component}"
        self.broadcast_to_room(
            component_room, "log_entry", {"entry": log_entry, "timestamp": time.time()}
        )


class WebSocketManagerFactory:
    """
    Factory for creating WebSocket managers.

    Features:
    - Manager creation
    - Configuration
    - Integration
    """

    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.managers: Dict[str, WebSocketManager] = {}

    def create_manager(self, manager_type: str, **config) -> WebSocketManager:
        """Create WebSocket manager by type."""
        if manager_type == "base":
            manager = WebSocketManager(self.socketio)
        elif manager_type == "server_status":
            manager = ServerStatusManager(self.socketio)
        elif manager_type == "workflow":
            manager = WorkflowManager(self.socketio)
        elif manager_type == "logs":
            manager = LogStreamManager(self.socketio)
        else:
            raise ValueError(f"Unknown manager type: {manager_type}")

        self.managers[manager_type] = manager
        return manager

    def get_manager(self, manager_type: str) -> Optional[WebSocketManager]:
        """Get existing manager by type."""
        return self.managers.get(manager_type)

    def initialize_all(self) -> Dict[str, WebSocketManager]:
        """Initialize all standard managers."""
        managers = {}

        # Create all standard manager types
        for manager_type in ["base", "server_status", "workflow", "logs"]:
            managers[manager_type] = self.create_manager(manager_type)

        logger.info("All WebSocket managers initialized")
        return managers
