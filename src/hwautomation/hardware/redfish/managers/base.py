"""
Base Redfish Manager Interface

Provides common interface and utilities for all Redfish managers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from hwautomation.logging import get_logger

from ..base import RedfishCredentials, RedfishError, RedfishOperation
from ..client import RedfishSession

logger = get_logger(__name__)


class BaseRedfishManager(ABC):
    """Base class for all Redfish managers."""

    def __init__(self, credentials: RedfishCredentials):
        self.credentials = credentials
        self.logger = get_logger(self.__class__.__name__)

    @property
    def host(self) -> str:
        """Get host."""
        return self.credentials.host

    @property
    def base_url(self) -> str:
        """Get base URL."""
        protocol = "https" if self.credentials.use_ssl else "http"
        return f"{protocol}://{self.credentials.host}:{self.credentials.port}"

    def create_session(self) -> RedfishSession:
        """Create a new Redfish session."""
        return RedfishSession(self.credentials)

    def test_connection(self) -> bool:
        """Test connection to Redfish service."""
        try:
            with self.create_session() as session:
                return session.test_connection()
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False

    @abstractmethod
    def get_supported_operations(self) -> Dict[str, bool]:
        """Get supported operations for this manager."""
        pass


class RedfishManagerError(RedfishError):
    """Base exception for Redfish manager errors."""

    pass


class RedfishManagerConnectionError(RedfishManagerError):
    """Raised when connection to Redfish service fails."""

    pass


class RedfishManagerOperationError(RedfishManagerError):
    """Raised when a Redfish operation fails."""

    pass
