"""Base classes and data models for Redfish management.

This module provides the foundational classes, enums, and data structures
used throughout the Redfish management system.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

import requests

T = TypeVar('T')


@dataclass
class RedfishCapabilities:
    """Redfish capabilities discovered from the BMC.
    
    Legacy compatibility class for existing test code.
    """
    
    supports_bios_config: bool = False
    supports_power_control: bool = False
    supports_system_info: bool = False
    supports_firmware_update: bool = False
    bios_settings_uri: Optional[str] = None
    systems_uri: Optional[str] = None
    chassis_uri: Optional[str] = None


class PowerAction(Enum):
    """Redfish power actions."""
    
    ON = "On"
    FORCE_ON = "ForceOn"
    OFF = "GracefulShutdown"
    FORCE_OFF = "ForceOff"
    RESTART = "GracefulRestart"
    FORCE_RESTART = "ForceRestart"
    PAUSE = "Pause"
    RESUME = "Resume"
    SUSPEND = "Suspend"
    RESET = "Reset"


class PowerState(Enum):
    """Redfish power states."""
    
    ON = "On"
    OFF = "Off"
    POWERING_ON = "PoweringOn"
    POWERING_OFF = "PoweringOff"
    PAUSED = "Paused"


class HealthStatus(Enum):
    """Redfish health status values."""
    
    OK = "OK"
    WARNING = "Warning"
    CRITICAL = "Critical"
    UNKNOWN = "Unknown"


@dataclass
class RedfishCredentials:
    """Redfish connection credentials."""
    
    host: str
    username: str
    password: str
    port: int = 443
    use_ssl: bool = True
    verify_ssl: bool = False
    timeout: int = 30


@dataclass
class RedfishCapabilities:
    """Redfish capabilities discovered from the BMC."""

    supports_bios_config: bool = False
    supports_power_control: bool = False
    supports_system_info: bool = False
    supports_firmware_update: bool = False
    bios_settings_uri: Optional[str] = None
    systems_uri: Optional[str] = None
    chassis_uri: Optional[str] = None
    firmware_uri: Optional[str] = None
    service_version: Optional[str] = None


@dataclass
class SystemInfo:
    """System information retrieved via Redfish."""

    id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    bios_version: Optional[str] = None
    power_state: Optional[str] = None
    health_status: Optional[str] = None
    health: Optional[str] = None  # Alternative name for health_status
    processor_count: Optional[int] = None
    memory_total_gb: Optional[float] = None
    sku: Optional[str] = None
    part_number: Optional[str] = None
    uuid: Optional[str] = None
    asset_tag: Optional[str] = None
    processor_summary: Optional[Dict[str, Any]] = None
    memory_summary: Optional[Dict[str, Any]] = None
    network_interfaces: Optional[List[Dict[str, Any]]] = None
    storage_summary: Optional[Dict[str, Any]] = None


@dataclass
class BiosAttribute:
    """BIOS attribute information."""
    
    name: str
    value: Any
    type: Optional[str] = None
    read_only: bool = False
    description: Optional[str] = None
    possible_values: Optional[List[Any]] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None


@dataclass
class FirmwareComponent:
    """Firmware component information."""
    
    name: str
    version: str
    updateable: bool = False
    component_type: Optional[str] = None
    manufacturer: Optional[str] = None
    release_date: Optional[str] = None
    description: Optional[str] = None


@dataclass
class RedfishResponse:
    """Standardized Redfish response wrapper."""
    
    success: bool
    status_code: int
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    headers: Optional[Dict[str, str]] = None


@dataclass
class RedfishOperation(Generic[T]):
    """Redfish operation result with generic result type."""
    
    success: bool
    result: Optional[T] = None
    error_message: Optional[str] = None
    response: Optional['RedfishResponse'] = None
    execution_time: float = 0.0
    task_id: Optional[str] = None


class BaseRedfishClient(ABC):
    """Abstract base class for Redfish HTTP clients."""

    def __init__(self, credentials: RedfishCredentials):
        """Initialize Redfish client.
        
        Args:
            credentials: Redfish connection credentials
        """
        self.credentials = credentials

    @abstractmethod
    def get(self, uri: str, **kwargs) -> RedfishResponse:
        """Perform GET request.
        
        Args:
            uri: Request URI
            **kwargs: Additional request parameters
            
        Returns:
            Redfish response
        """
        pass

    @abstractmethod
    def post(self, uri: str, data: Optional[Dict] = None, **kwargs) -> RedfishResponse:
        """Perform POST request.
        
        Args:
            uri: Request URI
            data: Request data
            **kwargs: Additional request parameters
            
        Returns:
            Redfish response
        """
        pass

    @abstractmethod
    def patch(self, uri: str, data: Optional[Dict] = None, **kwargs) -> RedfishResponse:
        """Perform PATCH request.
        
        Args:
            uri: Request URI
            data: Request data
            **kwargs: Additional request parameters
            
        Returns:
            Redfish response
        """
        pass

    @abstractmethod
    def put(self, uri: str, data: Optional[Dict] = None, **kwargs) -> RedfishResponse:
        """Perform PUT request.
        
        Args:
            uri: Request URI
            data: Request data
            **kwargs: Additional request parameters
            
        Returns:
            Redfish response
        """
        pass

    @abstractmethod
    def delete(self, uri: str, **kwargs) -> RedfishResponse:
        """Perform DELETE request.
        
        Args:
            uri: Request URI
            **kwargs: Additional request parameters
            
        Returns:
            Redfish response
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the client session."""
        pass


class BaseRedfishOperation(ABC):
    """Abstract base class for Redfish operations."""

    def __init__(self, client: BaseRedfishClient):
        """Initialize operation handler.
        
        Args:
            client: Redfish client instance
        """
        self.client = client

    @property
    @abstractmethod
    def operation_name(self) -> str:
        """Get operation name."""
        pass


class RedfishError(Exception):
    """Base exception for Redfish operations."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        """Initialize Redfish error.
        
        Args:
            message: Error message
            status_code: HTTP status code
        """
        super().__init__(message)
        self.status_code = status_code


class RedfishConnectionError(RedfishError):
    """Exception for Redfish connection errors."""
    pass


class RedfishAuthenticationError(RedfishError):
    """Exception for Redfish authentication errors."""
    pass


class RedfishOperationError(RedfishError):
    """Exception for Redfish operation errors."""
    
    def __init__(self, message: str, operation: str, status_code: Optional[int] = None):
        """Initialize operation error.
        
        Args:
            message: Error message
            operation: Failed operation name
            status_code: HTTP status code
        """
        super().__init__(message, status_code)
        self.operation = operation


class RedfishNotSupportedError(RedfishError):
    """Exception for unsupported Redfish operations."""
    pass
