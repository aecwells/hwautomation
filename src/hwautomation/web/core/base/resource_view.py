"""
RESTful resource view patterns for HWAutomation web interface.

This module provides BaseResourceView with standard CRUD operations,
resource identification, and validation helpers for RESTful APIs.
"""

import abc
from typing import Any, Dict, Optional

from flask import request

from .api_view import BaseAPIView


class BaseResourceView(BaseAPIView):
    """
    Base class for RESTful resource views.

    Features:
    - CRUD operations
    - Resource identification
    - Validation helpers
    - Common patterns
    """

    resource_name = "resource"

    def get(self, resource_id: Optional[str] = None):
        """Handle GET requests."""
        if resource_id:
            return self.get_single(resource_id)
        else:
            return self.get_list()

    def post(self):
        """Handle POST requests (create)."""
        return self.create()

    def put(self, resource_id: str):
        """Handle PUT requests (update)."""
        return self.update(resource_id)

    def delete(self, resource_id: str):
        """Handle DELETE requests."""
        return self.delete_resource(resource_id)

    @abc.abstractmethod
    def get_single(self, resource_id: str):
        """Get a single resource by ID."""
        pass

    @abc.abstractmethod
    def get_list(self):
        """Get a list of resources."""
        pass

    @abc.abstractmethod
    def create(self):
        """Create a new resource."""
        pass

    @abc.abstractmethod
    def update(self, resource_id: str):
        """Update an existing resource."""
        pass

    @abc.abstractmethod
    def delete_resource(self, resource_id: str):
        """Delete a resource."""
        pass

    def validate_resource_exists(self, resource_id: str) -> bool:
        """Validate that a resource exists."""
        # Override in subclasses with specific validation
        return True

    def get_request_data(self) -> Dict[str, Any]:
        """Get and validate request data."""
        if not request.is_json:
            raise ValueError("Request must be JSON")

        data = request.get_json()
        if data is None:
            raise ValueError("Invalid JSON data")

        return data
