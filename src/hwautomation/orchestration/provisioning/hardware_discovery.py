"""
Hardware discovery stage handler.

Handles hardware discovery and IPMI detection via SSH.
"""

import re
from typing import Any, Dict, Optional

from ...hardware.discovery.manager import HardwareDiscoveryManager
from ...logging import get_logger
from ...utils.network import SSHClient
from ..exceptions import SSHConnectionError
from ..workflow_manager import WorkflowContext
from .base import (
    ProvisioningConfig,
    ProvisioningStage,
    ProvisioningStageHandler,
    StageResult,
)

logger = get_logger(__name__)


class HardwareDiscoveryStageHandler(ProvisioningStageHandler):
    """Handles hardware discovery and IPMI detection."""

    def __init__(self):
        self.discovery_manager = HardwareDiscoveryManager()

    def get_stage(self) -> ProvisioningStage:
        """Get the stage this handler manages."""
        return ProvisioningStage.HARDWARE_DISCOVERY

    def validate_prerequisites(self, context: WorkflowContext) -> bool:
        """Validate that prerequisites for hardware discovery are met."""
        return (
            context.server_id is not None
            and context.server_ip is not None
            and context.db_helper is not None
        )

    def execute(
        self, context: WorkflowContext, config: ProvisioningConfig
    ) -> StageResult:
        """Execute hardware discovery."""
        logger.info(f"Starting hardware discovery for server {config.server_id}")

        try:
            # Establish SSH connection
            ssh_client = self._establish_ssh_connection(context, config)

            # Discover hardware information
            hardware_info = self._discover_hardware_info(ssh_client, context, config)

            # Detect IPMI configuration
            ipmi_info = self._detect_ipmi_configuration(ssh_client, context, config)

            # Store discovered information
            self._store_discovery_results(context, config, hardware_info, ipmi_info)

            ssh_client.disconnect()

            return StageResult(
                success=True,
                stage=self.get_stage(),
                data={
                    "hardware_info": hardware_info,
                    "ipmi_info": ipmi_info,
                },
                next_stage=ProvisioningStage.BIOS_CONFIGURATION,
            )

        except Exception as e:
            logger.error(f"Hardware discovery failed for {config.server_id}: {e}")
            return StageResult(
                success=False,
                stage=self.get_stage(),
                data={},
                error_message=str(e),
            )

    def _establish_ssh_connection(
        self, context: WorkflowContext, config: ProvisioningConfig
    ) -> SSHClient:
        """Establish SSH connection to the server."""
        context.report_sub_task("Establishing SSH connection for hardware discovery")

        ssh_client = SSHClient()
        success = ssh_client.connect(
            hostname=context.server_ip,
            username=config.ssh_username,
            key_path=config.ssh_key_path,
            timeout=30,
        )

        if not success:
            raise SSHConnectionError(
                f"Failed to establish SSH connection to {context.server_ip}"
            )

        logger.info(f"SSH connection established to {context.server_ip}")
        return ssh_client

    def _discover_hardware_info(
        self,
        ssh_client: SSHClient,
        context: WorkflowContext,
        config: ProvisioningConfig,
    ) -> Dict[str, Any]:
        """Discover hardware information via SSH."""
        context.report_sub_task("Discovering hardware information")

        try:
            # Use the hardware discovery manager
            discovery_result = self.discovery_manager.discover_hardware_via_ssh(
                ssh_client=ssh_client, server_id=config.server_id
            )

            hardware_info = {
                "vendor": discovery_result.get("vendor", "Unknown"),
                "model": discovery_result.get("model", "Unknown"),
                "serial_number": discovery_result.get("serial_number", "Unknown"),
                "cpu_info": discovery_result.get("cpu_info", {}),
                "memory_info": discovery_result.get("memory_info", {}),
                "network_interfaces": discovery_result.get("network_interfaces", []),
                "storage_devices": discovery_result.get("storage_devices", []),
            }

            logger.info(
                f"Discovered hardware info for {config.server_id}: {hardware_info['vendor']} {hardware_info['model']}"
            )
            return hardware_info

        except Exception as e:
            logger.warning(f"Hardware discovery failed, using fallback: {e}")
            return self._fallback_hardware_discovery(ssh_client, context, config)

    def _fallback_hardware_discovery(
        self,
        ssh_client: SSHClient,
        context: WorkflowContext,
        config: ProvisioningConfig,
    ) -> Dict[str, Any]:
        """Fallback hardware discovery using basic commands."""
        context.report_sub_task("Using fallback hardware discovery")

        hardware_info = {
            "vendor": "Unknown",
            "model": "Unknown",
            "serial_number": "Unknown",
            "cpu_info": {},
            "memory_info": {},
            "network_interfaces": [],
            "storage_devices": [],
        }

        try:
            # Try to get basic system information
            result = ssh_client.exec_command("dmidecode -s system-manufacturer")
            if result.exit_code == 0 and result.stdout.strip():
                hardware_info["vendor"] = result.stdout.strip()

            result = ssh_client.exec_command("dmidecode -s system-product-name")
            if result.exit_code == 0 and result.stdout.strip():
                hardware_info["model"] = result.stdout.strip()

            result = ssh_client.exec_command("dmidecode -s system-serial-number")
            if result.exit_code == 0 and result.stdout.strip():
                hardware_info["serial_number"] = result.stdout.strip()

        except Exception as e:
            logger.warning(f"Fallback hardware discovery failed: {e}")

        return hardware_info

    def _detect_ipmi_configuration(
        self,
        ssh_client: SSHClient,
        context: WorkflowContext,
        config: ProvisioningConfig,
    ) -> Dict[str, Any]:
        """Detect IPMI configuration."""
        context.report_sub_task("Detecting IPMI configuration")

        ipmi_info = {
            "ip_address": None,
            "mac_address": None,
            "gateway": None,
            "netmask": None,
            "vlan_id": None,
            "available": False,
        }

        try:
            # Check if ipmitool is available
            result = ssh_client.exec_command("which ipmitool")
            if result.exit_code != 0:
                logger.warning("ipmitool not available on server")
                return ipmi_info

            # Get IPMI LAN configuration
            result = ssh_client.exec_command("sudo ipmitool lan print 1")
            if result.exit_code == 0:
                ipmi_info = self._parse_ipmi_lan_output(result.stdout)
                ipmi_info["available"] = True
                logger.info(f"IPMI detected: {ipmi_info.get('ip_address', 'No IP')}")
            else:
                logger.warning(f"Failed to get IPMI info: {result.stderr}")

        except Exception as e:
            logger.warning(f"IPMI detection failed: {e}")

        return ipmi_info

    def _parse_ipmi_lan_output(self, output: str) -> Dict[str, Any]:
        """Parse ipmitool lan print output."""
        ipmi_info = {
            "ip_address": None,
            "mac_address": None,
            "gateway": None,
            "netmask": None,
            "vlan_id": None,
        }

        lines = output.split("\n")
        for line in lines:
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                if key == "IP Address":
                    ipmi_info["ip_address"] = value if value != "0.0.0.0" else None
                elif key == "MAC Address":
                    ipmi_info["mac_address"] = value
                elif key == "Default Gateway IP":
                    ipmi_info["gateway"] = value if value != "0.0.0.0" else None
                elif key == "Subnet Mask":
                    ipmi_info["netmask"] = value if value != "0.0.0.0" else None
                elif key == "802.1q VLAN ID":
                    ipmi_info["vlan_id"] = value if value != "Disabled" else None

        return ipmi_info

    def _store_discovery_results(
        self,
        context: WorkflowContext,
        config: ProvisioningConfig,
        hardware_info: Dict[str, Any],
        ipmi_info: Dict[str, Any],
    ):
        """Store discovery results in the database."""
        if context.db_helper:
            # Store hardware information
            context.db_helper.updateserverinfo(
                config.server_id, "vendor", hardware_info["vendor"]
            )
            context.db_helper.updateserverinfo(
                config.server_id, "server_model", hardware_info["model"]
            )
            context.db_helper.updateserverinfo(
                config.server_id, "serial_number", hardware_info["serial_number"]
            )

            # Store IPMI information
            if ipmi_info["ip_address"]:
                context.db_helper.updateserverinfo(
                    config.server_id, "ipmi_ip", ipmi_info["ip_address"]
                )
            if ipmi_info["mac_address"]:
                context.db_helper.updateserverinfo(
                    config.server_id, "ipmi_mac", ipmi_info["mac_address"]
                )

            # Update status
            context.db_helper.updateserverinfo(
                config.server_id, "status_name", "Hardware Discovered"
            )

            logger.info(f"Stored discovery results for {config.server_id}")

        # Store in context for next stages
        context.hardware_info = hardware_info
        context.ipmi_info = ipmi_info
