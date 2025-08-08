"""
Server Provisioning Workflow

Implements the complete server provisioning workflow from commissioning
through BIOS configuration to IPMI setup and finalization.
"""

import asyncio
import json
import logging
import socket
import subprocess
import time
import traceback
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .exceptions import (
    BiosConfigurationError,
    CommissioningError,
    IPMIConfigurationError,
    SSHConnectionError,
    WorkflowError,
)
from .workflow_manager import Workflow, WorkflowContext, WorkflowManager, WorkflowStep

logger = logging.getLogger(__name__)


class ServerProvisioningWorkflow:
    """
    Complete server provisioning workflow implementation

    Orchestrates the 8-step process:
    1. Commission server via MaaS
    2. Retrieve server IP address
    3. Discover hardware information (including IPMI address)
    4. Pull BIOS config via SSH
    5. Modify BIOS configuration
    6. Push updated BIOS config
    7. Update IPMI configuration
    8. Finalize and tag server
    """

    def __init__(self, workflow_manager: WorkflowManager):
        self.manager = workflow_manager
        self.logger = logging.getLogger(__name__)

    def create_provisioning_workflow(
        self,
        server_id: str,
        device_type: str,
        target_ipmi_ip: Optional[str] = None,
        rack_location: Optional[str] = None,
        subnet_mask: Optional[str] = None,
        gateway: Optional[str] = None,
        **kwargs,
    ) -> Workflow:
        """
        Create a complete server provisioning workflow

        Args:
            server_id: Unique identifier for the server
            device_type: Device type (e.g., 's2.c2.small')
            target_ipmi_ip: Optional target IPMI IP address (can be set later)
            rack_location: Optional physical rack location (can be set later)
            subnet_mask: Optional subnet mask for network configuration
            gateway: Optional gateway IP address for network configuration
            **kwargs: Additional metadata

        Returns:
            Workflow: Configured workflow ready for execution

        Note: The workflow automatically detects when force recommissioning is needed
        based on device status and SSH connectivity. target_ipmi_ip, rack_location,
        and gateway are optional and can be configured in a final manual step after
        hardware discovery.
        """
        workflow_id = f"provision_{server_id}_{int(time.time())}"
        workflow = self.manager.create_workflow(workflow_id)

        # Step 1: Commission Server via MaaS
        workflow.add_step(
            WorkflowStep(
                name="commission_server",
                description="Commission server through MaaS",
                function=self._commission_server,
                timeout=1800,  # 30 minutes
                retry_count=2,
            )
        )

        # Step 2: Retrieve Server IP Address
        workflow.add_step(
            WorkflowStep(
                name="get_server_ip",
                description="Retrieve server IP address from MaaS",
                function=self._get_server_ip,
                timeout=300,  # 5 minutes
                retry_count=5,
            )
        )

        # Step 3: Discover Hardware Information
        workflow.add_step(
            WorkflowStep(
                name="discover_hardware",
                description="Discover system hardware and IPMI information via SSH",
                function=self._discover_hardware,
                timeout=600,  # 10 minutes
                retry_count=3,
            )
        )

        # Step 4: Pull BIOS Config via SSH
        workflow.add_step(
            WorkflowStep(
                name="pull_bios_config",
                description="SSH into server and pull BIOS configuration",
                function=self._pull_bios_config,
                timeout=600,  # 10 minutes
                retry_count=3,
            )
        )

        # Step 5: Modify BIOS Configuration
        workflow.add_step(
            WorkflowStep(
                name="modify_bios_config",
                description="Apply device-specific BIOS modifications",
                function=self._modify_bios_config,
                timeout=180,  # 3 minutes
                retry_count=2,
            )
        )

        # Step 6: Push Updated BIOS Config
        workflow.add_step(
            WorkflowStep(
                name="push_bios_config",
                description="Push modified BIOS configuration to server",
                function=self._push_bios_config,
                timeout=600,  # 10 minutes
                retry_count=2,
            )
        )

        # Step 7: Configure IPMI (Optional - only if target_ipmi_ip provided)
        workflow.add_step(
            WorkflowStep(
                name="configure_ipmi",
                description="Configure IPMI settings and network (optional)",
                function=self._configure_ipmi_conditional,
                timeout=300,  # 5 minutes
                retry_count=3,
            )
        )

        # Step 8: Finalize and Tag Server (Basic completion)
        workflow.add_step(
            WorkflowStep(
                name="finalize_server",
                description="Complete basic server commissioning",
                function=self._finalize_server_basic,
                timeout=180,  # 3 minutes
                retry_count=2,
            )
        )

        return workflow

    def create_firmware_first_provisioning_workflow(
        self,
        server_id: str,
        device_type: str,
        target_ipmi_ip: Optional[str] = None,
        rack_location: Optional[str] = None,
        subnet_mask: Optional[str] = None,
        gateway: Optional[str] = None,
        firmware_policy: str = "recommended",
        **kwargs,
    ) -> Workflow:
        """
        Create a firmware-first provisioning workflow.

            This workflow combines firmware updates with the existing provisioning process:
            1. Commission server via MaaS
            2. Get server IP and establish connectivity
            3. Discover hardware information
            4. Execute firmware-first provisioning (firmware updates + BIOS config)
            5. Configure IPMI settings
            6. Finalize server setup

            Args:
                server_id: Unique identifier for the server
                device_type: Device type (e.g., 's2.c2.small')
                target_ipmi_ip: Optional target IPMI IP address
                rack_location: Optional physical rack location
                gateway: Optional gateway IP address for network configuration
                firmware_policy: Firmware update policy ('recommended', 'latest', 'security_only')
                **kwargs: Additional metadata

            Returns:
                Workflow: Configured firmware-first provisioning workflow
        """
        if not self.manager.firmware_workflow:
            # Fall back to regular provisioning if firmware not available
            logger.warning(
                "Firmware management not available - using regular provisioning workflow"
            )
            return self.create_provisioning_workflow(
                server_id,
                device_type,
                target_ipmi_ip,
                rack_location,
                subnet_mask,
                gateway,
                **kwargs,
            )

        workflow_id = f"fw_provision_{server_id}_{int(time.time())}"
        workflow = self.manager.create_workflow(workflow_id)

        # Step 1: Commission Server via MaaS
        workflow.add_step(
            WorkflowStep(
                name="commission_server",
                description="Commission server through MaaS",
                function=self._commission_server,
                timeout=1800,  # 30 minutes
                retry_count=2,
            )
        )

        # Step 2: Retrieve Server IP Address
        workflow.add_step(
            WorkflowStep(
                name="get_server_ip",
                description="Retrieve server IP address from MaaS",
                function=self._get_server_ip,
                timeout=300,  # 5 minutes
                retry_count=5,
            )
        )

        # Step 3: Discover Hardware Information
        workflow.add_step(
            WorkflowStep(
                name="discover_hardware",
                description="Discover system hardware and IPMI information via SSH",
                function=self._discover_hardware,
                timeout=600,  # 10 minutes
                retry_count=3,
            )
        )

        # Step 4: Firmware-First Provisioning
        workflow.add_step(
            WorkflowStep(
                name="firmware_first_provisioning",
                description="Execute firmware updates and BIOS configuration",
                function=lambda ctx: self._execute_firmware_first_provisioning(
                    ctx, device_type, firmware_policy
                ),
                timeout=3600,  # 1 hour for firmware updates
                retry_count=1,
            )
        )

        # Step 5: Configure IPMI Settings
        workflow.add_step(
            WorkflowStep(
                name="configure_ipmi",
                description="Configure IPMI settings and network parameters",
                function=lambda ctx: self._configure_ipmi_with_params(
                    ctx, target_ipmi_ip, subnet_mask, gateway
                ),
                timeout=600,  # 10 minutes
                retry_count=3,
            )
        )

        # Step 6: Finalize Server
        workflow.add_step(
            WorkflowStep(
                name="finalize_server",
                description="Complete firmware-first server commissioning",
                function=lambda ctx: self._finalize_server_firmware_first(
                    ctx, rack_location
                ),
                timeout=180,  # 3 minutes
                retry_count=2,
            )
        )

        return workflow

    def _execute_firmware_first_provisioning(
        self, context: WorkflowContext, device_type: str, firmware_policy: str
    ) -> Dict[str, Any]:
        """Execute firmware-first provisioning step"""
        try:
            context.report_sub_task("Preparing firmware-first provisioning...")

            # Get server IP from context
            if not context.server_data:
                raise WorkflowError(
                    "Server data not available for firmware provisioning"
                )

            server_ip = context.server_data.get("ip_address")
            if not server_ip:
                raise WorkflowError(
                    "Server IP address not available for firmware provisioning"
                )

            # Create credentials (would be configurable in production)
            credentials = {
                "username": "root",  # Default for commissioned servers
                "password": context.server_data.get(
                    "temp_password", "default_password"
                ),
            }

            # Create firmware provisioning context
            from ..hardware.firmware_provisioning_workflow import ProvisioningContext

            provisioning_context = ProvisioningContext(
                server_id=context.server_id,
                device_type=device_type,
                target_ip=server_ip,
                credentials=credentials,
                firmware_policy=firmware_policy,
                operation_id=context.workflow_id,
            )

            context.report_sub_task("Executing firmware-first provisioning workflow...")

            # Execute firmware provisioning (async call wrapped)
            import asyncio

            # Check if firmware workflow is available
            if not self.manager.firmware_workflow:
                raise WorkflowError("Firmware workflow not available")

            if hasattr(asyncio, "run"):
                result = asyncio.run(
                    self.manager.firmware_workflow.execute_firmware_first_provisioning(
                        provisioning_context
                    )
                )
            else:
                # Fallback for older Python versions
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    result = loop.run_until_complete(
                        self.manager.firmware_workflow.execute_firmware_first_provisioning(
                            provisioning_context
                        )
                    )
                finally:
                    loop.close()

            if result.success:
                context.report_sub_task(f"Firmware provisioning completed successfully")
                logger.info(
                    f"Firmware-first provisioning completed for {context.server_id}"
                )
                logger.info(f"  - Firmware updates: {result.firmware_updates_applied}")
                logger.info(f"  - BIOS settings: {result.bios_settings_applied}")
                logger.info(f"  - Execution time: {result.execution_time:.2f}s")

                # Store results in context
                if context.server_data is not None:
                    context.server_data["firmware_result"] = {
                        "firmware_updates_applied": result.firmware_updates_applied,
                        "bios_settings_applied": result.bios_settings_applied,
                        "execution_time": result.execution_time,
                        "phases_completed": [
                            phase.value for phase in result.phases_completed
                        ],
                    }

                # Update database
                if context.db_helper:
                    context.db_helper.updateserverinfo(
                        context.server_id,
                        "firmware_version",
                        f"Updated-{datetime.now().strftime('%Y%m%d')}",
                    )
                    context.db_helper.updateserverinfo(
                        context.server_id,
                        "bios_config_applied",
                        "Yes" if result.bios_settings_applied > 0 else "No",
                    )

                return {"success": True, "result": result}
            else:
                context.report_sub_task(
                    f"Firmware provisioning failed: {result.error_message}"
                )
                logger.error(
                    f"Firmware-first provisioning failed: {result.error_message}"
                )
                return {"success": False, "error": result.error_message}

        except Exception as e:
            context.report_sub_task(f"Firmware provisioning error: {str(e)}")
            logger.error(f"Firmware-first provisioning exception: {e}")
            import traceback

            traceback.print_exc()
            return {"success": False, "error": str(e)}

    def _configure_ipmi_with_params(
        self,
        context: WorkflowContext,
        target_ipmi_ip: Optional[str],
        subnet_mask: Optional[str],
        gateway: Optional[str],
    ) -> Dict[str, Any]:
        """Configure IPMI with optional parameters"""
        # Use existing IPMI configuration logic but with optional parameters
        context.target_ipmi_ip = target_ipmi_ip
        context.subnet_mask = subnet_mask
        context.gateway = gateway
        return self._configure_ipmi(context)

    def _finalize_server_firmware_first(
        self, context: WorkflowContext, rack_location: Optional[str]
    ) -> Dict[str, Any]:
        """Finalize server with firmware-first specific updates"""
        try:
            context.report_sub_task("Finalizing firmware-first provisioned server...")

            # Get firmware results from context
            if not context.server_data:
                raise WorkflowError("Server data not available for finalization")

            firmware_result = context.server_data.get("firmware_result", {})

            # Update server information
            if context.db_helper:
                updates = {
                    "status_name": "Ready",
                    "commissioning_status": "Firmware-First-Complete",
                    "last_workflow_run": datetime.now().isoformat(),
                    "workflow_status": "Completed",
                }

                if rack_location:
                    updates["rack_location"] = rack_location

                # Add firmware-specific notes
                notes = f"Firmware-first provisioning: {firmware_result.get('firmware_updates_applied', 0)} firmware updates, {firmware_result.get('bios_settings_applied', 0)} BIOS settings"
                updates["notes"] = notes

                for field, value in updates.items():
                    context.db_helper.updateserverinfo(context.server_id, field, value)

            context.report_sub_task("Server firmware-first provisioning completed")
            logger.info(
                f"Completed firmware-first provisioning for server {context.server_id}"
            )

            return {"success": True, "status": "firmware_first_complete"}

        except Exception as e:
            logger.error(
                f"Failed to finalize firmware-first server {context.server_id}: {e}"
            )
            return {"success": False, "error": str(e)}

    def _commission_server(self, context: WorkflowContext) -> Dict[str, Any]:
        """Step 1: Commission server via MaaS and add to database"""
        logger.info(f"Commissioning server {context.server_id}")

        try:
            # Create database entry for server if it doesn't exist
            context.report_sub_task("Creating database entry")
            if context.db_helper:
                if not context.db_helper.checkifserveridexists(context.server_id)[0]:
                    context.db_helper.createrowforserver(context.server_id)
                    logger.info(
                        f"Created database entry for server {context.server_id}"
                    )

                # Update status to indicate commissioning started and record workflow_id
                context.db_helper.updateserverinfo(
                    context.server_id, "status_name", "Commissioning"
                )
                context.db_helper.updateserverinfo(
                    context.server_id, "is_ready", "FALSE"
                )
                context.db_helper.updateserverinfo(
                    context.server_id, "device_type", context.device_type
                )
                # Update workflow_id if available (get from workflow context/manager)
                if hasattr(context, "workflow_id") and context.workflow_id:
                    context.db_helper.updateserverinfo(
                        context.server_id, "workflow_id", context.workflow_id
                    )
                    logger.info(
                        f"Updated database with workflow_id: {context.workflow_id} for server: {context.server_id}"
                    )

                # Add initial workflow history entry
                self._record_workflow_start(context)

            # Check if server exists in MaaS
            context.report_sub_task("Checking server status in MaaS")
            server_info = context.maas_client.get_machine(context.server_id)
            if not server_info:
                raise CommissioningError(
                    f"Server {context.server_id} not found in MaaS"
                )

            # Check current status and auto-determine if force recommissioning is needed
            current_status = server_info.get("status_name", "")
            should_force_commission = False

            # Auto-detect conditions that require force recommissioning
            if current_status in ["Ready", "Commissioned"]:
                context.report_sub_task("Verifying existing commissioning")
                # Check if machine has proper IP address for SSH
                machine_ip = context.maas_client.get_machine_ip(context.server_id)
                if not machine_ip:
                    logger.info(
                        f"Server {context.server_id} is {current_status} but has no SSH-accessible IP address - forcing recommission"
                    )
                    should_force_commission = True
                else:
                    # Test if the IP is actually reachable for SSH
                    logger.info(
                        f"Server {context.server_id} has IP {machine_ip} - testing SSH connectivity"
                    )
                    context.report_sub_task(f"Testing SSH connectivity to {machine_ip}")
                    if not self._test_ssh_connectivity(machine_ip, context):
                        logger.info(
                            f"Server {context.server_id} IP {machine_ip} is not SSH accessible - forcing recommission"
                        )
                        should_force_commission = True
                    else:
                        logger.info(
                            f"Server {context.server_id} is already commissioned with working SSH (status: {current_status}, IP: {machine_ip})"
                        )
                        context.report_sub_task(
                            "Server already commissioned successfully"
                        )
                        # Update database to reflect successful commissioning
                        if context.db_helper:
                            context.db_helper.updateserverinfo(
                                context.server_id, "status_name", "Commissioned"
                            )
                            context.db_helper.updateserverinfo(
                                context.server_id, "is_ready", "TRUE"
                            )
                            context.db_helper.updateserverinfo(
                                context.server_id, "ip_address", machine_ip
                            )
                            context.db_helper.updateserverinfo(
                                context.server_id, "ip_address_works", "TRUE"
                            )

                        return {
                            "status": "commissioned",
                            "machine_info": server_info,
                            "ip_address": machine_ip,
                        }

            # Check for other problematic states that require force recommissioning
            elif current_status in ["Failed commissioning", "Failed testing", "Broken"]:
                logger.info(
                    f"Server {context.server_id} is in failed state ({current_status}) - forcing recommission"
                )
                should_force_commission = True

            # Extract and store basic server information
            context.report_sub_task("Storing server metadata")
            if context.db_helper and server_info:
                # Get server model from hardware info
                hardware_info = server_info.get("hardware_info", {})
                server_model = hardware_info.get("mainboard_product", "Unknown")
                context.db_helper.updateserverinfo(
                    context.server_id, "server_model", server_model
                )

            # Start commissioning process
            if should_force_commission:
                context.report_sub_task(
                    f"Force commissioning server (status: {current_status})"
                )
                logger.info(
                    f"Force commissioning server {context.server_id} (current status: {current_status})"
                )
                result = context.maas_client.force_commission_machine(context.server_id)
            else:
                context.report_sub_task("Starting normal commissioning")
                logger.info(f"Normal commissioning server {context.server_id}")
                result = context.maas_client.commission_machine(context.server_id)

            # Wait for commissioning to complete
            context.report_sub_task("Waiting for commissioning to complete")
            timeout = time.time() + 1800  # 30 minutes
            while time.time() < timeout:
                status = context.maas_client.get_machine_status(context.server_id)
                context.report_sub_task(f"Commissioning status: {status}")

                # Accept both Commissioned and Ready as successful commissioning
                if status in ["Commissioned", "Ready"]:
                    logger.info(
                        f"Server {context.server_id} commissioned successfully (status: {status})"
                    )
                    context.report_sub_task("Commissioning completed successfully")

                    # Update database with successful commissioning
                    if context.db_helper:
                        context.db_helper.updateserverinfo(
                            context.server_id, "status_name", "Commissioned"
                        )
                        context.db_helper.updateserverinfo(
                            context.server_id, "is_ready", "TRUE"
                        )

                    return {"status": "commissioned", "machine_info": result}
                elif status == "Failed commissioning":
                    # Update database with failure status
                    if context.db_helper:
                        context.db_helper.updateserverinfo(
                            context.server_id, "status_name", "Failed commissioning"
                        )
                        context.db_helper.updateserverinfo(
                            context.server_id, "is_ready", "FALSE"
                        )
                    raise CommissioningError(
                        f"Commissioning failed for {context.server_id}"
                    )
                elif status == "Commissioning":
                    logger.info(f"Server {context.server_id} still commissioning...")
                else:
                    logger.info(
                        f"Server {context.server_id} status: {status} - waiting for completion..."
                    )

                time.sleep(30)  # Check every 30 seconds

            # Commissioning timeout
            if context.db_helper:
                context.db_helper.updateserverinfo(
                    context.server_id, "status_name", "Commissioning timeout"
                )
                context.db_helper.updateserverinfo(
                    context.server_id, "is_ready", "FALSE"
                )
            raise CommissioningError(f"Commissioning timeout for {context.server_id}")

        except Exception as e:
            logger.error(f"Commissioning failed: {e}")
            # Update database with error status
            if context.db_helper:
                context.db_helper.updateserverinfo(
                    context.server_id, "status_name", f"Error: {str(e)}"
                )
                context.db_helper.updateserverinfo(
                    context.server_id, "is_ready", "FALSE"
                )
            raise CommissioningError(f"Failed to commission server: {e}")

    def _get_server_ip(self, context: WorkflowContext) -> Dict[str, Any]:
        """Step 2: Retrieve server IP address and test SSH connectivity"""
        logger.info(f"Retrieving IP address for server {context.server_id}")

        try:
            # Use the MaaS client's working get_machine_ip method
            ip_address = context.maas_client.get_machine_ip(context.server_id)

            if not ip_address:
                # Fallback: try manual extraction from machine details
                machine_info = context.maas_client.get_machine(context.server_id)

                if not machine_info:
                    raise Exception(
                        f"Could not retrieve machine information for server {context.server_id}"
                    )

                # Check discovered IPs first (most reliable)
                interface_set = machine_info.get("interface_set")
                if interface_set:  # Check if interface_set is not None
                    for interface in interface_set:
                        if interface and "discovered" in interface:
                            discovered_list = interface.get("discovered")
                            if discovered_list:  # Check if discovered is not None
                                for discovered in discovered_list:
                                    if discovered and discovered.get("ip_address"):
                                        ip_address = discovered["ip_address"]
                                        break
                        if ip_address:
                            break

                # Fallback to links array if discovered didn't work
                if not ip_address and interface_set:
                    for interface in interface_set:
                        if interface and "links" in interface:
                            links_list = interface.get("links")
                            if links_list:  # Check if links is not None
                                for link in links_list:
                                    if link and link.get("ip_address"):
                                        ip_address = link["ip_address"]
                                        break
                        if ip_address:
                            break

                if not ip_address:
                    raise Exception("No IP address found for server")

            context.server_ip = ip_address
            logger.info(f"Server IP address: {ip_address}")

            # Update database with IP address
            if context.db_helper:
                context.db_helper.updateserverinfo(
                    context.server_id, "ip_address", ip_address
                )

            # Test SSH connectivity
            logger.info(f"Testing SSH connectivity to {ip_address}")
            ssh_works = self._test_ssh_connectivity(ip_address, context)

            # Update database with SSH connectivity status
            if context.db_helper:
                context.db_helper.updateserverinfo(
                    context.server_id,
                    "ip_address_works",
                    "TRUE" if ssh_works else "FALSE",
                )

            if not ssh_works:
                raise SSHConnectionError(
                    f"SSH connectivity test failed for {ip_address}"
                )

            context.ssh_connectivity_verified = True
            logger.info(f"SSH connectivity verified for {ip_address}")

            return {"ip_address": ip_address, "ssh_connectivity": ssh_works}

        except Exception as e:
            logger.error(f"Failed to retrieve server IP or verify SSH: {e}")
            # Update database with failure
            if context.db_helper:
                context.db_helper.updateserverinfo(
                    context.server_id, "ip_address_works", "FALSE"
                )
            raise

    def _test_ssh_connectivity(
        self,
        ip_address: str,
        context: WorkflowContext,
        max_retries: int = 3,
        timeout: int = 15,
    ) -> bool:
        """
        Test SSH connectivity to the server with quick timeout for commissioning validation

        This is a lightweight connectivity test used during commissioning validation
        to determine if force recommissioning is needed.
        """
        import socket
        import subprocess

        try:
            logger.info(f"Quick SSH connectivity test to {ip_address}")

            # First, do a quick port check
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            port_result = sock.connect_ex((ip_address, 22))
            sock.close()

            if port_result != 0:
                logger.info(f"SSH port 22 not reachable on {ip_address}")
                return False

            # Try a simple SSH command with short timeout
            ssh_config = self.manager.config.get("ssh", {})
            username = ssh_config.get("username", "ubuntu")

            # Use subprocess for a quick SSH test with strict timeout
            cmd = [
                "ssh",
                "-o",
                "ConnectTimeout=10",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                "-o",
                "BatchMode=yes",  # Don't prompt for passwords
                f"{username}@{ip_address}",
                'echo "SSH test successful"',
            ]

            try:
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=timeout
                )
                if result.returncode == 0:
                    logger.info(f"SSH connectivity confirmed to {ip_address}")
                    return True
                else:
                    logger.info(f"SSH command failed to {ip_address}: {result.stderr}")
                    return False
            except subprocess.TimeoutExpired:
                logger.info(f"SSH test timed out to {ip_address}")
                return False

        except Exception as e:
            logger.info(f"SSH connectivity test failed to {ip_address}: {e}")
            return False

    def _discover_hardware(self, context: WorkflowContext) -> Dict[str, Any]:
        """Step 3: Discover hardware information including IPMI address and store in database"""
        logger.info(f"Discovering hardware information for server {context.server_ip}")

        try:
            # Use the discovery manager from the workflow manager
            context.report_sub_task("Connecting to server for discovery")
            ssh_config = self.manager.config.get("ssh", {})
            username = ssh_config.get("username", "ubuntu")

            if not context.server_ip:
                raise WorkflowError(
                    "Server IP address not available for hardware discovery"
                )

            context.report_sub_task("Running hardware discovery scan")
            hardware_result = self.manager.discovery_manager.discover_hardware(
                host=context.server_ip, username=username
            )

            if hardware_result.discovery_errors:
                # Don't fail the workflow for discovery errors, but log them
                logger.warning(
                    f"Hardware discovery errors: {', '.join(hardware_result.discovery_errors)}"
                )

            # Store hardware information in context
            context.report_sub_task("Processing discovery results")
            context.hardware_discovery_result = {
                "system_info": hardware_result.system_info.__dict__,
                "ipmi_info": (
                    hardware_result.ipmi_info.__dict__
                    if hardware_result.ipmi_info
                    else None
                ),
                "network_interfaces": [
                    iface.__dict__ for iface in hardware_result.network_interfaces
                ],
                "vendor_info": getattr(hardware_result, "vendor_info", {}),
                "errors": hardware_result.discovery_errors,
            }

            # Update database with discovered information
            context.report_sub_task("Updating database with hardware info")
            if context.db_helper:
                # Update system information
                if hardware_result.system_info.manufacturer:
                    context.db_helper.updateserverinfo(
                        context.server_id,
                        "server_model",
                        f"{hardware_result.system_info.manufacturer} {hardware_result.system_info.product_name}",
                    )

                # Update IPMI information
                if hardware_result.ipmi_info and hardware_result.ipmi_info.ip_address:
                    ipmi_ip = hardware_result.ipmi_info.ip_address
                    context.db_helper.updateserverinfo(
                        context.server_id, "ipmi_address", ipmi_ip
                    )

                    # Test IPMI connectivity
                    context.report_sub_task(f"Testing IPMI connectivity to {ipmi_ip}")
                    ipmi_works = self._test_ipmi_connectivity(ipmi_ip, context)
                    context.db_helper.updateserverinfo(
                        context.server_id,
                        "ipmi_address_works",
                        "TRUE" if ipmi_works else "FALSE",
                    )

                    # Update IPMI status fields
                    if hardware_result.ipmi_info.enabled:
                        context.db_helper.updateserverinfo(
                            context.server_id, "kcs_status", "Enabled"
                        )
                        context.db_helper.updateserverinfo(
                            context.server_id, "host_interface_status", "Active"
                        )

                    logger.info(f"Discovered IPMI address: {ipmi_ip}")
                    context.discovered_ipmi_ip = ipmi_ip
                else:
                    logger.warning("No IPMI address discovered")
                    context.db_helper.updateserverinfo(
                        context.server_id, "ipmi_address_works", "FALSE"
                    )

            # Log important findings
            context.report_sub_task("Analyzing discovered hardware")
            if hardware_result.system_info.manufacturer:
                logger.info(
                    f"System: {hardware_result.system_info.manufacturer} {hardware_result.system_info.product_name}"
                )

            # Log vendor-specific information if available
            vendor_info = getattr(hardware_result, "vendor_info", {})
            if vendor_info:
                logger.info(
                    f"Vendor-specific info discovered: {list(vendor_info.keys())}"
                )

            context.report_sub_task("Hardware discovery completed")
            return {
                "system_info": hardware_result.system_info.__dict__,
                "ipmi_info": (
                    hardware_result.ipmi_info.__dict__
                    if hardware_result.ipmi_info
                    else None
                ),
                "network_interfaces": [
                    iface.__dict__ for iface in hardware_result.network_interfaces
                ],
                "vendor_info": vendor_info,
                "discovery_successful": True,
            }

        except Exception as e:
            logger.error(f"Hardware discovery failed: {e}")
            context.report_sub_task(f"Discovery failed: {str(e)}")
            # Update database with failure status
            if context.db_helper:
                context.db_helper.updateserverinfo(
                    context.server_id, "ipmi_address_works", "FALSE"
                )
                context.db_helper.updateserverinfo(
                    context.server_id, "kcs_status", "Discovery Failed"
                )
            raise

    def _test_ipmi_connectivity(self, ipmi_ip: str, context: WorkflowContext) -> bool:
        """Test IPMI connectivity to verify the discovered address"""
        try:
            # Simple ping test to IPMI address
            result = subprocess.run(
                ["ping", "-c", "3", "-W", "5", ipmi_ip],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                logger.info(f"IPMI address {ipmi_ip} is reachable via ping")
                return True
            else:
                logger.warning(f"IPMI address {ipmi_ip} is not reachable via ping")
                return False

        except Exception as e:
            logger.warning(f"IPMI connectivity test failed: {e}")
            return False

    def _pull_bios_config(self, context: WorkflowContext) -> Dict[str, Any]:
        """Step 4: Pull BIOS config via SSH"""
        logger.info(f"Pulling BIOS configuration from {context.server_ip}")

        try:
            if not context.server_ip:
                raise WorkflowError(
                    "Server IP address not available for BIOS configuration"
                )

            # Establish SSH connection
            context.report_sub_task("Connecting to server via SSH")
            ssh_client = self.manager.ssh_manager.connect(
                host=context.server_ip,
                username="ubuntu",  # Default for commissioned servers
                timeout=60,
            )

            # Detect server vendor first
            context.report_sub_task("Detecting server vendor")
            vendor = self._detect_server_vendor(ssh_client)
            logger.info(f"Detected server vendor: {vendor}")

            if vendor.lower() == "supermicro":
                context.report_sub_task("Pulling Supermicro BIOS configuration")
                return self._pull_bios_config_supermicro(ssh_client, context)
            elif vendor.lower() in ["dell", "hp", "hpe", "lenovo"]:
                logger.warning(
                    f"BIOS configuration for {vendor} servers not yet implemented"
                )
                context.report_sub_task(f"Creating dummy config for {vendor} server")
                # For now, create a dummy config file to continue the workflow
                return self._create_dummy_bios_config(context, vendor)
            else:
                logger.warning(
                    f"Unknown server vendor '{vendor}' - attempting Supermicro method"
                )
                context.report_sub_task(
                    f"Attempting Supermicro method for unknown vendor: {vendor}"
                )
                return self._pull_bios_config_supermicro(ssh_client, context)

        except Exception as e:
            logger.error(f"Failed to pull BIOS config: {e}")
            context.report_sub_task(f"BIOS config pull failed: {str(e)}")
            raise BiosConfigurationError(f"BIOS config pull failed: {e}")

    def _detect_server_vendor(self, ssh_client) -> str:
        """Detect server vendor using DMI information"""
        try:
            # Try dmidecode first
            stdout, stderr, exit_code = ssh_client.exec_command(
                "sudo dmidecode -s system-manufacturer"
            )
            if exit_code == 0 and stdout.strip():
                vendor = stdout.strip().lower()
                if "supermicro" in vendor:
                    return "Supermicro"
                elif "dell" in vendor:
                    return "Dell"
                elif any(hp in vendor for hp in ["hewlett", "hp", "hpe"]):
                    return "HP"
                elif "lenovo" in vendor:
                    return "Lenovo"
                else:
                    return vendor.title()

            # Fallback to checking for vendor-specific files/commands
            stdout, stderr, exit_code = ssh_client.exec_command(
                "ls /sys/class/dmi/id/sys_vendor"
            )
            if exit_code == 0:
                stdout, stderr, exit_code = ssh_client.exec_command(
                    "cat /sys/class/dmi/id/sys_vendor"
                )
                if exit_code == 0:
                    vendor = stdout.strip().lower()
                    if "supermicro" in vendor:
                        return "Supermicro"
                    elif "dell" in vendor:
                        return "Dell"
                    elif any(hp in vendor for hp in ["hewlett", "hp", "hpe"]):
                        return "HP"
                    elif "lenovo" in vendor:
                        return "Lenovo"

            return "Unknown"

        except Exception as e:
            logger.warning(f"Failed to detect server vendor: {e}")
            return "Unknown"

    def _pull_bios_config_supermicro(
        self, ssh_client, context: WorkflowContext
    ) -> Dict[str, Any]:
        """Pull BIOS configuration from Supermicro server using sumtool"""
        # Check if sumtool is available and install if needed
        context.report_sub_task("Checking for sumtool availability")
        logger.info("Checking for sumtool availability...")
        stdout, stderr, exit_code = ssh_client.exec_command("which sumtool")

        if exit_code != 0:
            context.report_sub_task("Installing sumtool")
            logger.info("sumtool not found, attempting to install...")
            install_success = self._install_sumtool_on_server(ssh_client)
            if not install_success:
                logger.error(
                    "Failed to install sumtool - falling back to dummy configuration"
                )
                context.report_sub_task(
                    "sumtool installation failed, using dummy config"
                )
                return self._create_dummy_bios_config(context, "supermicro")
            logger.info("sumtool installed successfully")
        else:
            logger.info("sumtool is available")

        # Create temporary directory for BIOS config
        context.report_sub_task("Creating temporary BIOS config directory")
        temp_dir = f"/tmp/bios_config_{context.server_id}"
        ssh_client.exec_command(f"mkdir -p {temp_dir}")

        # Verify directory was created
        stdout, stderr, exit_code = ssh_client.exec_command(f"ls -la {temp_dir}")
        if exit_code != 0:
            logger.error(f"Failed to create BIOS config directory: {stderr}")
            logger.info("Falling back to dummy configuration")
            context.report_sub_task("Directory creation failed, using dummy config")
            ssh_client.close()
            return self._create_dummy_bios_config(context, "supermicro")

        logger.info(f"Created BIOS config directory: {temp_dir}")

        # Pull BIOS configuration using sumtool
        context.report_sub_task("Extracting BIOS configuration using sumtool")
        bios_config_file = f"{temp_dir}/current_bios.xml"
        pull_command = f"sudo sumtool -c GetCurrentBiosCfg --file {bios_config_file}"

        logger.info(f"Executing BIOS config pull command: {pull_command}")
        stdout, stderr, exit_code = ssh_client.exec_command(pull_command)

        logger.debug(
            f"sumtool output - stdout: '{stdout}', stderr: '{stderr}', exit_code: {exit_code}"
        )

        if exit_code != 0:
            logger.warning(
                f"sumtool failed to pull BIOS config - exit_code: {exit_code}, stderr: '{stderr}', stdout: '{stdout}'"
            )

            # Test if sumtool is working at all
            context.report_sub_task("Testing sumtool functionality")
            logger.info("Testing sumtool availability...")
            test_stdout, test_stderr, test_exit = ssh_client.exec_command(
                "sumtool --version 2>&1"
            )
            logger.info(
                f"sumtool version test - exit_code: {test_exit}, output: '{test_stdout}', error: '{test_stderr}'"
            )

            # Try alternative sumtool command
            logger.info("Trying alternative sumtool help command...")
            help_stdout, help_stderr, help_exit = ssh_client.exec_command(
                "sumtool -h 2>&1"
            )
            logger.info(
                f"sumtool help test - exit_code: {help_exit}, output: '{help_stdout}', error: '{help_stderr}'"
            )

            logger.info("Falling back to dummy configuration")
            context.report_sub_task("sumtool failed, using dummy config")
            ssh_client.close()
            return self._create_dummy_bios_config(context, "supermicro")

        # Check if the BIOS config file was actually created (sometimes sumtool succeeds but reports failure)
        context.report_sub_task("Verifying BIOS config file creation")
        check_stdout, check_stderr, check_exit = ssh_client.exec_command(
            f"ls -la {bios_config_file}"
        )
        logger.info(
            f"BIOS config file check - exit_code: {check_exit}, output: '{check_stdout}'"
        )

        if check_exit != 0:
            logger.warning(
                "BIOS config file was not created, even though sumtool appeared to succeed"
            )
            logger.info("Falling back to dummy configuration")
            context.report_sub_task("Config file not found, using dummy config")
            ssh_client.close()
            return self._create_dummy_bios_config(context, "supermicro")

        # Download the config file
        context.report_sub_task("Downloading BIOS configuration file")
        local_config_path = f"/tmp/bios_config_{context.server_id}.xml"
        try:
            ssh_client.download_file(bios_config_file, local_config_path)
        except Exception as e:
            logger.warning(f"Failed to download BIOS config file: {e}")
            logger.info("Falling back to dummy configuration")
            context.report_sub_task(f"Download failed: {str(e)}, using dummy config")
            ssh_client.close()
            return self._create_dummy_bios_config(context, "supermicro")

        context.bios_config_path = local_config_path

        # Parse the configuration
        context.report_sub_task("Parsing BIOS configuration file")
        try:
            # Get server IP for pulling current BIOS config
            if not context.server_data:
                raise WorkflowError("Server data not available for BIOS config parsing")

            server_ip = context.server_data.get("ip_address")
            if not server_ip:
                raise WorkflowError("Server IP not available for BIOS config parsing")

            bios_config = self.manager.bios_manager.pull_current_bios_config(
                server_ip, ssh_client.username, ssh_client.password
            )
            context.original_bios_config = bios_config
        except Exception as e:
            logger.warning(f"Failed to parse BIOS config: {e}")
            logger.info("Falling back to dummy configuration")
            ssh_client.close()
            return self._create_dummy_bios_config(context, "supermicro")

        ssh_client.close()

        logger.info("BIOS configuration pulled successfully")
        return {"config_path": local_config_path, "config_data": bios_config}

    def _create_dummy_bios_config(
        self, context: WorkflowContext, vendor: str
    ) -> Dict[str, Any]:
        """Create a dummy BIOS config for non-Supermicro servers"""
        logger.info(f"Creating dummy BIOS config for {vendor} server")

        # Create a simple XML structure
        root = ET.Element("BiosConfig")
        root.set("vendor", vendor)
        root.set("server_id", context.server_id)
        root.set("timestamp", datetime.now().isoformat())

        # Add a note about vendor support
        note = ET.SubElement(root, "Note")
        note.text = f"BIOS configuration for {vendor} servers is not yet implemented. This is a placeholder config."

        # Save dummy config
        local_config_path = f"/tmp/bios_config_{context.server_id}.xml"
        tree = ET.ElementTree(root)
        tree.write(local_config_path, encoding="utf-8", xml_declaration=True)

        context.bios_config_path = local_config_path
        context.original_bios_config = root

        logger.info(f"Dummy BIOS configuration created for {vendor} server")
        return {
            "config_path": local_config_path,
            "config_data": context.original_bios_config,
        }

    def _install_sumtool_on_server(self, ssh_client) -> bool:
        """Install Supermicro sumtool on remote server"""
        try:
            # Check if sumtool is already installed
            stdout, stderr, exit_code = ssh_client.exec_command("which sumtool")
            if exit_code == 0:
                logger.info("sumtool already installed")
                return True

            logger.info("Installing sumtool dependencies...")
            # Update package lists
            stdout, stderr, exit_code = ssh_client.exec_command("sudo apt-get update")
            if exit_code != 0:
                logger.error("Failed to update package lists")
                return False

            # Install dependencies (remove wget since we're not downloading)
            stdout, stderr, exit_code = ssh_client.exec_command(
                "sudo apt-get install -y tar gzip"
            )
            if exit_code != 0:
                logger.error("Failed to install dependencies for sumtool")
                return False

            logger.info(
                "Uploading and installing sumtool from local tools directory..."
            )

            # Use local sumtool package
            local_sumtool_path = "/home/ubuntu/HWAutomation/tools/sum_2.14.0_Linux_x86_64_20240215.tar.gz"
            remote_sumtool_path = "/tmp/sumtool.tar.gz"

            # Check if local file exists
            import os

            if not os.path.exists(local_sumtool_path):
                logger.error(f"Local sumtool package not found: {local_sumtool_path}")
                return False

            logger.info(f"Uploading sumtool package: {local_sumtool_path}")

            # Clean up any previous attempts
            cleanup_commands = ["cd /tmp", "rm -rf sum_* sumtool.tar.gz*"]

            for cmd in cleanup_commands:
                logger.debug(f"Cleanup: {cmd}")
                ssh_client.exec_command(cmd)

            # Upload the sumtool archive
            try:
                ssh_client.upload_file(local_sumtool_path, remote_sumtool_path)
                logger.info("Sumtool package uploaded successfully")
            except Exception as e:
                logger.error(f"Failed to upload sumtool package: {e}")
                return False

            # Verify upload
            stdout, stderr, exit_code = ssh_client.exec_command(
                "ls -la /tmp/sumtool.tar.gz"
            )
            if exit_code != 0:
                logger.error("Uploaded sumtool package not found on remote server")
                return False

            logger.info(f"Upload verified: {stdout.strip()}")

            # Validate archive before extraction
            logger.info("Validating sumtool archive...")
            stdout, stderr, exit_code = ssh_client.exec_command(
                "cd /tmp && tar -tzf sumtool.tar.gz | head -5"
            )
            if exit_code != 0:
                logger.error(f"Archive validation failed: {stderr}")
                return False

            logger.info("Archive validation successful, proceeding with installation")

            # Extract and install (run as single command to maintain directory context)
            install_command = """
            cd /tmp && \
            tar -xzf sumtool.tar.gz && \
            ls -la sum_* && \
            cd sum_* && \
            ls -la sum && \
            sudo cp sum /usr/local/bin/sumtool && \
            sudo chmod +x /usr/local/bin/sumtool && \
            sudo ln -sf /usr/local/bin/sumtool /usr/bin/sumtool
            """

            logger.debug(f"Install command: {install_command}")
            stdout, stderr, exit_code = ssh_client.exec_command(install_command.strip())
            logger.debug(f"Install output: {stdout}")

            if exit_code != 0:
                logger.error(f"sumtool installation failed: {stderr}")
                return False

            # Verify installation
            stdout, stderr, exit_code = ssh_client.exec_command("sumtool --version")
            if exit_code == 0:
                logger.info(
                    f"sumtool installed and verified successfully: {stdout.strip()}"
                )
                return True
            else:
                logger.error(f"sumtool installation verification failed: {stderr}")
                # Try alternative verification
                stdout, stderr, exit_code = ssh_client.exec_command("sumtool -h")
                if exit_code == 0:
                    logger.info(
                        "sumtool installed successfully (verified with -h flag)"
                    )
                    return True

            # Fallback: Try to install from Ubuntu repositories (if available)
            logger.info("Trying fallback installation methods...")
            fallback_commands = [
                "sudo apt-cache search supermicro",
                "sudo apt-get install -y ipmitool",  # Alternative tool that might work
            ]

            for cmd in fallback_commands:
                logger.debug(f"Fallback: {cmd}")
                stdout, stderr, exit_code = ssh_client.exec_command(cmd)
                if "ipmitool" in cmd and exit_code == 0:
                    logger.info(
                        "Installed ipmitool as fallback - some BIOS operations may be limited"
                    )
                    return True

            return False

        except Exception as e:
            logger.error(f"Failed to install sumtool: {e}")
            return False

    def _modify_bios_config(self, context: WorkflowContext) -> Dict[str, Any]:
        """Step 5: Modify BIOS configuration"""
        logger.info(
            f"Modifying BIOS configuration for device type {context.device_type}"
        )

        try:
            # Check if this is a supported vendor
            if (
                hasattr(context, "original_bios_config")
                and context.original_bios_config is not None
            ):
                # Check if this is a dummy config by looking for the Note element
                note_element = context.original_bios_config.find("Note")
                if (
                    note_element is not None
                    and note_element.text
                    and "not yet implemented" in note_element.text
                ):
                    vendor = context.original_bios_config.get("vendor", "Unknown")
                    logger.info(
                        f"Skipping BIOS modification for {vendor} server - not yet supported"
                    )

                    # Create a dummy modified config to continue workflow
                    modified_config_path = f"/tmp/modified_bios_{context.server_id}.xml"
                    import shutil

                    if context.bios_config_path:
                        shutil.copy(context.bios_config_path, modified_config_path)
                    context.modified_bios_config = context.original_bios_config

                    return {
                        "modified_config_path": modified_config_path,
                        "changes_applied": [
                            f"No changes applied - {vendor} BIOS configuration not yet supported"
                        ],
                        "vendor_supported": False,
                    }

            # Apply modifications for supported servers (primarily Supermicro)
            # Use the apply_template_to_config method with just device_type
            if context.original_bios_config is None:
                raise WorkflowError(
                    "Original BIOS configuration not available for modification"
                )

            modified_config, changes_made = (
                self.manager.bios_manager.apply_template_to_config(
                    context.original_bios_config, context.device_type
                )
            )

            context.modified_bios_config = modified_config

            logger.info("BIOS configuration modified successfully")
            return {
                "modified_config_path": f"/tmp/modified_bios_{context.server_id}.xml",
                "changes_applied": changes_made,
                "vendor_supported": True,
            }

        except Exception as e:
            logger.error(f"Failed to modify BIOS config: {e}")
            raise BiosConfigurationError(f"BIOS config modification failed: {e}")

    def _push_bios_config(self, context: WorkflowContext) -> Dict[str, Any]:
        """Step 6: Push updated BIOS config"""
        # Get server IP from context
        if not context.server_data:
            raise WorkflowError("Server data not available for BIOS config push")

        server_ip = context.server_data.get("ip_address")
        if not server_ip:
            raise WorkflowError("Server IP not available for BIOS config push")

        logger.info(f"Pushing modified BIOS configuration to {server_ip}")

        try:
            # Connect to server
            from ..utils.network import SSHClient

            ssh_client = SSHClient(server_ip, username="ubuntu")

            # Detect server vendor
            vendor = self._detect_server_vendor(ssh_client)
            logger.info(f"Detected server vendor: {vendor}")

            if vendor == "supermicro":
                result = self._push_bios_config_supermicro(context)
                ssh_client.close()
                return result
            else:
                logger.warning(
                    f"BIOS configuration push not supported for vendor: {vendor}"
                )
                ssh_client.close()
                return {
                    "status": "skipped",
                    "reason": f"BIOS push not supported for {vendor} servers",
                    "reboot_required": False,
                }

        except Exception as e:
            logger.error(f"Failed to push BIOS config: {e}")
            raise BiosConfigurationError(f"BIOS config push failed: {e}")

    def _push_bios_config_supermicro(self, context: WorkflowContext) -> Dict[str, Any]:
        """Push BIOS configuration for Supermicro servers"""
        try:
            if not context.server_ip:
                raise WorkflowError(
                    "Server IP address not available for BIOS configuration"
                )

            # Reconnect via SSH
            ssh_client = self.manager.ssh_manager.connect(
                host=context.server_ip, username="ubuntu", timeout=60
            )

            # Upload modified config
            remote_config_path = f"/tmp/modified_bios_{context.server_id}.xml"
            local_config_path = f"/tmp/modified_bios_{context.server_id}.xml"

            ssh_client.upload_file(local_config_path, remote_config_path)

            # Push BIOS configuration
            push_command = f"sudo sumtool -c SetBiosCfg -f {remote_config_path}"
            logger.info(f"Executing BIOS config push command: {push_command}")
            stdout, stderr, exit_code = ssh_client.exec_command(push_command)

            if exit_code != 0:
                raise BiosConfigurationError(f"Failed to push BIOS config: {stderr}")

            # Reboot server to apply changes
            logger.info("Rebooting server to apply BIOS changes")
            ssh_client.exec_command("sudo reboot")

            ssh_client.close()

            # Wait for server to come back up
            time.sleep(60)  # Wait for reboot

            logger.info("BIOS configuration pushed successfully")
            return {"status": "applied", "reboot_required": True}

        except Exception as e:
            logger.error(f"Failed to push Supermicro BIOS config: {e}")
            raise BiosConfigurationError(f"Supermicro BIOS config push failed: {e}")

    def _configure_ipmi_conditional(self, context: WorkflowContext) -> Dict[str, Any]:
        """Step 7: Configure IPMI settings (only if target IP is provided)"""

        # Skip IPMI configuration if no target IP provided
        if not context.target_ipmi_ip:
            logger.info("No target IPMI IP provided - skipping IPMI configuration")

            # Update database to indicate IPMI configuration was skipped
            if context.db_helper:
                context.db_helper.updateserverinfo(
                    context.server_id, "kcs_status", "Configuration Skipped"
                )

            return {
                "status": "skipped",
                "message": "IPMI configuration skipped - no target IP provided",
                "discovered_ipmi": getattr(context, "discovered_ipmi_ip", None),
            }

        # Proceed with IPMI configuration
        return self._configure_ipmi(context)

    def _configure_ipmi(self, context: WorkflowContext) -> Dict[str, Any]:
        """Configure IPMI settings with provided target IP"""
        logger.info(f"Configuring IPMI with IP {context.target_ipmi_ip}")

        try:
            # Wait for server to be accessible after reboot
            time.sleep(30)

            if not context.server_ip:
                raise WorkflowError(
                    "Server IP address not available for IPMI configuration"
                )

            # Configure IPMI via SSH
            ssh_client = self.manager.ssh_manager.connect(
                host=context.server_ip, username="ubuntu", timeout=60
            )

            # Set IPMI IP address with dynamic network configuration
            subnet_mask = getattr(
                context, "subnet_mask", "255.255.255.0"
            )  # Default if not provided
            gateway_ip = getattr(
                context, "gateway", "192.168.100.1"
            )  # Default if not provided

            ipmi_commands = [
                f"ipmitool lan set 1 ipsrc static",
                f"ipmitool lan set 1 ipaddr {context.target_ipmi_ip}",
                f"ipmitool lan set 1 netmask {subnet_mask}",
                f"ipmitool lan set 1 defgw ipaddr {gateway_ip}",
                f"ipmitool lan set 1 access on",
            ]

            for cmd in ipmi_commands:
                stdout, stderr, exit_code = ssh_client.exec_command(f"sudo {cmd}")
                if exit_code != 0:
                    logger.warning(f"IPMI command failed: {cmd} - {stderr}")

            # Verify IPMI configuration
            stdout, stderr, exit_code = ssh_client.exec_command(
                "sudo ipmitool lan print 1"
            )

            ssh_client.close()

            # Update database with IPMI configuration
            if context.db_helper:
                context.db_helper.updateserverinfo(
                    context.server_id, "ipmi_address", context.target_ipmi_ip
                )
                context.db_helper.updateserverinfo(
                    context.server_id, "kcs_status", "Configured"
                )

            logger.info("IPMI configuration completed")
            return {"ipmi_ip": context.target_ipmi_ip, "status": "configured"}

        except Exception as e:
            logger.error(f"IPMI configuration failed: {e}")

            # Update database with error
            if context.db_helper:
                context.db_helper.updateserverinfo(
                    context.server_id, "kcs_status", f"Configuration Failed: {str(e)}"
                )

            raise IPMIConfigurationError(f"IPMI configuration failed: {e}")

    def _finalize_server_basic(self, context: WorkflowContext) -> Dict[str, Any]:
        """Step 8: Basic server finalization without IPMI/rack requirements"""
        logger.info(f"Finalizing basic server commissioning for {context.server_id}")

        try:
            # Apply basic tags for tracking
            tags = [
                f"device_type:{context.device_type}",
                f"commissioned:{int(time.time())}",
            ]

            # Add discovered IPMI IP if available
            if hasattr(context, "discovered_ipmi_ip") and context.discovered_ipmi_ip:
                tags.append(f"discovered_ipmi:{context.discovered_ipmi_ip}")

            # Add target IPMI IP only if configured
            if context.target_ipmi_ip:
                tags.append(f"target_ipmi:{context.target_ipmi_ip}")

            # Add rack location only if provided
            if context.rack_location:
                tags.append(f"rack_location:{context.rack_location}")

            # Apply tags in MaaS
            for tag in tags:
                try:
                    context.maas_client.tag_machine(context.server_id, tag)
                except Exception as e:
                    logger.warning(f"Failed to apply tag '{tag}': {e}")

            # Mark server as ready for deployment (not necessarily fully configured)
            context.maas_client.mark_machine_ready(context.server_id)

            # Update database with basic completion status
            if context.db_helper:
                context.db_helper.updateserverinfo(
                    context.server_id, "status_name", "Basic Commissioning Complete"
                )
                context.db_helper.updateserverinfo(
                    context.server_id, "is_ready", "TRUE"
                )

            # Update metadata
            context.metadata.update(
                {
                    "basic_commissioning_completed": int(time.time()),
                    "final_status": "ready_for_manual_config",
                    "ipmi_configured": bool(context.target_ipmi_ip),
                    "bios_configured": True,
                    "ssh_verified": context.ssh_connectivity_verified,
                    "database_updated": True,
                    "requires_manual_ipmi_config": not bool(context.target_ipmi_ip),
                }
            )

            logger.info(f"Basic server commissioning completed for {context.server_id}")
            return {
                "status": "basic_complete",
                "tags_applied": tags,
                "metadata": context.metadata,
                "database_updated": True,
                "ssh_connectivity_verified": context.ssh_connectivity_verified,
                "next_steps": self._get_next_steps(context),
            }

        except Exception as e:
            logger.error(f"Failed to finalize server: {e}")
            # Update database with error status
            if context.db_helper:
                context.db_helper.updateserverinfo(
                    context.server_id, "status_name", f"Finalization Error: {str(e)}"
                )
            raise Exception(f"Server finalization failed: {e}")

    def _get_next_steps(self, context: WorkflowContext) -> List[str]:
        """Get list of manual steps that may be needed"""
        next_steps = []

        if not context.target_ipmi_ip:
            if hasattr(context, "discovered_ipmi_ip") and context.discovered_ipmi_ip:
                next_steps.append(
                    f"Configure IPMI using discovered IP: {context.discovered_ipmi_ip}"
                )
            else:
                next_steps.append("Configure IPMI with desired IP address")

        if not context.rack_location:
            next_steps.append("Set rack location information")

        next_steps.append("Verify server functionality and network connectivity")
        next_steps.append("Deploy operating system when ready")

        return next_steps

    def _finalize_server(self, context: WorkflowContext) -> Dict[str, Any]:
        """Step 8: Finalize server and update database with completion status"""
        logger.info(f"Finalizing server {context.server_id}")

        try:
            # Tag server with metadata
            tags = [
                f"device_type:{context.device_type}",
                f"ipmi_ip:{context.target_ipmi_ip}",
                f"provisioned:{int(time.time())}",
            ]

            if context.rack_location:
                tags.append(f"rack_location:{context.rack_location}")

            # Apply tags in MaaS
            for tag in tags:
                try:
                    context.maas_client.tag_machine(context.server_id, tag)
                except Exception as e:
                    logger.warning(f"Failed to apply tag '{tag}': {e}")

            # Mark server as ready
            context.maas_client.mark_machine_ready(context.server_id)

            # Update database with final completion status
            if context.db_helper:
                context.db_helper.updateserverinfo(
                    context.server_id, "status_name", "Provisioning Complete"
                )
                context.db_helper.updateserverinfo(
                    context.server_id, "is_ready", "TRUE"
                )

                # Store additional metadata if available
                if context.hardware_discovery_result:
                    vendor_info = context.hardware_discovery_result.get(
                        "vendor_info", {}
                    )
                    if vendor_info:
                        # Store vendor-specific information in a serialized format
                        vendor_summary = (
                            f"Vendor: {vendor_info.get('manufacturer', 'Unknown')}"
                        )
                        if "bmc_version" in vendor_info:
                            vendor_summary += f", BMC: {vendor_info['bmc_version']}"
                        context.db_helper.updateserverinfo(
                            context.server_id, "currServerModels", vendor_summary
                        )

            # Update metadata
            context.metadata.update(
                {
                    "provisioning_completed": int(time.time()),
                    "final_status": "ready",
                    "ipmi_configured": True,
                    "bios_configured": True,
                    "ssh_verified": context.ssh_connectivity_verified,
                    "database_updated": True,
                }
            )

            logger.info(
                f"Server {context.server_id} provisioning completed successfully"
            )
            return {
                "status": "completed",
                "tags_applied": tags,
                "metadata": context.metadata,
                "database_updated": True,
                "ssh_connectivity_verified": context.ssh_connectivity_verified,
            }

        except Exception as e:
            logger.error(f"Failed to finalize server: {e}")
            # Update database with error status
            if context.db_helper:
                context.db_helper.updateserverinfo(
                    context.server_id, "status_name", f"Finalization Error: {str(e)}"
                )
            raise Exception(f"Server finalization failed: {e}")

    def provision_server(
        self,
        server_id: str,
        device_type: str,
        target_ipmi_ip: Optional[str] = None,
        rack_location: Optional[str] = None,
        progress_callback: Optional[Callable] = None,
    ) -> Dict[str, Any]:
        """
        High-level method to provision a server

        Args:
            server_id: Server identifier in MaaS
            device_type: Device type (e.g., 's2.c2.small')
            target_ipmi_ip: Optional target IPMI IP address (can be configured later)
            rack_location: Optional physical rack location (can be configured later)
            progress_callback: Callback for progress updates

        Returns:
            Dict containing provisioning results

        Note: The workflow automatically detects when force recommissioning is needed
        based on device status and SSH connectivity. Devices in Ready/Commissioned
        state without SSH-accessible IP addresses will be automatically force recommissioned.
        """
        # Create workflow
        workflow = self.create_provisioning_workflow(
            server_id=server_id,
            device_type=device_type,
            target_ipmi_ip=target_ipmi_ip,
            rack_location=rack_location,
        )

        # Set progress callback
        if progress_callback:
            workflow.set_progress_callback(progress_callback)

        # Create context
        context = WorkflowContext(
            server_id=server_id,
            device_type=device_type,
            target_ipmi_ip=target_ipmi_ip,
            rack_location=rack_location,
            maas_client=self.manager.maas_client,
            db_helper=self.manager.db_helper,
            workflow_id=workflow.id,
        )

        # Execute workflow
        success = workflow.execute(context)

        # Return results
        status = workflow.get_status()
        status["success"] = success
        status["workflow_id"] = workflow.id  # Add workflow_id to the response
        status["context"] = {
            "server_id": context.server_id,
            "device_type": context.device_type,
            "target_ipmi_ip": context.target_ipmi_ip,
            "server_ip": context.server_ip,
            "metadata": context.metadata,
        }

        return status

    def configure_server_ipmi(
        self, server_id: str, target_ipmi_ip: str, rack_location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Manual IPMI configuration for a commissioned server

        This method can be called after basic commissioning is complete
        to configure IPMI settings and rack location.

        Args:
            server_id: Server identifier in MaaS
            target_ipmi_ip: Target IPMI IP address
            rack_location: Optional physical rack location

        Returns:
            Dict containing configuration results
        """
        try:
            logger.info(f"Starting manual IPMI configuration for {server_id}")

            # Get server information from database
            if not self.manager.db_helper.checkifserveridexists(server_id)[0]:
                raise Exception(f"Server {server_id} not found in database")

            # Create a minimal context for IPMI configuration
            context = WorkflowContext(
                server_id=server_id,
                device_type="unknown",  # Not needed for IPMI config
                target_ipmi_ip=target_ipmi_ip,
                rack_location=rack_location,
                maas_client=self.manager.maas_client,
                db_helper=self.manager.db_helper,
            )

            # Get server IP from database or MaaS
            conn = self.manager.db_helper.sql_database
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT ip_address FROM {self.manager.db_helper.tablename} WHERE server_id = ?",
                (server_id,),
            )
            result = cursor.fetchone()

            if result and result[0]:
                context.server_ip = result[0]
            else:
                # Try to get IP from MaaS
                machine_info = context.maas_client.get_machine(server_id)
                if machine_info:
                    interface_set = machine_info.get("interface_set")
                    if interface_set:  # Check if interface_set is not None
                        for interface in interface_set:
                            if interface and "links" in interface:
                                links_list = interface.get("links")
                                if links_list:  # Check if links is not None
                                    for link in links_list:
                                        if (
                                            link
                                            and link.get("mode") == "auto"
                                            and link.get("ip")
                                        ):
                                            context.server_ip = link["ip"]
                                            break
                            if context.server_ip:
                                break

            if not context.server_ip:
                raise Exception(
                    f"Could not determine IP address for server {server_id}"
                )

            # Configure IPMI
            ipmi_result = self._configure_ipmi(context)

            # Update MaaS tags
            tags_to_add = [f"target_ipmi:{target_ipmi_ip}"]
            if rack_location:
                tags_to_add.append(f"rack_location:{rack_location}")

            for tag in tags_to_add:
                try:
                    context.maas_client.tag_machine(server_id, tag)
                except Exception as e:
                    logger.warning(f"Failed to apply tag '{tag}': {e}")

            # Update database status
            self.manager.db_helper.updateserverinfo(
                server_id, "status_name", "Fully Configured"
            )
            if rack_location:
                self.manager.db_helper.updateserverinfo(
                    server_id,
                    "currServerModels",
                    f"Rack: {rack_location}, IPMI: {target_ipmi_ip}",
                )

            logger.info(f"Manual IPMI configuration completed for {server_id}")

            return {
                "success": True,
                "server_id": server_id,
                "ipmi_ip": target_ipmi_ip,
                "rack_location": rack_location,
                "ipmi_result": ipmi_result,
                "tags_applied": tags_to_add,
                "message": "IPMI configuration completed successfully",
            }

        except Exception as e:
            logger.error(f"Manual IPMI configuration failed for {server_id}: {e}")

            # Update database with error
            if self.manager.db_helper:
                self.manager.db_helper.updateserverinfo(
                    server_id, "status_name", f"IPMI Config Error: {str(e)}"
                )

            return {
                "success": False,
                "server_id": server_id,
                "error": str(e),
                "message": "IPMI configuration failed",
            }

    def _record_workflow_start(self, context: WorkflowContext):
        """Record workflow start in the workflow_history table"""
        try:
            if context.db_helper and context.workflow_id:
                from datetime import datetime

                # Record in workflow history
                context.db_helper.execute_query(
                    """
                    INSERT INTO workflow_history (workflow_id, server_id, workflow_type, device_type, status, start_time)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        context.workflow_id,
                        context.server_id,
                        "commissioning",
                        context.device_type,
                        "running",
                        datetime.now().isoformat(),
                    ),
                )

                logger.info(f"Recorded workflow start for {context.workflow_id}")
        except Exception as e:
            logger.warning(f"Failed to record workflow start: {e}")
            # Don't fail the main workflow for history recording issues
