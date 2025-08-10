"""Network configuration workflow steps.

This module provides steps for network-related operations,
including SSH connectivity, network testing, and IP management.
"""

import subprocess
import time
from typing import Any, Dict, List, Optional

from hwautomation.logging import get_logger

from ...utils.network import SSHClient
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

    def __init__(
        self, ssh_username: str = "ubuntu", ssh_key_path: Optional[str] = None
    ):
        super().__init__(
            name="establish_ssh_connection",
            description="Establish SSH connection to server",
            max_retries=5,
            retry_delay=30.0,
        )
        self.ssh_username = ssh_username
        self.ssh_key_path = ssh_key_path

    def validate_prerequisites(self, context: StepContext) -> bool:
        """Validate server IP is available."""
        if not context.server_ip:
            context.add_error("Server IP address required for SSH connection")
            return False

        return True

    def _execute_with_retry(self, context: StepContext) -> StepExecutionResult:
        """Establish SSH connection with retry logic."""
        try:
            context.add_sub_task(f"Establishing SSH connection to {context.server_ip}")

            # Create SSH client
            ssh_client = SSHClient(
                hostname=context.server_ip,
                username=self.ssh_username,
                key_path=self.ssh_key_path,
            )

            # Test connection with a simple command
            result = ssh_client.execute_command("echo 'SSH connection test'")

            if not result.get("success"):
                return StepExecutionResult.retry(
                    f"SSH connection failed: {result.get('stderr', 'Unknown error')}"
                )

            # Store SSH client in context
            context.set_data("ssh_client", ssh_client)
            context.set_data("ssh_username", self.ssh_username)

            context.add_sub_task("SSH connection established successfully")

            return StepExecutionResult.success(
                f"SSH connection established to {context.server_ip}",
                {"ssh_username": self.ssh_username},
            )

        except Exception as e:
            return StepExecutionResult.retry(
                f"Exception establishing SSH connection: {e}"
            )


class TestNetworkConnectivityStep(BaseWorkflowStep):
    """Step to test network connectivity and gather network information."""

    def __init__(self):
        super().__init__(
            name="test_network_connectivity",
            description="Test network connectivity and gather network information",
        )

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Test various network connectivity aspects."""
        try:
            context.add_sub_task("Testing network connectivity")

            ssh_client = context.get_data("ssh_client")
            if not ssh_client:
                return StepExecutionResult.failure("SSH client not available")

            connectivity_results = {}

            # Test internet connectivity
            internet_result = ssh_client.execute_command("ping -c 3 8.8.8.8")
            connectivity_results["internet"] = internet_result.get("success", False)

            # Test DNS resolution
            dns_result = ssh_client.execute_command("nslookup google.com")
            connectivity_results["dns"] = dns_result.get("success", False)

            # Get network interface information
            interface_result = ssh_client.execute_command("ip addr show")
            if interface_result.get("success"):
                connectivity_results["interfaces"] = interface_result.get("stdout", "")

            # Get routing information
            route_result = ssh_client.execute_command("ip route show")
            if route_result.get("success"):
                connectivity_results["routes"] = route_result.get("stdout", "")

            # Store results in context
            context.set_data("network_connectivity", connectivity_results)

            # Determine overall connectivity status
            overall_status = (
                "good" if connectivity_results.get("internet") else "limited"
            )

            context.add_sub_task(
                f"Network connectivity test completed: {overall_status}"
            )

            return StepExecutionResult.success(
                f"Network connectivity tested: {overall_status}",
                {
                    "connectivity_status": overall_status,
                    "details": connectivity_results,
                },
            )

        except Exception as e:
            return StepExecutionResult.failure(f"Network connectivity test failed: {e}")


class ConfigureNetworkSettingsStep(ConditionalWorkflowStep):
    """Step to configure network settings if needed."""

    def __init__(self, target_gateway: Optional[str] = None):
        super().__init__(
            name="configure_network_settings",
            description="Configure network settings if required",
        )
        self.target_gateway = target_gateway

    def should_execute(self, context: StepContext) -> bool:
        """Configure network only if specific settings are required."""
        return self.target_gateway is not None or context.gateway is not None

    def _execute_conditional(self, context: StepContext) -> StepExecutionResult:
        """Configure network settings."""
        try:
            gateway = self.target_gateway or context.gateway
            context.add_sub_task(f"Configuring network settings (gateway: {gateway})")

            ssh_client = context.get_data("ssh_client")
            if not ssh_client:
                return StepExecutionResult.failure("SSH client not available")

            # Configure gateway if provided
            if gateway:
                gateway_result = self._configure_gateway(ssh_client, gateway)
                if not gateway_result["success"]:
                    return StepExecutionResult.failure(
                        f"Gateway configuration failed: {gateway_result.get('error')}"
                    )

            # Configure DNS if needed
            dns_result = self._configure_dns(ssh_client)
            if not dns_result["success"]:
                logger.warning(f"DNS configuration warning: {dns_result.get('error')}")

            context.add_sub_task("Network settings configured successfully")

            return StepExecutionResult.success(
                f"Network configured with gateway {gateway}", {"gateway": gateway}
            )

        except Exception as e:
            return StepExecutionResult.failure(f"Network configuration failed: {e}")

    def _configure_gateway(self, ssh_client: SSHClient, gateway: str) -> Dict[str, Any]:
        """Configure the default gateway."""
        try:
            # Remove existing default route
            ssh_client.execute_command("sudo ip route del default || true")

            # Add new default route
            result = ssh_client.execute_command(
                f"sudo ip route add default via {gateway}"
            )

            if not result.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to add gateway route: {result.get('stderr', 'Unknown error')}",
                }

            # Verify route was added
            verify_result = ssh_client.execute_command("ip route show default")
            if not verify_result.get("success") or gateway not in verify_result.get(
                "stdout", ""
            ):
                return {"success": False, "error": "Gateway route verification failed"}

            return {"success": True, "gateway": gateway}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _configure_dns(self, ssh_client: SSHClient) -> Dict[str, Any]:
        """Configure DNS settings."""
        try:
            # Configure basic DNS servers
            dns_config = """
