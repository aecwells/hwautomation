"""MaaS routes for HWAutomation Web Interface.

Handles MaaS integration, device discovery, and batch commissioning operations.
"""

from flask import Blueprint, current_app, jsonify, request

from hwautomation.logging import get_logger, log_activity

logger = get_logger(__name__)

# Create blueprint for MaaS routes
maas_bp = Blueprint("maas", __name__, url_prefix="/api/maas")


@maas_bp.route("/test")
def api_maas_test():
    """Test MaaS connectivity and configuration."""
    try:
        config = getattr(current_app, "_hwautomation_config", {})
        create_maas_client = getattr(
            current_app, "_hwautomation_create_maas_client", None
        )

        if not create_maas_client:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": "MaaS client not available",
                        "config": None,
                    }
                ),
                500,
            )

        maas_config = config.get("maas", {})

        # Show configuration (without secrets)
        config_display = {
            "url": maas_config.get("url"),
            "host": maas_config.get("host"),
            "consumer_key": (
                maas_config.get("consumer_key", "")[:10] + "..."
                if maas_config.get("consumer_key")
                else None
            ),
            "token_key": (
                maas_config.get("token_key", "")[:10] + "..."
                if maas_config.get("token_key")
                else None
            ),
            "has_token_secret": bool(maas_config.get("token_secret")),
            "timeout": maas_config.get("timeout", 30),
            "verify_ssl": maas_config.get("verify_ssl", True),
        }

        if not maas_config.get("url") and not maas_config.get("host"):
            return jsonify(
                {
                    "success": False,
                    "error": "MaaS URL/host not configured",
                    "config": config_display,
                }
            )

        if not (
            maas_config.get("consumer_key")
            and maas_config.get("token_key")
            and maas_config.get("token_secret")
        ):
            return jsonify(
                {
                    "success": False,
                    "error": "MaaS authentication not properly configured",
                    "config": config_display,
                }
            )

        try:
            maas_client = create_maas_client(maas_config)

            # Test basic connectivity
            machines = maas_client.get_machines()

            machine_summary = []
            status_counts = {}

            for machine in machines:
                hostname = machine.get("hostname", "Unknown")
                status = machine.get("status_name", "Unknown")
                system_id = machine.get("system_id", "Unknown")

                machine_summary.append(
                    {"hostname": hostname, "system_id": system_id, "status": status}
                )

                status_counts[status] = status_counts.get(status, 0) + 1

            return jsonify(
                {
                    "success": True,
                    "config": config_display,
                    "machine_count": len(machines),
                    "status_summary": status_counts,
                    "machines": machine_summary[:10],  # First 10 machines
                }
            )

        except Exception as e:
            return jsonify(
                {
                    "success": False,
                    "error": f"MaaS connection failed: {str(e)}",
                    "config": config_display,
                }
            )

    except Exception as e:
        logger.error(f"MaaS test error: {e}")
        return (
            jsonify(
                {"success": False, "error": f"Test failed: {str(e)}", "config": None}
            ),
            500,
        )


@maas_bp.route("/discover")
def api_maas_discover():
    """Discover devices from MaaS API."""
    try:
        log_activity(
            "maas",
            "discover_start",
            "Starting device discovery from MaaS API",
            level="INFO",
        )

        config = getattr(current_app, "_hwautomation_config", {})
        create_maas_client = getattr(
            current_app, "_hwautomation_create_maas_client", None
        )

        if not create_maas_client:
            log_activity(
                "maas", "discover_error", "MaaS client not available", level="ERROR"
            )
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
            log_activity(
                "maas", "discover_error", "MaaS not properly configured", level="ERROR"
            )
            return jsonify({"error": "MaaS not properly configured"}), 400

        maas_client = create_maas_client(maas_config)
        machines = maas_client.get_machines()

        # Return all machines with their status for filtering
        all_devices = []
        ready_devices = []

        for machine in machines:
            device_info = {
                "system_id": machine.get("system_id"),
                "hostname": machine.get("hostname", "Unknown"),
                "status": machine.get(
                    "status_name"
                ),  # Use status_name instead of status
                "architecture": machine.get("architecture", "Unknown"),
                "cpu_count": machine.get("cpu_count", 0),
            }
            all_devices.append(device_info)

            # Count ready devices separately for backward compatibility
            if machine.get("status_name") == "Ready":  # Use status_name
                ready_devices.append(device_info)

        log_activity(
            "maas",
            "discover_complete",
            f"Device discovery completed: {len(ready_devices)} ready, {len(machines)} total",
            level="INFO",
            details={
                "ready_count": len(ready_devices),
                "total_count": len(machines),
                "discovered_devices": [d["hostname"] for d in all_devices],
            },
        )

        return jsonify(
            {
                "devices": all_devices,  # Return all devices for filtering
                "available_count": len(ready_devices),  # Ready devices count
                "total_discovered": len(machines),
            }
        )

    except Exception as e:
        logger.error(f"MaaS discovery failed: {e}")
        log_activity(
            "maas", "discover_error", f"MaaS discovery failed: {str(e)}", level="ERROR"
        )
        return jsonify({"error": str(e)}), 500


def init_maas_routes(app, config, create_maas_client):
    """Initialize MaaS routes with dependencies."""
    # Store configuration and MaaS client factory in app for routes to access
    app._hwautomation_config = config
    app._hwautomation_create_maas_client = create_maas_client
