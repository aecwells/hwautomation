#!/usr/bin/env python3
"""
Logs routes for HWAutomation Web Interface

Handles log management, viewing, searching, and downloading.
"""

import logging

from flask import Blueprint, Response, jsonify, render_template, request

logger = logging.getLogger(__name__)

# Create blueprint for logs routes
logs_bp = Blueprint("logs", __name__, url_prefix="/api/logs")


@logs_bp.route("/")
def api_get_logs():
    """Get system logs with filtering."""
    try:
        level = request.args.get("level", "")
        component = request.args.get("component", "")
        lines = request.args.get("lines", "500")

        # Mock logs data for now
        # In a real implementation, you would read from log files
        mock_logs = [
            {
                "timestamp": "2024-01-01T12:00:00Z",
                "level": "INFO",
                "component": "web",
                "message": "HWAutomation web interface started",
            },
            {
                "timestamp": "2024-01-01T12:00:01Z",
                "level": "INFO",
                "component": "database",
                "message": "Database connection established",
            },
            {
                "timestamp": "2024-01-01T12:00:02Z",
                "level": "WARNING",
                "component": "maas",
                "message": "MaaS connection timeout, retrying...",
            },
        ]

        # Apply filters
        filtered_logs = mock_logs
        if level:
            filtered_logs = [log for log in filtered_logs if log["level"] == level]
        if component:
            filtered_logs = [
                log for log in filtered_logs if log["component"] == component
            ]

        # Apply lines limit
        try:
            lines_limit = int(lines)
            filtered_logs = filtered_logs[:lines_limit]
        except (ValueError, TypeError):
            pass

        return jsonify({"logs": filtered_logs})

    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        return jsonify({"error": str(e)}), 500


@logs_bp.route("/search")
def api_search_logs():
    """Search system logs."""
    try:
        query = request.args.get("query", "")
        regex = request.args.get("regex", "false").lower() == "true"

        # Mock search results
        mock_results = [
            {
                "timestamp": "2024-01-01T12:00:00Z",
                "level": "INFO",
                "component": "web",
                "message": f"Found log entry matching: {query}",
            }
        ]

        return jsonify({"results": mock_results})

    except Exception as e:
        logger.error(f"Failed to search logs: {e}")
        return jsonify({"error": str(e)}), 500


@logs_bp.route("/clear", methods=["POST"])
def api_clear_logs():
    """Clear system logs."""
    try:
        # In a real implementation, you would clear the actual log files
        logger.info("System logs cleared via API")
        return jsonify({"success": True, "message": "Logs cleared successfully"})

    except Exception as e:
        logger.error(f"Failed to clear logs: {e}")
        return jsonify({"error": str(e)}), 500


@logs_bp.route("/download")
def api_download_logs():
    """Download system logs as text file."""
    try:
        # Mock log content
        log_content = """[2024-01-01 12:00:00] [INFO] web: HWAutomation web interface started
[2024-01-01 12:00:01] [INFO] database: Database connection established
[2024-01-01 12:00:02] [WARNING] maas: MaaS connection timeout, retrying...
"""

        return Response(
            log_content,
            mimetype="text/plain",
            headers={
                "Content-Disposition": "attachment; filename=hwautomation_logs.txt"
            },
        )

    except Exception as e:
        logger.error(f"Failed to download logs: {e}")
        return jsonify({"error": str(e)}), 500


def init_logs_routes(app):
    """Initialize logs routes with dependencies."""

    # Page routes (not part of API blueprint)
    @app.route("/logs")
    def logs_view():
        """Logs view page."""
        return render_template("logs.html")