nameserver 8.8.8.8
nameserver 8.8.4.4
"""

            # Write DNS configuration
            write_cmd = f'echo "{dns_config.strip()}" | sudo tee /etc/resolv.conf'
            result = ssh_client.execute_command(write_cmd)

            if not result.get("success"):
                return {
                    "success": False,
                    "error": f"Failed to configure DNS: {result.get('stderr', 'Unknown error')}",
                }

            return {"success": True, "dns_servers": ["8.8.8.8", "8.8.4.4"]}

        except Exception as e:
            return {"success": False, "error": str(e)}


class ValidateNetworkConfigurationStep(BaseWorkflowStep):
    """Step to validate network configuration after changes."""

    def __init__(self):
        super().__init__(
            name="validate_network_configuration",
            description="Validate network configuration after changes",
        )

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Validate the network configuration."""
        try:
            context.add_sub_task("Validating network configuration")

            ssh_client = context.get_data("ssh_client")
            if not ssh_client:
                return StepExecutionResult.failure("SSH client not available")

            validation_results = {}

            # Validate gateway configuration
            gateway_result = ssh_client.execute_command("ip route show default")
            validation_results["gateway_configured"] = gateway_result.get(
                "success", False
            )

            # Validate DNS configuration
            dns_result = ssh_client.execute_command("cat /etc/resolv.conf")
            validation_results["dns_configured"] = dns_result.get("success", False)

            # Test external connectivity after configuration
            connectivity_result = ssh_client.execute_command("ping -c 2 8.8.8.8")
            validation_results["external_connectivity"] = connectivity_result.get(
                "success", False
            )

            # Store validation results
            context.set_data("network_validation", validation_results)

            # Determine overall validation status
            all_good = all(validation_results.values())
            status = "passed" if all_good else "partial"

            context.add_sub_task(f"Network validation completed: {status}")

            return StepExecutionResult.success(
                f"Network validation {status}",
                {"validation_status": status, "details": validation_results},
            )

        except Exception as e:
            return StepExecutionResult.failure(f"Network validation failed: {e}")


