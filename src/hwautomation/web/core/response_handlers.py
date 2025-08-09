"""
Response handlers for HWAutomation Web Interface.

This module provides standardized response handling patterns
for API endpoints and web routes.
"""

import json
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from flask import Response, jsonify, make_response, request

from hwautomation.logging import get_logger

from .serializers import APIResponseSerializer, BaseSerializer

logger = get_logger(__name__)


class BaseResponseHandler:
    """
    Base response handler with common functionality.

    Features:
    - Response formatting
    - Header management
    - CORS support
    - Content negotiation
    """

    def __init__(self, cors_enabled: bool = True):
        self.cors_enabled = cors_enabled
        self.default_headers = {
            "Content-Type": "application/json",
            "X-Powered-By": "HWAutomation",
        }

    def create_response(
        self,
        data: Any,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ) -> Response:
        """Create Flask response with standardized formatting."""
        response_headers = self.default_headers.copy()

        if headers:
            response_headers.update(headers)

        # Handle CORS if enabled
        if self.cors_enabled:
            response_headers.update(self._get_cors_headers())

        # Create response
        if isinstance(data, dict):
            response = make_response(jsonify(data), status_code, response_headers)
        else:
            response = make_response(data, status_code, response_headers)

        return response

    def _get_cors_headers(self) -> Dict[str, str]:
        """Get CORS headers based on request."""
        cors_headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": (
                "Content-Type, Authorization, X-API-Key, X-Correlation-ID, "
                "X-Session-ID, X-Request-ID"
            ),
            "Access-Control-Max-Age": "3600",
        }

        # Handle preflight requests
        if request.method == "OPTIONS":
            cors_headers["Access-Control-Allow-Credentials"] = "true"

        return cors_headers


class APIResponseHandler(BaseResponseHandler):
    """
    Response handler for API endpoints.

    Features:
    - JSON responses
    - Error formatting
    - Validation error handling
    - Pagination support
    """

    def success(
        self,
        data: Any = None,
        message: str = "Success",
        serializer: Optional[BaseSerializer] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status_code: int = 200,
    ) -> Response:
        """Create success response."""
        response_data = APIResponseSerializer.success_response(
            data=data, message=message, serializer=serializer, metadata=metadata
        )

        return self.create_response(response_data, status_code)

    def error(
        self,
        message: str,
        error_code: str,
        status_code: int = 400,
        details: Optional[str] = None,
        validation_errors: Optional[List[str]] = None,
    ) -> Response:
        """Create error response."""
        response_data = APIResponseSerializer.error_response(
            message=message,
            error_code=error_code,
            details=details,
            validation_errors=validation_errors,
        )

        return self.create_response(response_data, status_code)

    def paginated(
        self,
        items: List[Any],
        pagination_info: Dict[str, Any],
        serializer: Optional[BaseSerializer] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Response:
        """Create paginated response."""
        response_data = APIResponseSerializer.paginated_response(
            items=items,
            pagination_info=pagination_info,
            serializer=serializer,
            metadata=metadata,
        )

        return self.create_response(response_data, 200)

    def created(
        self,
        data: Any = None,
        message: str = "Resource created",
        location: Optional[str] = None,
        serializer: Optional[BaseSerializer] = None,
    ) -> Response:
        """Create 201 Created response."""
        response_data = APIResponseSerializer.success_response(
            data=data, message=message, serializer=serializer
        )

        headers = {}
        if location:
            headers["Location"] = location

        return self.create_response(response_data, 201, headers)

    def accepted(
        self,
        data: Any = None,
        message: str = "Request accepted",
        task_id: Optional[str] = None,
    ) -> Response:
        """Create 202 Accepted response for async operations."""
        response_data = APIResponseSerializer.success_response(
            data=data, message=message
        )

        if task_id:
            response_data["task_id"] = task_id

        return self.create_response(response_data, 202)

    def no_content(self, message: str = "No content") -> Response:
        """Create 204 No Content response."""
        return self.create_response("", 204)

    def bad_request(
        self,
        message: str = "Bad request",
        details: Optional[str] = None,
        validation_errors: Optional[List[str]] = None,
    ) -> Response:
        """Create 400 Bad Request response."""
        return self.error(
            message=message,
            error_code="BAD_REQUEST",
            status_code=400,
            details=details,
            validation_errors=validation_errors,
        )

    def unauthorized(self, message: str = "Unauthorized") -> Response:
        """Create 401 Unauthorized response."""
        return self.error(message=message, error_code="UNAUTHORIZED", status_code=401)

    def forbidden(self, message: str = "Forbidden") -> Response:
        """Create 403 Forbidden response."""
        return self.error(message=message, error_code="FORBIDDEN", status_code=403)

    def not_found(self, message: str = "Resource not found") -> Response:
        """Create 404 Not Found response."""
        return self.error(message=message, error_code="NOT_FOUND", status_code=404)

    def method_not_allowed(self, allowed_methods: List[str]) -> Response:
        """Create 405 Method Not Allowed response."""
        headers = {"Allow": ", ".join(allowed_methods)}
        return self.error(
            message="Method not allowed",
            error_code="METHOD_NOT_ALLOWED",
            status_code=405,
        )

    def conflict(self, message: str = "Resource conflict") -> Response:
        """Create 409 Conflict response."""
        return self.error(message=message, error_code="CONFLICT", status_code=409)

    def rate_limited(self, retry_after: Optional[int] = None) -> Response:
        """Create 429 Rate Limited response."""
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)

        response_data = APIResponseSerializer.error_response(
            message="Rate limit exceeded", error_code="RATE_LIMIT_EXCEEDED"
        )

        return self.create_response(response_data, 429, headers)

    def internal_error(self, message: str = "Internal server error") -> Response:
        """Create 500 Internal Server Error response."""
        return self.error(
            message=message, error_code="INTERNAL_SERVER_ERROR", status_code=500
        )


