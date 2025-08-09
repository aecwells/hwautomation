"""Main IPMI manager coordinating all IPMI operations.

This module provides the primary interface for IPMI management,
consolidating basic operations with vendor-specific configuration.
"""

import subprocess
import time
from typing import Dict, List, Optional

from hwautomation.logging import get_logger
from hwautomation.utils.network import get_ipmi_ip_via_ssh
from .base import (
    BaseIPMIHandler,
    IPMICommand,
    IPMICommandError,
    IPMIConfigResult,
    IPMIConnectionError,
    IPMICredentials,
    IPMISettings,
    IPMISystemInfo,
    IPMIVendor,
    PowerState,
    PowerStatus,
    SensorReading,
)
from .operations.config import IPMIConfigurator
from .operations.power import PowerManager
from .operations.sensors import SensorManager
from .vendors.factory import VendorHandlerFactory

logger = get_logger(__name__)


class IpmiManager(BaseIPMIHandler):
    """Unified IPMI manager combining basic operations with vendor-specific configuration."""

    def __init__(
        self,
        username: str = "ADMIN",
        password: str = "",
        timeout: int = 30,
        config: Optional[Dict] = None,
    ):
        """Initialize IPMI manager.

        Args:
            username: Default IPMI username
            password: Default IPMI password
            timeout: Command timeout in seconds
            config: Additional configuration dictionary
        """
        # Create default credentials (IP will be set per operation)
        default_credentials = IPMICredentials(
            ip_address="", username=username, password=password
        )
        super().__init__(default_credentials, timeout)
        
        self.config = config or {}
        
        # Initialize operation managers
        self.power_manager = PowerManager(timeout=timeout)
        self.sensor_manager = SensorManager(timeout=timeout)
        self.configurator = IPMIConfigurator(config=self.config)
        self.vendor_factory = VendorHandlerFactory()

        logger.info(f"Initialized IpmiManager with username: {username}")

    def execute_command(
        self,
        command: str,
        credentials: IPMICredentials,
        additional_args: Optional[List[str]] = None,
    ) -> subprocess.CompletedProcess:
        """Execute an IPMI command.

        Args:
            command: IPMI command to execute
            credentials: IPMI connection credentials
            additional_args: Additional command arguments

        Returns:
            Completed process result
        """
        cmd_args = [
            "ipmitool",
            "-I", credentials.interface,
            "-H", credentials.ip_address,
            "-U", credentials.username,
            "-P", credentials.password,
        ]
        
        if additional_args:
            cmd_args.extend(additional_args)
            
        cmd_args.extend(command.split())

        try:
            result = subprocess.run(
                cmd_args,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            
            if result.returncode != 0:
                logger.error(f"IPMI command failed: {' '.join(cmd_args)}")
                logger.error(f"Error output: {result.stderr}")
                
            return result
            
        except subprocess.TimeoutExpired:
            logger.error(f"IPMI command timed out: {' '.join(cmd_args)}")
            raise IPMICommandError(f"Command timed out after {self.timeout}s", command)
        except Exception as e:
            logger.error(f"IPMI command execution failed: {e}")
            raise IPMICommandError(f"Command execution failed: {e}", command)

    # Legacy compatibility methods (from original ipmi.py)
    
    def get_ipmi_ips_from_servers(
        self, server_ips: List[str], ssh_username: str = "ubuntu"
    ) -> List[str]:
        """Get IPMI IPs from a list of server IPs via SSH.

        Args:
            server_ips: List of server IP addresses
            ssh_username: SSH username for connecting to servers

        Returns:
            List of discovered IPMI IP addresses
        """
        ipmi_ips = []

        for server_ip in server_ips:
            if server_ip and server_ip != "Unreachable":
                ipmi_ip = get_ipmi_ip_via_ssh(server_ip, ssh_username, self.timeout)
                if ipmi_ip:
                    ipmi_ips.append(ipmi_ip)
                    logger.info(f"Found IPMI IP {ipmi_ip} for server {server_ip}")
                else:
                    logger.warning(f"Could not get IPMI IP from {server_ip}")

        return ipmi_ips

    def set_ipmi_password(
        self,
        ipmi_ip: str,
        current_password: str,
        new_password: str,
        user_id: str = "2",
    ) -> bool:
        """Set IPMI password for a specific user.

        Args:
            ipmi_ip: IPMI IP address
            current_password: Current password
            new_password: New password to set
            user_id: User ID to modify (default: "2")

        Returns:
            True if password was set successfully, False otherwise
        """
        credentials = IPMICredentials(
            ip_address=ipmi_ip,
            username=self.credentials.username,
            password=current_password,
        )

        try:
            # Set password using ipmitool
            result = self.execute_command(
                f"user set password {user_id} {new_password}",
                credentials,
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully set IPMI password for {ipmi_ip}")
                return True
            else:
                logger.error(f"Failed to set IPMI password for {ipmi_ip}: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting IPMI password for {ipmi_ip}: {e}")
            return False

    def set_ipmi_passwords_bulk(
        self,
        ipmi_ips: List[str],
        current_password: str,
        new_password: str,
        user_id: str = "2",
    ) -> Dict[str, bool]:
        """Set IPMI passwords for multiple systems.

        Args:
            ipmi_ips: List of IPMI IP addresses
            current_password: Current password
            new_password: New password to set
            user_id: User ID to modify

        Returns:
            Dictionary mapping IP addresses to success status
        """
        results = {}
        
        for ipmi_ip in ipmi_ips:
            results[ipmi_ip] = self.set_ipmi_password(
                ipmi_ip, current_password, new_password, user_id
            )
            time.sleep(1)  # Brief delay between operations
            
        return results

    def get_power_status(self, ipmi_ip: str, password: str) -> Optional[str]:
        """Get power status using power manager.

        Args:
            ipmi_ip: IPMI IP address
            password: IPMI password

        Returns:
            Power status string or None if failed
        """
        credentials = IPMICredentials(
            ip_address=ipmi_ip,
            username=self.credentials.username,
            password=password,
        )
        
        try:
            status = self.power_manager.get_power_status(credentials)
            return status.state
        except Exception as e:
            logger.error(f"Failed to get power status for {ipmi_ip}: {e}")
            return None

    def set_power_state(self, ipmi_ip: str, password: str, action: str) -> bool:
        """Set power state using power manager.

        Args:
            ipmi_ip: IPMI IP address
            password: IPMI password
            action: Power action ('on', 'off', 'reset', 'cycle', 'soft')

        Returns:
            True if successful, False otherwise
        """
        credentials = IPMICredentials(
            ip_address=ipmi_ip,
            username=self.credentials.username,
            password=password,
        )
        
        try:
            # Convert string action to PowerState enum
            power_state = PowerState(action.lower())
            return self.power_manager.set_power_state(credentials, power_state)
        except ValueError:
            logger.error(f"Invalid power action: {action}")
            return False
        except Exception as e:
            logger.error(f"Failed to set power state for {ipmi_ip}: {e}")
            return False

    def get_sensor_data(self, ipmi_ip: str, password: str) -> Optional[Dict]:
        """Get sensor data using sensor manager.

        Args:
            ipmi_ip: IPMI IP address
            password: IPMI password

        Returns:
            Sensor data dictionary or None if failed
        """
        credentials = IPMICredentials(
            ip_address=ipmi_ip,
            username=self.credentials.username,
            password=password,
        )
        
        try:
            sensors = self.sensor_manager.get_sensor_data(credentials)
            
            # Convert to legacy format
            sensor_dict = {}
            for sensor in sensors:
                sensor_dict[sensor.name] = {
                    "value": sensor.value,
                    "unit": sensor.unit,
                    "status": sensor.status,
                }
                
            return sensor_dict
            
        except Exception as e:
            logger.error(f"Failed to get sensor data for {ipmi_ip}: {e}")
            return None

    # New unified configuration methods (from ipmi_automation.py)
    
    def detect_ipmi_vendor(self, ipmi_ip: str, password: str) -> IPMIVendor:
        """Detect IPMI vendor for the target system.

        Args:
            ipmi_ip: IPMI IP address
            password: IPMI password

        Returns:
            Detected vendor type
        """
        credentials = IPMICredentials(
            ip_address=ipmi_ip,
            username=self.credentials.username,
            password=password,
        )
        
        return self.configurator.detect_vendor(credentials)

    def configure_ipmi(
        self,
        ipmi_ip: str,
        password: str,
        admin_password: str,
        vendor: Optional[IPMIVendor] = None,
    ) -> IPMIConfigResult:
        """Configure IPMI settings for the target system.

        Args:
            ipmi_ip: IPMI IP address
            password: Current IPMI password
            admin_password: New admin password to set
            vendor: Target vendor (auto-detected if not provided)

        Returns:
            Configuration result
        """
        credentials = IPMICredentials(
            ip_address=ipmi_ip,
            username=self.credentials.username,
            password=password,
        )
        
        settings = IPMISettings(admin_password=admin_password)
        
        return self.configurator.configure_ipmi(credentials, settings, vendor)

    def validate_ipmi_configuration(
        self,
        ipmi_ip: str,
        password: str,
        settings: IPMISettings,
    ) -> bool:
        """Validate IPMI configuration.

        Args:
            ipmi_ip: IPMI IP address
            password: IPMI password
            settings: Settings to validate

        Returns:
            True if configuration is valid
        """
        credentials = IPMICredentials(
            ip_address=ipmi_ip,
            username=self.credentials.username,
            password=password,
        )
        
        return self.configurator.validate_configuration(credentials, settings)

    def get_system_info(self, ipmi_ip: str, password: str) -> Optional[IPMISystemInfo]:
        """Get system information for the target system.

        Args:
            ipmi_ip: IPMI IP address
            password: IPMI password

        Returns:
            System information or None if failed
        """
        credentials = IPMICredentials(
            ip_address=ipmi_ip,
            username=self.credentials.username,
            password=password,
        )
        
        try:
            return self.configurator.get_system_info(credentials)
        except Exception as e:
            logger.error(f"Failed to get system info for {ipmi_ip}: {e}")
            return None
