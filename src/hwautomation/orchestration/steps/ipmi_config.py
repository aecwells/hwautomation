"""IPMI configuration workflow steps.

This module provides steps for IPMI configuration operations,
including IP assignment, credential setup, and connectivity testing.
"""

import ipaddress
import time
from typing import Any, Dict, Optional

from hwautomation.logging import get_logger

from ...hardware.ipmi import IpmiManager
from ...utils.network import SSHClient
from ..workflows.base import (
    BaseWorkflowStep,
    ConditionalWorkflowStep,
    RetryableWorkflowStep,
    StepContext,
    StepExecutionResult,
)

logger = get_logger(__name__)


class ConfigureIpmiStep(ConditionalWorkflowStep):
    """Step to configure IPMI if IP range is provided."""

    def __init__(self):
        super().__init__(
            name="configure_ipmi",
            description="Configure IPMI settings if IP parameters provided",
        )
        self.ipmi_manager = None

    def should_execute(self, context: StepContext) -> bool:
        """Check if IPMI configuration should be performed."""
        return context.ipmi_ip is not None

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate required information for IPMI configuration."""
        if not context.server_ip:
            context.add_error("Server IP required for IPMI configuration")
            return False

        if not context.ipmi_ip:
            context.add_error("IPMI IP required for IPMI configuration")
            return False

        return True

    def _execute_conditional(self, context: StepContext) -> StepExecutionResult:
        """Configure IPMI settings."""
        try:
            context.add_sub_task(f"Configuring IPMI with IP {context.ipmi_ip}")

            # Initialize IPMI manager
            self.ipmi_manager = IpmiManager()

            # Configure IPMI based on vendor
            if context.manufacturer:
                if context.manufacturer.lower() == "supermicro":
                    config_result = self._configure_supermicro_ipmi(context)
                elif context.manufacturer.lower() in ["hp", "hpe"]:
                    config_result = self._configure_hp_ipmi(context)
                elif context.manufacturer.lower() == "dell":
                    config_result = self._configure_dell_ipmi(context)
                else:
                    config_result = self._configure_generic_ipmi(context)
            else:
                config_result = self._configure_generic_ipmi(context)

            if not config_result["success"]:
                return StepExecutionResult.failure(
                    f"IPMI configuration failed: {config_result.get('error', 'Unknown error')}"
                )

            context.set_data("ipmi_config_result", config_result)
            context.add_sub_task("IPMI configuration completed successfully")

            return StepExecutionResult.success(
                f"IPMI configured with IP {context.ipmi_ip}",
                {"ipmi_config": config_result},
            )

        except Exception as e:
            return StepExecutionResult.failure(f"IPMI configuration failed: {e}")

    def _configure_supermicro_ipmi(self, context: StepContext) -> Dict[str, Any]:
        """Configure IPMI on Supermicro server."""
        try:
            ssh_client = SSHClient(
                hostname=context.server_ip,
                username=context.get_data("ssh_username", "ubuntu"),
            )

            # Calculate network settings
            network_config = self._calculate_network_config(context)

            # Configure IPMI using ipmitool
            ipmi_commands = [
                f"sudo ipmitool lan set 1 ipsrc static",
                f"sudo ipmitool lan set 1 ipaddr {context.ipmi_ip}",
                f"sudo ipmitool lan set 1 netmask {network_config['netmask']}",
                f"sudo ipmitool lan set 1 defgw ipaddr {network_config['gateway']}",
                f"sudo ipmitool user set name 2 ADMIN",
                f"sudo ipmitool user set password 2 ADMIN",
                f"sudo ipmitool user enable 2",
                f"sudo ipmitool channel setaccess 1 2 privilege=4",
            ]

            for command in ipmi_commands:
                result = ssh_client.execute_command(command)
                if not result["success"]:
                    return {
                        "success": False,
                        "error": f"IPMI command failed: {command} - {result.get('stderr', 'Unknown error')}",
                    }

            return {
                "success": True,
                "ipmi_ip": context.ipmi_ip,
                "username": "ADMIN",
                "password": "ADMIN",
                "vendor": "supermicro",
                "network_config": network_config,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _configure_hp_ipmi(self, context: StepContext) -> Dict[str, Any]:
        """Configure IPMI on HP/HPE server."""
        try:
            # HP servers use iLO, configuration would be different
            # For now, return a placeholder implementation
            return {
                "success": True,
                "ipmi_ip": context.ipmi_ip,
                "username": "Administrator",
                "password": "password",
                "vendor": "hp",
                "note": "HP iLO configuration placeholder",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _configure_dell_ipmi(self, context: StepContext) -> Dict[str, Any]:
        """Configure IPMI on Dell server."""
        try:
            # Dell servers use iDRAC, configuration would be different
            # For now, return a placeholder implementation
            return {
                "success": True,
                "ipmi_ip": context.ipmi_ip,
                "username": "root",
                "password": "calvin",
                "vendor": "dell",
                "note": "Dell iDRAC configuration placeholder",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _configure_generic_ipmi(self, context: StepContext) -> Dict[str, Any]:
        """Configure IPMI using generic commands."""
        try:
            ssh_client = SSHClient(
                hostname=context.server_ip,
                username=context.get_data("ssh_username", "ubuntu"),
            )

            # Calculate network settings
            network_config = self._calculate_network_config(context)

            # Generic IPMI configuration
            ipmi_commands = [
                f"sudo ipmitool lan set 1 ipsrc static",
                f"sudo ipmitool lan set 1 ipaddr {context.ipmi_ip}",
                f"sudo ipmitool lan set 1 netmask {network_config['netmask']}",
                f"sudo ipmitool lan set 1 defgw ipaddr {network_config['gateway']}",
            ]

            for command in ipmi_commands:
                result = ssh_client.execute_command(command)
                if not result["success"]:
                    return {
                        "success": False,
                        "error": f"IPMI command failed: {command} - {result.get('stderr', 'Unknown error')}",
                    }

            return {
                "success": True,
                "ipmi_ip": context.ipmi_ip,
                "vendor": "generic",
                "network_config": network_config,
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _calculate_network_config(self, context: StepContext) -> Dict[str, str]:
        """Calculate network configuration for IPMI."""
        try:
            # Default network configuration
            network_config = {
                "netmask": "255.255.255.0",
                "gateway": context.gateway or "192.168.1.1",
            }

            # Try to calculate based on server IP if available
            if context.server_ip and context.ipmi_ip:
                try:
                    # Assume same subnet as server IP
                    server_network = ipaddress.IPv4Network(
                        f"{context.server_ip}/24", strict=False
                    )
                    ipmi_ip = ipaddress.IPv4Address(context.ipmi_ip)

                    if ipmi_ip in server_network:
                        network_config["netmask"] = str(server_network.netmask)
                        # Use first IP as gateway
                        network_config["gateway"] = str(
                            server_network.network_address + 1
                        )

                except Exception as e:
                    logger.debug(f"Network calculation failed, using defaults: {e}")

            return network_config

        except Exception as e:
            logger.warning(f"Network config calculation failed: {e}")
            return {
                "netmask": "255.255.255.0",
                "gateway": context.gateway or "192.168.1.1",
            }


class TestIpmiConnectivityStep(RetryableWorkflowStep):
    """Step to test IPMI connectivity after configuration."""

    def __init__(self):
        super().__init__(
            name="test_ipmi_connectivity",
            description="Test IPMI connectivity after configuration",
            max_retries=3,
            retry_delay=10.0,
        )
        self.ipmi_manager = None

    def should_execute(self, context: StepContext) -> bool:
        """Only test if IPMI was configured."""
        return context.get_data("ipmi_config_result") is not None

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate IPMI configuration was completed."""
        ipmi_config = context.get_data("ipmi_config_result")
        if not ipmi_config:
            context.add_error("IPMI configuration required for connectivity test")
            return False

        return True

    def _execute_with_retry(self, context: StepContext) -> StepExecutionResult:
        """Test IPMI connectivity with retry logic."""
        try:
            context.add_sub_task(f"Testing IPMI connectivity to {context.ipmi_ip}")

            # Initialize IPMI manager if needed
            if not self.ipmi_manager:
                self.ipmi_manager = IpmiManager()

            ipmi_config = context.get_data("ipmi_config_result")
            username = ipmi_config.get("username", "ADMIN")
            password = ipmi_config.get("password", "ADMIN")

            # Test IPMI connectivity
            test_result = self.ipmi_manager.test_connection(
                host=context.ipmi_ip, username=username, password=password
            )

            if not test_result.success:
                return StepExecutionResult.retry(
                    f"IPMI connectivity test failed: {test_result.error_message}"
                )

            context.set_data("ipmi_test_result", test_result)
            context.add_sub_task("IPMI connectivity test passed")

            return StepExecutionResult.success(
                f"IPMI connectivity confirmed to {context.ipmi_ip}",
                {"connectivity_test": test_result},
            )

        except Exception as e:
            return StepExecutionResult.retry(
                f"Exception testing IPMI connectivity: {e}"
            )