class WebResponseHandler(BaseResponseHandler):
    """
    Response handler for web interface (HTML) endpoints.

    Features:
    - HTML responses
    - Template rendering
    - Flash messages
    - Redirects
    """

    def __init__(self, cors_enabled: bool = False):
        super().__init__(cors_enabled)
        self.default_headers = {
            "Content-Type": "text/html; charset=utf-8",
            "X-Powered-By": "HWAutomation",
        }

    def render_template(self, template_name: str, **context) -> Response:
        """Render HTML template with context."""
        try:
            from flask import render_template

            html_content = render_template(template_name, **context)
            return self.create_response(html_content, 200)
        except Exception as e:
            logger.error(f"Template rendering failed: {e}", exc_info=True)
            return self.error_page("Template rendering failed", 500)

    def redirect(self, location: str, status_code: int = 302) -> Response:
        """Create redirect response."""
        from flask import redirect as flask_redirect

        return flask_redirect(location, code=status_code)

    def error_page(self, message: str, status_code: int = 500) -> Response:
        """Create error page."""
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Error {status_code}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .error {{ color: #d32f2f; }}
                .code {{ font-size: 2em; font-weight: bold; }}
            </style>
        </head>
        <body>
            <h1 class="error">Error <span class="code">{status_code}</span></h1>
            <p>{message}</p>
            <p><a href="/">Return to Home</a></p>
        </body>
        </html>
        """

        return self.create_response(error_html, status_code)


class StreamingResponseHandler:
    """
    Handler for streaming responses.

    Features:
    - Server-sent events
    - File streaming
    - Progress tracking
    - Real-time updates
    """

    @staticmethod
    def create_sse_response(generator_func, **kwargs) -> Response:
        """Create Server-Sent Events response."""

        def event_stream():
            try:
                for data in generator_func(**kwargs):
                    if isinstance(data, dict):
                        json_data = json.dumps(data)
                        yield f"data: {json_data}\n\n"
                    else:
                        yield f"data: {data}\n\n"
            except Exception as e:
                error_data = {
                    "error": "Stream error",
                    "message": str(e),
                    "timestamp": time.time(),
                }
                yield f"data: {json.dumps(error_data)}\n\n"
            finally:
                # Send close event
                yield "event: close\ndata: Stream ended\n\n"

        response = Response(
            event_stream(),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control",
            },
        )

        return response

    @staticmethod
    def create_progress_stream(task_func, task_args=None, task_kwargs=None):
        """Create progress streaming response."""

        def progress_generator():
            args = task_args or []
            kwargs = task_kwargs or {}

            try:
                # Start task
                yield {
                    "status": "started",
                    "message": "Task started",
                    "progress": 0,
                    "timestamp": time.time(),
                }

                # Execute task with progress updates
                for progress_update in task_func(*args, **kwargs):
                    if isinstance(progress_update, dict):
                        progress_update["timestamp"] = time.time()
                        yield progress_update
                    else:
                        yield {
                            "status": "progress",
                            "message": str(progress_update),
                            "timestamp": time.time(),
                        }

                # Task completed
                yield {
                    "status": "completed",
                    "message": "Task completed successfully",
                    "progress": 100,
                    "timestamp": time.time(),
                }

            except Exception as e:
                logger.error(f"Task streaming failed: {e}", exc_info=True)
                yield {
                    "status": "error",
                    "message": f"Task failed: {str(e)}",
                    "error": True,
                    "timestamp": time.time(),
                }

        return StreamingResponseHandler.create_sse_response(progress_generator)

    @staticmethod
    def create_file_stream(
        file_path: str,
        chunk_size: int = 8192,
        mimetype: str = "application/octet-stream",
    ) -> Response:
        """Create file streaming response."""

        def file_generator():
            try:
                with open(file_path, "rb") as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
            except FileNotFoundError:
                logger.error(f"File not found: {file_path}")
                yield b"File not found"
            except Exception as e:
                logger.error(f"File streaming failed: {e}", exc_info=True)
                yield f"Stream error: {str(e)}".encode()

        response = Response(
            file_generator(),
            mimetype=mimetype,
            headers={
                "Content-Disposition": f'attachment; filename="{file_path.split("/")[-1]}"',
                "Cache-Control": "no-cache",
            },
        )

        return response


class ResponseHandlerFactory:
    """
    Factory for creating appropriate response handlers.

    Features:
    - Handler selection
    - Configuration management
    - Context-aware creation
    """

    @staticmethod
    def get_handler(
        handler_type: str = "api", **config
    ) -> Union[BaseResponseHandler, StreamingResponseHandler]:
        """Get response handler by type."""
        if handler_type == "api":
            return APIResponseHandler(**config)
        elif handler_type == "web":
            return WebResponseHandler(**config)
        elif handler_type == "streaming":
            return StreamingResponseHandler()
        else:
            raise ValueError(f"Unknown handler type: {handler_type}")

    @staticmethod
    def from_request() -> BaseResponseHandler:
        """Create handler based on request context."""
        if request.path.startswith("/api/"):
            return APIResponseHandler()
        elif "application/json" in request.headers.get("Accept", ""):
            return APIResponseHandler()
        else:
            return WebResponseHandler()


# Convenience functions for common response patterns
def success_response(data: Any = None, **kwargs) -> Response:
    """Create success response using default API handler."""
    handler = APIResponseHandler()
    return handler.success(data=data, **kwargs)


def error_response(message: str, error_code: str, **kwargs) -> Response:
    """Create error response using default API handler."""
    handler = APIResponseHandler()
    return handler.error(message=message, error_code=error_code, **kwargs)


def paginated_response(
    items: List[Any], pagination_info: Dict[str, Any], **kwargs
) -> Response:
    """Create paginated response using default API handler."""
    handler = APIResponseHandler()
    return handler.paginated(items=items, pagination_info=pagination_info, **kwargs)


def stream_progress(task_func, *args, **kwargs) -> Response:
    """Create progress streaming response."""
    return StreamingResponseHandler.create_progress_stream(task_func, args, kwargs)
