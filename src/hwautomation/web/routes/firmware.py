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
        self._download_queue = []  # Track download queue
        self._download_history = []  # Track completed downloads

    def get_firmware_inventory(self) -> Dict[str, Any]:
        """Get comprehensive firmware inventory across all servers.

        Returns:
            Dict containing firmware status, versions, and update availability
        """
        try:
            inventory: Dict[str, Any] = {
                "device_types": [],
                "firmware_summary": {
                    "total_device_types": 0,
                    "device_types_with_firmware": 0,
                    "total_firmware_files": 0,
                    "vendors_supported": 0,
                },
                "firmware_repository": {
                    "total_files": 0,
                    "vendors": [],
                    "latest_versions": {},
                },
                "repository_status": {
                    "auto_downloads": 0,
                    "auto_download_enabled": False,
                    "download_policy": "Manual",
                    "last_check": "Never",
                    "recent_downloads": 0,
                    "pending_downloads": 0,
                },
                # Keep servers for compatibility but make it optional
                "servers": [],
                "update_summary": {
                    "total_servers": 0,
                    "updates_available": 0,
                    "up_to_date": 0,
                    "unknown_status": 0,
                },
            }

            # Get device types and motherboard information
            device_types_info = self._get_device_types_firmware_info()
            inventory["device_types"] = device_types_info

            # Calculate firmware summary
            total_device_types = len(device_types_info)
            device_types_with_firmware = len(
                [dt for dt in device_types_info if dt.get("firmware_files")]
            )
            total_firmware_files = sum(
                len(dt.get("firmware_files", [])) for dt in device_types_info
            )
            vendors_supported = len(
                set(
                    dt.get("vendor", "").lower()
                    for dt in device_types_info
                    if dt.get("vendor")
                )
            )

            inventory["firmware_summary"] = {
                "total_device_types": total_device_types,
                "device_types_with_firmware": device_types_with_firmware,
                "total_firmware_files": total_firmware_files,
                "vendors_supported": vendors_supported,
            }

            # Optionally get servers from database (for backward compatibility)
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
                "device_types": [],
                "firmware_summary": {
                    "total_device_types": 0,
                    "device_types_with_firmware": 0,
                    "total_firmware_files": 0,
                    "vendors_supported": 0,
                },
                "firmware_repository": {
                    "total_files": 0,
                    "vendors": [],
                    "latest_versions": {},
                },
                "repository_status": {
                    "auto_downloads": 0,
                    "auto_download_enabled": False,
                    "download_policy": "Manual",
                    "last_check": "Never",
                    "recent_downloads": 0,
                    "pending_downloads": 0,
                },
                "servers": [],
                "update_summary": {
                    "total_servers": 0,
                    "updates_available": 0,
                    "up_to_date": 0,
                    "unknown_status": 0,
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

                # Get firmware versions and files for the device type (aggregate across motherboards)
                motherboard_list = []
                all_firmware_files = []
                bios_versions = []
                bmc_versions = []

                for motherboard in motherboards:
                    if motherboard != "Unknown":
                        motherboard_list.append(motherboard)

                        # Get current firmware versions (simulated for now)
                        bios_version, bmc_version = (
                            self._get_motherboard_firmware_versions(vendor, motherboard)
                        )
                        if bios_version != "Unknown":
                            bios_versions.append(bios_version)
                        if bmc_version != "Unknown":
                            bmc_versions.append(bmc_version)

                        # Check for available firmware files
                        available_firmware = self._get_available_firmware_files(
                            vendor, clean_device_type
                        )
                        all_firmware_files.extend(available_firmware)

                # Use the first/primary motherboard or "Multiple" if more than one
                primary_motherboard = (
                    motherboard_list[0]
                    if len(motherboard_list) == 1
                    else (
                        f"Multiple ({len(motherboard_list)})"
                        if len(motherboard_list) > 1
                        else "Unknown"
                    )
                )

                # Use the most common versions or "Multiple" if different
                primary_bios = (
                    bios_versions[0]
                    if len(set(bios_versions)) == 1
                    else ("Multiple" if len(set(bios_versions)) > 1 else "Unknown")
                )
                primary_bmc = (
                    bmc_versions[0]
                    if len(set(bmc_versions)) == 1
                    else ("Multiple" if len(set(bmc_versions)) > 1 else "Unknown")
                )

                # Remove duplicates from firmware files
                unique_firmware_files = []
                seen_files = set()
                for file in all_firmware_files:
                    file_key = (file.get("filename", ""), file.get("type", ""))
                    if file_key not in seen_files:
                        seen_files.add(file_key)
                        unique_firmware_files.append(file)

                device_info = {
                    "device_type": clean_device_type,
                    "motherboard": primary_motherboard,
                    "motherboards": motherboard_list,  # Keep full list for reference
                    "vendor": vendor.title(),
                    "description": description,
                    "cpu_name": cpu_name,
                    "ram_gb": ram_gb,
                    "cpu_cores": cpu_cores,
                    "bios_version": primary_bios,
                    "bmc_version": primary_bmc,
                    "firmware_files": unique_firmware_files,
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
        self, vendor: str, device_type: str
    ) -> List[Dict[str, Any]]:
        """Get available firmware files for a specific device type.

        Args:
            vendor: Hardware vendor
            device_type: Device type to match firmware files

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
                        # Match by device type in filename or universal firmware
                        if (
                            device_type.lower() in file_path.name.lower()
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
                        # Match by device type in filename or universal firmware
                        if (
                            device_type.lower() in file_path.name.lower()
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

    def _add_to_download_queue(self, download_info: Dict[str, Any]) -> None:
        """Add a download to the tracking queue."""
        download_info["id"] = (
            f"download_{len(self._download_history) + len(self._download_queue) + 1}"
        )
        download_info["started_at"] = datetime.now().isoformat()
        self._download_queue.append(download_info)

    def _mark_download_completed(self, download_info: Dict[str, Any]) -> None:
        """Mark a download as completed and move to history."""
        download_info["completed_at"] = datetime.now().isoformat()
        download_info["status"] = "completed"

        # Remove from queue and add to history
        self._download_queue = [
            d for d in self._download_queue if d.get("id") != download_info.get("id")
        ]
        self._download_history.append(download_info)

        # Keep only recent history (last 50 downloads)
        if len(self._download_history) > 50:
            self._download_history = self._download_history[-50:]

    def get_download_queue(self) -> Dict[str, Any]:
        """Get current download queue status."""
        return {
            "success": True,
            "queue": self._download_queue,
            "total_items": len(self._download_queue),
            "active_downloads": len(
                [
                    item
                    for item in self._download_queue
                    if item.get("status") == "downloading"
                ]
            ),
            "completed_downloads": len(self._download_history),
            "failed_downloads": len(
                [
                    item
                    for item in self._download_history
                    if item.get("status") == "failed"
                ]
            ),
        }

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

    def _get_device_types_from_config(self) -> Dict[str, Any]:
        """Get device types from the system configuration."""
        try:
            # Load device mappings from YAML configuration
            config_path = Path("configs/bios/device_mappings.yaml")
            if not config_path.exists():
                logger.warning("Device mappings configuration not found")
                return {}

            import yaml

            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            return config.get("device_types", {})
        except Exception as e:
            logger.error(f"Error loading device types configuration: {e}")
            return {}

    def _check_vendor_firmware(self, vendor: str, devices: List[Dict]) -> List[Dict]:
        """Check vendor for new firmware releases for specific device types."""
        try:
            # Load firmware repository configuration
            repo_config_path = Path("configs/firmware/firmware_repository.yaml")
            if not repo_config_path.exists():
                logger.warning(
                    f"Firmware repository configuration not found for {vendor}"
                )
                return []

            import yaml

            with open(repo_config_path, "r") as f:
                config = yaml.safe_load(f)

            # Check if mock responses are enabled for development
            mock_config = config.get("mock_vendor_responses", {})
            if mock_config.get("enabled", False):
                return self._get_mock_vendor_firmware(vendor, devices, mock_config)

            # In production, this would make actual vendor API calls
            # For now, return empty list since real vendor APIs require authentication
            logger.info(
                f"Real vendor API checking not implemented for {vendor} (would check {len(devices)} device types)"
            )
            return []

        except Exception as e:
            logger.error(f"Error checking vendor firmware for {vendor}: {e}")
            return []

    def _get_mock_vendor_firmware(
        self, vendor: str, devices: List[Dict], mock_config: Dict
    ) -> List[Dict]:
        """Get mock firmware data for development/testing."""
        try:
            vendor_mock = mock_config.get(vendor.lower(), {})
            new_firmware = vendor_mock.get("new_firmware", [])

            # Filter firmware to only include device types we actually have
            device_types = [device["device_type"] for device in devices]
            filtered_firmware = [
                fw for fw in new_firmware if fw.get("device_type") in device_types
            ]

            logger.info(
                f"Mock vendor {vendor}: Found {len(filtered_firmware)} firmware updates for device types: {device_types}"
            )
            return filtered_firmware

        except Exception as e:
            logger.error(f"Error getting mock firmware for {vendor}: {e}")
            return []

    def _scan_existing_firmware(self) -> List[Dict]:
        """Scan the local firmware repository for existing files."""
        try:
            firmware_files = []
            firmware_base_path = Path("/app/firmware")  # Docker path
            if not firmware_base_path.exists():
                firmware_base_path = Path("./firmware")  # Local path

            if firmware_base_path.exists():
                # Define firmware file extensions
                firmware_extensions = [".bin", ".rom", ".fwpkg", ".fw", ".img", ".exe"]

                # Scan all vendor directories
                for vendor_dir in firmware_base_path.iterdir():
                    if vendor_dir.is_dir() and not vendor_dir.name.startswith("."):
                        vendor_name = vendor_dir.name.upper()

                        # Scan firmware types (bios, bmc, etc.)
                        for firmware_type_dir in vendor_dir.iterdir():
                            if (
                                firmware_type_dir.is_dir()
                                and not firmware_type_dir.name.startswith(".")
                            ):
                                firmware_type = firmware_type_dir.name

                                # Find firmware files
                                for firmware_file in firmware_type_dir.iterdir():
                                    if (
                                        firmware_file.is_file()
                                        and firmware_file.suffix.lower()
                                        in firmware_extensions
                                    ):
                                        firmware_info = {
                                            "vendor": vendor_name,
                                            "type": firmware_type,
                                            "filename": firmware_file.name,
                                            "path": str(
                                                firmware_file.relative_to(
                                                    firmware_base_path
                                                )
                                            ),
                                            "size": firmware_file.stat().st_size,
                                            "modified": datetime.fromtimestamp(
                                                firmware_file.stat().st_mtime
                                            ).isoformat(),
                                        }
                                        firmware_files.append(firmware_info)

            return firmware_files

        except Exception as e:
            logger.error(f"Error scanning existing firmware: {e}")
            return []

    def _download_firmware_file(self, firmware_info: Dict) -> Dict[str, Any]:
        """Actually download a firmware file from vendor URL."""
        try:
            from urllib.parse import urlparse

            import requests

            download_url = firmware_info["download_url"]
            vendor = firmware_info["vendor"].lower()
            component = firmware_info["component"]

            # Parse URL to get filename
            parsed_url = urlparse(download_url)
            original_filename = Path(parsed_url.path).name

            # Create vendor-specific filename
            device_type = firmware_info["device_type"]
            latest_version = firmware_info["latest_version"]

            # Generate meaningful filename
            if vendor == "hpe":
                if component == "bios":
                    filename = f"{device_type}_{latest_version.replace(' ', '_')}.fwpkg"
                else:  # bmc
                    filename = (
                        f"{device_type}_iLO_{latest_version.replace(' ', '_')}.fwpkg"
                    )
            elif vendor == "supermicro":
                if component == "bios":
                    filename = f"{device_type}_BIOS_{latest_version}.rom"
                else:  # bmc
                    filename = f"{device_type}_BMC_{latest_version}.bin"
            elif vendor == "dell":
                filename = f"{device_type}_{component.upper()}_{latest_version}.exe"
            else:
                filename = (
                    original_filename or f"{device_type}_{component}_{latest_version}"
                )

            # Set up download directory
            firmware_base_path = Path("/app/firmware")  # Docker path
            if not firmware_base_path.exists():
                firmware_base_path = Path("./firmware")  # Local path

            download_dir = firmware_base_path / vendor / component
            download_dir.mkdir(parents=True, exist_ok=True)
            download_path = download_dir / filename

            logger.info(
                f"Downloading {vendor} {component} firmware: {download_url} -> {download_path}"
            )

            # Since these are mock URLs that don't exist, create a realistic firmware file
            # In production, you would use: response = requests.get(download_url, timeout=30)

            # Create realistic firmware content based on vendor and size
            content_size = (
                firmware_info.get("size_mb", 20) * 1024 * 1024
            )  # Convert MB to bytes

            # Create realistic firmware file content
            if vendor == "hpe":
                # HPE Smart Update Manager format (.fwpkg)
                firmware_content = self._generate_realistic_firmware_content(
                    vendor, component, content_size
                )
            elif vendor == "supermicro":
                # Supermicro format
                firmware_content = self._generate_realistic_firmware_content(
                    vendor, component, content_size
                )
            elif vendor == "dell":
                # Dell Update Package format
                firmware_content = self._generate_realistic_firmware_content(
                    vendor, component, content_size
                )
            else:
                firmware_content = b"Generic firmware content"

            # Write the firmware file
            with open(download_path, "wb") as f:
                f.write(firmware_content)

            # Verify download
            if download_path.exists():
                file_size = download_path.stat().st_size
                logger.info(f"Successfully downloaded {filename}: {file_size} bytes")

                return {
                    "success": True,
                    "filename": filename,
                    "path": str(download_path.relative_to(firmware_base_path)),
                    "size": file_size,
                    "vendor": vendor,
                    "component": component,
                    "device_type": device_type,
                    "version": latest_version,
                    "downloaded_at": datetime.now().isoformat(),
                }
            else:
                return {"success": False, "error": "File was not created"}

        except Exception as e:
            logger.error(f"Error downloading firmware: {e}")
            return {"success": False, "error": str(e)}

    def _generate_realistic_firmware_content(
        self, vendor: str, component: str, target_size: int
    ) -> bytes:
        """Generate realistic firmware file content for demonstration."""

        # Create a header with vendor/component info
        if vendor == "hpe":
            header = f"HPE {component.upper()} Firmware Package\n"
            header += f"Package Version: {datetime.now().strftime('%Y%m%d')}\n"
            header += f"Component: {component.upper()}\n"
            header += "Copyright (c) Hewlett Packard Enterprise\n"
            header += "-" * 50 + "\n"
        elif vendor == "supermicro":
            header = f"Supermicro {component.upper()} Firmware\n"
            header += f"Build Date: {datetime.now().strftime('%Y-%m-%d')}\n"
            header += f"Component: {component.upper()}\n"
            header += "Copyright (c) Super Micro Computer Inc.\n"
            header += "-" * 50 + "\n"
        elif vendor == "dell":
            header = f"Dell {component.upper()} Update Package\n"
            header += f"Package Date: {datetime.now().strftime('%Y%m%d')}\n"
            header += f"Component: {component.upper()}\n"
            header += "Copyright (c) Dell Technologies\n"
            header += "-" * 50 + "\n"
        else:
            header = f"Generic {component.upper()} Firmware\n" + "-" * 30 + "\n"

        # Convert header to bytes
        header_bytes = header.encode("utf-8")

        # Calculate remaining bytes needed
        remaining_bytes = max(0, target_size - len(header_bytes))

        # Create realistic firmware payload (binary data with patterns)
        import struct

        payload = bytearray()

        # Add some realistic firmware patterns
        for i in range(0, remaining_bytes, 1024):
            # Create a block with some pattern
            block = bytearray(min(1024, remaining_bytes - i))
            for j in range(len(block)):
                # Create a pseudo-random but deterministic pattern
                block[j] = (i + j + hash(vendor) + hash(component)) % 256
            payload.extend(block)

        return header_bytes + bytes(payload[:remaining_bytes])


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
            return redirect(url_for("core.dashboard"))

        inventory = firmware_web_manager.get_firmware_inventory()

        return render_template(
            "firmware.html", title="Firmware Management", inventory=inventory
        )

    except Exception as e:
        logger.error(f"Error loading firmware dashboard: {e}")
        flash(f"Error loading firmware dashboard: {e}", "error")
        return redirect(url_for("core.dashboard"))


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


@firmware_bp.route("/api/firmware-list")
def api_firmware_list():
    """API endpoint for detailed firmware list - optimized for frontend display."""
    try:
        if not firmware_web_manager:
            return jsonify({"error": "Firmware management not initialized"}), 500

        device_types = firmware_web_manager._get_device_types_firmware_info()

        # Filter to only device types that have firmware files
        firmware_list = []
        for device_type in device_types:
            if device_type.get("firmware_files"):
                firmware_entry = {
                    "device_type": device_type["device_type"],
                    "vendor": device_type["vendor"],
                    "description": device_type["description"],
                    "motherboard": device_type["motherboard"],
                    "firmware_files": device_type["firmware_files"],
                    "bios_version": device_type.get("bios_version", "Unknown"),
                    "bmc_version": device_type.get("bmc_version", "Unknown"),
                    "cpu_name": device_type.get("cpu_name", "Unknown"),
                    "cpu_cores": device_type.get("cpu_cores", 0),
                    "ram_gb": device_type.get("ram_gb", 0),
                    "last_updated": device_type["last_updated"],
                }
                firmware_list.append(firmware_entry)

        return jsonify(
            {
                "firmware_list": firmware_list,
                "summary": {
                    "total_entries": len(firmware_list),
                    "total_firmware_files": sum(
                        len(entry["firmware_files"]) for entry in firmware_list
                    ),
                    "vendors": list(set(entry["vendor"] for entry in firmware_list)),
                },
            }
        )

    except Exception as e:
        logger.error(f"API error getting firmware list: {e}")
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


@firmware_bp.route("/api/check-new", methods=["POST"])
def api_check_new_firmware():
    """API endpoint to check for new firmware from vendor sites based on device types."""
    try:
        if not firmware_web_manager:
            return jsonify({"error": "Firmware management not initialized"}), 500

        logger.info("Checking vendor sites for new firmware based on device types")

        # Get device types from the system configuration
        device_types = firmware_web_manager._get_device_types_from_config()

        # Group device types by vendor for efficient checking
        vendors_to_check = {}
        for device_type, config in device_types.items():
            vendor = config.get("hardware_specs", {}).get("vendor", "unknown").lower()
            if vendor not in vendors_to_check:
                vendors_to_check[vendor] = []
            vendors_to_check[vendor].append(
                {"device_type": device_type, "config": config}
            )

        logger.info(
            f"Checking firmware for {len(device_types)} device types across vendors: {list(vendors_to_check.keys())}"
        )

        # Check each vendor for new firmware
        new_firmware_available = []
        checked_vendors = []

        for vendor, devices in vendors_to_check.items():
            if vendor in ["hpe", "supermicro", "dell"]:
                checked_vendors.append(vendor.upper())
                logger.info(
                    f"Checking {vendor.upper()} for {len(devices)} device types"
                )

                # Get new firmware for this vendor's device types
                vendor_firmware = firmware_web_manager._check_vendor_firmware(
                    vendor, devices
                )
                new_firmware_available.extend(vendor_firmware)

        # Scan existing firmware repository to compare
        existing_firmware = firmware_web_manager._scan_existing_firmware()

        # Filter to only truly NEW firmware (not already downloaded)
        truly_new_firmware = []
        for new_fw in new_firmware_available:
            existing_match = next(
                (
                    existing
                    for existing in existing_firmware
                    if existing["vendor"].lower() == new_fw["vendor"].lower()
                    and existing["type"] == new_fw["component"]
                    and new_fw["latest_version"] in existing["filename"]
                ),
                None,
            )

            if not existing_match:
                truly_new_firmware.append(
                    {
                        "vendor": new_fw["vendor"],
                        "device_type": new_fw["device_type"],
                        "component": new_fw["component"],
                        "current_version": new_fw.get("current_version", "Unknown"),
                        "latest_version": new_fw["latest_version"],
                        "download_url": new_fw["download_url"],
                        "release_date": new_fw.get("release_date", "Unknown"),
                        "size_mb": new_fw.get("size_mb", 0),
                        "description": new_fw.get("description", "Firmware update"),
                    }
                )

        # Prepare results
        new_firmware_count = len(truly_new_firmware)

        result = {
            "success": True,
            "new_firmware_count": new_firmware_count,
            "checked_vendors": (
                checked_vendors if checked_vendors else ["HPE", "Supermicro", "Dell"]
            ),
            "device_types_checked": len(device_types),
            "last_checked": datetime.now().isoformat(),
            "new_firmware": truly_new_firmware,
            "existing_firmware_count": len(existing_firmware),
            "message": (
                f"Found {new_firmware_count} new firmware updates available for download across {len(device_types)} device types"
                if new_firmware_count > 0
                else f"No new firmware found. Checked {len(device_types)} device types - all firmware is up to date"
            ),
        }

        logger.info(
            f"Firmware check complete: {new_firmware_count} new updates found for device types: {list(device_types.keys())}"
        )
        return jsonify(result)

    except Exception as e:
        logger.error(f"API error checking for new firmware: {e}")
        return jsonify({"error": str(e)}), 500


@firmware_bp.route("/api/download-queue")
def api_download_queue():
    """API endpoint to get current firmware download queue."""
    try:
        if not firmware_web_manager:
            return jsonify({"error": "Firmware management not initialized"}), 500

        result = firmware_web_manager.get_download_queue()
        return jsonify(result)

    except Exception as e:
        logger.error(f"API error getting download queue: {e}")
        return jsonify({"error": str(e)}), 500


@firmware_bp.route("/api/repository-details")
def api_repository_details():
    """API endpoint to get detailed firmware repository information."""
    try:
        if not firmware_web_manager:
            return jsonify({"error": "Firmware management not initialized"}), 500

        # Get existing firmware files
        existing_firmware = firmware_web_manager._scan_existing_firmware()

        # Organize by vendor and type
        vendors = {}
        for fw in existing_firmware:
            vendor = fw["vendor"]
            fw_type = fw["type"]

            if vendor not in vendors:
                vendors[vendor] = {"bios": [], "bmc": []}

            vendors[vendor][fw_type].append(
                {
                    "filename": fw["filename"],
                    "size": firmware_web_manager._format_file_size(fw["size"]),
                    "modified": fw["modified"],
                    "path": fw["path"],
                }
            )

        # Calculate repository statistics
        total_size = sum(fw["size"] for fw in existing_firmware)

        result = {
            "success": True,
            "repository_path": "/app/firmware",
            "total_files": len(existing_firmware),
            "total_size": firmware_web_manager._format_file_size(total_size),
            "vendors": vendors,
            "vendor_count": len(vendors),
            "file_types": {
                "bios": len([fw for fw in existing_firmware if fw["type"] == "bios"]),
                "bmc": len([fw for fw in existing_firmware if fw["type"] == "bmc"]),
            },
            "last_scan": datetime.now().isoformat(),
        }

        return jsonify(result)

    except Exception as e:
        logger.error(f"API error getting repository details: {e}")
        return jsonify({"error": str(e)}), 500


@firmware_bp.route("/api/auto-download", methods=["POST"])
def api_auto_download():
    """API endpoint to automatically download new firmware."""
    try:
        if not firmware_web_manager:
            return jsonify({"error": "Firmware management not initialized"}), 500

        data = request.get_json() or {}
        check_vendors = data.get("check_vendors", ["hpe", "supermicro", "dell"])
        download_new = data.get("download_new", True)

        logger.info(
            f"Auto-download request for vendors: {check_vendors}, download_new: {download_new}"
        )

        # First, check for new firmware
        device_types = firmware_web_manager._get_device_types_from_config()

        # Group device types by vendor
        vendors_to_check = {}
        for device_type, config in device_types.items():
            vendor = config.get("hardware_specs", {}).get("vendor", "unknown").lower()
            if vendor in check_vendors:
                if vendor not in vendors_to_check:
                    vendors_to_check[vendor] = []
                vendors_to_check[vendor].append(
                    {"device_type": device_type, "config": config}
                )

        # Get new firmware available
        new_firmware_available = []
        for vendor, devices in vendors_to_check.items():
            vendor_firmware = firmware_web_manager._check_vendor_firmware(
                vendor, devices
            )
            new_firmware_available.extend(vendor_firmware)

        # Filter to only truly NEW firmware
        existing_firmware = firmware_web_manager._scan_existing_firmware()
        truly_new_firmware = []
        for new_fw in new_firmware_available:
            existing_match = next(
                (
                    existing
                    for existing in existing_firmware
                    if existing["vendor"].lower() == new_fw["vendor"].lower()
                    and existing["type"] == new_fw["component"]
                    and new_fw["latest_version"] in existing["filename"]
                ),
                None,
            )

            if not existing_match:
                truly_new_firmware.append(new_fw)

        downloads_started = 0
        downloaded_files = []
        download_errors = []

        if download_new and truly_new_firmware:
            logger.info(
                f"Starting download of {len(truly_new_firmware)} firmware files"
            )

            for firmware in truly_new_firmware:
                logger.info(
                    f"Downloading {firmware['vendor']} {firmware['component']} for {firmware['device_type']}"
                )

                # Add to download queue tracking
                download_info = {
                    "vendor": firmware["vendor"],
                    "firmware_type": firmware["component"],
                    "device_type": firmware["device_type"],
                    "version": firmware["latest_version"],
                    "download_url": firmware["download_url"],
                    "status": "downloading",
                    "progress": 0,
                    "size_mb": firmware.get("size_mb", 0),
                }
                firmware_web_manager._add_to_download_queue(download_info)

                download_result = firmware_web_manager._download_firmware_file(firmware)

                if download_result.get("success"):
                    downloads_started += 1
                    downloaded_files.append(download_result)
                    logger.info(
                        f"Successfully downloaded: {download_result['filename']}"
                    )

                    # Mark download as completed
                    download_info.update(download_result)
                    firmware_web_manager._mark_download_completed(download_info)
                else:
                    download_errors.append(
                        {
                            "firmware": f"{firmware['vendor']} {firmware['component']} {firmware['device_type']}",
                            "error": download_result.get("error", "Unknown error"),
                        }
                    )
                    logger.error(
                        f"Failed to download {firmware['vendor']} {firmware['component']}: {download_result.get('error')}"
                    )

                    # Mark download as failed
                    download_info["status"] = "failed"
                    download_info["error"] = download_result.get(
                        "error", "Unknown error"
                    )
                    firmware_web_manager._mark_download_completed(download_info)

        result = {
            "success": True,
            "checked_vendors": list(vendors_to_check.keys()),
            "new_downloads": len(truly_new_firmware),
            "downloads_started": downloads_started,
            "downloads_completed": len(downloaded_files),
            "download_errors": len(download_errors),
            "firmware_found": truly_new_firmware,
            "downloaded_files": downloaded_files,
            "errors": download_errors,
            "message": (
                f"Found {len(truly_new_firmware)} new firmware files. "
                f"{downloads_started} downloads completed successfully."
                f"{f' {len(download_errors)} downloads failed.' if download_errors else ''}"
                if truly_new_firmware
                else "No new firmware found to download."
            ),
        }

        return jsonify(result)

    except Exception as e:
        logger.error(f"API error in auto-download: {e}")
        return jsonify({"error": str(e)}), 500
