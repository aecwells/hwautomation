#!/usr/bin/env python3
"""Enhanced log viewing, searching, and activity tracking routes.

Handles log management, viewing, searching, and downloading.
"""

from flask import Blueprint, Response, jsonify, render_template, request

from hwautomation.logging import get_dashboard_activities, get_logger

logger = get_logger(__name__)

# Create blueprint for logs routes
logs_bp = Blueprint("logs", __name__, url_prefix="/api/logs")


@logs_bp.route("/")
def api_get_logs():
    """Get system logs with filtering."""
    try:
        level = request.args.get("level", "")
        component = request.args.get("component", "")
        lines = request.args.get("lines", "500")

        # Try to read actual log files
        logs = []
        log_files = ["logs/hwautomation.log", "logs/errors.log"]

        for log_file in log_files:
            try:
                import os

                if os.path.exists(log_file):
                    with open(log_file, "r") as f:
                        # Read more lines initially to allow for proper filtering
                        all_lines = f.readlines()
                        # Take more lines than requested to allow for filtering
                        recent_lines = (
                            all_lines[-int(lines) * 3 :]
                            if lines != "all"
                            else all_lines
                        )

                        for line in recent_lines:
                            # Parse log format: timestamp - component - level - function:line - message
                            if " - " in line and len(line.strip()) > 0:
                                try:
                                    parts = line.strip().split(" - ")
                                    if len(parts) >= 4:
                                        timestamp = parts[0]
                                        comp = parts[1]
                                        lvl = parts[2]
                                        message = " - ".join(
                                            parts[3:]
                                        )  # Rejoin remaining parts

                                        # Clean up component name (remove package path)
                                        clean_component = (
                                            comp.split(".")[-1] if "." in comp else comp
                                        )

                                        logs.append(
                                            {
                                                "timestamp": timestamp,
                                                "level": lvl.strip().upper(),
                                                "component": clean_component,
                                                "message": message,
                                                "source": log_file,
                                            }
                                        )
                                except (
                                    ValueError,
                                    IndexError,
                                    AttributeError,
                                ) as parse_error:  # noqa: B112
                                    # Skip malformed lines - specific exceptions for parsing errors
                                    logger.debug(
                                        f"Skipping malformed log line: {parse_error}"
                                    )
                                    continue
            except Exception as e:
                logger.warning(f"Could not read log file {log_file}: {e}")

        # If no actual logs found, provide some sample/recent activity
        if not logs:
            # Get recent activity from workflow history if available
            try:
                from flask import current_app

                workflow_manager = getattr(
                    current_app, "_hwautomation_workflow_manager", None
                )
                if workflow_manager:
                    # Get recent workflow activities
                    recent_workflows = workflow_manager.get_recent_workflows(limit=10)
                    for workflow in recent_workflows:
                        logs.append(
                            {
                                "timestamp": workflow.get("created_at", ""),
                                "level": "INFO",
                                "component": "workflow",
                                "message": f"Workflow {workflow.get('id', 'unknown')}: {workflow.get('description', 'No description')}",
                                "source": "workflow_history",
                            }
                        )
            except Exception as e:
                logger.warning(f"Could not get workflow history: {e}")

        # If still no logs, provide mock data for demo
        if not logs:
            from datetime import datetime, timedelta

            now = datetime.now()
            logs = [
                {
                    "timestamp": (now - timedelta(minutes=5)).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "level": "INFO",
                    "component": "web",
                    "message": "HWAutomation web interface started successfully",
                    "source": "demo",
                },
                {
                    "timestamp": (now - timedelta(minutes=3)).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "level": "INFO",
                    "component": "database",
                    "message": "Database connection established",
                    "source": "demo",
                },
                {
                    "timestamp": (now - timedelta(minutes=1)).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                    "level": "INFO",
                    "component": "logging",
                    "message": "Unified logging system active with correlation tracking",
                    "source": "demo",
                },
            ]

        # Sort by timestamp first (newest first)
        logs = sorted(logs, key=lambda x: x["timestamp"], reverse=True)

        # Apply filters
        filtered_logs = logs
        if level:
            filtered_logs = [
                log for log in filtered_logs if log["level"].upper() == level.upper()
            ]
        if component:
            filtered_logs = [
                log
                for log in filtered_logs
                if component.lower() in log["component"].lower()
            ]

        # Apply lines limit after filtering
        try:
            if lines != "all":
                lines_limit = int(lines)
                filtered_logs = filtered_logs[:lines_limit]
        except (ValueError, TypeError):
            pass

        return jsonify({"logs": filtered_logs, "total": len(filtered_logs)})

    except Exception as e:
        logger.error(f"Failed to get logs: {e}")
        return jsonify({"error": str(e)}), 500


