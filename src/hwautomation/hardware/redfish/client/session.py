"""Redfish HTTP session management.

This module provides HTTP session management for Redfish operations
with proper authentication, error handling, and connection management.
"""

import json
import time
from typing import Any, Dict, Optional
from urllib.parse import urljoin

import requests
from requests.auth import HTTPBasicAuth

from hwautomation.logging import get_logger
from ..base import (
    BaseRedfishClient,
    RedfishAuthenticationError,
    RedfishConnectionError,
    RedfishCredentials,
    RedfishError,
    RedfishResponse,
)

logger = get_logger(__name__)


class RedfishSession(BaseRedfishClient):
    """Redfish HTTP session management."""

    def __init__(self, credentials: RedfishCredentials):
        """Initialize Redfish session.
        
        Args:
            credentials: Redfish connection credentials
        """
        super().__init__(credentials)
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(credentials.username, credentials.password)
        
        # Configure session
        self.session.verify = credentials.verify_ssl
        self.session.timeout = credentials.timeout
        
        # Set default headers
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
        
        # Build base URL
        protocol = "https" if credentials.use_ssl else "http"
        self.base_url = f"{protocol}://{credentials.host}:{credentials.port}"
        
        logger.info(f"Initialized Redfish session for {credentials.host}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def get(self, uri: str, **kwargs) -> RedfishResponse:
        """Perform GET request.
        
        Args:
            uri: Request URI
            **kwargs: Additional request parameters
            
        Returns:
            Redfish response
        """
        return self._make_request("GET", uri, **kwargs)

    def post(self, uri: str, data: Optional[Dict] = None, **kwargs) -> RedfishResponse:
        """Perform POST request.
        
        Args:
            uri: Request URI
            data: Request data
            **kwargs: Additional request parameters
            
        Returns:
            Redfish response
        """
        return self._make_request("POST", uri, json=data, **kwargs)

    def patch(self, uri: str, data: Optional[Dict] = None, **kwargs) -> RedfishResponse:
        """Perform PATCH request.
        
        Args:
            uri: Request URI
            data: Request data
            **kwargs: Additional request parameters
            
        Returns:
            Redfish response
        """
        return self._make_request("PATCH", uri, json=data, **kwargs)

    def put(self, uri: str, data: Optional[Dict] = None, **kwargs) -> RedfishResponse:
        """Perform PUT request.
        
        Args:
            uri: Request URI
            data: Request data
            **kwargs: Additional request parameters
            
        Returns:
            Redfish response
        """
        return self._make_request("PUT", uri, json=data, **kwargs)

    def delete(self, uri: str, **kwargs) -> RedfishResponse:
        """Perform DELETE request.
        
        Args:
            uri: Request URI
            **kwargs: Additional request parameters
            
        Returns:
            Redfish response
        """
        return self._make_request("DELETE", uri, **kwargs)

    def close(self) -> None:
        """Close the session."""
        if self.session:
            self.session.close()
            logger.debug("Closed Redfish session")

    def _make_request(self, method: str, uri: str, **kwargs) -> RedfishResponse:
        """Make HTTP request to Redfish service.

        Args:
            method: HTTP method
            uri: Request URI
            **kwargs: Additional request parameters

        Returns:
            Redfish response

        Raises:
            RedfishConnectionError: If connection fails
            RedfishAuthenticationError: If authentication fails
            RedfishError: For other HTTP errors
        """
        # Build full URL
        if uri.startswith('http'):
            url = uri
        else:
            url = urljoin(self.base_url, uri.lstrip('/'))

        logger.debug(f"Redfish {method} request to {url}")

        try:
            response = self.session.request(method, url, **kwargs)
            
            # Handle authentication errors
            if response.status_code == 401:
                raise RedfishAuthenticationError(
                    "Authentication failed - invalid credentials",
                    response.status_code
                )
            
            # Parse response data
            response_data = None
            if response.content:
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON response from {url}")
                    response_data = {"raw_content": response.text}

            # Create response object
            redfish_response = RedfishResponse(
                success=response.ok,
                status_code=response.status_code,
                data=response_data,
                headers=dict(response.headers),
            )

            # Handle errors
            if not response.ok:
                error_msg = self._extract_error_message(response_data)
                redfish_response.error_message = error_msg
                
                if response.status_code >= 500:
                    logger.error(f"Server error {response.status_code}: {error_msg}")
                elif response.status_code >= 400:
                    logger.warning(f"Client error {response.status_code}: {error_msg}")

            return redfish_response

        except requests.exceptions.ConnectionError as e:
            raise RedfishConnectionError(f"Connection failed: {e}")
        except requests.exceptions.Timeout as e:
            raise RedfishConnectionError(f"Request timeout: {e}")
        except requests.exceptions.RequestException as e:
            raise RedfishError(f"Request failed: {e}")

    def _extract_error_message(self, response_data: Optional[Dict]) -> str:
        """Extract error message from response data.

        Args:
            response_data: Response JSON data

        Returns:
            Error message string
        """
        if not response_data:
            return "Unknown error"

        # Try different error message fields
        error_fields = [
            "error.message",
            "error.@Message.ExtendedInfo[0].Message",
            "Message",
            "message",
        ]

        for field in error_fields:
            value = self._get_nested_value(response_data, field)
            if value:
                return str(value)

        return "Unknown error"

    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get nested value from dictionary using dot notation.

        Args:
            data: Dictionary to search
            path: Dot-separated path

        Returns:
            Value if found, None otherwise
        """
        try:
            parts = path.split('.')
            current = data
            
            for part in parts:
                if '[' in part and ']' in part:
                    # Handle array indexing like "field[0]"
                    field, index_part = part.split('[', 1)
                    index = int(index_part.rstrip(']'))
                    current = current[field][index]
                else:
                    current = current[part]
                    
            return current
        except (KeyError, IndexError, TypeError, ValueError):
            return None

    def test_connection(self) -> bool:
        """Test connection to Redfish service.

        Returns:
            True if connection successful
        """
        try:
            response = self.get("/redfish/v1/")
            return response.success
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
