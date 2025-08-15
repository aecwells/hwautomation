"""
Base API view functionality for the HWAutomation web interface.

This module provides the core BaseAPIView class with standard request handling,
response formatting, error management, and logging integration.
"""

import os
import time
from typing import Any, Dict, List, Optional, Tuple

from flask import g, jsonify, request
from flask.views import View

from hwautomation.database import DbHelper
from hwautomation.logging import get_logger

logger = get_logger(__name__)


class BaseAPIView(View):
    """
    Base class for all API views with common functionality.

    Features:
    - Standard response formatting
    - Error handling
    - Pagination support
    - Request validation
    - Logging integration
    """

    methods = ["GET", "POST", "PUT", "DELETE"]

    def __init__(self):
        # Use DATABASE_PATH from environment, defaulting to data/hw_automation.db
        db_path = os.getenv("DATABASE_PATH", "data/hw_automation.db")
        self.db_helper = DbHelper(db_path)
        self.start_time = time.time()

    def dispatch_request(self, *args, **kwargs):
        """Handle request dispatch with common processing."""
        try:
            # Log request start
            logger.info(
                f"API request started: {request.method} {request.endpoint}",
                extra={
                    "endpoint": request.endpoint,
                    "method": request.method,
                    "args": args,
                    "kwargs": kwargs,
                },
            )

            # Set correlation ID for request tracking
            if not hasattr(g, "correlation_id"):
                g.correlation_id = f"{int(time.time())}-{id(request)}"

            # Call the appropriate method
            method_name = request.method.lower()
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                result = method(*args, **kwargs)
            else:
                result = self.method_not_allowed()

            # Log request completion
            duration = time.time() - self.start_time
            logger.info(
                f"API request completed: {request.method} {request.endpoint}",
                extra={
                    "endpoint": request.endpoint,
                    "method": request.method,
                    "duration": duration,
                    "status": "success",
                },
            )

            return result

        except Exception as e:
            # Log error and return standardized error response
            duration = time.time() - self.start_time
            logger.error(
                f"API request failed: {request.method} {request.endpoint}",
                extra={
                    "endpoint": request.endpoint,
                    "method": request.method,
                    "duration": duration,
                    "error": str(e),
                },
                exc_info=True,
            )
            return self.handle_error(e)

    def method_not_allowed(self):
        """Handle method not allowed errors."""
        return self.error_response("Method not allowed", "METHOD_NOT_ALLOWED", 405)

    def handle_error(self, error: Exception):
        """Handle exceptions and return appropriate error responses."""
        if isinstance(error, ValueError):
            return self.error_response(str(error), "VALIDATION_ERROR", 400)
        elif isinstance(error, KeyError):
            return self.error_response(
                f"Missing required field: {error}", "MISSING_FIELD", 400
            )
        elif isinstance(error, PermissionError):
            return self.error_response("Access denied", "ACCESS_DENIED", 403)
        elif isinstance(error, FileNotFoundError):
            return self.error_response("Resource not found", "NOT_FOUND", 404)
        else:
            # Log unexpected errors with full stack trace
            logger.error(f"Unexpected error in API view: {error}", exc_info=True)
            return self.error_response(
                "Internal server error", "INTERNAL_SERVER_ERROR", 500
            )

    def success_response(
        self,
        data: Any = None,
        message: str = "Success",
        status_code: int = 200,
        **kwargs,
    ) -> Tuple[Dict, int]:
        """Create standardized success response."""
        response_data = {
            "success": True,
            "message": message,
            "timestamp": time.time(),
            "correlation_id": getattr(g, "correlation_id", "unknown"),
        }

        if data is not None:
            response_data["data"] = data

        # Add any additional fields
        response_data.update(kwargs)

        return jsonify(response_data), status_code

    def error_response(
        self,
        message: str,
        error_code: str,
        status_code: int,
        details: Optional[str] = None,
        **kwargs,
    ) -> Tuple[Dict, int]:
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

        # Add any additional fields
        response_data.update(kwargs)

        return jsonify(response_data), status_code

    def paginate_response(
        self,
        items: List[Any],
        page: int = 1,
        per_page: int = 50,
        total: Optional[int] = None,
    ) -> Dict:
        """Create paginated response."""
        if total is None:
            total = len(items)

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_items = items[start_idx:end_idx]

        total_pages = (total + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1

        return {
            "items": page_items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
                "next_page": page + 1 if has_next else None,
                "prev_page": page - 1 if has_prev else None,
            },
        }
