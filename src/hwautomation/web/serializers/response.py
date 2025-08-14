"""
API response serializers and utilities.

This module provides standardized API response formatting including
success responses, error responses, and pagination support.
"""

import time
from typing import Any, Dict, List, Optional

from .base import BaseSerializer


class APIResponseSerializer:
    """
    Serializer for complete API responses with metadata.

    Features:
    - Response envelope
    - Metadata inclusion
    - Error formatting
    - Pagination support
    """

    @staticmethod
    def success_response(
        data: Any = None,
        message: str = "Success",
        serializer: Optional[BaseSerializer] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create standardized success response."""
        response = {"success": True, "message": message, "timestamp": time.time()}

        if data is not None:
            if serializer:
                response["data"] = serializer.serialize(data)
            else:
                response["data"] = data

        if metadata:
            response["metadata"] = metadata

        return response

    @staticmethod
    def error_response(
        message: str,
        error_code: str,
        details: Optional[str] = None,
        validation_errors: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create standardized error response."""
        response = {
            "success": False,
            "error": message,
            "error_code": error_code,
            "timestamp": time.time(),
        }

        if details:
            response["details"] = details

        if validation_errors:
            response["validation_errors"] = validation_errors

        return response

    @staticmethod
    def paginated_response(
        items: List[Any],
        pagination_info: Dict[str, Any],
        serializer: Optional[BaseSerializer] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create paginated response."""
        if serializer:
            serialized_items = serializer.serialize(items)
        else:
            serialized_items = items

        response = {
            "success": True,
            "data": serialized_items,
            "pagination": pagination_info,
            "timestamp": time.time(),
        }

        if metadata:
            response["metadata"] = metadata

        return response

    @staticmethod
    def validation_response(
        is_valid: bool,
        data: Any = None,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
        serializer: Optional[BaseSerializer] = None,
    ) -> Dict[str, Any]:
        """Create validation response."""
        response = {
            "success": True,
            "valid": is_valid,
            "timestamp": time.time(),
        }

        if data is not None:
            if serializer:
                response["data"] = serializer.serialize(data)
            else:
                response["data"] = data

        if errors:
            response["errors"] = errors

        if warnings:
            response["warnings"] = warnings

        return response

    @staticmethod
    def status_response(
        status: str,
        message: str = "",
        data: Any = None,
        serializer: Optional[BaseSerializer] = None,
    ) -> Dict[str, Any]:
        """Create status response."""
        response = {
            "success": True,
            "status": status,
            "message": message,
            "timestamp": time.time(),
        }

        if data is not None:
            if serializer:
                response["data"] = serializer.serialize(data)
            else:
                response["data"] = data

        return response


class PaginationHelper:
    """Helper for pagination calculations and metadata."""

    @staticmethod
    def calculate_pagination(
        total_items: int,
        page: int = 1,
        per_page: int = 20,
        max_per_page: int = 100,
    ) -> Dict[str, Any]:
        """Calculate pagination metadata."""
        # Validate and adjust parameters
        per_page = min(max(1, per_page), max_per_page)
        page = max(1, page)

        # Calculate pagination values
        total_pages = max(1, (total_items + per_page - 1) // per_page)
        page = min(page, total_pages)

        offset = (page - 1) * per_page
        has_prev = page > 1
        has_next = page < total_pages

        return {
            "page": page,
            "per_page": per_page,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_prev": has_prev,
            "has_next": has_next,
            "prev_page": page - 1 if has_prev else None,
            "next_page": page + 1 if has_next else None,
            "offset": offset,
            "limit": per_page,
        }

    @staticmethod
    def get_pagination_urls(
        base_url: str,
        pagination: Dict[str, Any],
        query_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Optional[str]]:
        """Generate pagination URLs."""
        query_params = query_params or {}

        def build_url(page_num: Optional[int]) -> Optional[str]:
            if page_num is None:
                return None

            params = query_params.copy()
            params["page"] = page_num
            params["per_page"] = pagination["per_page"]

            query_string = "&".join(f"{k}={v}" for k, v in params.items())
            return f"{base_url}?{query_string}"

        return {
            "first": build_url(1),
            "prev": build_url(pagination["prev_page"]),
            "next": build_url(pagination["next_page"]),
            "last": build_url(pagination["total_pages"]),
        }