class GatherNetworkInventoryStep(BaseWorkflowStep):
    """Step to gather comprehensive network inventory information."""

    def __init__(self):
        super().__init__(
            name="gather_network_inventory",
            description="Gather comprehensive network inventory information",
        )

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Gather network inventory information."""
        try:
            context.add_sub_task("Gathering network inventory information")

            ssh_client = context.get_data("ssh_client")
            if not ssh_client:
                return StepExecutionResult.failure("SSH client not available")

            inventory = {}

            # Get network interfaces
            interfaces_cmd = (
                "ip addr show | grep -E '^[0-9]+:' | awk '{print $2}' | sed 's/:$//'"
            )
            interfaces_result = ssh_client.execute_command(interfaces_cmd)
            if interfaces_result.get("success"):
                interfaces = interfaces_result.get("stdout", "").strip().split("\n")
                inventory["interfaces"] = [iface for iface in interfaces if iface]

            # Get MAC addresses
            for interface in inventory.get("interfaces", []):
                if interface in ["lo"]:  # Skip loopback
                    continue

                mac_cmd = (
                    f"cat /sys/class/net/{interface}/address 2>/dev/null || echo 'N/A'"
                )
                mac_result = ssh_client.execute_command(mac_cmd)
                if mac_result.get("success"):
                    mac_address = mac_result.get("stdout", "").strip()
                    inventory[f"{interface}_mac"] = mac_address

            # Get IP addresses
            ip_result = ssh_client.execute_command("hostname -I")
            if ip_result.get("success"):
                ips = ip_result.get("stdout", "").strip().split()
                inventory["ip_addresses"] = ips

            # Get hostname
            hostname_result = ssh_client.execute_command("hostname")
            if hostname_result.get("success"):
                inventory["hostname"] = hostname_result.get("stdout", "").strip()

            # Get default gateway
            gateway_result = ssh_client.execute_command(
                "ip route show default | awk '{print $3}' | head -1"
            )
            if gateway_result.get("success"):
                inventory["default_gateway"] = gateway_result.get("stdout", "").strip()

            # Store inventory in context
            context.set_data("network_inventory", inventory)

            context.add_sub_task("Network inventory gathered successfully")

            return StepExecutionResult.success(
                "Network inventory gathered", {"inventory": inventory}
            )

        except Exception as e:
            return StepExecutionResult.failure(
                f"Network inventory gathering failed: {e}"
            )


class PingTestStep(BaseWorkflowStep):
    """Step to perform ping tests to various targets."""

    def __init__(self, targets: Optional[List[str]] = None):
        super().__init__(
            name="ping_test", description="Perform ping tests to verify connectivity"
        )
        self.targets = targets or ["8.8.8.8", "google.com"]

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Perform ping tests to specified targets."""
        try:
            context.add_sub_task(
                f"Performing ping tests to {len(self.targets)} targets"
            )

            ssh_client = context.get_data("ssh_client")
            if not ssh_client:
                return StepExecutionResult.failure("SSH client not available")

            ping_results = {}

            for target in self.targets:
                ping_cmd = f"ping -c 3 -W 5 {target}"
                result = ssh_client.execute_command(ping_cmd)

                ping_results[target] = {
                    "success": result.get("success", False),
                    "output": result.get("stdout", ""),
                    "error": result.get("stderr", ""),
                }

                if result.get("success"):
                    # Extract latency information if available
                    output = result.get("stdout", "")
                    if "min/avg/max" in output:
                        # Try to extract timing info
                        try:
                            timing_line = [
                                line
                                for line in output.split("\n")
                                if "min/avg/max" in line
                            ][0]
                            ping_results[target]["timing"] = timing_line
                        except:
                            pass

            # Store results in context
            context.set_data("ping_test_results", ping_results)

            # Calculate success rate
            successful_pings = sum(
                1 for result in ping_results.values() if result["success"]
            )
            success_rate = successful_pings / len(self.targets)

            context.add_sub_task(
                f"Ping tests completed: {successful_pings}/{len(self.targets)} successful"
            )

            return StepExecutionResult.success(
                f"Ping tests completed: {success_rate:.1%} success rate",
                {"success_rate": success_rate, "results": ping_results},
            )

        except Exception as e:
            return StepExecutionResult.failure(f"Ping tests failed: {e}")


class RecordNetworkInfoStep(BaseWorkflowStep):
    """Step to record network information in the database."""

    def __init__(self):
        super().__init__(
            name="record_network_info",
            description="Record network information in database",
        )

    def execute(self, context: StepContext) -> StepExecutionResult:
        """Record network information in the database."""
        try:
            from ...database.helper import DbHelper

            context.add_sub_task("Recording network information in database")

            db_helper = DbHelper()

            # Record network inventory
            inventory = context.get_data("network_inventory")
            if inventory:
                if inventory.get("hostname"):
                    db_helper.updateserverinfo(
                        context.server_id, "hostname", inventory["hostname"]
                    )

                if inventory.get("ip_addresses"):
                    primary_ip = (
                        inventory["ip_addresses"][0]
                        if inventory["ip_addresses"]
                        else None
                    )
                    if primary_ip:
                        db_helper.updateserverinfo(
                            context.server_id, "primary_ip", primary_ip
                        )

                if inventory.get("default_gateway"):
                    db_helper.updateserverinfo(
                        context.server_id,
                        "default_gateway",
                        inventory["default_gateway"],
                    )

                # Record MAC addresses for primary interface
                interfaces = inventory.get("interfaces", [])
                for interface in interfaces:
                    if interface in ["lo"]:  # Skip loopback
                        continue
                    mac_key = f"{interface}_mac"
                    if inventory.get(mac_key):
                        db_helper.updateserverinfo(
                            context.server_id, f"mac_{interface}", inventory[mac_key]
                        )
                        break  # Record primary interface MAC

            # Record connectivity test results
            connectivity = context.get_data("network_connectivity")
            if connectivity:
                db_helper.updateserverinfo(
                    context.server_id,
                    "internet_connectivity",
                    "yes" if connectivity.get("internet") else "no",
                )
                db_helper.updateserverinfo(
                    context.server_id,
                    "dns_resolution",
                    "yes" if connectivity.get("dns") else "no",
                )

            # Record ping test results
            ping_results = context.get_data("ping_test_results")
            if ping_results:
                successful_targets = [
                    target
                    for target, result in ping_results.items()
                    if result["success"]
                ]
                db_helper.updateserverinfo(
                    context.server_id, "ping_test_targets", str(len(successful_targets))
                )

            return StepExecutionResult.success(
                f"Network information recorded for server {context.server_id}",
                {"database_updated": True},
            )

        except Exception as e:
            return StepExecutionResult.failure(
                f"Failed to record network information: {e}"
            )
