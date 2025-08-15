#!/usr/bin/env python3
"""
Firmware Management Routes for HWAutomation Web Interface

Provides web endpoints for firmware inventory, scheduling, and monitoring.
Integrates with FirmwareManager and FirmwareProvisioningWorkflow.
"""

import json
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_socketio import emit

from ...logging import get_logger

logger = get_logger(__name__)

# Create blueprint for firmware routes
firmware_bp = Blueprint("firmware", __name__, url_prefix="/firmware")


class FirmwareWebManager:
    """Manages firmware operations for web interface."""

    def __init__(self, firmware_manager, workflow_manager, db_helper, socketio=None):
        """Initialize firmware web manager.

        Args:
            firmware_manager: FirmwareManager instance (can be None)
            workflow_manager: WorkflowManager instance
            db_helper: Database helper instance
            socketio: SocketIO instance for real-time updates
        """
        self.firmware_manager = firmware_manager
        self.workflow_manager = workflow_manager
        self.db_helper = db_helper
        self.socketio = socketio
        self._active_updates = {}  # Track active firmware updates

    def get_firmware_inventory(self) -> Dict[str, Any]:
        """Get comprehensive firmware inventory across all servers.

        Returns:
            Dict containing firmware status, versions, and update availability
        """
        try:
            inventory: Dict[str, Any] = {
                "servers": [],
                "device_types": [],
                "update_summary": {
                    "total_servers": 0,
                    "updates_available": 0,
                    "up_to_date": 0,
                    "unknown_status": 0,
                },
                "firmware_repository": {
                    "total_files": 0,
                    "vendors": [],
                    "latest_versions": {},
                },
            }

            # Get device types and motherboard information
            inventory["device_types"] = self._get_device_types_firmware_info()

            # Get all servers from database
            try:
                cursor = self.db_helper.sql_db_worker.execute(
                    """
                    SELECT server_id, server_id as hostname, status_name, device_type, ipmi_address
                    FROM servers
                    WHERE status_name != 'Deleted'
                    ORDER BY server_id
                """
                )
                servers = cursor.fetchall()
            except Exception as e:
                logger.warning(f"Failed to query servers from database: {e}")
                servers = []

            inventory["update_summary"]["total_servers"] = len(servers)

            # Check firmware status for each server
            for server in servers:
                server_id, hostname, status, device_type, ipmi_ip = server

                server_info = {
                    "id": server_id,
                    "hostname": hostname or f"Server-{server_id}",
                    "status": status,
                    "device_type": device_type,
                    "ipmi_ip": ipmi_ip,
                    "firmware_status": "unknown",
                    "bios_version": "Unknown",
                    "bmc_version": "Unknown",
                    "updates_available": False,
                    "last_checked": None,
                }

                # Try to get current firmware versions if server is accessible
                if ipmi_ip and status in ["Ready", "Deployed"]:
                    try:
                        # This would integrate with actual firmware detection
                        # For now, simulate firmware version detection
                        server_info["firmware_status"] = "detected"
                        server_info["bios_version"] = "Simulated-v1.0"
                        server_info["bmc_version"] = "Simulated-BMC-v2.0"
                        server_info["last_checked"] = datetime.now().isoformat()

                        # Check for available updates
                        available_updates = self._check_available_updates(device_type)
                        if available_updates:
                            server_info["updates_available"] = True
                            server_info["available_updates"] = available_updates
                            inventory["update_summary"]["updates_available"] += 1
                        else:
                            inventory["update_summary"]["up_to_date"] += 1

                    except Exception as e:
                        logger.warning(
                            f"Failed to check firmware for server {server_id}: {e}"
                        )
                        inventory["update_summary"]["unknown_status"] += 1
                else:
                    inventory["update_summary"]["unknown_status"] += 1

                inventory["servers"].append(server_info)

            # Get firmware repository information
            try:
                from pathlib import Path

                firmware_base_path = Path("/app/firmware")  # Docker path
                if not firmware_base_path.exists():
                    firmware_base_path = Path("./firmware")  # Local path

                if firmware_base_path.exists():
                    # Count firmware files
                    firmware_extensions = [".bin", ".rom", ".fwpkg", ".fw", ".img"]
                    firmware_files: List[Path] = []
                    for ext in firmware_extensions:
                        firmware_files.extend(firmware_base_path.rglob(f"*{ext}"))

                    inventory["firmware_repository"]["total_files"] = len(
                        firmware_files
                    )

                    # Get vendor directories
                    vendor_dirs = [
                        d.name
                        for d in firmware_base_path.iterdir()
                        if d.is_dir() and not d.name.startswith(".")
                    ]
                    inventory["firmware_repository"]["vendors"] = vendor_dirs
                else:
                    inventory["firmware_repository"]["total_files"] = 0
                    inventory["firmware_repository"]["vendors"] = []

            except Exception as e:
                logger.warning(f"Failed to get firmware repository info: {e}")

            return inventory

        except Exception as e:
            logger.error(f"Failed to get firmware inventory: {e}")
            return {
                "servers": [],
                "update_summary": {
                    "total_servers": 0,
                    "updates_available": 0,
                    "up_to_date": 0,
                    "unknown_status": 0,
                },
                "firmware_repository": {
                    "total_files": 0,
                    "vendors": [],
                    "latest_versions": {},
                },
            }

    def _check_available_updates(self, device_type: str) -> List[Dict]:
        """Check for available firmware updates for device type.

        Args:
            device_type: Device type to check updates for

        Returns:
            List of available updates
        """
        try:
            # This would integrate with actual firmware version comparison
            # For now, simulate available updates
            if device_type and "large" in device_type:
                return [
                    {
                        "component": "BIOS",
                        "current": "v1.0",
                        "available": "v1.2",
                        "priority": "recommended",
                    },
                    {
                        "component": "BMC",
                        "current": "v2.0",
                        "available": "v2.1",
                        "priority": "optional",
                    },
                ]
            return []

        except Exception as e:
            logger.warning(f"Failed to check updates for {device_type}: {e}")
            return []

    def _get_device_types_firmware_info(self) -> List[Dict[str, Any]]:
        """Get firmware information for all device types from device mappings.

        Returns:
            List of device types with motherboard and firmware information
        """
        try:
            device_types = []

            # Load device mappings
            device_mappings_path = Path("./configs/bios/device_mappings.yaml")
            if not device_mappings_path.exists():
                device_mappings_path = Path("/app/configs/bios/device_mappings.yaml")

            if not device_mappings_path.exists():
                logger.warning("Device mappings file not found")
                return []

            with open(device_mappings_path, "r") as f:
                mappings = yaml.safe_load(f)

            device_types_config = mappings.get("device_types", {})

            for device_type, config in device_types_config.items():
                # Clean up device type name (remove extra spaces)
                clean_device_type = device_type.strip()

                motherboards = config.get("motherboards", ["Unknown"])
                vendor = config.get("hardware_specs", {}).get("vendor", "unknown")
                description = config.get("description", "No description available")
                cpu_name = config.get("hardware_specs", {}).get(
                    "cpu_name", "Unknown CPU"
                )
                ram_gb = config.get("hardware_specs", {}).get("ram_gb", 0)
                cpu_cores = config.get("hardware_specs", {}).get("cpu_cores", 0)

                # Get firmware versions for each motherboard
                for motherboard in motherboards:
                    if motherboard != "Unknown":
                        # Get current firmware versions (simulated for now)
                        bios_version, bmc_version = (
                            self._get_motherboard_firmware_versions(vendor, motherboard)
                        )

                        # Check for available firmware files
                        available_firmware = self._get_available_firmware_files(
                            vendor, motherboard
                        )

                        device_info = {
                            "device_type": clean_device_type,
                            "motherboard": motherboard,
                            "vendor": vendor.title(),
                            "description": description,
                            "cpu_name": cpu_name,
                            "ram_gb": ram_gb,
                            "cpu_cores": cpu_cores,
                            "bios_version": bios_version,
                            "bmc_version": bmc_version,
                            "firmware_files": available_firmware,
                            "last_updated": datetime.now().strftime("%Y-%m-%d"),
                        }
                        device_types.append(device_info)

            return sorted(device_types, key=lambda x: x["device_type"])

        except Exception as e:
            logger.error(f"Failed to get device types firmware info: {e}")
            return []

    def _get_motherboard_firmware_versions(
        self, vendor: str, motherboard: str
    ) -> tuple:
        """Get current firmware versions for a specific motherboard.

        Args:
            vendor: Hardware vendor (supermicro, hpe, etc.)
            motherboard: Motherboard model

        Returns:
            Tuple of (bios_version, bmc_version)
        """
        try:
            # This would integrate with actual firmware detection
            # For now, provide realistic simulated versions based on vendor/motherboard

            if vendor.lower() == "supermicro":
                if "X12" in motherboard:
                    return ("3.7", "1.73.14")
                elif "X13" in motherboard:
                    return ("1.2", "1.00.25")
                elif "X11" in motherboard:
                    return ("3.4", "1.66.07")
                else:
                    return ("2.5", "1.50.10")
            elif vendor.lower() == "hpe":
                return ("U46 2.78", "iLO 5 2.82")
            else:
                return ("1.0.0", "1.0.0")

        except Exception as e:
            logger.warning(
                f"Failed to get firmware versions for {vendor}/{motherboard}: {e}"
            )
            return ("Unknown", "Unknown")

    def _get_available_firmware_files(
        self, vendor: str, motherboard: str
    ) -> List[Dict[str, Any]]:
        """Get available firmware files for a specific motherboard.

        Args:
            vendor: Hardware vendor
            motherboard: Motherboard model

        Returns:
            List of available firmware files with metadata
        """
        try:
            firmware_files = []

            # Check firmware directory
            firmware_base_path = Path("/app/firmware")  # Docker path
            if not firmware_base_path.exists():
                firmware_base_path = Path("./firmware")  # Local path

            if not firmware_base_path.exists():
                return []

            vendor_path = firmware_base_path / vendor.lower()
            if not vendor_path.exists():
                return []

            # Check BIOS files
            bios_path = vendor_path / "bios"
            if bios_path.exists():
                firmware_extensions = [".bin", ".rom", ".fwpkg", ".fw", ".img", ".cap"]
                for ext in firmware_extensions:
                    for file_path in bios_path.glob(f"*{ext}"):
                        if (
                            motherboard.lower() in file_path.name.lower()
                            or "universal" in file_path.name.lower()
                        ):
                            file_info = {
                                "filename": file_path.name,
                                "type": "BIOS",
                                "size": self._format_file_size(
                                    file_path.stat().st_size
                                ),
                                "date_modified": datetime.fromtimestamp(
                                    file_path.stat().st_mtime
                                ).strftime("%Y-%m-%d"),
                                "path": str(file_path.relative_to(firmware_base_path)),
                                "download_url": f"/firmware/api/download/{vendor.lower()}/bios/{file_path.name}",
                            }
                            firmware_files.append(file_info)

            # Check BMC files
            bmc_path = vendor_path / "bmc"
            if bmc_path.exists():
                firmware_extensions = [".bin", ".rom", ".fwpkg", ".fw", ".img", ".cap"]
                for ext in firmware_extensions:
                    for file_path in bmc_path.glob(f"*{ext}"):
                        if (
                            motherboard.lower() in file_path.name.lower()
                            or "universal" in file_path.name.lower()
                        ):
                            file_info = {
                                "filename": file_path.name,
                                "type": "BMC",
                                "size": self._format_file_size(
                                    file_path.stat().st_size
                                ),
                                "date_modified": datetime.fromtimestamp(
                                    file_path.stat().st_mtime
                                ).strftime("%Y-%m-%d"),
                                "path": str(file_path.relative_to(firmware_base_path)),
                                "download_url": f"/firmware/api/download/{vendor.lower()}/bmc/{file_path.name}",
                            }
                            firmware_files.append(file_info)

            return sorted(firmware_files, key=lambda x: (x["type"], x["filename"]))

        except Exception as e:
            logger.warning(
                f"Failed to get firmware files for {vendor}/{motherboard}: {e}"
            )
            return []

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB"]
        import math

        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"

    def schedule_firmware_update(
        self, server_ids: List[str], update_config: Dict
    ) -> Dict[str, Any]:
        """Schedule firmware updates for specified servers.

        Args:
            server_ids: List of server IDs to update
            update_config: Update configuration (components, scheduling, etc.)

        Returns:
            Dict with scheduling results
        """
        try:
            scheduled_updates = []
            failed_schedules = []

            for server_id in server_ids:
                try:
                    # Create firmware update workflow
                    workflow_data = {
                        "server_id": server_id,
                        "firmware_components": update_config.get(
                            "components", ["bios", "bmc"]
                        ),
                        "scheduled_time": update_config.get("scheduled_time"),
                        "maintenance_window": update_config.get(
                            "maintenance_window", 60
                        ),
                        "rollback_enabled": update_config.get("rollback_enabled", True),
                    }

                    # For now, simulate workflow creation
                    # This would integrate with actual FirmwareProvisioningWorkflow
                    workflow_id = f"fw-update-{server_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

                    scheduled_updates.append(
                        {
                            "server_id": server_id,
                            "workflow_id": workflow_id,
                            "scheduled_time": update_config.get("scheduled_time"),
                            "status": "scheduled",
                        }
                    )

                    logger.info(
                        f"Scheduled firmware update for server {server_id}: {workflow_id}"
                    )

                except Exception as e:
                    logger.error(
                        f"Failed to schedule firmware update for server {server_id}: {e}"
                    )
                    failed_schedules.append({"server_id": server_id, "error": str(e)})

            return {
                "success": True,
                "scheduled_updates": scheduled_updates,
                "failed_schedules": failed_schedules,
                "total_scheduled": len(scheduled_updates),
            }

        except Exception as e:
            logger.error(f"Failed to schedule firmware updates: {e}")
            return {
                "success": False,
                "error": str(e),
                "scheduled_updates": [],
                "failed_schedules": [],
            }

    def get_update_progress(self, workflow_id: str) -> Dict[str, Any]:
        """Get real-time progress for firmware update workflow.

        Args:
            workflow_id: Workflow ID to check progress for

        Returns:
            Dict with current progress information
        """
        try:
            # This would integrate with actual workflow progress tracking
            # For now, simulate progress data
            if workflow_id in self._active_updates:
                progress = self._active_updates[workflow_id]
            else:
                # Simulate initial progress
                progress = {
                    "workflow_id": workflow_id,
                    "status": "running",
                    "current_phase": "firmware_analysis",
                    "progress_percentage": 25,
                    "steps_completed": 2,
                    "total_steps": 8,
                    "current_step": "Analyzing current firmware versions",
                    "estimated_remaining": "15 minutes",
                    "started_at": datetime.now().isoformat(),
                    "phases": {
                        "hardware_discovery": {"status": "completed", "duration": 120},
                        "firmware_analysis": {"status": "running", "duration": None},
                        "bios_configuration": {"status": "pending", "duration": None},
                        "firmware_updates": {"status": "pending", "duration": None},
                        "validation": {"status": "pending", "duration": None},
                        "documentation": {"status": "pending", "duration": None},
                    },
                }
                self._active_updates[workflow_id] = progress

            return progress

        except Exception as e:
            logger.error(f"Failed to get update progress for {workflow_id}: {e}")
            return {"workflow_id": workflow_id, "status": "error", "error": str(e)}


