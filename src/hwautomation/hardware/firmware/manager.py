"""Main firmware manager - coordinates all firmware operations.

This module provides the primary interface for firmware management,
orchestrating between type handlers, repositories, and operations.
"""

import asyncio
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

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
        self.repository = self._load_firmware_repository()
        self.version_checker = VersionChecker()
        self.vendor_tools = self._initialize_vendor_tools()
        self.update_policy = UpdatePolicy.RECOMMENDED

        logger.info(f"Initialized FirmwareManager with config: {self.config_path}")

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
        """Extract vendor information from device type."""
        # Device type mapping for tests and operations
        if device_type == "a1.c5.large":
            return {"vendor": "hpe", "model": "Gen10"}
        elif "supermicro" in device_type.lower() or device_type.startswith("s"):
            return {"vendor": "supermicro", "model": "x11"}
        elif "dell" in device_type.lower() or device_type.startswith("d"):
            return {"vendor": "dell", "model": "poweredge"}
        elif "hpe" in device_type.lower() or device_type.startswith("h"):
            return {"vendor": "hpe", "model": "proliant"}
        else:
            return {"vendor": "unknown", "model": "unknown"}

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
                        execution_time=0.0,
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
        if not firmware_info.file_path:
            return FirmwareUpdateResult(
                firmware_type=firmware_info.firmware_type,
                success=False,
                old_version=firmware_info.current_version,
                new_version=firmware_info.current_version,
                execution_time=0.0,
                requires_reboot=firmware_info.requires_reboot,
                error_message="No firmware file available",
                operation_id=operation_id,
            )

        # Get appropriate handler
        handler = self.version_checker.get_handler(
            firmware_info.firmware_type,
            firmware_info.vendor or "unknown",
            firmware_info.model or "unknown",
        )

        if not handler:
            return FirmwareUpdateResult(
                firmware_type=firmware_info.firmware_type,
                success=False,
                old_version=firmware_info.current_version,
                new_version=firmware_info.current_version,
                execution_time=0.0,
                requires_reboot=firmware_info.requires_reboot,
                error_message="No handler available for firmware type",
                operation_id=operation_id,
            )

        logger.info(
            f"Updating {firmware_info.firmware_type.value} firmware on {target_ip}"
        )

        return await handler.update_firmware(
            target_ip, username, password, firmware_info.file_path, operation_id
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
