"""
Redfish hardware management module for standardized BMC operations.

This module provides a standardized interface for hardware management operations
using the DMTF Redfish standard. It handles basic operations like power control,
system information retrieval, and simple BIOS configuration.
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import requests
from requests.auth import HTTPBasicAuth

logger = logging.getLogger(__name__)


@dataclass
class RedfishCapabilities:
    """Redfish capabilities discovered from the BMC"""

    supports_bios_config: bool = False
    supports_power_control: bool = False
    supports_system_info: bool = False
    supports_firmware_update: bool = False
    bios_settings_uri: Optional[str] = None
    systems_uri: Optional[str] = None
    chassis_uri: Optional[str] = None


@dataclass
class SystemInfo:
    """System information retrieved via Redfish"""

    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    bios_version: Optional[str] = None
    power_state: Optional[str] = None
    health_status: Optional[str] = None
    processor_count: Optional[int] = None
    memory_total_gb: Optional[float] = None


class RedfishManager:
    """
    Redfish hardware management interface.

    Provides standardized hardware operations using the DMTF Redfish API.
    Handles authentication, service discovery, and basic hardware operations.
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 443,
        use_https: bool = True,
        verify_ssl: bool = False,
    ):
        """
        Initialize Redfish manager.

        Args:
            host: BMC hostname or IP address
            username: BMC username
            password: BMC password
            port: BMC port (default 443 for HTTPS)
            use_https: Whether to use HTTPS (default True)
            verify_ssl: Whether to verify SSL certificates (default False)
        """
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.use_https = use_https
        self.verify_ssl = verify_ssl

        self.base_url = f"{'https' if use_https else 'http'}://{host}:{port}"
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(username, password)
        self.session.verify = verify_ssl

        # Disable SSL warnings if not verifying
        if not verify_ssl:
            requests.packages.urllib3.disable_warnings()

        self._service_root = None
        self._capabilities = None

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def close(self):
        """Close the session"""
        if self.session:
            self.session.close()

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Make HTTP request with error handling.

        Args:
            method: HTTP method (GET, POST, PATCH, etc.)
            url: Request URL
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            Exception: If request fails
        """
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Redfish request failed: {method} {url} - {e}")
            raise Exception(f"Redfish request failed: {e}")

    def _get_json(self, url: str) -> Dict[str, Any]:
        """
        Get JSON response from URL.

        Args:
            url: Request URL

        Returns:
            JSON response as dictionary
        """
        response = self._make_request("GET", url)
        return response.json()

    def discover_service_root(self) -> Dict[str, Any]:
        """
        Discover Redfish service root and capabilities.

        Returns:
            Service root information
        """
        if self._service_root is None:
            logger.info(f"Discovering Redfish service root at {self.host}")
            service_url = urljoin(self.base_url, "/redfish/v1/")
            self._service_root = self._get_json(service_url)

        return self._service_root

    def discover_capabilities(self) -> RedfishCapabilities:
        """
        Discover BMC capabilities.

        Returns:
            RedfishCapabilities object
        """
        if self._capabilities is not None:
            return self._capabilities

        try:
            service_root = self.discover_service_root()
            capabilities = RedfishCapabilities()

            # Check for Systems collection
            if "Systems" in service_root:
                capabilities.supports_system_info = True
                capabilities.supports_power_control = True
                capabilities.systems_uri = service_root["Systems"]["@odata.id"]

                # Check for BIOS settings
                systems = self._get_json(
                    urljoin(self.base_url, capabilities.systems_uri)
                )
                if "Members" in systems and len(systems["Members"]) > 0:
                    system_uri = systems["Members"][0]["@odata.id"]
                    system_data = self._get_json(urljoin(self.base_url, system_uri))

                    if "Bios" in system_data:
                        capabilities.supports_bios_config = True
                        capabilities.bios_settings_uri = system_data["Bios"][
                            "@odata.id"
                        ]

            # Check for Chassis collection
            if "Chassis" in service_root:
                capabilities.chassis_uri = service_root["Chassis"]["@odata.id"]

            self._capabilities = capabilities
            logger.info(f"Discovered Redfish capabilities: {capabilities}")
            return capabilities

        except Exception as e:
            logger.error(f"Failed to discover Redfish capabilities: {e}")
            return RedfishCapabilities()

    def get_system_info(self) -> Optional[SystemInfo]:
        """
        Get basic system information.

        Returns:
            SystemInfo object or None if failed
        """
        try:
            capabilities = self.discover_capabilities()
            if not capabilities.supports_system_info:
                logger.warning("System info not supported via Redfish")
                return None

            systems = self._get_json(urljoin(self.base_url, capabilities.systems_uri))
            if "Members" not in systems or len(systems["Members"]) == 0:
                logger.warning("No systems found in Redfish")
                return None

            # Get first system (typically there's only one)
            system_uri = systems["Members"][0]["@odata.id"]
            system_data = self._get_json(urljoin(self.base_url, system_uri))

            # Extract system information
            info = SystemInfo()
            info.manufacturer = system_data.get("Manufacturer")
            info.model = system_data.get("Model")
            info.serial_number = system_data.get("SerialNumber")
            info.power_state = system_data.get("PowerState")

            # Get BIOS version if available
            if "BiosVersion" in system_data:
                info.bios_version = system_data["BiosVersion"]

            # Get processor info
            if "ProcessorSummary" in system_data:
                proc_summary = system_data["ProcessorSummary"]
                info.processor_count = proc_summary.get("Count")

            # Get memory info
            if "MemorySummary" in system_data:
                mem_summary = system_data["MemorySummary"]
                total_size_mb = mem_summary.get("TotalSystemMemoryGiB")
                if total_size_mb:
                    info.memory_total_gb = float(total_size_mb)

            # Get health status
            if "Status" in system_data:
                status = system_data["Status"]
                info.health_status = status.get("Health", "Unknown")

            logger.info(f"Retrieved system info: {info.manufacturer} {info.model}")
            return info

        except Exception as e:
            logger.error(f"Failed to get system info via Redfish: {e}")
            return None

    def get_power_state(self) -> Optional[str]:
        """
        Get current power state.

        Returns:
            Power state string ('On', 'Off', etc.) or None if failed
        """
        try:
            system_info = self.get_system_info()
            if system_info:
                return system_info.power_state
            return None
        except Exception as e:
            logger.error(f"Failed to get power state via Redfish: {e}")
            return None

    def power_control(self, action: str) -> bool:
        """
        Control system power.

        Args:
            action: Power action ('On', 'ForceOff', 'GracefulShutdown', 'ForceRestart', 'GracefulRestart')

        Returns:
            True if successful, False otherwise
        """
        try:
            capabilities = self.discover_capabilities()
            if not capabilities.supports_power_control:
                logger.warning("Power control not supported via Redfish")
                return False

            systems = self._get_json(urljoin(self.base_url, capabilities.systems_uri))
            if "Members" not in systems or len(systems["Members"]) == 0:
                return False

            system_uri = systems["Members"][0]["@odata.id"]
            system_data = self._get_json(urljoin(self.base_url, system_uri))

            # Find Actions
            if "Actions" not in system_data:
                logger.error("No Actions found in system data")
                return False

            actions = system_data["Actions"]
            reset_action_key = "#ComputerSystem.Reset"

            if reset_action_key not in actions:
                logger.error("Reset action not available")
                return False

            reset_action = actions[reset_action_key]
            reset_uri = reset_action["target"]

            # Validate action is supported
            allowed_values = reset_action.get("ResetType@Redfish.AllowableValues", [])
            if action not in allowed_values:
                logger.error(
                    f"Action '{action}' not supported. Available: {allowed_values}"
                )
                return False

            # Send power control request
            reset_url = urljoin(self.base_url, reset_uri)
            payload = {"ResetType": action}

            logger.info(f"Sending power control action: {action}")
            response = self._make_request("POST", reset_url, json=payload)

            if response.status_code in [200, 202, 204]:
                logger.info(f"Power control action '{action}' successful")
                return True
            else:
                logger.error(
                    f"Power control failed with status: {response.status_code}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to control power via Redfish: {e}")
            return False

    def get_bios_settings(self) -> Optional[Dict[str, Any]]:
        """
        Get current BIOS settings.

        Returns:
            Dictionary of BIOS settings or None if failed
        """
        try:
            capabilities = self.discover_capabilities()
            if not capabilities.supports_bios_config:
                logger.warning("BIOS configuration not supported via Redfish")
                return None

            bios_url = urljoin(self.base_url, capabilities.bios_settings_uri)
            bios_data = self._get_json(bios_url)

            # BIOS settings are typically in 'Attributes'
            if "Attributes" in bios_data:
                settings = bios_data["Attributes"]
                logger.info(f"Retrieved {len(settings)} BIOS settings via Redfish")
                return settings
            else:
                logger.warning("No BIOS attributes found in response")
                return {}

        except Exception as e:
            logger.error(f"Failed to get BIOS settings via Redfish: {e}")
            return None

    def set_bios_setting(self, attribute: str, value: Any) -> bool:
        """
        Set a single BIOS setting.

        Args:
            attribute: BIOS attribute name
            value: New value for the attribute

        Returns:
            True if successful, False otherwise
        """
        return self.set_bios_settings({attribute: value})

    def set_bios_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Set multiple BIOS settings.

        Args:
            settings: Dictionary of attribute names and values

        Returns:
            True if successful, False otherwise
        """
        try:
            capabilities = self.discover_capabilities()
            if not capabilities.supports_bios_config:
                logger.warning("BIOS configuration not supported via Redfish")
                return False

            bios_url = urljoin(self.base_url, capabilities.bios_settings_uri)

            # PATCH the BIOS settings
            payload = {"Attributes": settings}

            logger.info(f"Setting BIOS attributes via Redfish: {list(settings.keys())}")
            response = self._make_request("PATCH", bios_url, json=payload)

            if response.status_code in [200, 202, 204]:
                logger.info("BIOS settings updated successfully")
                return True
            else:
                logger.error(
                    f"BIOS settings update failed with status: {response.status_code}"
                )
                return False

        except Exception as e:
            logger.error(f"Failed to set BIOS settings via Redfish: {e}")
            return False

    async def get_firmware_versions(
        self, target_ip: str, username: str, password: str
    ) -> Dict[str, str]:
        """
        Get firmware versions via Redfish API.

        Args:
            target_ip: Target BMC IP address
            username: BMC username
            password: BMC password

        Returns:
            Dictionary mapping firmware types to versions
        """
        try:
            # Temporarily create a new manager instance for the target
            temp_manager = RedfishManager(
                target_ip, username, password, port=self.port, use_ssl=self.use_ssl
            )

            firmware_versions = {}

            # Try to get system information first
            service_root = temp_manager.discover_service_root()
            systems_uri = service_root.get("Systems", {}).get("@odata.id")

            if not systems_uri:
                logger.warning(f"No Systems endpoint found for {target_ip}")
                return firmware_versions

            # Get systems collection
            systems_response = temp_manager._make_request("GET", systems_uri)
            if not systems_response or "Members" not in systems_response:
                logger.warning(f"No system members found for {target_ip}")
                return firmware_versions

            # Get first system
            system_uri = systems_response["Members"][0]["@odata.id"]
            system_info = temp_manager._make_request("GET", system_uri)

            if system_info:
                # Extract BIOS version
                bios_version = system_info.get("BiosVersion")
                if bios_version:
                    # Import here to avoid circular import
                    from .firmware_manager import FirmwareType

                    firmware_versions[FirmwareType.BIOS] = bios_version

                # Try to get BMC version from manager info
                managers_uri = service_root.get("Managers", {}).get("@odata.id")
                if managers_uri:
                    managers_response = temp_manager._make_request("GET", managers_uri)
                    if managers_response and "Members" in managers_response:
                        manager_uri = managers_response["Members"][0]["@odata.id"]
                        manager_info = temp_manager._make_request("GET", manager_uri)

                        if manager_info:
                            bmc_version = manager_info.get("FirmwareVersion")
                            if bmc_version:
                                firmware_versions[FirmwareType.BMC] = bmc_version

            logger.debug(
                f"Retrieved firmware versions via Redfish: {firmware_versions}"
            )
            return firmware_versions

        except Exception as e:
            logger.error(f"Failed to get firmware versions via Redfish: {e}")
            return {}

    async def update_firmware(
        self,
        target_ip: str,
        username: str,
        password: str,
        firmware_path: str,
        firmware_type,
        operation_id: Optional[str] = None,
    ) -> bool:
        """
        Update firmware via Redfish API (unified interface).

        Args:
            target_ip: Target server IP address
            username: BMC username
            password: BMC password
            firmware_path: Path to firmware file
            firmware_type: Type of firmware (FirmwareType enum)
            operation_id: Optional operation ID for tracking

        Returns:
            True if update was successful, False otherwise
        """
        logger.info(
            f"Starting Redfish firmware update for {firmware_type.value} on {target_ip}"
        )

        try:
            # Set up temporary manager for this operation
            original_host = self.host
            original_auth = self.auth

            self.host = target_ip
            self.auth = HTTPBasicAuth(username, password)

            # Check connection first
            if not await self.test_connection(target_ip, username, password):
                logger.error(f"Cannot establish Redfish connection to {target_ip}")
                return False

            # Call the actual update method
            result = await self.update_firmware_redfish(
                firmware_type.value, firmware_path, operation_id
            )

            # Restore original configuration
            self.host = original_host
            self.auth = original_auth

            return result

        except Exception as e:
            logger.error(f"Redfish firmware update failed: {e}")
            # Restore original configuration on error
            self.host = original_host if "original_host" in locals() else self.host
            self.auth = original_auth if "original_auth" in locals() else self.auth
            return False

    async def update_firmware_redfish(
        self, firmware_type: str, firmware_path: str, operation_id: Optional[str] = None
    ) -> bool:
        """
        Update firmware via Redfish API using SimpleUpdate or MultipartHTTP.

        Args:
            firmware_type: Type of firmware (BIOS, BMC, etc.)
            firmware_path: Path to firmware file
            operation_id: Optional operation ID for tracking

        Returns:
            True if update was successful, False otherwise
        """
        try:
            logger.info(f"Starting Redfish firmware update: {firmware_type}")

            # Discover update service
            service_root = self.discover_service_root()
            update_service_uri = service_root.get("UpdateService", {}).get("@odata.id")

            if not update_service_uri:
                logger.warning("UpdateService not available via Redfish")
                return False

            # Get update service info
            update_service = self._make_request("GET", update_service_uri)
            if not update_service:
                logger.error("Failed to get UpdateService information")
                return False

            # Check available update methods
            actions = update_service.get("Actions", {})
            simple_update_action = actions.get("#UpdateService.SimpleUpdate")

            # Method 1: Try SimpleUpdate (most common)
            if simple_update_action and firmware_path:
                logger.info("Attempting SimpleUpdate method")
                success = await self._perform_simple_update(
                    simple_update_action, firmware_path, firmware_type
                )
                if success:
                    return True

            # Method 2: Try MultipartHTTPPush (for direct file upload)
            multipart_uri = update_service.get("MultipartHttpPushUri")
            if multipart_uri and firmware_path:
                logger.info("Attempting MultipartHTTPPush method")
                success = await self._perform_multipart_update(
                    multipart_uri, firmware_path, firmware_type
                )
                if success:
                    return True

            # Method 3: Try HttpPushUri (for HTTP upload)
            http_push_uri = update_service.get("HttpPushUri")
            if http_push_uri and firmware_path:
                logger.info("Attempting HttpPushUri method")
                success = await self._perform_http_push_update(
                    http_push_uri, firmware_path, firmware_type
                )
                if success:
                    return True

            logger.warning(
                f"No suitable Redfish update method available for {firmware_type}"
            )
            return False

        except Exception as e:
            logger.error(f"Redfish firmware update exception: {e}")
            return False

    async def _perform_simple_update(
        self,
        simple_update_action: Dict[str, Any],
        firmware_path: str,
        firmware_type: str,
    ) -> bool:
        """Perform firmware update using SimpleUpdate action"""
        try:
            update_uri = simple_update_action.get("target")
            if not update_uri:
                logger.error("No update target URI found in SimpleUpdate action")
                return False

            # Check if we need to upload file first or provide URI
            # For now, simulate the update process since we'd need a proper firmware repository
            logger.info(f"Executing SimpleUpdate for {firmware_type}")

            # In production, this would:
            # 1. Upload firmware to a web server
            # 2. POST to update_uri with ImageURI pointing to uploaded file
            # 3. Monitor task status until completion

            payload = {
                "ImageURI": f"file://{firmware_path}",  # This would be HTTP URL in production
                "Targets": ["/redfish/v1/Systems/System.Embedded.1"],  # Dell example
                "TransferProtocol": "HTTP",
            }

            response = self._make_request("POST", update_uri, payload)

            if response:
                # Check for task or immediate success
                if response.get("@odata.type") == "#Task.v1_0_0.Task":
                    task_uri = response.get("@odata.id")
                    logger.info(f"Firmware update task created: {task_uri}")

                    # Monitor task status (simplified for demo)
                    return await self._monitor_update_task(task_uri, firmware_type)
                else:
                    logger.info(
                        f"Firmware update initiated successfully for {firmware_type}"
                    )
                    return True
            else:
                logger.error("SimpleUpdate request failed")
                return False

        except Exception as e:
            logger.error(f"SimpleUpdate failed: {e}")
            return False

    async def _perform_multipart_update(
        self, multipart_uri: str, firmware_path: str, firmware_type: str
    ) -> bool:
        """Perform firmware update using MultipartHTTPPush"""
        try:
            logger.info(f"Executing MultipartHTTPPush for {firmware_type}")

            # Check if firmware file exists
            import os

            if not os.path.exists(firmware_path):
                logger.error(f"Firmware file not found: {firmware_path}")
                return False

            # Prepare multipart upload
            with open(firmware_path, "rb") as firmware_file:
                files = {
                    "UpdateFile": (
                        os.path.basename(firmware_path),
                        firmware_file,
                        "application/octet-stream",
                    )
                }

                # Additional form data
                data = {
                    "UpdateParameters": json.dumps(
                        {
                            "Targets": ["/redfish/v1/Systems/System.Embedded.1"],
                            "@Redfish.OperationApplyTime": "OnReset",
                        }
                    )
                }

                # Make multipart request
                url = urljoin(f"https://{self.host}", multipart_uri)

                response = requests.post(
                    url,
                    files=files,
                    data=data,
                    auth=self.auth,
                    verify=False,
                    timeout=1800,  # 30 minute timeout for firmware upload
                )

                if response.status_code in [200, 202]:
                    logger.info(f"MultipartHTTPPush successful for {firmware_type}")

                    # Check for task
                    if response.status_code == 202:
                        task_location = response.headers.get("Location")
                        if task_location:
                            return await self._monitor_update_task(
                                task_location, firmware_type
                            )

                    return True
                else:
                    logger.error(
                        f"MultipartHTTPPush failed: {response.status_code} - {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"MultipartHTTPPush failed: {e}")
            return False

    async def _perform_http_push_update(
        self, http_push_uri: str, firmware_path: str, firmware_type: str
    ) -> bool:
        """Perform firmware update using HttpPushUri"""
        try:
            logger.info(f"Executing HttpPushUri update for {firmware_type}")

            # Check if firmware file exists
            import os

            if not os.path.exists(firmware_path):
                logger.error(f"Firmware file not found: {firmware_path}")
                return False

            # Upload firmware file
            with open(firmware_path, "rb") as firmware_file:
                url = urljoin(f"https://{self.host}", http_push_uri)

                headers = {"Content-Type": "application/octet-stream"}

                response = requests.post(
                    url,
                    data=firmware_file,
                    headers=headers,
                    auth=self.auth,
                    verify=False,
                    timeout=1800,  # 30 minute timeout
                )

                if response.status_code in [200, 202]:
                    logger.info(f"HttpPushUri update successful for {firmware_type}")

                    # Check for task
                    if response.status_code == 202:
                        task_location = response.headers.get("Location")
                        if task_location:
                            return await self._monitor_update_task(
                                task_location, firmware_type
                            )

                    return True
                else:
                    logger.error(
                        f"HttpPushUri update failed: {response.status_code} - {response.text}"
                    )
                    return False

        except Exception as e:
            logger.error(f"HttpPushUri update failed: {e}")
            return False

    async def _monitor_update_task(self, task_uri: str, firmware_type: str) -> bool:
        """Monitor firmware update task status"""
        try:
            logger.info(f"Monitoring firmware update task for {firmware_type}")

            max_wait_time = 1800  # 30 minutes
            check_interval = 30  # 30 seconds
            elapsed_time = 0

            while elapsed_time < max_wait_time:
                task_info = self._make_request("GET", task_uri)

                if not task_info:
                    logger.error("Failed to get task information")
                    return False

                task_state = task_info.get("TaskState")
                task_status = task_info.get("TaskStatus")

                logger.debug(f"Task state: {task_state}, status: {task_status}")

                if task_state == "Completed":
                    if task_status == "OK":
                        logger.info(
                            f"Firmware update completed successfully for {firmware_type}"
                        )
                        return True
                    else:
                        logger.error(
                            f"Firmware update completed with errors: {task_status}"
                        )
                        return False
                elif task_state in ["Exception", "Killed", "Cancelled"]:
                    logger.error(f"Firmware update failed with state: {task_state}")
                    return False
                elif task_state in ["New", "Starting", "Running"]:
                    # Task is still running
                    progress = task_info.get("PercentComplete", 0)
                    logger.info(f"Firmware update progress: {progress}%")
                else:
                    logger.warning(f"Unknown task state: {task_state}")

                # Wait before next check
                import asyncio

                await asyncio.sleep(check_interval)
                elapsed_time += check_interval

            logger.error(
                f"Firmware update task timed out after {max_wait_time} seconds"
            )
            return False

        except Exception as e:
            logger.error(f"Task monitoring failed: {e}")
            return False

    def test_connection(self) -> Tuple[bool, str]:
        """
        Test Redfish connection and authentication.

        Returns:
            Tuple of (success, message)
        """
        try:
            service_root = self.discover_service_root()
            service_version = service_root.get("RedfishVersion", "Unknown")

            # Try to get system info as a more comprehensive test
            system_info = self.get_system_info()
            if system_info:
                message = (
                    f"Redfish connection successful (v{service_version}). "
                    f"System: {system_info.manufacturer} {system_info.model}"
                )
            else:
                message = f"Redfish connection successful (v{service_version}) but limited system access"

            return True, message

        except Exception as e:
            return False, f"Redfish connection failed: {e}"


def create_redfish_manager(
    host: str, username: str, password: str, **kwargs
) -> RedfishManager:
    """
    Factory function to create RedfishManager instance.

    Args:
        host: BMC hostname or IP
        username: BMC username
        password: BMC password
        **kwargs: Additional arguments for RedfishManager

    Returns:
        RedfishManager instance
    """
    return RedfishManager(host, username, password, **kwargs)