# Global firmware web manager instance
firmware_web_manager = None


def init_firmware_routes(firmware_manager, workflow_manager, db_helper, socketio=None):
    """Initialize firmware routes with dependencies.

    Args:
        firmware_manager: FirmwareManager instance (can be None for basic functionality)
        workflow_manager: WorkflowManager instance
        db_helper: Database helper instance
        socketio: SocketIO instance for real-time updates
    """
    global firmware_web_manager
    firmware_web_manager = FirmwareWebManager(
        firmware_manager, workflow_manager, db_helper, socketio
    )


@firmware_bp.route("/")
def firmware_dashboard():
    """Firmware management dashboard."""
    try:
        if not firmware_web_manager:
            flash("Firmware management not initialized", "error")
            return redirect(url_for("index"))

        inventory = firmware_web_manager.get_firmware_inventory()

        return render_template(
            "firmware.html", title="Firmware Management", inventory=inventory
        )

    except Exception as e:
        logger.error(f"Error loading firmware dashboard: {e}")
        flash(f"Error loading firmware dashboard: {e}", "error")
        return redirect(url_for("index"))


# API Endpoints


@firmware_bp.route("/api/inventory")
def api_firmware_inventory():
    """API endpoint for firmware inventory data."""
    try:
        if not firmware_web_manager:
            return jsonify({"error": "Firmware management not initialized"}), 500

        inventory = firmware_web_manager.get_firmware_inventory()
        return jsonify(inventory)

    except Exception as e:
        logger.error(f"API error getting firmware inventory: {e}")
        return jsonify({"error": str(e)}), 500


