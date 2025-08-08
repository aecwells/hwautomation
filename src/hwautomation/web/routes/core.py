#!/usr/bin/env python3
"""
Core routes for HWAutomation Web Interface

Handles main dashboard, health checks, and core application routes.
."""

import logging
from datetime import datetime

from flask import Blueprint, jsonify, render_template, request

logger = logging.getLogger(__name__)

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
    """Main dashboard with device overview and quick actions."""
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
        if not maas_config.get("host") or not maas_config.get("consumer_key"):
            # MaaS not configured
            stats["maas_status"] = "not_configured"
        else:
            try:
                from hwautomation.maas.client import create_maas_client

                maas_client_instance = create_maas_client(maas_config)
                machines = maas_client_instance.get_machines()
                stats["available_machines"] = len(
                    [m for m in machines if m.get("status") == "Ready"]
                )
                stats["maas_status"] = "connected"
            except Exception as e:
                logger.warning(f"Could not get MaaS stats: {e}")
                stats["maas_status"] = "disconnected"

        # Get available device types
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


def init_core_routes(app, db_helper, maas_client, config):
    """Initialize core routes with dependencies."""
    # Store dependencies in app context for route access
    app._hwautomation_config = config
    app._hwautomation_db_helper = db_helper
    app._hwautomation_maas_client = maas_client
