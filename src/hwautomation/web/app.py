#!/usr/bin/env python3
"""
Flask Web Application for HWAutomation - Refactored with Blueprints.

Clean modular web interface with organized route blueprints.
Core workflow: MaaS device discovery → Device type selection → Batch commissioning → IPMI/BIOS configuration.
"""

import logging
import os
import sys
import threading
import time
import uuid
from pathlib import Path

from flask import Flask
from flask_socketio import SocketIO

# Configure unified logging
from hwautomation.logging import get_logger, set_correlation_id, setup_logging

# Set up unified logging system
environment = os.getenv("HW_AUTOMATION_ENV", "development")
setup_logging(environment=environment)
logger = get_logger(__name__)


def create_app():
    """Application factory for Flask app with blueprint architecture."""
    # Add src to path for development
    project_root = Path(__file__).parent.parent.parent.parent
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    # Import dependencies
    from hwautomation.database.helper import DbHelper
    from hwautomation.hardware.bios_config import BiosConfigManager
    from hwautomation.maas.client import create_maas_client
    from hwautomation.orchestration.device_selection import DeviceSelectionService
    from hwautomation.orchestration.server_provisioning import (
        ServerProvisioningWorkflow,
    )
    from hwautomation.orchestration.workflow_manager import WorkflowManager
    from hwautomation.utils.env_config import load_config

    # Initialize Flask app
    app = Flask(
        __name__,
        template_folder=str(Path(__file__).parent / "templates"),
        static_folder=str(Path(__file__).parent / "static"),
    )
    app.secret_key = os.environ.get("FLASK_SECRET_KEY", "hwautomation-web-interface")

    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")

    # Add correlation tracking to all requests
    from flask import request

    @app.before_request
    def before_request():
        """Set correlation ID for each request for better debugging."""
        correlation_id = (
            request.headers.get("X-Correlation-ID") or f"req-{uuid.uuid4().hex[:8]}"
        )
        set_correlation_id(correlation_id)

        # Log request start with correlation
        logger.info(f"Request started: {request.method} {request.path}")

    @app.after_request
    def after_request(response):
        """Log request completion with correlation."""
        logger.info(
            f"Request completed: {request.method} {request.path} - Status: {response.status_code}"
        )
        return response

    # Load configuration and initialize services
    config = load_config()

    # Database
    database_path = config.get("database", {}).get("path", "hw_automation.db")
    db_helper = DbHelper(database_path)

    # Workflow Manager (pass config, not db_helper)
    workflow_manager = WorkflowManager(config)

    # MaaS Client (if configured) - WorkflowManager already initializes MaaS client
    maas_client = None
    try:
        maas_config = config.get("maas", {})
        if maas_config:
            maas_client = create_maas_client(maas_config)
            # WorkflowManager already has its own MaaS client, but we can set it for compatibility
            if hasattr(workflow_manager, "maas_client"):
                workflow_manager.maas_client = maas_client
    except Exception as e:
        logger.warning(f"MaaS client initialization failed: {e}")

    # Global context processor for status indicators
    def get_global_stats():
        """Get global stats for status indicators."""
        stats = {
            "available_machines": 0,
            "device_types": 0,
            "database_servers": 0,
            "ready_servers": 0,
            "maas_status": "disconnected",
        }

        # Get server count from database if available
        if db_helper:
            try:
                cursor = db_helper.sql_db_worker.cursor()
                cursor.execute("SELECT COUNT(*) FROM servers")
                stats["database_servers"] = cursor.fetchone()[0]

                # Count ready servers
                cursor.execute(
                    "SELECT COUNT(*) FROM servers WHERE status_name = 'Ready'"
                )
                stats["ready_servers"] = cursor.fetchone()[0]
                cursor.close()
            except Exception as e:
                logger.warning(f"Could not get database stats: {e}")

        # Get MaaS machines count if configured
        maas_config = config.get("maas", {})
        maas_host = maas_config.get("host") or maas_config.get("url")
        maas_auth = maas_config.get("consumer_key") or maas_config.get("api_key")
        if not maas_host or not maas_auth:
            # MaaS not configured
            stats["maas_status"] = "not_configured"
        else:
            try:
                maas_client_instance = create_maas_client(maas_config)
                machines = maas_client_instance.get_machines()
                stats["available_machines"] = len(
                    [m for m in machines if m.get("status") == "Ready"]
                )
                stats["maas_status"] = "connected"
            except Exception as e:
                logger.warning(f"Could not get MaaS stats: {e}")
                stats["maas_status"] = "disconnected"

        # Get available device types from BIOS configuration
        try:
            bios_manager = BiosConfigManager()
            device_types = bios_manager.get_device_types()
            if not device_types:
                # Fallback to default types if none loaded
                device_types = [
                    "a1.c5.large",
                    "d1.c1.small",
                    "d1.c2.medium",
                    "d1.c2.large",
                ]
                logger.warning("No device types loaded from config, using defaults")
        except Exception as e:
            logger.warning(f"Could not load device types from config: {e}")
            # Fallback to default types
            device_types = ["a1.c5.large", "d1.c1.small", "d1.c2.medium", "d1.c2.large"]

        stats["device_types"] = len(device_types)

        return stats

    @app.context_processor
    def inject_global_stats():
        """Inject global stats into all templates."""
        return {"global_stats": get_global_stats()}

    # Import and register blueprints
    from hwautomation.web.routes import (
        core_bp,
        database_bp,
        firmware_bp,
        init_core_routes,
        init_database_routes,
        init_firmware_routes,
        init_logs_routes,
        init_maas_routes,
        init_orchestration_routes,
        logs_bp,
        maas_bp,
        orchestration_bp,
    )

    # Register blueprints
    if core_bp:
        app.register_blueprint(core_bp)
        if init_core_routes is not None:
            init_core_routes(app, db_helper, maas_client, config)

    if database_bp:
        app.register_blueprint(database_bp)
        if init_database_routes is not None:
            init_database_routes(app, db_helper)

    if orchestration_bp:
        app.register_blueprint(orchestration_bp)
        if init_orchestration_routes is not None:
            init_orchestration_routes(app, workflow_manager, socketio)

    if maas_bp:
        app.register_blueprint(maas_bp)
        if init_maas_routes is not None:
            init_maas_routes(app, config, create_maas_client)

    if logs_bp:
        app.register_blueprint(logs_bp)
        if init_logs_routes is not None:
            init_logs_routes(app)

    if firmware_bp:
        app.register_blueprint(firmware_bp)
        if init_firmware_routes is not None:
            init_firmware_routes(app, workflow_manager, db_helper, socketio)

    # WebSocket event handlers
    @socketio.on("connect")
    def handle_connect():
        """Handle WebSocket connection."""
        logger.info("WebSocket client connected")

    @socketio.on("disconnect")
    def handle_disconnect():
        """Handle WebSocket disconnection."""
        logger.info("WebSocket client disconnected")

    @socketio.on("subscribe_workflow")
    def handle_subscribe_workflow(data):
        """Subscribe to workflow progress updates."""
        workflow_id = data.get("workflow_id")
        logger.info(f"Client subscribed to workflow {workflow_id}")

    logger.info("HWAutomation Web Interface initialized with blueprint architecture")
    return app, socketio


# For backward compatibility and standalone usage
app, socketio = create_app()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="HWAutomation Web Interface")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    logger.info(f"Starting HWAutomation Web Interface on {args.host}:{args.port}")
    logger.info(f"Debug mode: {args.debug}")

    socketio.run(app, host=args.host, port=args.port, debug=args.debug)
