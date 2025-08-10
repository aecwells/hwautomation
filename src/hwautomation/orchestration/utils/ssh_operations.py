"""SSH operations utilities for orchestration workflows.

This module provides high-level SSH operation utilities that build on the
basic SSHClient to provide workflow-specific functionality.
"""

import os
import time
from typing import Any, Dict, List, Optional, Tuple

from hwautomation.logging import get_logger

from ...utils.network import SSHClient

logger = get_logger(__name__)


class SSHOperations:
    """High-level SSH operations for workflow orchestration."""

    def __init__(self, ssh_client: SSHClient):
        """Initialize with an SSH client."""
        self.ssh_client = ssh_client

    @classmethod
    def create_for_host(cls, hostname: str, username: str = "ubuntu", 
                       key_path: Optional[str] = None) -> "SSHOperations":
        """Create SSH operations for a specific host."""
        ssh_client = SSHClient(hostname=hostname, username=username, key_path=key_path)
        return cls(ssh_client)

    def test_connectivity(self, timeout: int = 30) -> Dict[str, Any]:
        """Test basic SSH connectivity."""
        try:
            result = self.ssh_client.execute_command("echo 'connectivity_test'", timeout=timeout)
            return {
                "success": result.get("success", False),
                "response_time": result.get("execution_time", 0),
                "error": result.get("stderr") if not result.get("success") else None
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def install_packages(self, packages: List[str], update_first: bool = True) -> Dict[str, Any]:
        """Install packages using the system package manager."""
        try:
            results = {}
            
            # Update package lists if requested
            if update_first:
                update_result = self.ssh_client.execute_command("sudo apt update")
                results["update"] = update_result.get("success", False)
                
                if not results["update"]:
                    return {
                        "success": False,
                        "error": "Failed to update package lists",
                        "details": results
                    }
            
            # Install packages
            if packages:
                package_list = " ".join(packages)
                install_cmd = f"sudo apt install -y {package_list}"
                install_result = self.ssh_client.execute_command(install_cmd)
                results["install"] = install_result.get("success", False)
                results["installed_packages"] = packages
                
                if not results["install"]:
                    return {
                        "success": False,
                        "error": f"Failed to install packages: {packages}",
                        "details": results
                    }
            
            return {
                "success": True,
                "packages_installed": packages,
                "details": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Package installation failed: {e}"
            }

    def check_service_status(self, service_name: str) -> Dict[str, Any]:
        """Check the status of a system service."""
        try:
            # Check if service exists
            exists_result = self.ssh_client.execute_command(f"systemctl list-unit-files | grep {service_name}")
            service_exists = exists_result.get("success", False)
            
            if not service_exists:
                return {
                    "exists": False,
                    "active": False,
                    "enabled": False
                }
            
            # Check if service is active
            active_result = self.ssh_client.execute_command(f"systemctl is-active {service_name}")
            is_active = active_result.get("success", False) and "active" in active_result.get("stdout", "")
            
            # Check if service is enabled
            enabled_result = self.ssh_client.execute_command(f"systemctl is-enabled {service_name}")
            is_enabled = enabled_result.get("success", False) and "enabled" in enabled_result.get("stdout", "")
            
            return {
                "exists": True,
                "active": is_active,
                "enabled": is_enabled,
                "status": "running" if is_active else "stopped"
            }
            
        except Exception as e:
            logger.error(f"Failed to check service status for {service_name}: {e}")
            return {
                "exists": False,
                "active": False,
                "enabled": False,
                "error": str(e)
            }

    def manage_service(self, service_name: str, action: str) -> Dict[str, Any]:
        """Manage a system service (start, stop, restart, enable, disable)."""
        try:
            valid_actions = ["start", "stop", "restart", "enable", "disable", "reload"]
            if action not in valid_actions:
                return {
                    "success": False,
                    "error": f"Invalid action: {action}. Valid actions: {valid_actions}"
                }
            
            cmd = f"sudo systemctl {action} {service_name}"
            result = self.ssh_client.execute_command(cmd)
            
            if result.get("success"):
                # Get updated status
                status = self.check_service_status(service_name)
                return {
                    "success": True,
                    "action": action,
                    "service": service_name,
                    "status": status
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to {action} service {service_name}",
                    "stderr": result.get("stderr", "")
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Service management failed: {e}"
            }

    def transfer_file(self, local_path: str, remote_path: str, 
                     create_dirs: bool = True) -> Dict[str, Any]:
        """Transfer a file to the remote host."""
        try:
            # Create remote directory if requested
            if create_dirs:
                remote_dir = os.path.dirname(remote_path)
                if remote_dir:
                    mkdir_result = self.ssh_client.execute_command(f"mkdir -p {remote_dir}")
                    if not mkdir_result.get("success"):
                        return {
                            "success": False,
                            "error": f"Failed to create remote directory: {remote_dir}"
                        }
            
            # Transfer file using scp
            transfer_result = self.ssh_client.transfer_file(local_path, remote_path)
            
            if transfer_result.get("success"):
                # Verify file was transferred
                verify_result = self.ssh_client.execute_command(f"test -f {remote_path} && echo 'exists'")
                file_exists = "exists" in verify_result.get("stdout", "")
                
                return {
                    "success": file_exists,
                    "local_path": local_path,
                    "remote_path": remote_path,
                    "verified": file_exists
                }
            else:
                return {
                    "success": False,
                    "error": "File transfer failed",
                    "details": transfer_result
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"File transfer failed: {e}"
            }

    def gather_system_info(self) -> Dict[str, Any]:
        """Gather comprehensive system information."""
        try:
            info = {}
            
            # Operating system information
            os_result = self.ssh_client.execute_command("cat /etc/os-release")
            if os_result.get("success"):
                info["os_release"] = os_result.get("stdout", "")
            
            # Kernel information
            kernel_result = self.ssh_client.execute_command("uname -a")
            if kernel_result.get("success"):
                info["kernel"] = kernel_result.get("stdout", "").strip()
            
            # CPU information
            cpu_result = self.ssh_client.execute_command("cat /proc/cpuinfo | grep -E '^(processor|model name|cpu MHz)' | head -20")
            if cpu_result.get("success"):
                info["cpu_info"] = cpu_result.get("stdout", "")
            
            # Memory information
            memory_result = self.ssh_client.execute_command("cat /proc/meminfo | head -5")
            if memory_result.get("success"):
                info["memory_info"] = memory_result.get("stdout", "")
            
            # Disk information
            disk_result = self.ssh_client.execute_command("df -h")
            if disk_result.get("success"):
                info["disk_info"] = disk_result.get("stdout", "")
            
            # Network interfaces
            network_result = self.ssh_client.execute_command("ip addr show")
            if network_result.get("success"):
                info["network_interfaces"] = network_result.get("stdout", "")
            
            # Uptime
            uptime_result = self.ssh_client.execute_command("uptime")
            if uptime_result.get("success"):
                info["uptime"] = uptime_result.get("stdout", "").strip()
            
            return {
                "success": True,
                "system_info": info
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to gather system information: {e}"
            }

    def execute_commands_batch(self, commands: List[str], 
                              stop_on_error: bool = True) -> Dict[str, Any]:
        """Execute a batch of commands."""
        try:
            results = []
            
            for i, command in enumerate(commands):
                logger.debug(f"Executing command {i+1}/{len(commands)}: {command}")
                
                result = self.ssh_client.execute_command(command)
                results.append({
                    "command": command,
                    "success": result.get("success", False),
                    "stdout": result.get("stdout", ""),
                    "stderr": result.get("stderr", ""),
                    "index": i
                })
                
                if not result.get("success") and stop_on_error:
                    return {
                        "success": False,
                        "error": f"Command failed at index {i}: {command}",
                        "failed_command": command,
                        "results": results
                    }
            
            # Check overall success
            all_successful = all(r["success"] for r in results)
            
            return {
                "success": all_successful,
                "commands_executed": len(commands),
                "results": results
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Batch command execution failed: {e}"
            }

    def wait_for_condition(self, command: str, expected_output: str, 
                          timeout: int = 300, check_interval: int = 10) -> Dict[str, Any]:
        """Wait for a command to produce expected output."""
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                result = self.ssh_client.execute_command(command)
                
                if result.get("success"):
                    output = result.get("stdout", "")
                    if expected_output in output:
                        return {
                            "success": True,
                            "condition_met": True,
                            "elapsed_time": time.time() - start_time,
                            "output": output
                        }
                
                time.sleep(check_interval)
            
            return {
                "success": False,
                "condition_met": False,
                "timeout": True,
                "elapsed_time": time.time() - start_time
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Condition waiting failed: {e}"
            }

    def check_hardware_tools(self) -> Dict[str, Any]:
        """Check for availability of hardware management tools."""
        try:
            tools_status = {}
            
            # Common hardware tools to check
            tools = {
                "ipmitool": "ipmitool",
                "dmidecode": "dmidecode", 
                "lshw": "lshw",
                "smartctl": "smartctl",
                "hdparm": "hdparm"
            }
            
            for tool_name, command in tools.items():
                check_result = self.ssh_client.execute_command(f"which {command}")
                tools_status[tool_name] = {
                    "available": check_result.get("success", False),
                    "path": check_result.get("stdout", "").strip() if check_result.get("success") else None
                }
                
                # Get version if available
                if tools_status[tool_name]["available"]:
                    version_result = self.ssh_client.execute_command(f"{command} --version 2>/dev/null || {command} -V 2>/dev/null || echo 'version unknown'")
                    if version_result.get("success"):
                        tools_status[tool_name]["version"] = version_result.get("stdout", "").strip()
            
            return {
                "success": True,
                "tools": tools_status
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Hardware tools check failed: {e}"
            }
