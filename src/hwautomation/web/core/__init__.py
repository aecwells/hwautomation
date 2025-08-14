"""
Core web interface components for HWAutomation.

This module provides the foundation for the HWAutomation web interface
with modular, reusable components for API and web development.
"""

from .base import (
    BaseAPIView,
    BaseResource,
    BaseResourceView,
    CacheMixin,
    DatabaseMixin,
    TimestampMixin,
    ValidationMixin,
)
from .middleware import (
    AuthenticationMiddleware,
    ErrorHandlingMiddleware,
    RequestMiddleware,
    ValidationMiddleware,
)
from .response_handlers import (
    APIResponseHandler,
    ResponseHandlerFactory,
    StreamingResponseHandler,
    WebResponseHandler,
    error_response,
    paginated_response,
    stream_progress,
    success_response,
)
from .serializers import (
    APIResponseSerializer,
    BaseSerializer,
    DeviceSerializer,
    ServerSerializer,
    WorkflowSerializer,
)
from .template_helpers import (
    FormHelper,
    NavigationHelper,
    PaginationHelper,
    TemplateHelpers,
    register_all_helpers,
)
from .websocket_managers import (
    LogStreamManager,
    ServerStatusManager,
    WebSocketManager,
    WebSocketManagerFactory,
    WorkflowManager,
)

__version__ = "1.0.0"
__all__ = [
    # Base classes
    "BaseAPIView",
    "BaseResourceView",
    "BaseResource",
    "DatabaseMixin",
    "ValidationMixin",
    "CacheMixin",
    "TimestampMixin",
    # Middleware
    "RequestMiddleware",
    "ValidationMiddleware",
    "AuthenticationMiddleware",
    "ErrorHandlingMiddleware",
    # Response handlers
    "APIResponseHandler",
    "WebResponseHandler",
    "StreamingResponseHandler",
    "ResponseHandlerFactory",
    "success_response",
    "error_response",
    "paginated_response",
    "stream_progress",
    # Serializers
    "BaseSerializer",
    "ServerSerializer",
    "WorkflowSerializer",
    "DeviceSerializer",
    "APIResponseSerializer",
    # Template helpers
    "TemplateHelpers",
    "PaginationHelper",
    "NavigationHelper",
    "FormHelper",
    "register_all_helpers",
    # WebSocket managers
    "WebSocketManager",
    "ServerStatusManager",
    "WorkflowManager",
    "LogStreamManager",
    "WebSocketManagerFactory",
]


def create_web_core(app=None, socketio=None, **config):
    """
    Initialize web core components with Flask app.

    Args:
        app: Flask application instance
        socketio: SocketIO instance for WebSocket support
        **config: Additional configuration options

    Returns:
        Dictionary of initialized components
    """
    components = {}

    if app is not None:
        # Initialize middleware
        components["request_middleware"] = RequestMiddleware(app)
        components["error_middleware"] = ErrorHandlingMiddleware(app)
        components["auth_middleware"] = AuthenticationMiddleware(app)

        # Register template helpers
        register_all_helpers(app)
        components["template_helpers"] = True

        # Initialize response handler factory
        components["response_factory"] = ResponseHandlerFactory()

    if socketio is not None:
        # Initialize WebSocket managers
        ws_factory = WebSocketManagerFactory(socketio)
        components["websocket_managers"] = ws_factory.initialize_all()
        components["websocket_factory"] = ws_factory

    return components


class WebCoreConfig:
    """
    Configuration class for web core components.

    Features:
    - Centralized configuration
    - Component settings
    - Environment-specific configs
    """

    def __init__(self):
        # Middleware configuration
        self.middleware = {
            "cors_enabled": True,
            "rate_limiting": True,
            "max_requests_per_minute": 100,
            "authentication_required": False,
            "error_logging": True,
        }

        # Response handler configuration
        self.response_handlers = {
            "default_cors": True,
            "json_sort_keys": True,
            "json_indent": 2,
            "streaming_chunk_size": 8192,
        }

        # Serializer configuration
        self.serializers = {
            "datetime_format": "iso",
            "exclude_private_fields": True,
            "include_metadata": True,
        }

        # Template configuration
        self.templates = {
            "auto_reload": True,
            "cache_size": 50,
            "trim_blocks": True,
            "lstrip_blocks": True,
        }

        # WebSocket configuration
        self.websockets = {
            "async_mode": "threading",
            "ping_timeout": 60,
            "ping_interval": 25,
            "max_connections": 1000,
        }

    def update(self, **kwargs):
        """Update configuration with new values."""
        for section, values in kwargs.items():
            if hasattr(self, section) and isinstance(getattr(self, section), dict):
                getattr(self, section).update(values)

    def to_dict(self):
        """Convert configuration to dictionary."""
        return {
            "middleware": self.middleware,
            "response_handlers": self.response_handlers,
            "serializers": self.serializers,
            "templates": self.templates,
            "websockets": self.websockets,
        }
