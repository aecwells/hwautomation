"""Firmware repository management.

This module handles firmware repository configuration, file management,
and download operations.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from ....logging import get_logger
from ..base import BaseFirmwareRepository, FirmwareType

logger = get_logger(__name__)


@dataclass
class FirmwareRepository(BaseFirmwareRepository):
    """Firmware repository configuration."""

    base_path: str
    vendors: Dict[str, Dict[str, Any]]
    download_enabled: bool = True
    auto_verify: bool = True
    cache_duration: int = 86400  # 24 hours

    @classmethod
    def from_config(cls, config_path: str) -> "FirmwareRepository":
        """Load repository configuration from file."""
        try:
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

            repo_config = config.get("firmware_repository", {})
            return cls(
                base_path=repo_config.get("base_path", "/opt/firmware"),
                vendors=repo_config.get("vendors", {}),
                download_enabled=repo_config.get("download_enabled", True),
                auto_verify=repo_config.get("auto_verify", True),
                cache_duration=repo_config.get("cache_duration", 86400),
            )
        except Exception as e:
            logger.warning(f"Failed to load firmware repository config: {e}")
            return cls(base_path="/opt/firmware", vendors={})

    def get_latest_version(
        self, firmware_type: FirmwareType, vendor: str, model: str
    ) -> Optional[str]:
        """Get latest available version."""
        vendor_config = self.vendors.get(vendor.lower(), {})
        model_config = vendor_config.get("models", {}).get(model.lower(), {})
        firmware_config = model_config.get("firmware", {}).get(firmware_type.value, {})

        return firmware_config.get("latest_version")

    def get_firmware_file_path(
        self, firmware_type: FirmwareType, vendor: str, model: str, version: str
    ) -> Optional[str]:
        """Get path to firmware file."""
        # Build path: base_path/vendor/model/firmware_type/version/
        path = (
            Path(self.base_path)
            / vendor.lower()
            / model.lower()
            / firmware_type.value
            / version
        )

        if path.exists():
            # Look for common firmware file extensions
            for ext in [".bin", ".rom", ".fw", ".img", ".cap", ".exe"]:
                for file in path.glob(f"*{ext}"):
                    return str(file)

        return None

    def download_firmware(
        self, firmware_type: FirmwareType, vendor: str, model: str, version: str
    ) -> Optional[str]:
        """Download firmware file."""
        # TODO: Implement firmware download from vendor sources
        logger.warning("Firmware download not yet implemented")
        return None

    def get_vendor_config(self, vendor: str) -> Dict[str, Any]:
        """Get vendor-specific configuration."""
        return self.vendors.get(vendor.lower(), {})

    def get_model_config(self, vendor: str, model: str) -> Dict[str, Any]:
        """Get model-specific configuration."""
        vendor_config = self.get_vendor_config(vendor)
        return vendor_config.get("models", {}).get(model.lower(), {})

    def list_available_firmware(self, vendor: str, model: str) -> Dict[str, Any]:
        """List all available firmware for a vendor/model."""
        model_config = self.get_model_config(vendor, model)
        return model_config.get("firmware", {})
