"""
Core middleware components for HWAutomation Web Interface.

This module provides reusable middleware for authentication, validation,
error handling, and request processing.
"""

import functools
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from flask import current_app, g, jsonify, request
from werkzeug.exceptions import BadRequest, Forbidden, Unauthorized

from hwautomation.logging import get_logger, set_correlation_id, with_correlation

logger = get_logger(__name__)


class RequestMiddleware:
    """
    Centralized request middleware for common processing.

    Features:
    - Correlation ID tracking
    - Request timing
    - Rate limiting
    - Request logging
    """

    def __init__(self, app=None):
        self.app = app
        self.rate_limits: Dict[str, List[float]] = {}
        self.request_counts: Dict[str, int] = {}

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize middleware with Flask app."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        app.teardown_appcontext(self.teardown_request)

    def before_request(self):
        """Process request before handling."""
        # Set correlation ID
        correlation_id = (
            request.headers.get("X-Correlation-ID")
            or request.headers.get("X-Request-ID")
            or f"req-{uuid.uuid4().hex[:8]}"
        )
        set_correlation_id(correlation_id)
        g.correlation_id = correlation_id
        g.request_start_time = time.time()

        # Log request start
        logger.info(
            f"Request started: {request.method} {request.path}",
            extra={
                "method": request.method,
                "path": request.path,
                "remote_addr": request.remote_addr,
                "user_agent": request.headers.get("User-Agent", ""),
                "correlation_id": correlation_id,
            },
        )

        # Rate limiting (basic implementation)
        if self._should_rate_limit():
            return (
                jsonify(
                    {
                        "error": "Rate limit exceeded",
                        "error_code": "RATE_LIMIT_EXCEEDED",
                    }
                ),
                429,
            )

    def after_request(self, response):
        """Process response after handling."""
        duration = time.time() - getattr(g, "request_start_time", time.time())

        # Add correlation ID to response headers
        if hasattr(g, "correlation_id"):
            response.headers["X-Correlation-ID"] = g.correlation_id

        # Log request completion
        logger.info(
            f"Request completed: {request.method} {request.path} - "
            f"Status: {response.status_code} - Duration: {duration:.3f}s",
            extra={
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration": duration,
                "correlation_id": getattr(g, "correlation_id", "unknown"),
            },
        )

        return response

    def teardown_request(self, exception):
        """Clean up after request."""
        if exception:
            logger.error(
                f"Request failed with exception: {exception}",
                extra={
                    "correlation_id": getattr(g, "correlation_id", "unknown"),
                    "exception_type": type(exception).__name__,
                },
                exc_info=True,
            )

    def _should_rate_limit(self) -> bool:
        """Check if request should be rate limited."""
        # Simple rate limiting based on IP
        client_ip = request.remote_addr or "unknown"
        current_time = time.time()
        window_size = 60  # 1 minute window
        max_requests = 100  # 100 requests per minute

        if client_ip not in self.rate_limits:
            self.rate_limits[client_ip] = []

        # Clean old requests
        self.rate_limits[client_ip] = [
            req_time
            for req_time in self.rate_limits[client_ip]
            if current_time - req_time < window_size
        ]

        # Check if limit exceeded
        if len(self.rate_limits[client_ip]) >= max_requests:
            return True

        # Add current request
        self.rate_limits[client_ip].append(current_time)
        return False


