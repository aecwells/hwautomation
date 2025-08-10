"""Base classes and data models for IPMI management.

This module provides the foundational classes, enums, and data structures
used throughout the IPMI management system.
"""

import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class IPMIVendor(Enum):
    """Supported IPMI vendors."""

    SUPERMICRO = "supermicro"
    HP_ILO = "hp_ilo"
    DELL_IDRAC = "dell_idrac"
    UNKNOWN = "unknown"


class PowerState(Enum):
    """IPMI power states."""

    ON = "on"
    OFF = "off"
    RESET = "reset"
    CYCLE = "cycle"
    SOFT = "soft"


class IPMICommand(Enum):
    """Common IPMI commands."""

    POWER_STATUS = "power status"
    POWER_ON = "power on"
    POWER_OFF = "power off"
    POWER_RESET = "power reset"
    POWER_CYCLE = "power cycle"
    POWER_SOFT = "power soft"
    SENSOR_LIST = "sensor list"
    FRU_LIST = "fru list"
    MC_INFO = "mc info"


@dataclass
class IPMICredentials:
    """IPMI connection credentials."""

    ip_address: str
    username: str = "ADMIN"
    password: str = ""
    interface: str = "lanplus"
    port: int = 623


@dataclass
class IPMISettings:
    """IPMI configuration settings."""

    admin_password: str
    kcs_control: Optional[str] = None  # 'user' for Supermicro
    host_interface: Optional[str] = None  # 'off' for Supermicro
    ipmi_over_lan: Optional[str] = None  # 'enabled' for HP
    require_host_auth: Optional[str] = None  # 'enabled' for HP
    require_login_rbsu: Optional[str] = None  # 'enabled' for HP
    oob_license_required: bool = True


@dataclass
class IPMIConfigResult:
    """Result of IPMI configuration attempt."""

    success: bool
    vendor: IPMIVendor
    firmware_version: Optional[str] = None
    settings_applied: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    execution_time: float = 0.0


@dataclass
class PowerStatus:
    """Power status information."""

    state: str
    raw_output: str
    timestamp: Optional[str] = None


@dataclass
class SensorReading:
    """IPMI sensor reading."""

    name: str
    value: Optional[str]
    unit: Optional[str]
    status: Optional[str]
    lower_threshold: Optional[str] = None
    upper_threshold: Optional[str] = None


@dataclass
class IPMISystemInfo:
    """IPMI system information."""

    manufacturer: Optional[str] = None
    product_name: Optional[str] = None
    firmware_version: Optional[str] = None
    serial_number: Optional[str] = None
    guid: Optional[str] = None
    vendor: IPMIVendor = IPMIVendor.UNKNOWN


class BaseIPMIHandler(ABC):
    """Abstract base class for IPMI handlers."""

    def __init__(self, credentials: IPMICredentials, timeout: int = 30):
        """Initialize IPMI handler.

        Args:
            credentials: IPMI connection credentials
            timeout: Command timeout in seconds
        """
        self.credentials = credentials
        self.timeout = timeout

    @abstractmethod
    def execute_command(
        self,
        command: Union[str, IPMICommand],
        additional_args: Optional[List[str]] = None,
    ) -> subprocess.CompletedProcess:
        """Execute an IPMI command.

        Args:
            command: IPMI command to execute
            additional_args: Additional command arguments

        Returns:
            Completed process result
        """
        pass

    @abstractmethod
    def get_power_status(self) -> PowerStatus:
        """Get current power status.

        Returns:
            Power status information
        """
        pass

    @abstractmethod
    def set_power_state(self, state: PowerState) -> bool:
        """Set power state.

        Args:
            state: Target power state

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    def get_sensor_data(self) -> List[SensorReading]:
        """Get sensor readings.

        Returns:
            List of sensor readings
        """
        pass


class BaseVendorHandler(ABC):
    """Abstract base class for vendor-specific IPMI configuration."""

    def __init__(self, vendor: IPMIVendor):
        """Initialize vendor handler.

        Args:
            vendor: IPMI vendor type
        """
        self.vendor = vendor

    @abstractmethod
    def detect_vendor(self, credentials: IPMICredentials) -> bool:
        """Detect if this handler supports the target system.

        Args:
            credentials: IPMI credentials for detection

        Returns:
            True if this handler supports the system
        """
        pass

    @abstractmethod
    def configure_ipmi(
        self, credentials: IPMICredentials, settings: IPMISettings
    ) -> IPMIConfigResult:
        """Configure IPMI settings for this vendor.

        Args:
            credentials: IPMI connection credentials
            settings: Configuration settings to apply

        Returns:
            Configuration result
        """
        pass

    @abstractmethod
    def get_system_info(self, credentials: IPMICredentials) -> IPMISystemInfo:
        """Get system information for this vendor.

        Args:
            credentials: IPMI connection credentials

        Returns:
            System information
        """
        pass

    @abstractmethod
    def validate_configuration(
        self, credentials: IPMICredentials, settings: IPMISettings
    ) -> bool:
        """Validate IPMI configuration.

        Args:
            credentials: IPMI connection credentials
            settings: Settings to validate

        Returns:
            True if configuration is valid
        """
        pass


class IPMICommandError(Exception):
    """Exception raised for IPMI command execution errors."""

    def __init__(self, message: str, command: str, exit_code: Optional[int] = None):
        """Initialize IPMI command error.

        Args:
            message: Error message
            command: Command that failed
            exit_code: Process exit code
        """
        super().__init__(message)
        self.command = command
        self.exit_code = exit_code


class IPMIConnectionError(Exception):
    """Exception raised for IPMI connection errors."""

    pass


class IPMIConfigurationError(Exception):
    """Exception raised for IPMI configuration errors."""

    pass
