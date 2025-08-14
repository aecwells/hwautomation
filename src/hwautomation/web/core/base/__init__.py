"""
HWAutomation Web Interface Base Classes Module.

This module provides modular base classes and mixins for the web interface,
offering reusable functionality for API views, RESTful resources, database
operations, validation, caching, and timestamp utilities.
"""

# Import all components
from .api_view import BaseAPIView
from .cache_mixin import CacheMixin
from .combined_resource import BaseResource
from .database_mixin import DatabaseMixin
from .resource_view import BaseResourceView
from .timestamp_mixin import TimestampMixin
from .validation_mixin import ValidationMixin

# Public API
__all__ = [
    # Core view classes
    "BaseAPIView",
    "BaseResourceView",
    "BaseResource",
    # Mixins
    "DatabaseMixin",
    "ValidationMixin",
    "CacheMixin",
    "TimestampMixin",
]

# Version info
__version__ = "2.0.0"
__author__ = "HWAutomation Team"

# Module metadata
MODULAR_COMPONENTS = {
    "api_view": {
        "description": "Core API view functionality with request handling and response formatting",
        "classes": ["BaseAPIView"],
        "features": [
            "Standard response formatting",
            "Error handling",
            "Pagination",
            "Logging",
        ],
    },
    "resource_view": {
        "description": "RESTful resource patterns with CRUD operations",
        "classes": ["BaseResourceView"],
        "features": [
            "CRUD operations",
            "Resource identification",
            "Validation helpers",
        ],
    },
    "database_mixin": {
        "description": "Database operations and connection management",
        "classes": ["DatabaseMixin"],
        "features": ["Connection management", "Transaction handling", "Query helpers"],
    },
    "validation_mixin": {
        "description": "Common validation patterns and business rules",
        "classes": ["ValidationMixin"],
        "features": ["Field validation", "Type checking", "Format validation"],
    },
    "cache_mixin": {
        "description": "In-memory caching with TTL support",
        "classes": ["CacheMixin"],
        "features": ["TTL-based caching", "Cache invalidation", "Memory management"],
    },
    "timestamp_mixin": {
        "description": "Timestamp utilities and time formatting",
        "classes": ["TimestampMixin"],
        "features": ["Timestamp formatting", "Duration calculations", "Time parsing"],
    },
    "combined_resource": {
        "description": "Complete resource foundation combining all mixins",
        "classes": ["BaseResource"],
        "features": ["All mixin features combined", "Unified interface"],
    },
}


def get_component_info(component_name: str = None) -> dict:
    """Get information about modular components."""
    if component_name:
        return MODULAR_COMPONENTS.get(component_name, {})
    return MODULAR_COMPONENTS


def list_available_classes() -> list:
    """List all available classes in the module."""
    return __all__


def get_module_stats() -> dict:
    """Get module statistics."""
    return {
        "total_components": len(MODULAR_COMPONENTS),
        "total_classes": len(__all__),
        "version": __version__,
        "author": __author__,
    }
