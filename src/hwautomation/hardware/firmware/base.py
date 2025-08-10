"""Base classes and data structures for firmware management.

This module contains the core data structures, enums, and interfaces
used throughout the firmware management system.
"""

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from ...logging import get_logger

logger = get_logger(__name__)


class FirmwareUpdateException(Exception):
    """Exception raised during firmware update operations."""

    pass


class FirmwareType(Enum):
    """Types of firmware that can be updated."""

    BIOS = "bios"
    BMC = "bmc"
    UEFI = "uefi"
    CPLD = "cpld"
    NIC = "nic"
    STORAGE = "storage"


class Priority(Enum):
    """Priority levels for firmware updates."""

    CRITICAL = "critical"  # Security updates, must install
    HIGH = "high"  # Important bug fixes
    NORMAL = "normal"  # General improvements
    LOW = "low"  # Feature updates


class UpdatePolicy(Enum):
    """Firmware update policies."""

    MANUAL = "manual"  # Manual approval required
    RECOMMENDED = "recommended"  # Install recommended updates
    LATEST = "latest"  # Always use latest firmware
    SECURITY_ONLY = "security"  # Only security updates


@dataclass
class FirmwareInfo:
    """Firmware information structure."""

    firmware_type: FirmwareType
    current_version: str
    latest_version: str
    update_required: bool
    priority: Priority
    file_path: Optional[str] = None
    checksum: Optional[str] = None
    release_notes: Optional[str] = None
    estimated_time: int = 300  # seconds
    requires_reboot: bool = True
    vendor: Optional[str] = None
    model: Optional[str] = None
    download_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class FirmwareUpdateResult:
    """Firmware update operation result."""

    firmware_type: FirmwareType
    success: bool
    old_version: str
    new_version: str
    execution_time: float
    requires_reboot: bool
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    operation_id: Optional[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = asdict(self)
        result["firmware_type"] = self.firmware_type.value
        return result


class BaseFirmwareHandler(ABC):
    """Abstract base class for firmware type handlers."""

    def __init__(self, vendor: str, model: str):
        self.vendor = vendor
        self.model = model
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def get_current_version(
        self, target_ip: str, username: str, password: str
    ) -> str:
        """Get current firmware version."""
        pass

    @abstractmethod
    async def update_firmware(
        self,
        target_ip: str,
        username: str,
        password: str,
        firmware_file: str,
        operation_id: Optional[str] = None,
    ) -> FirmwareUpdateResult:
        """Update firmware component."""
        pass

    @abstractmethod
    def validate_firmware_file(self, firmware_file: str) -> bool:
        """Validate firmware file integrity."""
        pass

    @abstractmethod
    def get_update_time_estimate(self) -> int:
        """Get estimated update time in seconds."""
        pass


class BaseFirmwareRepository(ABC):
    """Abstract base class for firmware repositories."""

    @abstractmethod
    def get_latest_version(
        self, firmware_type: FirmwareType, vendor: str, model: str
    ) -> Optional[str]:
        """Get latest available version."""
        pass

    @abstractmethod
    def get_firmware_file_path(
        self, firmware_type: FirmwareType, vendor: str, model: str, version: str
    ) -> Optional[str]:
        """Get path to firmware file."""
        pass

    @abstractmethod
    def download_firmware(
        self, firmware_type: FirmwareType, vendor: str, model: str, version: str
    ) -> Optional[str]:
        """Download firmware file."""
        pass
