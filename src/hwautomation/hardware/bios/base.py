"""Base classes and data structures for BIOS configuration management.

This module contains the core data structures, abstract base classes,
and interfaces used throughout the BIOS configuration system.
"""

import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ...logging import get_logger

logger = get_logger(__name__)


class ConfigMethod(Enum):
    """BIOS configuration methods."""
    
    REDFISH_STANDARD = "redfish_standard"
    REDFISH_OEM = "redfish_oem"
    VENDOR_TOOLS = "vendor_tools"
    HYBRID = "hybrid"
    MANUAL = "manual"


class OperationStatus(Enum):
    """Status of BIOS operations."""
    
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"


@dataclass
class BiosConfigResult:
    """Result of a BIOS configuration operation."""
    
    success: bool
    method_used: ConfigMethod
    settings_applied: Dict[str, str]
    settings_failed: Dict[str, str]
    backup_file: Optional[str] = None
    validation_errors: List[str] = None
    execution_time: Optional[float] = None
    reboot_required: bool = True

    def __post_init__(self):
        """Initialize default values."""
        if self.validation_errors is None:
            self.validation_errors = []


@dataclass
class DeviceConfig:
    """Configuration for a specific device type."""
    
    device_type: str
    manufacturer: str
    model: str
    motherboard: List[str]
    redfish_enabled: bool = True
    vendor_tools_available: bool = False
    special_handling: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.special_handling is None:
            self.special_handling = {}


@dataclass
class MethodSelectionResult:
    """Result of BIOS method selection analysis."""
    
    recommended_method: ConfigMethod
    available_methods: List[ConfigMethod]
    redfish_capabilities: Dict[str, bool]
    vendor_tools_status: Dict[str, bool]
    confidence_score: float
    reasoning: str
    fallback_methods: List[ConfigMethod]


class BaseBiosManager(ABC):
    """Abstract base class for BIOS configuration managers."""
    
    def __init__(self):
        """Initialize base manager."""
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def pull_current_config(self, target_ip: str, username: str, password: str) -> ET.Element:
        """Pull current BIOS configuration from target system."""
        pass

    @abstractmethod
    def apply_template(self, config: ET.Element, device_type: str) -> ET.Element:
        """Apply template modifications to configuration."""
        pass

    @abstractmethod
    def validate_config(self, config: ET.Element, device_type: str) -> List[str]:
        """Validate modified configuration."""
        pass

    @abstractmethod
    def push_config(self, config: ET.Element, target_ip: str, username: str, password: str) -> bool:
        """Push modified configuration to target system."""
        pass


class BaseDeviceHandler(ABC):
    """Abstract base class for device-specific BIOS handlers."""
    
    def __init__(self, device_config: DeviceConfig):
        """Initialize device handler."""
        self.device_config = device_config
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def can_handle(self, device_type: str) -> bool:
        """Check if this handler can manage the given device type."""
        pass

    @abstractmethod
    def get_supported_methods(self) -> List[ConfigMethod]:
        """Get list of supported configuration methods for this device."""
        pass

    @abstractmethod
    def apply_device_specific_settings(self, config: ET.Element) -> ET.Element:
        """Apply device-specific BIOS settings."""
        pass

    def get_priority(self) -> int:
        """Get priority for device handler selection (lower = higher priority)."""
        return 100


class BaseConfigLoader(ABC):
    """Abstract base class for configuration loaders."""
    
    def __init__(self, config_dir: str):
        """Initialize configuration loader."""
        self.config_dir = config_dir
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from storage."""
        pass

    @abstractmethod
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to storage."""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration structure and content."""
        pass


class BaseConfigParser(ABC):
    """Abstract base class for configuration parsers."""
    
    def __init__(self):
        """Initialize parser."""
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def parse(self, data: str) -> ET.Element:
        """Parse configuration data into XML Element."""
        pass

    @abstractmethod
    def serialize(self, config: ET.Element) -> str:
        """Serialize XML Element to string format."""
        pass

    def safe_parse(self, data: str) -> Optional[ET.Element]:
        """Safely parse data with error handling."""
        try:
            return self.parse(data)
        except Exception as e:
            self.logger.warning(f"Failed to parse configuration data: {e}")
            return None


class BaseOperationHandler(ABC):
    """Abstract base class for BIOS operation handlers."""
    
    def __init__(self):
        """Initialize operation handler."""
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def execute(self, **kwargs) -> BiosConfigResult:
        """Execute the BIOS operation."""
        pass

    @abstractmethod
    def validate_inputs(self, **kwargs) -> List[str]:
        """Validate input parameters for the operation."""
        pass

    @abstractmethod
    def can_rollback(self) -> bool:
        """Check if this operation supports rollback."""
        pass

    def rollback(self, **kwargs) -> BiosConfigResult:
        """Rollback the operation (default: not supported)."""
        return BiosConfigResult(
            success=False,
            method_used=ConfigMethod.MANUAL,
            settings_applied={},
            settings_failed={"rollback": "Operation does not support rollback"},
            validation_errors=["Rollback not supported for this operation"]
        )
