"""Firmware version checking operations.

This module handles firmware version detection and comparison across
different vendors and firmware types.
"""

import asyncio
from typing import Dict, List, Optional, Tuple

from ....logging import get_logger
from ..base import FirmwareInfo, FirmwareType, Priority
from ..types.bios import BiosFirmwareHandler
from ..types.bmc import BmcFirmwareHandler

logger = get_logger(__name__)


class VersionChecker:
    """Handles firmware version checking operations."""

    def __init__(self):
        self.handlers = {}
        self._initialize_handlers()

    def _initialize_handlers(self):
        """Initialize firmware type handlers."""
        # These will be registered per vendor/model as needed
        pass

    def get_handler(self, firmware_type: FirmwareType, vendor: str, model: str):
        """Get appropriate firmware handler."""
        handler_key = f"{firmware_type.value}_{vendor}_{model}"
        
        if handler_key not in self.handlers:
            if firmware_type == FirmwareType.BIOS:
                self.handlers[handler_key] = BiosFirmwareHandler(vendor, model)
            elif firmware_type == FirmwareType.BMC:
                self.handlers[handler_key] = BmcFirmwareHandler(vendor, model)
            else:
                # TODO: Add other firmware type handlers
                logger.warning(f"No handler for firmware type: {firmware_type}")
                return None
                
        return self.handlers[handler_key]

    async def check_all_firmware_versions(
        self,
        device_type: str,
        target_ip: str,
        username: str,
        password: str,
        vendor_info: Dict[str, str],
        repository,
    ) -> Dict[str, FirmwareInfo]:
        """Check all firmware versions for a device."""
        results = {}
        
        # Define firmware types to check based on device
        firmware_types = [FirmwareType.BIOS, FirmwareType.BMC]
        
        vendor = vendor_info.get("vendor", "unknown")
        model = vendor_info.get("model", "unknown")
        
        for fw_type in firmware_types:
            try:
                fw_info = await self.check_firmware_version(
                    fw_type, target_ip, username, password, vendor, model, repository
                )
                if fw_info:
                    results[fw_type.value] = fw_info
            except Exception as e:
                logger.error(f"Failed to check {fw_type.value} firmware: {e}")
                
        return results

    async def check_firmware_version(
        self,
        firmware_type: FirmwareType,
        target_ip: str,
        username: str,
        password: str,
        vendor: str,
        model: str,
        repository,
    ) -> Optional[FirmwareInfo]:
        """Check version for a specific firmware type."""
        handler = self.get_handler(firmware_type, vendor, model)
        if not handler:
            return None
            
        try:
            # Get current version
            current_version = await handler.get_current_version(
                target_ip, username, password
            )
            
            # Get latest version from repository
            latest_version = repository.get_latest_version(firmware_type, vendor, model)
            if not latest_version:
                latest_version = current_version
                
            # Determine if update is required
            update_required = self._compare_versions(current_version, latest_version)
            
            # Determine priority
            priority = self._determine_update_priority(
                firmware_type, current_version, latest_version
            )
            
            # Get firmware file path
            file_path = repository.get_firmware_file_path(
                firmware_type, vendor, model, latest_version
            )
            
            return FirmwareInfo(
                firmware_type=firmware_type,
                current_version=current_version,
                latest_version=latest_version,
                update_required=update_required,
                priority=priority,
                file_path=file_path,
                estimated_time=handler.get_update_time_estimate(),
                requires_reboot=(firmware_type == FirmwareType.BIOS),
                vendor=vendor,
                model=model,
            )
            
        except Exception as e:
            logger.error(f"Failed to check {firmware_type.value} version: {e}")
            return None

    def _compare_versions(self, current: str, latest: str) -> bool:
        """Compare firmware versions to determine if update is needed."""
        if current == "unknown" or latest == "unknown":
            return False
            
        if current == latest:
            return False
            
        # Simple version comparison - in production this would be more sophisticated
        try:
            # Try to parse as semantic versions
            current_parts = current.replace('-', '.').split('.')
            latest_parts = latest.replace('-', '.').split('.')
            
            # Pad with zeros for comparison
            max_len = max(len(current_parts), len(latest_parts))
            current_parts.extend(['0'] * (max_len - len(current_parts)))
            latest_parts.extend(['0'] * (max_len - len(latest_parts)))
            
            for i in range(max_len):
                try:
                    curr_num = int(current_parts[i])
                    latest_num = int(latest_parts[i])
                    
                    if latest_num > curr_num:
                        return True
                    elif latest_num < curr_num:
                        return False
                except ValueError:
                    # Non-numeric version parts, do string comparison
                    if latest_parts[i] > current_parts[i]:
                        return True
                    elif latest_parts[i] < current_parts[i]:
                        return False
                        
            return False
            
        except Exception:
            # Fallback to string comparison
            return latest > current

    def _determine_update_priority(
        self, firmware_type: FirmwareType, current: str, latest: str
    ) -> Priority:
        """Determine update priority based on firmware type and versions."""
        if current == "unknown":
            return Priority.HIGH
            
        # TODO: Implement more sophisticated priority logic based on:
        # - Security vulnerability databases
        # - Release notes parsing
        # - Critical bug fixes
        
        if firmware_type == FirmwareType.BMC:
            return Priority.HIGH  # BMC updates are generally important
        elif firmware_type == FirmwareType.BIOS:
            return Priority.NORMAL  # BIOS updates can be more disruptive
        else:
            return Priority.LOW
