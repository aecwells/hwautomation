"""
Network setup stage handler.

Handles network configuration and SSH connectivity setup.
"""

import socket
import time
from typing import Any, Dict

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


class NetworkSetupStageHandler(ProvisioningStageHandler):
    """Handles network setup and SSH connectivity."""

    def get_stage(self) -> ProvisioningStage:
        """Get the stage this handler manages."""
        return ProvisioningStage.NETWORK_SETUP

    def validate_prerequisites(self, context: WorkflowContext) -> bool:
        """Validate that prerequisites for network setup are met."""
        return (
            context.server_id is not None
            and context.maas_client is not None
            and context.db_helper is not None
        )

    def execute(
        self, context: WorkflowContext, config: ProvisioningConfig
    ) -> StageResult:
        """Execute network setup."""
        logger.info(f"Starting network setup for server {config.server_id}")

        try:
            # Get server IP address
            server_ip = self._get_server_ip(context, config)

            # Test SSH connectivity
            ssh_success = self._test_ssh_connectivity(server_ip, config)

            # Store network information
            self._store_network_info(context, config, server_ip, ssh_success)

            return StageResult(
                success=True,
                stage=self.get_stage(),
                data={
                    "server_ip": server_ip,
                    "ssh_available": ssh_success,
                },
                next_stage=ProvisioningStage.HARDWARE_DISCOVERY,
            )

        except Exception as e:
            logger.error(f"Network setup failed for {config.server_id}: {e}")
            return StageResult(
                success=False,
                stage=self.get_stage(),
                data={},
                error_message=str(e),
            )

    def _get_server_ip(
        self,
        context: WorkflowContext,
        config: ProvisioningConfig,
        max_retries: int = 5,
        retry_delay: int = 30,
    ) -> str:
        """Retrieve server IP address from MaaS."""
        context.report_sub_task("Retrieving server IP address from MaaS")

        for attempt in range(max_retries):
            try:
                machine_info = context.maas_client.get_machine_info(config.server_id)
                if not machine_info:
                    raise ValueError(f"Machine {config.server_id} not found in MaaS")

                # Extract IP address
                ip_addresses = machine_info.get("ip_addresses", [])
                if not ip_addresses:
                    if attempt < max_retries - 1:
                        context.report_sub_task(
                            f"No IP address yet, retrying in {retry_delay}s (attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(retry_delay)
                        continue
                    else:
                        raise ValueError(
                            f"No IP address found for machine {config.server_id}"
                        )

                # Get the first non-loopback IP
                server_ip = None
                for ip in ip_addresses:
                    if ip != "127.0.0.1" and not ip.startswith("169.254."):
                        server_ip = ip
                        break

                if not server_ip:
                    raise ValueError(
                        f"No usable IP address found for machine {config.server_id}"
                    )

                logger.info(
                    f"Retrieved IP address {server_ip} for server {config.server_id}"
                )
                context.server_ip = server_ip
                return server_ip

            except Exception as e:
                if attempt < max_retries - 1:
                    context.report_sub_task(
                        f"Failed to get IP, retrying in {retry_delay}s: {e}"
                    )
                    time.sleep(retry_delay)
                else:
                    raise

        raise ValueError(f"Failed to retrieve IP address after {max_retries} attempts")

    def _test_ssh_connectivity(
        self,
        server_ip: str,
        config: ProvisioningConfig,
        timeout: int = 300,  # 5 minutes
    ) -> bool:
        """Test SSH connectivity to the server."""
        logger.info(f"Testing SSH connectivity to {server_ip}")

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Test basic TCP connectivity first
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((server_ip, 22))
                sock.close()

                if result == 0:
                    # TCP connection successful, try SSH
                    try:
                        ssh_client = SSHClient()
                        success = ssh_client.connect(
                            hostname=server_ip,
                            username=config.ssh_username,
                            key_path=config.ssh_key_path,
                            timeout=10,
                        )

                        if success:
                            # Test a simple command
                            result = ssh_client.exec_command(
                                "echo 'SSH test successful'"
                            )
                            ssh_client.disconnect()

                            if result.exit_code == 0:
                                logger.info(
                                    f"SSH connectivity confirmed to {server_ip}"
                                )
                                return True
                            else:
                                logger.warning(
                                    f"SSH command failed on {server_ip}: {result.stderr}"
                                )
                        else:
                            logger.warning(f"SSH connection failed to {server_ip}")

                    except Exception as ssh_e:
                        logger.warning(f"SSH test failed to {server_ip}: {ssh_e}")

                # If we get here, connection failed - wait and retry
                time.sleep(10)

            except Exception as e:
                logger.warning(f"Network connectivity test failed to {server_ip}: {e}")
                time.sleep(10)

        logger.warning(f"SSH connectivity test timed out for {server_ip}")
        return False

    def _store_network_info(
        self,
        context: WorkflowContext,
        config: ProvisioningConfig,
        server_ip: str,
        ssh_available: bool,
    ):
        """Store network information in the database."""
        if context.db_helper:
            context.db_helper.updateserverinfo(
                config.server_id, "ip_address", server_ip
            )
            context.db_helper.updateserverinfo(
                config.server_id,
                "ip_address_works",
                "TRUE" if ssh_available else "FALSE",
            )

            if ssh_available:
                context.db_helper.updateserverinfo(
                    config.server_id, "status_name", "Network Ready"
                )
            else:
                context.db_helper.updateserverinfo(
                    config.server_id, "status_name", "Network Issues"
                )

            logger.info(
                f"Stored network info for {config.server_id}: IP={server_ip}, SSH={ssh_available}"
            )