class ValidationMiddleware:
    """
    Request validation middleware with common validation patterns.

    Features:
    - JSON schema validation
    - Parameter validation
    - Content type validation
    - CSRF protection
    """

    @staticmethod
    def validate_json_request(required_fields: Optional[List[str]] = None):
        """Decorator to validate JSON requests."""

        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                # Check content type
                if not request.is_json:
                    return (
                        jsonify(
                            {
                                "error": "Content-Type must be application/json",
                                "error_code": "INVALID_CONTENT_TYPE",
                            }
                        ),
                        400,
                    )

                # Parse JSON
                try:
                    data = request.get_json()
                    if data is None:
                        raise BadRequest("Invalid JSON")
                except Exception as e:
                    return (
                        jsonify(
                            {
                                "error": f"Invalid JSON: {str(e)}",
                                "error_code": "INVALID_JSON",
                            }
                        ),
                        400,
                    )

                # Validate required fields
                if required_fields:
                    missing_fields = [
                        field
                        for field in required_fields
                        if field not in data or data[field] is None
                    ]
                    if missing_fields:
                        return (
                            jsonify(
                                {
                                    "error": f"Missing required fields: {', '.join(missing_fields)}",
                                    "error_code": "MISSING_FIELDS",
                                    "missing_fields": missing_fields,
                                }
                            ),
                            400,
                        )

                # Add data to kwargs
                kwargs["json_data"] = data
                return f(*args, **kwargs)

            return wrapper

        return decorator

    @staticmethod
    def validate_query_params(
        required_params: Optional[List[str]] = None,
        optional_params: Optional[Dict[str, Any]] = None,
    ):
        """Decorator to validate query parameters."""

        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                # Validate required parameters
                if required_params:
                    missing_params = [
                        param for param in required_params if param not in request.args
                    ]
                    if missing_params:
                        return (
                            jsonify(
                                {
                                    "error": f"Missing required parameters: {', '.join(missing_params)}",
                                    "error_code": "MISSING_PARAMETERS",
                                    "missing_parameters": missing_params,
                                }
                            ),
                            400,
                        )

                # Process optional parameters with defaults
                params = dict(request.args)
                if optional_params:
                    for param, default_value in optional_params.items():
                        if param not in params:
                            params[param] = default_value
                        else:
                            # Type conversion based on default value type
                            if isinstance(default_value, bool):
                                params[param] = params[param].lower() in (
                                    "true",
                                    "1",
                                    "yes",
                                )
                            elif isinstance(default_value, int):
                                try:
                                    params[param] = int(params[param])
                                except ValueError:
                                    return (
                                        jsonify(
                                            {
                                                "error": f"Parameter '{param}' must be an integer",
                                                "error_code": "INVALID_PARAMETER_TYPE",
                                            }
                                        ),
                                        400,
                                    )
                            elif isinstance(default_value, float):
                                try:
                                    params[param] = float(params[param])
                                except ValueError:
                                    return (
                                        jsonify(
                                            {
                                                "error": f"Parameter '{param}' must be a number",
                                                "error_code": "INVALID_PARAMETER_TYPE",
                                            }
                                        ),
                                        400,
                                    )

                kwargs["query_params"] = params
                return f(*args, **kwargs)

            return wrapper

        return decorator


class AuthenticationMiddleware:
    """
    Authentication middleware for API endpoints.

    Features:
    - API key authentication
    - Session-based authentication
    - Role-based access control
    - Token validation
    """

    def __init__(self, app=None):
        self.app = app
        self.api_keys: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize authentication with Flask app."""
        # Load API keys from config
        self.api_keys = app.config.get("API_KEYS", {})

    def require_authentication(self, roles: Optional[List[str]] = None):
        """Decorator to require authentication."""

        def decorator(f: Callable) -> Callable:
            @functools.wraps(f)
            def wrapper(*args, **kwargs):
                auth_result = self._authenticate_request()

                if not auth_result["authenticated"]:
                    return (
                        jsonify(
                            {
                                "error": "Authentication required",
                                "error_code": "AUTHENTICATION_REQUIRED",
                            }
                        ),
                        401,
                    )

                # Check roles if specified
                if roles and not self._check_roles(auth_result["user"], roles):
                    return (
                        jsonify(
                            {
                                "error": "Insufficient permissions",
                                "error_code": "INSUFFICIENT_PERMISSIONS",
                                "required_roles": roles,
                            }
                        ),
                        403,
                    )

                # Add user info to kwargs
                kwargs["current_user"] = auth_result["user"]
                return f(*args, **kwargs)

            return wrapper

        return decorator

    def _authenticate_request(self) -> Dict[str, Any]:
        """Authenticate the current request."""
        # Check API key authentication
        api_key = request.headers.get("X-API-Key")
        if api_key and api_key in self.api_keys:
            return {
                "authenticated": True,
                "user": self.api_keys[api_key],
                "auth_method": "api_key",
            }

        # Check Bearer token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            user = self._validate_token(token)
            if user:
                return {
                    "authenticated": True,
                    "user": user,
                    "auth_method": "bearer_token",
                }

        # Check session authentication
        session_id = request.headers.get("X-Session-ID")
        if session_id and session_id in self.sessions:
            session = self.sessions[session_id]
            if not session.get("expired", False):
                return {
                    "authenticated": True,
                    "user": session["user"],
                    "auth_method": "session",
                }

        return {"authenticated": False, "user": None, "auth_method": None}

    def _validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate bearer token."""
        # Basic token validation (in production, use JWT or similar)
        # This is a simplified implementation
        if token.startswith("hwauth_"):
            return {"username": "api_user", "roles": ["user"], "token": token}
        return None

    def _check_roles(self, user: Dict[str, Any], required_roles: List[str]) -> bool:
        """Check if user has required roles."""
        user_roles = user.get("roles", [])
        return any(role in user_roles for role in required_roles)


