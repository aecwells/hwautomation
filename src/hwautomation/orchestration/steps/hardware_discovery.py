"""Hardware discovery workflow steps.

This module provides steps for hardware discovery, vendor detection,
and system information gathering through various methods.
"""

import re
from typing import Any, Dict, Optional

from hwautomation.logging import get_logger

from ...hardware.discovery import HardwareDiscoveryManager
from ...utils.network import SSHClient, SSHManager
from ..workflows.base import (
    BaseWorkflowStep,
    ConditionalWorkflowStep,
    RetryableWorkflowStep,
    StepContext,
    StepExecutionResult,
)

logger = get_logger(__name__)


class EstablishSSHConnectionStep(RetryableWorkflowStep):
    """Step to establish SSH connection to the server."""

    def __init__(self):
        super().__init__(
            name="establish_ssh_connection",
            description="Establish SSH connection to commissioned server",
            max_retries=3,
            retry_delay=10.0,
        )

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate server IP is available."""
        if not context.server_ip:
            context.add_error("No server IP available for SSH connection")
            return False
        return True

    def _execute_with_retry(self, context: StepContext) -> StepExecutionResult:
        """Establish SSH connection with retry logic."""
        try:
            context.add_sub_task(f"Connecting to server via SSH at {context.server_ip}")

            # Add debug delay to make workflow visible
            import time

            context.add_sub_task("Preparing SSH connection (debug mode)")
            time.sleep(10)  # 10 second delay for debugging

            # Test SSH connectivity
            ssh_manager = SSHManager()
            connection_result = ssh_manager.test_connection(
                hostname=context.server_ip,
                username="ubuntu",  # Default username for commissioned machines
                timeout=30,
            )

            if not connection_result["success"]:
                return StepExecutionResult.retry(
                    f"SSH connection failed: {connection_result.get('error', 'Unknown error')}"
                )

            context.add_sub_task("SSH connection established successfully")
            context.set_data("ssh_available", True)
            context.set_data("ssh_username", "ubuntu")

            return StepExecutionResult.success(
                f"SSH connection established to {context.server_ip}",
                {"ssh_connection": connection_result},
            )

        except Exception as e:
            return StepExecutionResult.retry(f"Exception during SSH connection: {e}")


class DiscoverHardwareStep(BaseWorkflowStep):
    """Step to discover hardware information using the discovery manager."""

    def __init__(self):
        super().__init__(
            name="discover_hardware",
            description="Discover hardware information and vendor details",
        )
        self.discovery_manager = None

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate SSH connection is available."""
        if not context.get_data("ssh_available"):
            context.add_error("SSH connection required for hardware discovery")
            return False
        return True

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Discover hardware information."""
        try:
            context.add_sub_task("Initializing hardware discovery")

            # Initialize discovery manager
            self.discovery_manager = HardwareDiscoveryManager()

            context.add_sub_task("Performing hardware discovery")

            # Add debug delay to make workflow visible in dashboard
            import time

            context.add_sub_task("Processing hardware information (debug mode)")
            time.sleep(15)  # 15 second delay for debugging

            # Perform discovery
            discovery_result = self.discovery_manager.discover_system(
                target_ip=context.server_ip,
                username=context.get_data("ssh_username", "ubuntu"),
            )

            if not discovery_result.success:
                return StepExecutionResult.failure(
                    f"Hardware discovery failed: {discovery_result.error_message}"
                )

            hardware_info = discovery_result.hardware_info

            # Update context with discovered information
            if hardware_info:
                context.manufacturer = hardware_info.manufacturer
                context.model = hardware_info.model
                context.serial_number = hardware_info.serial_number

                context.set_data(
                    "hardware_info",
                    {
                        "manufacturer": hardware_info.manufacturer,
                        "model": hardware_info.model,
                        "serial_number": hardware_info.serial_number,
                        "cpu_info": hardware_info.cpu_info,
                        "memory_info": hardware_info.memory_info,
                        "network_interfaces": [
                            {
                                "name": iface.name,
                                "mac_address": iface.mac_address,
                                "speed": iface.speed,
                            }
                            for iface in hardware_info.network_interfaces
                        ],
                    },
                )

                context.add_sub_task(
                    f"Discovered {hardware_info.manufacturer} {hardware_info.model}"
                )

                # Enhanced device classification (if unified configuration available)
                try:
                    context.add_sub_task("Performing intelligent device classification")

                    # Check if enhanced discovery is available through context
                    if (
                        hasattr(context, "enhanced_discovery")
                        and context.enhanced_discovery
                    ):
                        # Use enhanced discovery manager for device classification
                        from ...hardware.discovery.base import SystemInfo

                        # Create system info for classification
                        sys_info = SystemInfo(
                            manufacturer=hardware_info.manufacturer,
                            product_name=hardware_info.model,
                            cpu_model=(
                                hardware_info.cpu_info.get("model")
                                if hardware_info.cpu_info
                                else None
                            ),
                            cpu_cores=(
                                hardware_info.cpu_info.get("cores")
                                if hardware_info.cpu_info
                                else None
                            ),
                            memory_total=(
                                hardware_info.memory_info.get("total")
                                if hardware_info.memory_info
                                else None
                            ),
                        )

                        # Classify device type
                        classification = self.discovery_manager.classify_device_type(
                            sys_info
                        )

                        if classification and classification.get("device_type"):
                            device_type = classification["device_type"]
                            confidence = classification["confidence"]

                            context.set_data("device_type", device_type)
                            context.set_data("classification_confidence", confidence)
                            context.set_data("classification_result", classification)

                            context.add_sub_task(
                                f"Device classified as '{device_type}' with {confidence} confidence"
                            )

                            logger.info(
                                f"Server {context.server_ip} classified as {device_type} "
                                f"(confidence: {confidence})"
                            )
                        else:
                            context.add_sub_task("Device classification inconclusive")
                            logger.warning(
                                f"Could not classify device type for {context.server_ip}"
                            )

                except Exception as e:
                    logger.warning(f"Device classification failed: {e}")
                    context.add_sub_task(f"Device classification failed: {str(e)}")

            return StepExecutionResult.success(
                "Hardware discovery completed successfully",
                {"discovery_result": discovery_result},
            )

        except Exception as e:
            return StepExecutionResult.failure(f"Hardware discovery failed: {e}")


class DetectServerVendorStep(BaseWorkflowStep):
    """Step to detect server vendor through SSH commands."""

    def __init__(self):
        super().__init__(
            name="detect_server_vendor",
            description="Detect server vendor using system information",
        )

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate SSH connection is available."""
        if not context.get_data("ssh_available"):
            context.add_error("SSH connection required for vendor detection")
            return False
        return True

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Detect server vendor."""
        try:
            context.add_sub_task("Detecting server vendor")

            ssh_client = SSHClient(
                hostname=context.server_ip,
                username=context.get_data("ssh_username", "ubuntu"),
            )

            vendor = self._detect_vendor(ssh_client)

            if vendor:
                context.manufacturer = vendor
                context.set_data("detected_vendor", vendor)
                context.add_sub_task(f"Detected vendor: {vendor}")

                return StepExecutionResult.success(
                    f"Server vendor detected: {vendor}", {"vendor": vendor}
                )
            else:
                return StepExecutionResult.failure("Could not detect server vendor")

        except Exception as e:
            return StepExecutionResult.failure(f"Vendor detection failed: {e}")

    def _detect_vendor(self, ssh_client: SSHClient) -> Optional[str]:
        """Detect vendor using various system commands."""

        vendor_commands = [
            ("dmidecode -s system-manufacturer", r"Supermicro|Dell|HP|HPE|Lenovo"),
            ("cat /sys/class/dmi/id/sys_vendor", r"Supermicro|Dell|HP|HPE|Lenovo"),
            (
                "ipmitool mc info | grep 'Manufacturer Name'",
                r"Supermicro|Dell|HP|HPE|Lenovo",
            ),
        ]

        for command, vendor_pattern in vendor_commands:
            try:
                result = ssh_client.execute_command(command)
                if result["success"] and result["stdout"]:
                    output = result["stdout"].strip()

                    # Match known vendors
                    vendor_match = re.search(vendor_pattern, output, re.IGNORECASE)
                    if vendor_match:
                        vendor = vendor_match.group().lower()

                        # Normalize vendor names
                        if vendor in ["hp", "hpe"]:
                            return "HP"
                        elif vendor == "supermicro":
                            return "Supermicro"
                        elif vendor == "dell":
                            return "Dell"
                        elif vendor == "lenovo":
                            return "Lenovo"

                        return vendor.title()

            except Exception as e:
                self.logger.debug(f"Vendor detection command failed: {command} - {e}")
                continue

        return None


class GatherSystemInfoStep(BaseWorkflowStep):
    """Step to gather comprehensive system information."""

    def __init__(self):
        super().__init__(
            name="gather_system_info",
            description="Gather comprehensive system information",
        )

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate SSH connection is available."""
        if not context.get_data("ssh_available"):
            context.add_error("SSH connection required for system info gathering")
            return False
        return True

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Gather system information."""
        try:
            context.add_sub_task("Gathering system information")

            ssh_client = SSHClient(
                hostname=context.server_ip,
                username=context.get_data("ssh_username", "ubuntu"),
            )

            system_info = self._gather_system_info(ssh_client)

            # Update context with system information
            context.set_data("system_info", system_info)

            # Update specific fields if not already set
            if not context.manufacturer and system_info.get("manufacturer"):
                context.manufacturer = system_info["manufacturer"]

            if not context.model and system_info.get("model"):
                context.model = system_info["model"]

            if not context.serial_number and system_info.get("serial_number"):
                context.serial_number = system_info["serial_number"]

            context.add_sub_task("System information gathered successfully")

            return StepExecutionResult.success(
                "System information gathered successfully", {"system_info": system_info}
            )

        except Exception as e:
            return StepExecutionResult.failure(f"Failed to gather system info: {e}")

    def _gather_system_info(self, ssh_client: SSHClient) -> Dict[str, Any]:
        """Gather comprehensive system information."""

        system_info = {}

        # System identification commands
        info_commands = {
            "manufacturer": "dmidecode -s system-manufacturer",
            "model": "dmidecode -s system-product-name",
            "serial_number": "dmidecode -s system-serial-number",
            "bios_version": "dmidecode -s bios-version",
            "bios_date": "dmidecode -s bios-release-date",
            "cpu_model": "lscpu | grep 'Model name' | cut -d: -f2 | xargs",
            "cpu_cores": "nproc",
            "memory_total": "free -h | grep Mem | awk '{print $2}'",
            "kernel_version": "uname -r",
            "os_release": "lsb_release -d | cut -d: -f2 | xargs",
        }

        for key, command in info_commands.items():
            try:
                result = ssh_client.execute_command(command)
                if result["success"] and result["stdout"]:
                    value = result["stdout"].strip()
                    if value and value.lower() not in [
                        "not specified",
                        "to be filled by o.e.m.",
                        "unknown",
                    ]:
                        system_info[key] = value
            except Exception as e:
                self.logger.debug(f"System info command failed: {command} - {e}")
                continue

        # Network interfaces
        try:
            result = ssh_client.execute_command(
                "ip -o link show | grep -E 'eth|ens|enp'"
            )
            if result["success"] and result["stdout"]:
                interfaces = []
                for line in result["stdout"].strip().split("\n"):
                    if "link/ether" in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            interface_name = parts[1].rstrip(":")
                            interfaces.append(interface_name)
                system_info["network_interfaces"] = interfaces
        except Exception as e:
            self.logger.debug(f"Network interface detection failed: {e}")

        return system_info


class RecordHardwareInfoStep(BaseWorkflowStep):
    """Step to record hardware information in the database."""

    def __init__(self):
        super().__init__(
            name="record_hardware_info",
            description="Record discovered hardware information in database",
        )

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Record hardware information in the database."""
        try:
            from ...database.helper import DbHelper

            context.add_sub_task("Recording hardware information in database")

            # Use DATABASE_PATH from environment, defaulting to data/hw_automation.db
            import os

            db_path = os.getenv("DATABASE_PATH", "data/hw_automation.db")
            db_helper = DbHelper(db_path)

            # Update hardware information
            if context.manufacturer:
                db_helper.updateserverinfo(
                    context.server_id, "manufacturer", context.manufacturer
                )

            if context.model:
                db_helper.updateserverinfo(context.server_id, "model", context.model)

            if context.serial_number:
                db_helper.updateserverinfo(
                    context.server_id, "serial_number", context.serial_number
                )

            # Record system info if available
            system_info = context.get_data("system_info", {})
            for key, value in system_info.items():
                if value:
                    db_helper.updateserverinfo(context.server_id, key, str(value))

            # Record hardware discovery results
            hardware_info = context.get_data("hardware_info", {})
            if hardware_info:
                db_helper.updateserverinfo(
                    context.server_id, "hardware_discovery", "completed"
                )

                # Store network interfaces if available
                network_interfaces = hardware_info.get("network_interfaces", [])
                if network_interfaces:
                    interface_names = [iface["name"] for iface in network_interfaces]
                    db_helper.updateserverinfo(
                        context.server_id,
                        "network_interfaces",
                        ",".join(interface_names),
                    )

            return StepExecutionResult.success(
                f"Hardware information recorded for server {context.server_id}",
                {"database_updated": True},
            )

        except Exception as e:
            return StepExecutionResult.failure(
                f"Failed to record hardware information: {e}"
            )
