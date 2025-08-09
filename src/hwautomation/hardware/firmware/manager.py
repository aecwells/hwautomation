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
            
            logger.info(f"Found {len(firmware_info)} firmware components for {device_type}")
            return firmware_info
            
        except Exception as e:
            logger.error(f"Failed to check firmware versions: {e}")
            return {}

    def _get_vendor_info(self, device_type: str) -> Dict[str, str]:
        """Extract vendor information from device type."""
        # TODO: Implement proper device type parsing
        # For now, return mock data based on device type patterns
        
        if "supermicro" in device_type.lower() or device_type.startswith("s"):
            return {"vendor": "supermicro", "model": "x11"}
        elif "dell" in device_type.lower() or device_type.startswith("d"):
            return {"vendor": "dell", "model": "poweredge"}
        elif "hpe" in device_type.lower() or device_type.startswith("h"):
            return {"vendor": "hpe", "model": "proliant"}
        else:
            return {"vendor": "generic", "model": "unknown"}

    async def update_firmware_batch(
        self,
        firmware_updates: List[FirmwareInfo],
        target_ip: str,
        username: str,
        password: str,
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
                if not result.success and fw_info.priority.value in ["critical", "high"]:
                    logger.error(f"Critical firmware update failed, stopping batch")
                    break
                    
            except Exception as e:
                logger.error(f"Firmware update failed: {e}")
                results.append(FirmwareUpdateResult(
                    firmware_type=fw_info.firmware_type,
                    success=False,
                    old_version=fw_info.current_version,
                    new_version=fw_info.current_version,
                    execution_time=0.0,
                    requires_reboot=fw_info.requires_reboot,
                    error_message=str(e),
                    operation_id=operation_id,
                ))
        
        logger.info(f"Batch firmware update completed: {len(results)} updates processed")
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
            )
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
            firmware_info.model or "unknown"
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

        logger.info(f"Updating {firmware_info.firmware_type.value} firmware on {target_ip}")
        
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