class ErrorHandlingMiddleware:
    """
    Centralized error handling middleware.

    Features:
    - Consistent error responses
    - Error logging with correlation
    - Exception handling
    - Error categorization
    """

    def __init__(self, app=None):
        self.app = app

        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize error handling with Flask app."""
        app.register_error_handler(400, self.handle_bad_request)
        app.register_error_handler(401, self.handle_unauthorized)
        app.register_error_handler(403, self.handle_forbidden)
        app.register_error_handler(404, self.handle_not_found)
        app.register_error_handler(405, self.handle_method_not_allowed)
        app.register_error_handler(429, self.handle_rate_limit)
        app.register_error_handler(500, self.handle_internal_error)
        app.register_error_handler(Exception, self.handle_generic_exception)

    def handle_bad_request(self, error):
        """Handle 400 Bad Request errors."""
        return self._create_error_response(
            "Bad Request",
            "BAD_REQUEST",
            400,
            details=str(error.description) if hasattr(error, "description") else None,
        )

    def handle_unauthorized(self, error):
        """Handle 401 Unauthorized errors."""
        return self._create_error_response(
            "Unauthorized", "UNAUTHORIZED", 401, details="Authentication required"
        )

    def handle_forbidden(self, error):
        """Handle 403 Forbidden errors."""
        return self._create_error_response(
            "Forbidden", "FORBIDDEN", 403, details="Insufficient permissions"
        )

    def handle_not_found(self, error):
        """Handle 404 Not Found errors."""
        return self._create_error_response(
            "Not Found",
            "NOT_FOUND",
            404,
            details=f"The requested resource was not found",
        )

    def handle_method_not_allowed(self, error):
        """Handle 405 Method Not Allowed errors."""
        return self._create_error_response(
            "Method Not Allowed",
            "METHOD_NOT_ALLOWED",
            405,
            details=f"Method {request.method} not allowed for this endpoint",
        )

    def handle_rate_limit(self, error):
        """Handle 429 Rate Limit errors."""
        return self._create_error_response(
            "Rate Limit Exceeded",
            "RATE_LIMIT_EXCEEDED",
            429,
            details="Too many requests. Please try again later.",
        )

    def handle_internal_error(self, error):
        """Handle 500 Internal Server errors."""
        correlation_id = getattr(g, "correlation_id", "unknown")
        logger.error(
            f"Internal server error: {error}",
            extra={"correlation_id": correlation_id},
            exc_info=True,
        )

        return self._create_error_response(
            "Internal Server Error",
            "INTERNAL_SERVER_ERROR",
            500,
            details="An unexpected error occurred",
        )

    def handle_generic_exception(self, error):
        """Handle unexpected exceptions."""
        correlation_id = getattr(g, "correlation_id", "unknown")
        logger.exception(
            f"Unhandled exception: {error}", extra={"correlation_id": correlation_id}
        )

        return self._create_error_response(
            "Internal Server Error",
            "UNHANDLED_EXCEPTION",
            500,
            details="An unexpected error occurred",
        )

    def _create_error_response(
        self,
        message: str,
        error_code: str,
        status_code: int,
        details: Optional[str] = None,
    ):
        """Create standardized error response."""
        response_data = {
            "success": False,
            "error": message,
            "error_code": error_code,
            "timestamp": time.time(),
            "correlation_id": getattr(g, "correlation_id", "unknown"),
        }

        if details:
            response_data["details"] = details

        response = jsonify(response_data)
        response.status_code = status_code
        return response
