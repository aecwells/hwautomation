#!/usr/bin/env python3
"""
MaaS routes for HWAutomation Web Interface

Handles MaaS integration, device discovery, and batch commissioning operations.
"""

import logging

from flask import Blueprint, current_app, jsonify, request

logger = logging.getLogger(__name__)

# Create blueprint for MaaS routes
maas_bp = Blueprint("maas", __name__, url_prefix="/api/maas")


@maas_bp.route("/discover")
def api_maas_discover():
    """Discover devices from MaaS API."""
    try:
        config = getattr(current_app, "_hwautomation_config", {})
        create_maas_client = getattr(
            current_app, "_hwautomation_create_maas_client", None
        )

        if not create_maas_client:
            return jsonify({"error": "MaaS client not available"}), 500

        maas_config = config.get("maas", {})
        # Use host as url if url is not set
        if not maas_config.get("url") and maas_config.get("host"):
            maas_config["url"] = maas_config["host"]

        if not maas_config.get("url") or not (
            maas_config.get("consumer_key")
            and maas_config.get("token_key")
            and maas_config.get("token_secret")
        ):
            return jsonify({"error": "MaaS not properly configured"}), 400

        maas_client = create_maas_client(maas_config)
        machines = maas_client.get_machines()

        # Filter for available machines
        available_devices = []
        for machine in machines:
            if machine.get("status") == "Ready":
                available_devices.append(
                    {
                        "system_id": machine.get("system_id"),
                        "hostname": machine.get("hostname", "Unknown"),
                        "status": machine.get("status"),
                        "architecture": machine.get("architecture", "Unknown"),
                        "cpu_count": machine.get("cpu_count", 0),
                    }
                )

        return jsonify(
            {
                "devices": available_devices,
                "available_count": len(available_devices),
                "total_discovered": len(machines),
            }
        )

    except Exception as e:
        logger.error(f"MaaS discovery failed: {e}")
        return jsonify({"error": str(e)}), 500


def init_maas_routes(app, config, create_maas_client):
    """Initialize MaaS routes with dependencies."""
    pass  # Routes now defined outside