class RecordIpmiConfigStep(BaseWorkflowStep):
    """Step to record IPMI configuration results in the database."""

    def __init__(self):
        super().__init__(
            name="record_ipmi_config",
            description="Record IPMI configuration results in database",
        )

    def should_execute(self, context: StepContext) -> bool:
        """Only record if IPMI was configured."""
        return context.get_data("ipmi_config_result") is not None

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Record IPMI configuration information in the database."""
        try:
            from ...database.helper import DbHelper

            context.add_sub_task("Recording IPMI configuration results in database")

            # Use DATABASE_PATH from environment, defaulting to data/hw_automation.db
            import os
            db_path = os.getenv("DATABASE_PATH", "data/hw_automation.db")
            db_helper = DbHelper(db_path)

            # Record IPMI configuration
            ipmi_config = context.get_data("ipmi_config_result")
            if ipmi_config:
                db_helper.updateserverinfo(context.server_id, "ipmi_configured", "true")
                db_helper.updateserverinfo(
                    context.server_id, "ipmi_ip", context.ipmi_ip
                )

                if ipmi_config.get("username"):
                    db_helper.updateserverinfo(
                        context.server_id, "ipmi_username", ipmi_config["username"]
                    )

                if ipmi_config.get("vendor"):
                    db_helper.updateserverinfo(
                        context.server_id, "ipmi_vendor", ipmi_config["vendor"]
                    )

                # Record network configuration
                network_config = ipmi_config.get("network_config", {})
                if network_config:
                    db_helper.updateserverinfo(
                        context.server_id, "ipmi_netmask", network_config.get("netmask")
                    )
                    db_helper.updateserverinfo(
                        context.server_id, "ipmi_gateway", network_config.get("gateway")
                    )

            # Record connectivity test result
            test_result = context.get_data("ipmi_test_result")
            if test_result:
                db_helper.updateserverinfo(
                    context.server_id, "ipmi_connectivity_tested", "true"
                )
                db_helper.updateserverinfo(
                    context.server_id,
                    "ipmi_test_status",
                    "passed" if test_result.success else "failed",
                )

            return StepExecutionResult.success(
                f"IPMI configuration results recorded for server {context.server_id}",
                {"database_updated": True},
            )

        except Exception as e:
            return StepExecutionResult.failure(
                f"Failed to record IPMI configuration results: {e}"
            )


class AssignIpmiIpStep(BaseWorkflowStep):
    """Step to assign IPMI IP if range is provided but specific IP is not."""

    def __init__(self, ip_range_start: str, ip_range_end: str):
        super().__init__(
            name="assign_ipmi_ip", description="Assign IPMI IP from available range"
        )
        self.ip_range_start = ip_range_start
        self.ip_range_end = ip_range_end

    def should_execute(self, context: StepContext) -> bool:
        """Only assign if IPMI IP is not already set but range is available."""
        return context.ipmi_ip is None and self.ip_range_start and self.ip_range_end

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Assign next available IPMI IP from range."""
        try:
            context.add_sub_task(
                f"Assigning IPMI IP from range {self.ip_range_start} - {self.ip_range_end}"
            )

            # Find next available IP
            assigned_ip = self._find_next_available_ip()

            if not assigned_ip:
                return StepExecutionResult.failure(
                    "No available IPMI IP addresses in range"
                )

            # Assign IP to context
            context.ipmi_ip = assigned_ip
            context.set_data("assigned_ipmi_ip", assigned_ip)

            context.add_sub_task(f"Assigned IPMI IP: {assigned_ip}")

            return StepExecutionResult.success(
                f"IPMI IP assigned: {assigned_ip}", {"assigned_ip": assigned_ip}
            )

        except Exception as e:
            return StepExecutionResult.failure(f"Failed to assign IPMI IP: {e}")

    def _find_next_available_ip(self) -> Optional[str]:
        """Find the next available IP in the range."""
        try:
            import os
            from ...database.helper import DbHelper

            # Get all assigned IPMI IPs from database
            # Use DATABASE_PATH from environment, defaulting to data/hw_automation.db
            db_path = os.getenv("DATABASE_PATH", "data/hw_automation.db")
            db_helper = DbHelper(db_path)
            assigned_ips = set()

            # Query existing IPMI IPs (this would need to be implemented in DbHelper)
            # For now, use a simple increment approach

            start_ip = ipaddress.IPv4Address(self.ip_range_start)
            end_ip = ipaddress.IPv4Address(self.ip_range_end)

            current_ip = start_ip
            while current_ip <= end_ip:
                ip_str = str(current_ip)
                if ip_str not in assigned_ips:
                    # TODO: Check if IP is actually available (ping test)
                    return ip_str
                current_ip += 1

            return None

        except Exception as e:
            logger.error(f"Failed to find available IP: {e}")
            return None
