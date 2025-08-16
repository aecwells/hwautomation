"""
Core routes for HWAutomation Web Interface.

Handles main dashboard, health checks, documentation, and core application routes.
"""

import os
from datetime import datetime

from flask import (
    Blueprint,
    abort,
    jsonify,
    render_template,
    request,
    send_from_directory,
)

from hwautomation.hardware.bios import BiosConfigManager
from hwautomation.logging import get_logger

logger = get_logger(__name__)

# Create blueprint for core routes
core_bp = Blueprint("core", __name__)


@core_bp.route("/health")
def health_check():
    """Health check endpoint for load balancers."""
    return jsonify(
        {
            "status": "healthy",
            "service": "hwautomation-web",
            "timestamp": datetime.utcnow().isoformat(),
        }
    )


@core_bp.route("/")
def dashboard():
    """Display main dashboard with device overview and quick actions."""
    try:
        # Import here to avoid circular import
        from flask import current_app

        # Get configuration and dependencies from app context
        config = getattr(current_app, "_hwautomation_config", {})
        db_helper = getattr(current_app, "_hwautomation_db_helper", None)

        # Get dashboard statistics
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
        logger.info(
            f"MaaS config check - host: {bool(maas_config.get('host'))}, consumer_key: {bool(maas_config.get('consumer_key'))}"
        )

        if not maas_config.get("host") or not maas_config.get("consumer_key"):
            # MaaS not configured
            logger.info("MaaS not configured, skipping connection")
            stats["maas_status"] = "not_configured"
        else:
            try:
                import threading
                import time

                from hwautomation.maas.client import create_maas_client

                maas_result = {"completed": False, "data": None, "error": None}

                def maas_request():
                    try:
                        logger.info("Starting MaaS client creation...")
                        maas_client_instance = create_maas_client(maas_config)
                        logger.info("MaaS client created, getting machines...")
                        machines = maas_client_instance.get_machines()
                        logger.info(f"Got {len(machines)} machines from MaaS")
                        maas_result["data"] = len(
                            [m for m in machines if m.get("status") == "Ready"]
                        )
                        maas_result["completed"] = True
                        logger.info(
                            f"MaaS request completed successfully with {maas_result['data']} ready machines"
                        )
                    except Exception as e:
                        logger.error(f"MaaS request failed: {e}")
                        maas_result["error"] = str(e)
                        maas_result["completed"] = True

                # Start MaaS request in thread with timeout
                logger.info("Starting MaaS request thread...")
                thread = threading.Thread(target=maas_request)
                thread.daemon = True
                thread.start()
                thread.join(timeout=3)  # 3 second timeout for dashboard
                logger.info(f"MaaS thread completed: {maas_result['completed']}")

                if maas_result["completed"]:
                    if maas_result["error"]:
                        logger.warning(f"MaaS request failed: {maas_result['error']}")
                        stats["maas_status"] = "error"
                        stats["available_machines"] = 0
                    else:
                        stats["available_machines"] = maas_result["data"]
                        stats["maas_status"] = "connected"
                        logger.info(
                            f"MaaS connected successfully with {stats['available_machines']} ready machines"
                        )
                else:
                    logger.warning("MaaS request timed out after 3 seconds")
                    stats["maas_status"] = "timeout"
                    stats["available_machines"] = 0

            except Exception as e:
                logger.warning(f"Could not get MaaS stats: {e}")
                stats["maas_status"] = "disconnected"

        # Get available device types from unified configuration (Phase 4 enhancement)
        try:
            # Try unified configuration first (Phase 4)
            try:
                from hwautomation.config.unified_loader import UnifiedConfigLoader

                unified_loader = UnifiedConfigLoader()
                device_types = unified_loader.list_all_device_types()
                logger.info(
                    f"Loaded {len(device_types)} device types from unified config"
                )
            except Exception as unified_error:
                logger.warning(
                    f"Unified config failed, falling back to legacy: {unified_error}"
                )
                # Fallback to legacy BIOS configuration
                bios_manager = BiosConfigManager("configs/bios")
                device_types = bios_manager.get_device_types()

            if not device_types:
                # Final fallback to default types if none loaded
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

        return render_template("dashboard.html", stats=stats, device_types=device_types)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        # Provide default stats when there's an error
        default_stats = {
            "available_machines": 0,
            "device_types": 0,
            "database_servers": 0,
            "ready_servers": 0,
            "maas_status": "disconnected",
        }
        return render_template(
            "dashboard.html", stats=default_stats, device_types=[], error=str(e)
        )


@core_bp.route("/docs")
@core_bp.route("/docs/")
def documentation_index():
    """Redirect to the main documentation page."""
    return documentation("index.html")


@core_bp.route("/docs/<path:filename>")
def documentation(filename):
    """Serve Sphinx-generated HTML documentation."""
    try:
        # Get the project root directory - works in both local and Docker environments
        from flask import current_app

        # Try multiple paths for Docker and local development compatibility
        possible_paths = [
            # Docker container path (when running in /app)
            "/app/docs/_build/html",
            # Relative to Flask app root (local development)
            os.path.join(
                current_app.root_path, "..", "..", "..", "docs", "_build", "html"
            ),
            # Alternative relative path
            os.path.join(os.getcwd(), "docs", "_build", "html"),
        ]

        docs_build_dir = None
        for path in possible_paths:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path):
                docs_build_dir = abs_path
                logger.debug(f"Found documentation at: {docs_build_dir}")
                break

        if not docs_build_dir:
            logger.warning(
                f"Documentation build directory not found in any of: {possible_paths}"
            )
            return render_template("documentation_not_built.html"), 404

        # Serve the requested file
        if filename == "" or filename == "/":
            filename = "index.html"

        file_path = os.path.join(docs_build_dir, filename)
        if not os.path.exists(file_path):
            logger.warning(f"Documentation file not found: {file_path}")
            abort(404)

        return send_from_directory(docs_build_dir, filename)

    except Exception as e:
        logger.error(f"Error serving documentation: {e}")
        return render_template("error.html", error="Documentation unavailable"), 500


def init_core_routes(app, db_helper, maas_client, config):
    """Initialize core routes with dependencies."""
    # Store dependencies in app context for route access
    app._hwautomation_config = config
    app._hwautomation_db_helper = db_helper
    app._hwautomation_maas_client = maas_client
