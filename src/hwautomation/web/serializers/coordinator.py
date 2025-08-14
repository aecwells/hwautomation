"""
Serialization coordinator and factory.

This module provides centralized coordination for all serialization
operations and factory functions for creating appropriate serializers.
"""

from typing import Any, Dict, Optional, Type

from .base import BaseSerializer
from .device import DeviceSerializer, HardwareSpecSerializer
from .response import APIResponseSerializer, PaginationHelper
from .server import ServerListSerializer, ServerSerializer
from .validation import (
    BoardingValidationSerializer,
    ValidationErrorSerializer,
    ValidationResultSerializer,
)
from .workflow import WorkflowListSerializer, WorkflowSerializer


class SerializerFactory:
    """Factory for creating appropriate serializers based on data type and context."""

    _serializer_map = {
        "server": ServerSerializer,
        "server_list": ServerListSerializer,
        "workflow": WorkflowSerializer,
        "workflow_list": WorkflowListSerializer,
        "device": DeviceSerializer,
        "hardware_spec": HardwareSpecSerializer,
        "validation": ValidationResultSerializer,
        "boarding_validation": BoardingValidationSerializer,
        "validation_error": ValidationErrorSerializer,
    }

    @classmethod
    def get_serializer(
        self,
        serializer_type: str,
        fields: Optional[list] = None,
        exclude_fields: Optional[list] = None,
    ) -> BaseSerializer:
        """Get appropriate serializer for the given type."""
        serializer_class = self._serializer_map.get(serializer_type)

        if not serializer_class:
            # Fallback to base serializer
            serializer_class = BaseSerializer

        return serializer_class(fields=fields, exclude_fields=exclude_fields)

    @classmethod
    def register_serializer(self, name: str, serializer_class: Type[BaseSerializer]):
        """Register a custom serializer."""
        self._serializer_map[name] = serializer_class

    @classmethod
    def list_serializers(self) -> Dict[str, str]:
        """List all registered serializers."""
        return {name: cls.__name__ for name, cls in self._serializer_map.items()}


class SerializationCoordinator:
    """Coordinates serialization operations across the application."""

    def __init__(self):
        self.factory = SerializerFactory()

    def serialize(
        self,
        data: Any,
        serializer_type: str = "base",
        fields: Optional[list] = None,
        exclude_fields: Optional[list] = None,
        **kwargs,
    ) -> Any:
        """Serialize data using the appropriate serializer."""
        serializer = self.factory.get_serializer(
            serializer_type, fields=fields, exclude_fields=exclude_fields
        )
        return serializer.serialize(data)

    def create_api_response(
        self,
        data: Any = None,
        success: bool = True,
        message: str = "Success",
        error_code: str = None,
        serializer_type: str = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Create standardized API response."""
        if success:
            serializer = None
            if serializer_type:
                serializer = self.factory.get_serializer(serializer_type)

            return APIResponseSerializer.success_response(
                data=data,
                message=message,
                serializer=serializer,
                metadata=metadata,
            )
        else:
            return APIResponseSerializer.error_response(
                message=message,
                error_code=error_code or "UNKNOWN_ERROR",
                details=kwargs.get("details"),
                validation_errors=kwargs.get("validation_errors"),
            )

    def create_paginated_response(
        self,
        items: list,
        page: int = 1,
        per_page: int = 20,
        total_items: Optional[int] = None,
        serializer_type: str = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create paginated API response."""
        if total_items is None:
            total_items = len(items)

        pagination_info = PaginationHelper.calculate_pagination(
            total_items=total_items, page=page, per_page=per_page
        )

        serializer = None
        if serializer_type:
            serializer = self.factory.get_serializer(serializer_type)

        return APIResponseSerializer.paginated_response(
            items=items,
            pagination_info=pagination_info,
            serializer=serializer,
            metadata=metadata,
        )


# Global coordinator instance
coordinator = SerializationCoordinator()


# Convenience functions
def serialize(data: Any, serializer_type: str = "base", **kwargs) -> Any:
    """Convenience function for serialization."""
    return coordinator.serialize(data, serializer_type, **kwargs)


def api_response(
    data: Any = None,
    success: bool = True,
    message: str = "Success",
    serializer_type: str = None,
    **kwargs,
) -> Dict[str, Any]:
    """Convenience function for API responses."""
    return coordinator.create_api_response(
        data=data,
        success=success,
        message=message,
        serializer_type=serializer_type,
        **kwargs,
    )


def paginated_response(
    items: list,
    page: int = 1,
    per_page: int = 20,
    serializer_type: str = None,
    **kwargs,
) -> Dict[str, Any]:
    """Convenience function for paginated responses."""
    return coordinator.create_paginated_response(
        items=items,
        page=page,
        per_page=per_page,
        serializer_type=serializer_type,
        **kwargs,
    )
