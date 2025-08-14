"""
Base classes and mixins for HWAutomation Web Interface.

This module provides reusable base classes for views, resources,
and common patterns in the web interface.

DEPRECATED: This module has been refactored into modular components.
Please use: from hwautomation.web.core.base import BaseAPIView, BaseResource, etc.

For backward compatibility, all classes are still available from this module.
"""

# Import all components from the new modular structure
from .base import (
    BaseAPIView,
    BaseResource,
    BaseResourceView,
    CacheMixin,
    DatabaseMixin,
    TimestampMixin,
    ValidationMixin,
)

# Maintain backward compatibility by exporting all classes
__all__ = [
    "BaseAPIView",
    "BaseResourceView",
    "BaseResource",
    "DatabaseMixin",
    "ValidationMixin",
    "CacheMixin",
    "TimestampMixin",
]

# Deprecation warning for future migration
import warnings

warnings.warn(
    "hwautomation.web.core.base_classes is deprecated. "
    "Use hwautomation.web.core.base.* modules instead.",
    DeprecationWarning,
    stacklevel=2,
)