@firmware_bp.route("/api/device-types")
def api_device_types_firmware():
    """API endpoint for device types firmware information."""
    try:
        if not firmware_web_manager:
            return jsonify({"error": "Firmware management not initialized"}), 500

        device_types = firmware_web_manager._get_device_types_firmware_info()
        return jsonify({"device_types": device_types})

    except Exception as e:
        logger.error(f"API error getting device types firmware: {e}")
        return jsonify({"error": str(e)}), 500


@firmware_bp.route("/api/download/<vendor>/<firmware_type>/<filename>")
def api_download_firmware(vendor, firmware_type, filename):
    """API endpoint to download firmware files."""
    try:
        # Validate inputs
        allowed_vendors = ["supermicro", "hpe"]
        allowed_types = ["bios", "bmc"]

        if vendor.lower() not in allowed_vendors:
            return jsonify({"error": "Invalid vendor"}), 400

        if firmware_type.lower() not in allowed_types:
            return jsonify({"error": "Invalid firmware type"}), 400

        # Construct file path
        firmware_base_path = Path("/app/firmware")  # Docker path
        if not firmware_base_path.exists():
            firmware_base_path = Path("./firmware")  # Local path

        if not firmware_base_path.exists():
            return jsonify({"error": "Firmware directory not found"}), 404

        file_path = (
            firmware_base_path / vendor.lower() / firmware_type.lower() / filename
        )

        if not file_path.exists():
            return jsonify({"error": "Firmware file not found"}), 404

        # Security check - ensure file is within firmware directory
        try:
            file_path.resolve().relative_to(firmware_base_path.resolve())
        except ValueError:
            return jsonify({"error": "Invalid file path"}), 400

        return send_file(
            str(file_path),
            as_attachment=True,
            download_name=filename,
            mimetype="application/octet-stream",
        )

    except Exception as e:
        logger.error(
            f"Error downloading firmware {vendor}/{firmware_type}/{filename}: {e}"
        )
        return jsonify({"error": str(e)}), 500