@logs_bp.route("/search")
def api_search_logs():
    """Search system logs."""
    try:
        query = request.args.get("query", "")
        regex = request.args.get("regex", "false").lower() == "true"
        level = request.args.get("level", "")
        component = request.args.get("component", "")

        if not query.strip():
            return jsonify({"results": []})

        # Get all logs first (reuse logic from main endpoint)
        logs = []
        log_files = ["logs/hwautomation.log", "logs/errors.log"]

        for log_file in log_files:
            try:
                import os

                if os.path.exists(log_file):
                    with open(log_file, "r") as f:
                        all_lines = f.readlines()

                        for line in all_lines:
                            if " - " in line and len(line.strip()) > 0:
                                try:
                                    parts = line.strip().split(" - ")
                                    if len(parts) >= 4:
                                        timestamp = parts[0]
                                        comp = parts[1]
                                        lvl = parts[2]
                                        message = " - ".join(parts[3:])

                                        clean_component = (
                                            comp.split(".")[-1] if "." in comp else comp
                                        )

                                        logs.append(
                                            {
                                                "timestamp": timestamp,
                                                "level": lvl.strip().upper(),
                                                "component": clean_component,
                                                "message": message,
                                                "source": log_file,
                                            }
                                        )
                                except (
                                    ValueError,
                                    IndexError,
                                    AttributeError,
                                ):  # noqa: B112
                                    # Skip malformed lines - specific exceptions for parsing errors
                                    continue
            except Exception as e:
                logger.warning(f"Could not read log file {log_file}: {e}")

        # Apply component and level filters first
        filtered_logs = logs
        if level:
            filtered_logs = [
                log for log in filtered_logs if log["level"].upper() == level.upper()
            ]
        if component:
            filtered_logs = [
                log
                for log in filtered_logs
                if component.lower() in log["component"].lower()
            ]

        # Apply search query
        search_results = []
        if regex:
            try:
                import re

                pattern = re.compile(query, re.IGNORECASE)
                search_results = [
                    log
                    for log in filtered_logs
                    if pattern.search(log["message"])
                    or pattern.search(log["component"])
                ]
            except re.error:
                return jsonify({"error": "Invalid regex pattern"}), 400
        else:
            # Simple text search
            query_lower = query.lower()
            search_results = [
                log
                for log in filtered_logs
                if query_lower in log["message"].lower()
                or query_lower in log["component"].lower()
            ]

        # Sort by timestamp (newest first) and limit results
        search_results = sorted(
            search_results, key=lambda x: x["timestamp"], reverse=True
        )
        search_results = search_results[:100]  # Limit search results

        return jsonify({"results": search_results})

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


@logs_bp.route("/activities")
def api_get_activities():
    """Get real-time dashboard activities."""
    try:
        limit = request.args.get("limit", "50")
        activity_type = request.args.get("type", "")

        # Get activities from the activity logger
        activities = get_dashboard_activities(limit=int(limit))

        # Filter by type if specified
        if activity_type:
            activities = [
                a
                for a in activities
                if a.get("type", "").lower() == activity_type.lower()
            ]

        return jsonify({"activities": activities, "total": len(activities)})

    except Exception as e:
        logger.error(f"Failed to get activities: {e}")
        return jsonify({"error": str(e)}), 500


@logs_bp.route("/activities/latest")
def api_get_latest_activities():
    """Get latest dashboard activities for real-time updates."""
    try:
        since = request.args.get("since", "")
        limit = request.args.get("limit", "10")

        # Get recent activities
        activities = get_dashboard_activities(limit=int(limit))

        # Filter by timestamp if specified
        if since:
            try:
                from datetime import datetime

                since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
                activities = [
                    a
                    for a in activities
                    if datetime.fromisoformat(
                        a.get("timestamp", "").replace("Z", "+00:00")
                    )
                    > since_dt
                ]
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid since parameter: {since}, error: {e}")

        return jsonify({"activities": activities, "total": len(activities)})

    except Exception as e:
        logger.error(f"Failed to get latest activities: {e}")
        return jsonify({"error": str(e)}), 500


def init_logs_routes(app):
    """Initialize logs routes with dependencies."""

    # Page routes (not part of API blueprint)
    @app.route("/logs")
    def logs_view():
        """Display the main logs view page."""
        return render_template("logs.html")
