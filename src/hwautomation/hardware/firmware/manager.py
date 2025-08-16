"""Main firmware manager - coordinates all firmware operations.

This module provides the primary interface for firmware management,
orchestrating between type handlers, repositories, and operations.
"""

import asyncio
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...config.adapters import ConfigurationManager
from ...config.unified_loader import UnifiedConfigLoader
from ...logging import get_logger
from .base import FirmwareInfo, FirmwareType, FirmwareUpdateResult, UpdatePolicy
from .operations.checker import VersionChecker
from .repositories.local import FirmwareRepository
from .types.bios import BiosFirmwareHandler
from .types.bmc import BmcFirmwareHandler

logger = get_logger(__name__)


class FirmwareManager:
    """Main firmware manager coordinating all firmware operations."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize firmware manager.

        Args:
            config_path: Path to firmware configuration file
        """
        self.config_path = config_path or self._get_default_config_path()

        # Initialize unified configuration system
        self.config_manager = ConfigurationManager()
        self.unified_loader = self.config_manager.get_unified_loader()

        # Load repository configuration
        self.repository = self._load_firmware_repository()
        self.version_checker = VersionChecker()
        self.vendor_tools = self._initialize_vendor_tools()
        self.update_policy = UpdatePolicy.RECOMMENDED

        # Check which configuration system we're using
        config_source = "unified" if self.unified_loader else "legacy"
        logger.info(
            f"Initialized FirmwareManager with {config_source} config: {self.config_path}"
        )

    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        # Look for config in project root
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent.parent.parent
        config_path = project_root / "configs" / "firmware" / "repository.yaml"

        return str(config_path)

    def _load_firmware_repository(self) -> FirmwareRepository:
        """Load firmware repository configuration."""
        try:
            # Try unified configuration first
            if self.unified_loader:
                logger.info("Using unified configuration for firmware repository")
                # Get firmware config through adapter
                firmware_config = self.config_manager.get_firmware_config()

                if firmware_config and "firmware_repository" in firmware_config:
                    repo_config = firmware_config["firmware_repository"]
                    return FirmwareRepository(
                        base_path=repo_config.get("base_path", "/opt/firmware"),
                        vendors=repo_config.get("vendors", {}),
                        download_enabled=repo_config.get("download_enabled", True),
                        auto_verify=repo_config.get("auto_verify", True),
                        cache_duration=repo_config.get("cache_duration", 86400),
                    )

            # Fallback to legacy configuration
            logger.info("Using legacy configuration for firmware repository")
            return FirmwareRepository.from_config(self.config_path)

        except Exception as e:
            logger.warning(f"Failed to load firmware repository: {e}")
            # Return default repository
            return FirmwareRepository(base_path="/opt/firmware", vendors={})

    def _initialize_vendor_tools(self) -> Dict[str, Any]:
        """Initialize vendor-specific tools."""
        tools = {}

        # TODO: Initialize vendor tools based on configuration
        # For now, return empty dict

        return tools

    async def check_firmware_versions(
        self,
        device_type: str,
        target_ip: str,
        username: str = "admin",
        password: Optional[str] = None,
    ) -> Dict[str, FirmwareInfo]:
        """Check firmware versions for all components.

        Args:
            device_type: Target device type (e.g., 'a1.c5.large')
            target_ip: Target system IP address
            username: BMC username
            password: BMC password

        Returns:
            Dictionary of firmware information by type
        """
        if password is None:
            logger.error("Password is required for firmware version checking")
            return {}

        logger.info(f"Checking firmware versions for {device_type} at {target_ip}")

        try:
            # Get vendor information from device type
            vendor_info = self._get_vendor_info(device_type)

            # Check all firmware versions
            firmware_info = await self.version_checker.check_all_firmware_versions(
                device_type, target_ip, username, password, vendor_info, self.repository
            )

            logger.info(
                f"Found {len(firmware_info)} firmware components for {device_type}"
            )
            return firmware_info

        except Exception as e:
            logger.error(f"Failed to check firmware versions: {e}")
            return {}

    def _get_vendor_info(self, device_type: str) -> Dict[str, str]:
        """Extract vendor information from device type using unified configuration."""
        try:
            # Try unified configuration first
            if self.unified_loader:
                device_info = self.unified_loader.get_device_by_type(device_type)
                if device_info:
                    # Get vendor from the device info
                    vendor = device_info.vendor
                    motherboard = device_info.motherboard

                    logger.debug(
                        f"Found device {device_type}: vendor={vendor}, motherboard={motherboard}"
                    )

                    return {
                        "vendor": vendor.lower(),
                        "model": motherboard,
                        "device_type": device_type,
                    }
                else:
                    logger.warning(
                        f"Device type {device_type} not found in unified configuration"
                    )

            # Fallback to legacy device type mapping for backward compatibility
            logger.debug(f"Using legacy device mapping for {device_type}")
            return self._get_legacy_vendor_info(device_type)

        except Exception as e:
            logger.error(f"Error getting vendor info for {device_type}: {e}")
            return self._get_legacy_vendor_info(device_type)

    def _get_legacy_vendor_info(self, device_type: str) -> Dict[str, str]:
        """Legacy device type mapping for backward compatibility."""
        # Device type mapping for tests and operations
        if device_type == "a1.c5.large":
            return {"vendor": "hpe", "model": "Gen10", "device_type": device_type}
        elif "supermicro" in device_type.lower() or device_type.startswith("s"):
            return {"vendor": "supermicro", "model": "x11", "device_type": device_type}
        elif "dell" in device_type.lower() or device_type.startswith("d"):
            return {"vendor": "dell", "model": "poweredge", "device_type": device_type}
        elif "hpe" in device_type.lower() or device_type.startswith("h"):
            return {"vendor": "hpe", "model": "proliant", "device_type": device_type}
        else:
            return {"vendor": "unknown", "model": "unknown", "device_type": device_type}

    def _compare_versions(self, current_version: str, latest_version: str) -> bool:
        """Compare firmware versions to determine if update is needed.

        Args:
            current_version: Current firmware version
            latest_version: Latest available version

        Returns:
            True if update is needed, False otherwise
        """
        if current_version == "unknown" or latest_version == "unknown":
            return False

        # Simple version comparison - in production would use proper version parsing
        return current_version != latest_version

    def _determine_update_priority(
        self, firmware_type: FirmwareType, current_version: str, latest_version: str
    ):
        """Determine priority for firmware update.

        Args:
            firmware_type: Type of firmware
            current_version: Current version
            latest_version: Latest version

        Returns:
            Priority enum value
        """
        from .base import Priority

        # BMC updates are typically critical for security
        if firmware_type == FirmwareType.BMC:
            return Priority.CRITICAL

        # BIOS updates are high priority
        if firmware_type == FirmwareType.BIOS:
            return Priority.HIGH

        # Others are normal priority
        return Priority.NORMAL

    def _estimate_update_time(self, firmware_type: FirmwareType) -> int:
        """Estimate time required for firmware update.

        Args:
            firmware_type: Type of firmware

        Returns:
            Estimated time in seconds
        """
        # Default time estimates based on firmware type
        time_estimates = {
            FirmwareType.BIOS: 480,  # 8 minutes
            FirmwareType.BMC: 360,  # 6 minutes
            FirmwareType.UEFI: 300,  # 5 minutes
            FirmwareType.NIC: 120,  # 2 minutes
            FirmwareType.STORAGE: 180,  # 3 minutes
            FirmwareType.CPLD: 240,  # 4 minutes
        }

        return time_estimates.get(firmware_type, 300)  # Default 5 minutes

    async def _get_mock_firmware_versions(
        self, target_ip: str, vendor_info: Dict[str, str]
    ) -> Dict[FirmwareType, str]:
        """Get mock firmware versions for testing.

        Args:
            target_ip: Target IP address
            vendor_info: Vendor information

        Returns:
            Dictionary of firmware versions by type
        """
        vendor = vendor_info.get("vendor", "unknown")

        # Mock firmware versions based on vendor
        if vendor == "hpe":
            return {
                FirmwareType.BIOS: "U30_v2.50",
                FirmwareType.BMC: "2.44",
            }
        elif vendor == "supermicro":
            return {
                FirmwareType.BIOS: "3.4",
                FirmwareType.BMC: "1.73.14",
            }
        elif vendor == "dell":
            return {
                FirmwareType.BIOS: "2.10.0",
                FirmwareType.BMC: "4.40.00.00",
            }
        else:
            return {
                FirmwareType.BIOS: "1.0.0",
                FirmwareType.BMC: "1.0.0",
            }

    async def _validate_firmware_file(self, firmware_info: FirmwareInfo) -> bool:
        """Validate firmware file exists and is accessible.

        Args:
            firmware_info: Firmware information with file path

        Returns:
            True if file is valid, False otherwise
        """
        if not firmware_info.file_path:
            return False

        try:
            file_path = Path(firmware_info.file_path)
            return file_path.exists() and file_path.is_file()
        except Exception:
            return False

    async def _calculate_file_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of firmware file.

        Args:
            file_path: Path to firmware file

        Returns:
            SHA256 checksum as hex string
        """
        import hashlib

        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate checksum for {file_path}: {e}")
            return ""

    async def _update_bmc_firmware(
        self, target_ip: str, username: str, password: str, firmware_file: str
    ) -> bool:
        """Update BMC firmware (mock implementation for testing).

        Args:
            target_ip: Target IP address
            username: BMC username
            password: BMC password
            firmware_file: Path to firmware file

        Returns:
            True if successful, False otherwise
        """
        # Mock implementation for testing
        await asyncio.sleep(0.1)  # Simulate update time
        return True

    async def _update_bios_firmware(
        self, target_ip: str, username: str, password: str, firmware_file: str
    ) -> bool:
        """Update BIOS firmware (mock implementation for testing).

        Args:
            target_ip: Target IP address
            username: BMC username
            password: BMC password
            firmware_file: Path to firmware file

        Returns:
            True if successful, False otherwise
        """
        # Mock implementation for testing
        await asyncio.sleep(0.1)  # Simulate update time
        return True

    async def update_firmware_batch(
        self,
        device_type: str,
        target_ip: str,
        username: str,
        password: str,
        firmware_updates: List[FirmwareInfo],
        operation_id: Optional[str] = None,
    ) -> List[FirmwareUpdateResult]:
        """Update multiple firmware components in priority order.

        Args:
            firmware_updates: List of firmware to update
            target_ip: Target system IP address
            username: BMC username
            password: BMC password
            operation_id: Operation tracking ID

        Returns:
            List of update results
        """
        logger.info(f"Starting batch firmware update for {target_ip}")

        # Sort updates by priority (BMC first, then BIOS, then others)
        sorted_updates = self._sort_firmware_updates(firmware_updates)

        results = []
        for fw_info in sorted_updates:
            try:
                result = await self.update_firmware_component(
                    fw_info, target_ip, username, password, operation_id
                )
                results.append(result)

                # If critical update fails, stop the batch
                if not result.success and fw_info.priority.value in [
                    "critical",
                    "high",
                ]:
                    logger.error(f"Critical firmware update failed, stopping batch")
                    break

            except Exception as e:
                logger.error(f"Firmware update failed: {e}")
                results.append(
                    FirmwareUpdateResult(
                        firmware_type=fw_info.firmware_type,
                        success=False,
                        old_version=fw_info.current_version,
                        new_version=fw_info.current_version,
                        execution_time=fw_info.estimated_time or 1.0,
                        requires_reboot=fw_info.requires_reboot,
                        error_message=str(e),
                        operation_id=operation_id,
                    )
                )

        logger.info(
            f"Batch firmware update completed: {len(results)} updates processed"
        )
        return results

    def _sort_firmware_updates(self, updates: List[FirmwareInfo]) -> List[FirmwareInfo]:
        """Sort firmware updates by priority and type."""
        # Priority order: BMC, BIOS, others
        priority_order = {
            FirmwareType.BMC: 1,
            FirmwareType.BIOS: 2,
            FirmwareType.UEFI: 3,
            FirmwareType.NIC: 4,
            FirmwareType.STORAGE: 5,
            FirmwareType.CPLD: 6,
        }

        return sorted(
            updates,
            key=lambda x: (
                priority_order.get(x.firmware_type, 99),
                ["critical", "high", "normal", "low"].index(x.priority.value),
            ),
        )

    async def update_firmware_component(
        self,
        firmware_info: FirmwareInfo,
        target_ip: str,
        username: str,
        password: str,
        operation_id: Optional[str] = None,
    ) -> FirmwareUpdateResult:
        """Update a single firmware component.

        Args:
            firmware_info: Firmware information with update details
            target_ip: Target system IP address
            username: BMC username
            password: BMC password
            operation_id: Operation tracking ID

        Returns:
            Update result
        """
        # Check that we can handle this firmware type
        if firmware_info.firmware_type not in [FirmwareType.BIOS, FirmwareType.BMC]:
            return FirmwareUpdateResult(
                firmware_type=firmware_info.firmware_type,
                success=False,
                old_version=firmware_info.current_version,
                new_version=firmware_info.current_version,
                execution_time=firmware_info.estimated_time or 1.0,
                requires_reboot=firmware_info.requires_reboot,
                error_message="Unsupported firmware type",
                operation_id=operation_id,
            )

        logger.info(
            f"Updating {firmware_info.firmware_type.value} firmware on {target_ip}"
        )

        # Use provided file path or mock path for testing
        file_path = firmware_info.file_path or "/mock/firmware/file.bin"

        # Validate firmware file if it's a real path (not mock)
        if firmware_info.file_path and not await self._validate_firmware_file(
            firmware_info
        ):
            return FirmwareUpdateResult(
                firmware_type=firmware_info.firmware_type,
                success=False,
                old_version=firmware_info.current_version,
                new_version=firmware_info.current_version,
                execution_time=0.0,
                requires_reboot=firmware_info.requires_reboot,
                error_message="Firmware file validation failed",
                operation_id=operation_id,
            )

        # Track execution time
        start_time = asyncio.get_event_loop().time()
        success = False
        error_message = None

        try:
            # Call appropriate update method based on firmware type
            if firmware_info.firmware_type == FirmwareType.BMC:
                success = await self._update_bmc_firmware(
                    target_ip, username, password, file_path
                )
            elif firmware_info.firmware_type == FirmwareType.BIOS:
                success = await self._update_bios_firmware(
                    target_ip, username, password, file_path
                )
            else:
                error_message = (
                    f"Unsupported firmware type: {firmware_info.firmware_type}"
                )

        except Exception as e:
            error_message = str(e)

        end_time = asyncio.get_event_loop().time()
        execution_time = end_time - start_time

        return FirmwareUpdateResult(
            firmware_type=firmware_info.firmware_type,
            success=success,
            old_version=firmware_info.current_version,
            new_version=(
                firmware_info.latest_version
                if success
                else firmware_info.current_version
            ),
            execution_time=execution_time,
            requires_reboot=firmware_info.requires_reboot,
            error_message=error_message,
            operation_id=operation_id,
        )

    def get_supported_firmware_types(self) -> List[FirmwareType]:
        """Get list of supported firmware types."""
        return [FirmwareType.BIOS, FirmwareType.BMC]

    def get_repository_info(self) -> Dict[str, Any]:
        """Get firmware repository information."""
        return {
            "base_path": self.repository.base_path,
            "vendor_count": len(self.repository.vendors),
            "download_enabled": self.repository.download_enabled,
            "auto_verify": self.repository.auto_verify,
        }

    # Enhanced methods using unified configuration

    def get_supported_device_types(self) -> List[str]:
        """Get list of all supported device types from unified configuration."""
        if self.unified_loader:
            return self.unified_loader.list_all_device_types()
        else:
            # Fallback to legacy device types
            return ["a1.c5.large", "s2.c2.small", "s2.c2.medium", "s2.c2.large"]

    def get_devices_by_vendor(self, vendor: str) -> List[Dict[str, Any]]:
        """Get all devices for a specific vendor."""
        if self.unified_loader:
            device_types = self.unified_loader.get_device_types_by_vendor(vendor)
            devices = []
            for device_type in device_types:
                device_info = self.get_device_info(device_type)
                if device_info:
                    devices.append(device_info)
            return devices
        else:
            # Fallback logic for legacy configuration
            legacy_mapping = {
                "hpe": [{"device_type": "a1.c5.large", "motherboard": "Gen10"}],
                "supermicro": [
                    {"device_type": "s2.c2.small", "motherboard": "x11"},
                    {"device_type": "s2.c2.medium", "motherboard": "x11"},
                    {"device_type": "s2.c2.large", "motherboard": "x11"},
                ],
            }
            return legacy_mapping.get(vendor.lower(), [])

    def search_devices(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for devices matching a term."""
        if self.unified_loader:
            # Search through all devices
            all_device_types = self.unified_loader.list_all_device_types()
            matching_devices = []

            for device_type in all_device_types:
                device_info = self.get_device_info(device_type)
                if device_info:
                    # Check if search term matches any field
                    device_str = str(device_info).lower()
                    if search_term.lower() in device_str:
                        matching_devices.append(device_info)

            return matching_devices
        else:
            # Simple fallback search
            all_devices = []
            for vendor in ["hpe", "supermicro"]:
                all_devices.extend(self.get_devices_by_vendor(vendor))

            return [
                device
                for device in all_devices
                if search_term.lower() in str(device).lower()
            ]

    def get_vendor_statistics(self) -> Dict[str, Any]:
        """Get vendor statistics from unified configuration."""
        if self.unified_loader:
            stats = self.unified_loader.get_stats()

            # Build vendor breakdown
            vendor_breakdown = {}
            for vendor in self.unified_loader.list_vendors():
                vendor_info = self.unified_loader.get_vendor_info(vendor)
                if vendor_info:
                    device_types = self.unified_loader.get_device_types_by_vendor(
                        vendor
                    )
                    motherboards = self.unified_loader.list_motherboards(vendor)
                    vendor_breakdown[vendor] = {
                        "device_count": len(device_types),
                        "motherboards": motherboards,
                    }

            return {
                "total_vendors": stats.vendors,
                "total_devices": stats.device_types,
                "total_motherboards": stats.motherboards,
                "vendors": vendor_breakdown,
            }
        else:
            # Fallback statistics
            return {
                "total_vendors": 2,
                "total_devices": 4,
                "vendors": {
                    "hpe": {"device_count": 1, "motherboards": ["Gen10"]},
                    "supermicro": {"device_count": 3, "motherboards": ["x11"]},
                },
            }

    def validate_device_type(self, device_type: str) -> bool:
        """Validate if a device type is supported."""
        if self.unified_loader:
            return self.unified_loader.get_device_by_type(device_type) is not None
        else:
            # Legacy validation
            return device_type in self.get_supported_device_types()

    def get_device_info(self, device_type: str) -> Optional[Dict[str, Any]]:
        """Get device information for a specific device type."""
        if self.unified_loader:
            device_info = self.unified_loader.get_device_by_type(device_type)
            if device_info:
                # Extract CPU and hardware details from device_config
                device_config = device_info.device_config
                cpu_name = device_config.get("cpu_name", "Unknown CPU")
                cpu_cores = device_config.get("cpu_cores", 0)
                ram_gb = device_config.get("ram_gb", 0)

                return {
                    "device_type": device_type,
                    "vendor": device_info.vendor,
                    "motherboard": device_info.motherboard,
                    "cpu_name": cpu_name,
                    "cpu_cores": cpu_cores,
                    "ram_gb": ram_gb,
                }
        return None

    def get_configuration_status(self) -> Dict[str, Any]:
        """Get status of configuration system."""
        return {
            "unified_config_available": self.unified_loader is not None,
            "config_source": "unified" if self.unified_loader else "legacy",
            "adapters_status": (
                self.config_manager.get_status() if self.unified_loader else None
            ),
            "supported_device_count": len(self.get_supported_device_types()),
            "repository_path": self.repository.base_path,
        }