@firmware_bp.route("/api/schedule", methods=["POST"])
def api_schedule_firmware_update():
    """API endpoint to schedule firmware updates."""
    try:
        if not firmware_web_manager:
            return jsonify({"error": "Firmware management not initialized"}), 500

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        server_ids = data.get("server_ids", [])
        if not server_ids:
            return jsonify({"error": "No servers specified"}), 400

        update_config = {
            "components": data.get("components", ["bios", "bmc"]),
            "scheduled_time": data.get("scheduled_time"),
            "maintenance_window": data.get("maintenance_window", 60),
            "rollback_enabled": data.get("rollback_enabled", True),
        }

        result = firmware_web_manager.schedule_firmware_update(
            server_ids, update_config
        )

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 400

    except Exception as e:
        logger.error(f"API error scheduling firmware update: {e}")
        return jsonify({"error": str(e)}), 500


@firmware_bp.route("/api/progress/<workflow_id>")
def api_firmware_update_progress(workflow_id):
    """API endpoint to get firmware update progress."""
    try:
        if not firmware_web_manager:
            return jsonify({"error": "Firmware management not initialized"}), 500

        progress = firmware_web_manager.get_update_progress(workflow_id)
        return jsonify(progress)

    except Exception as e:
        logger.error(f"API error getting firmware update progress: {e}")
        return jsonify({"error": str(e)}), 500


@firmware_bp.route("/api/cancel/<workflow_id>", methods=["POST"])
def api_cancel_firmware_update(workflow_id):
    """API endpoint to cancel firmware update."""
    try:
        if not firmware_web_manager:
            return jsonify({"error": "Firmware management not initialized"}), 500

        # This would integrate with actual workflow cancellation
        # For now, simulate cancellation
        result = {
            "success": True,
            "workflow_id": workflow_id,
            "status": "cancelled",
            "message": "Firmware update cancelled successfully",
        }

        return jsonify(result)

    except Exception as e:
        logger.error(f"API error cancelling firmware update: {e}")
        return jsonify({"error": str(e)}), 500
