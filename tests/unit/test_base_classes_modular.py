"""
Comprehensive test suite for the modular base classes in hwautomation.web.core.base.

This module tests all the newly refactored base class components:
- BaseAPIView: Core API functionality
- BaseResourceView: RESTful resource patterns
- DatabaseMixin: Database operations
- ValidationMixin: Validation utilities
- CacheMixin: Caching functionality
- TimestampMixin: Time utilities
- BaseResource: Combined functionality
"""

import ipaddress
import time
from unittest.mock import MagicMock, Mock, patch

import pytest
from flask import Flask, g, request

from hwautomation.web.core.base import (
    BaseAPIView,
    BaseResource,
    BaseResourceView,
    CacheMixin,
    DatabaseMixin,
    TimestampMixin,
    ValidationMixin,
)


class TestBaseAPIView:
    """Test suite for BaseAPIView core API functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True

    def test_base_api_view_initialization(self):
        """Test BaseAPIView initializes properly."""
        with self.app.app_context():
            view = BaseAPIView()
            assert hasattr(view, "db_helper")
            assert hasattr(view, "start_time")
            assert view.methods == ["GET", "POST", "PUT", "DELETE"]

    def test_success_response_format(self):
        """Test success response formatting."""
        with self.app.app_context():
            view = BaseAPIView()
            g.correlation_id = "test-correlation-123"

            response, status_code = view.success_response(
                data={"key": "value"}, message="Test success"
            )

            assert status_code == 200
            response_json = response.get_json()
            assert response_json["success"] is True
            assert response_json["message"] == "Test success"
            assert response_json["data"] == {"key": "value"}
            assert response_json["correlation_id"] == "test-correlation-123"
            assert "timestamp" in response_json

    def test_error_response_format(self):
        """Test error response formatting."""
        with self.app.app_context():
            view = BaseAPIView()
            g.correlation_id = "test-correlation-456"

            response, status_code = view.error_response(
                message="Test error",
                error_code="TEST_ERROR",
                status_code=400,
                details="Additional error details",
            )

            assert status_code == 400
            response_json = response.get_json()
            assert response_json["success"] is False
            assert response_json["error"] == "Test error"
            assert response_json["error_code"] == "TEST_ERROR"
            assert response_json["details"] == "Additional error details"
            assert response_json["correlation_id"] == "test-correlation-456"

    def test_pagination_response(self):
        """Test pagination response generation."""
        with self.app.app_context():
            view = BaseAPIView()
            items = list(range(100))  # 100 items

            paginated = view.paginate_response(items, page=2, per_page=10)

            assert len(paginated["items"]) == 10
            assert paginated["pagination"]["page"] == 2
            assert paginated["pagination"]["per_page"] == 10
            assert paginated["pagination"]["total"] == 100
            assert paginated["pagination"]["total_pages"] == 10
            assert paginated["pagination"]["has_next"] is True
            assert paginated["pagination"]["has_prev"] is True
            assert paginated["pagination"]["next_page"] == 3
            assert paginated["pagination"]["prev_page"] == 1

    def test_error_handling_value_error(self):
        """Test ValueError handling."""
        with self.app.app_context():
            view = BaseAPIView()
            error = ValueError("Invalid input")

            response, status_code = view.handle_error(error)

            assert status_code == 400
            response_json = response.get_json()
            assert response_json["error_code"] == "VALIDATION_ERROR"

    def test_error_handling_key_error(self):
        """Test KeyError handling."""
        with self.app.app_context():
            view = BaseAPIView()
            error = KeyError("missing_field")

            response, status_code = view.handle_error(error)

            assert status_code == 400
            response_json = response.get_json()
            assert response_json["error_code"] == "MISSING_FIELD"
            assert "missing_field" in response_json["error"]


class TestBaseResourceView:
    """Test suite for BaseResourceView RESTful patterns."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True

        # Create concrete implementation for testing
        class TestResourceView(BaseResourceView):
            def get_single(self, resource_id):
                return {"id": resource_id, "name": f"Resource {resource_id}"}

            def get_list(self):
                return [
                    {"id": 1, "name": "Resource 1"},
                    {"id": 2, "name": "Resource 2"},
                ]

            def create(self):
                return {"id": 3, "name": "New Resource"}

            def update(self, resource_id):
                return {"id": resource_id, "name": "Updated Resource"}

            def delete_resource(self, resource_id):
                return {"message": f"Resource {resource_id} deleted"}

        self.resource_view = TestResourceView

    def test_get_single_resource(self):
        """Test getting a single resource."""
        with self.app.app_context():
            view = self.resource_view()
            result = view.get("test-123")

            assert result["id"] == "test-123"
            assert result["name"] == "Resource test-123"

    def test_get_resource_list(self):
        """Test getting resource list."""
        with self.app.app_context():
            view = self.resource_view()
            result = view.get()

            assert len(result) == 2
            assert result[0]["id"] == 1
            assert result[1]["id"] == 2

    def test_resource_crud_operations(self):
        """Test CRUD operations."""
        with self.app.app_context():
            view = self.resource_view()

            # Create
            create_result = view.post()
            assert create_result["id"] == 3

            # Update
            update_result = view.put("test-456")
            assert update_result["id"] == "test-456"
            assert "Updated" in update_result["name"]

            # Delete
            delete_result = view.delete("test-789")
            assert "deleted" in delete_result["message"]

    def test_get_request_data_json(self):
        """Test getting JSON request data."""

        # Create a concrete resource view instance
        class TestResourceView(BaseResourceView):
            def get(self, resource_id=None):
                return {}

            def get_list(self):
                return []

            def create(self):
                return {}

            def update(self, resource_id):
                return {}

            def delete_resource(self, resource_id):
                return {}

        with self.app.test_request_context(
            "/test", json={"key": "value"}, content_type="application/json"
        ):
            resource_view = TestResourceView()
            data = resource_view.get_request_data()
            assert data == {"key": "value"}

    def test_get_request_data_not_json(self):
        """Test handling non-JSON request data."""

        # Create a concrete resource view instance
        class TestResourceView(BaseResourceView):
            def get(self, resource_id=None):
                return {}

            def get_list(self):
                return []

            def create(self):
                return {}

            def update(self, resource_id):
                return {}

            def delete_resource(self, resource_id):
                return {}

        with self.app.test_request_context("/test", data="form_data"):
            resource_view = TestResourceView()

            # This should raise a ValueError since it's not JSON
            with pytest.raises(ValueError, match="Request must be JSON"):
                resource_view.get_request_data()


class TestDatabaseMixin:
    """Test suite for DatabaseMixin database functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db_helper = Mock()
        self.mock_connection = Mock()
        self.mock_cursor = Mock()

        # Properly mock the context manager
        self.mock_db_helper.get_connection.return_value = MagicMock()
        self.mock_db_helper.get_connection.return_value.__enter__.return_value = (
            self.mock_connection
        )
        self.mock_db_helper.get_connection.return_value.__exit__.return_value = None

        self.mock_connection.cursor.return_value = self.mock_cursor

        self.database_mixin = DatabaseMixin()
        self.database_mixin.db_helper = self.mock_db_helper
        self.mock_connection = Mock()
        self.mock_cursor = Mock()

        self.mock_db_helper.get_connection.return_value.__enter__.return_value = (
            self.mock_connection
        )
        self.mock_connection.cursor.return_value = self.mock_cursor

        class TestDatabaseClass(DatabaseMixin):
            def __init__(self, mock_db_helper):
                self.db_helper = mock_db_helper

        self.test_class = TestDatabaseClass(self.mock_db_helper)

    def test_database_mixin_initialization(self):
        """Test DatabaseMixin initializes properly."""

        class NewClass(DatabaseMixin):
            pass

        instance = NewClass()
        assert hasattr(instance, "db_helper")

    def test_execute_query_fetch_all(self):
        """Test query execution with fetch all."""
        self.mock_cursor.fetchall.return_value = [("row1",), ("row2",)]

        result = self.test_class.execute_query("SELECT * FROM test")

        self.mock_cursor.execute.assert_called_once_with("SELECT * FROM test", ())
        self.mock_cursor.fetchall.assert_called_once()
        assert result == [("row1",), ("row2",)]

    def test_execute_query_fetch_one(self):
        """Test query execution with fetch one."""
        self.mock_cursor.fetchone.return_value = ("single_row",)

        result = self.test_class.execute_query(
            "SELECT * FROM test WHERE id = ?", (123,), fetch_one=True
        )

        self.mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM test WHERE id = ?", (123,)
        )
        self.mock_cursor.fetchone.assert_called_once()
        assert result == ("single_row",)

    def test_execute_query_no_fetch(self):
        """Test query execution without fetching."""
        self.mock_cursor.rowcount = 3

        result = self.test_class.execute_query(
            "UPDATE test SET name = ?", ("new_name",), fetch_all=False
        )

        self.mock_cursor.execute.assert_called_once()
        assert result == 3

    def test_execute_many(self):
        """Test batch query execution."""
        self.mock_cursor.rowcount = 5
        params_list = [("name1",), ("name2",), ("name3",)]

        result = self.test_class.execute_many(
            "INSERT INTO test (name) VALUES (?)", params_list
        )

        self.mock_cursor.executemany.assert_called_once_with(
            "INSERT INTO test (name) VALUES (?)", params_list
        )
        assert result == 5

    def test_get_table_info(self):
        """Test table schema information retrieval."""
        # Mock PRAGMA table_info response
        self.mock_cursor.fetchall.return_value = [
            (0, "id", "INTEGER", 1, None, 1),
            (1, "name", "TEXT", 0, None, 0),
            (2, "created_at", "TIMESTAMP", 0, "CURRENT_TIMESTAMP", 0),
        ]

        result = self.test_class.get_table_info("test_table")

        assert len(result) == 3
        assert result[0]["name"] == "id"
        assert result[0]["type"] == "INTEGER"
        assert result[0]["primary_key"] is True
        assert result[1]["name"] == "name"
        assert result[1]["not_null"] is False


class TestValidationMixin:
    """Test suite for ValidationMixin validation utilities."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = ValidationMixin()

    def test_validate_required_fields(self):
        """Test required field validation."""
        data = {"name": "test", "email": "test@example.com"}
        required = ["name", "email", "phone"]

        missing = self.validator.validate_required_fields(data, required)

        assert missing == ["phone"]

    def test_validate_required_fields_empty_values(self):
        """Test required field validation with empty values."""
        data = {"name": "", "email": None, "phone": "123-456-7890"}
        required = ["name", "email", "phone"]

        missing = self.validator.validate_required_fields(data, required)

        assert set(missing) == {"name", "email"}

    def test_validate_field_types(self):
        """Test field type validation."""
        data = {"count": 42, "rate": 3.14, "name": "test", "active": True}
        types = {"count": int, "rate": float, "name": str, "active": bool}

        errors = self.validator.validate_field_types(data, types)

        assert len(errors) == 0

    def test_validate_field_types_invalid(self):
        """Test field type validation with invalid types."""
        data = {"count": "not_a_number", "rate": "not_a_float"}
        types = {"count": int, "rate": float}

        errors = self.validator.validate_field_types(data, types)

        assert len(errors) == 2
        assert "count must be int" in errors
        assert "rate must be float" in errors

    def test_validate_string_length(self):
        """Test string length validation."""
        data = {"short": "hi", "medium": "hello", "long": "hello world"}
        rules = {
            "short": {"min": 1, "max": 5},
            "medium": {"min": 3, "max": 10},
            "long": {"min": 5, "max": 8},
        }

        errors = self.validator.validate_string_length(data, rules)

        assert len(errors) == 1
        assert "long must be at most 8 characters" in errors

    def test_validate_ip_address_valid(self):
        """Test valid IP address validation."""
        assert self.validator.validate_ip_address("192.168.1.1") is True
        assert self.validator.validate_ip_address("10.0.0.1") is True
        assert self.validator.validate_ip_address("2001:db8::1") is True

    def test_validate_ip_address_invalid(self):
        """Test invalid IP address validation."""
        assert self.validator.validate_ip_address("not.an.ip") is False
        assert self.validator.validate_ip_address("999.999.999.999") is False
        assert self.validator.validate_ip_address("") is False

    def test_validate_server_id(self):
        """Test server ID validation."""
        assert self.validator.validate_server_id("server-123") is True
        assert self.validator.validate_server_id("SERVER_456") is True
        assert self.validator.validate_server_id("server123") is True

        assert self.validator.validate_server_id("server@123") is False
        assert self.validator.validate_server_id("server 123") is False

    def test_validate_device_type(self):
        """Test device type validation."""
        # New format
        assert self.validator.validate_device_type("a1.c5.large") is True
        assert self.validator.validate_device_type("d2.c8.medium") is True

        # Legacy format
        assert self.validator.validate_device_type("s2_c2_small") is True
        assert self.validator.validate_device_type("s1_c4_large") is True

        # Invalid
        assert self.validator.validate_device_type("invalid") is False
        assert self.validator.validate_device_type("a1.c5.invalid") is False

    def test_validate_workflow_status(self):
        """Test workflow status validation."""
        valid_statuses = ["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"]

        for status in valid_statuses:
            assert self.validator.validate_workflow_status(status) is True

        assert self.validator.validate_workflow_status("INVALID") is False

    def test_validate_email(self):
        """Test email validation."""
        assert self.validator.validate_email("test@example.com") is True
        assert self.validator.validate_email("user+tag@domain.co.uk") is True

        assert self.validator.validate_email("invalid-email") is False
        assert self.validator.validate_email("@domain.com") is False

    def test_validate_url(self):
        """Test URL validation."""
        assert self.validator.validate_url("https://example.com") is True
        assert self.validator.validate_url("http://localhost:8080") is True

        assert self.validator.validate_url("not-a-url") is False
        assert self.validator.validate_url("ftp://example.com") is False


class TestCacheMixin:
    """Test suite for CacheMixin caching functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.cache = CacheMixin()

    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        self.cache.cache_set("test_key", "test_value")

        result = self.cache.cache_get("test_key")
        assert result == "test_value"

    def test_cache_get_nonexistent(self):
        """Test getting non-existent cache key."""
        result = self.cache.cache_get("nonexistent_key")
        assert result is None

    def test_cache_ttl_expiry(self):
        """Test cache TTL expiry."""
        self.cache.cache_set("expiring_key", "expiring_value")

        # Should be valid immediately
        result = self.cache.cache_get("expiring_key", ttl=1)
        assert result == "expiring_value"

        # Mock time passage
        current_time = time.time()
        with patch("time.time") as mock_time:
            mock_time.return_value = current_time + 2  # 2 seconds later

            result = self.cache.cache_get("expiring_key", ttl=1)
            assert result is None

    def test_cache_delete(self):
        """Test cache deletion."""
        self.cache.cache_set("delete_me", "value")

        # Verify it exists
        assert self.cache.cache_get("delete_me") == "value"

        # Delete and verify
        deleted = self.cache.cache_delete("delete_me")
        assert deleted is True
        assert self.cache.cache_get("delete_me") is None

        # Try deleting non-existent
        deleted = self.cache.cache_delete("nonexistent")
        assert deleted is False

    def test_cache_clear(self):
        """Test clearing all cache entries."""
        self.cache.cache_set("key1", "value1")
        self.cache.cache_set("key2", "value2")

        self.cache.cache_clear()

        assert self.cache.cache_get("key1") is None
        assert self.cache.cache_get("key2") is None

    def test_cache_cleanup(self):
        """Test cache cleanup of expired entries."""
        current_time = time.time()

        with patch("time.time", return_value=current_time):
            self.cache.cache_set("fresh_key", "fresh_value")

        with patch("time.time", return_value=current_time - 400):  # 400 seconds ago
            self.cache.cache_set("old_key", "old_value")

        # Run cleanup with 5-minute TTL
        with patch("time.time", return_value=current_time):
            removed_count = self.cache.cache_cleanup(ttl=300)

        assert removed_count == 1
        assert self.cache.cache_get("fresh_key") == "fresh_value"
        assert self.cache.cache_get("old_key") is None

    def test_cache_stats(self):
        """Test cache statistics."""
        # Empty cache
        stats = self.cache.cache_stats()
        assert stats["total_entries"] == 0

        # Add some entries
        self.cache.cache_set("key1", "value1")
        self.cache.cache_set("key2", "value2")

        stats = self.cache.cache_stats()
        assert stats["total_entries"] == 2
        assert stats["valid_entries"] <= 2
        assert "memory_usage_kb" in stats

    def test_cache_has(self):
        """Test cache existence check."""
        assert self.cache.cache_has("nonexistent") is False

        self.cache.cache_set("exists", "value")
        assert self.cache.cache_has("exists") is True


class TestTimestampMixin:
    """Test suite for TimestampMixin time utilities."""

    def setup_method(self):
        """Set up test fixtures."""
        self.timestamp_util = TimestampMixin()

    def test_current_timestamp(self):
        """Test current timestamp generation."""
        timestamp = self.timestamp_util.current_timestamp()

        assert isinstance(timestamp, float)
        assert timestamp > 0
        assert abs(timestamp - time.time()) < 1  # Should be very recent

    def test_format_timestamp_default(self):
        """Test timestamp formatting with default format."""
        test_timestamp = 1692000000.0  # Fixed timestamp for testing

        formatted = self.timestamp_util.format_timestamp(test_timestamp)

        # Should return string representation of timestamp for default format
        assert isinstance(formatted, str)

    def test_format_timestamp_iso(self):
        """Test ISO format timestamp."""
        test_timestamp = 1692000000.0

        formatted = self.timestamp_util.format_timestamp(
            test_timestamp, format_str="iso"
        )

        assert "2023-08-14" in formatted  # Should contain the date
        assert "T" in formatted  # ISO format separator

    def test_parse_timestamp_iso(self):
        """Test parsing ISO format timestamp."""
        iso_string = "2023-08-14T12:00:00"

        parsed = self.timestamp_util.parse_timestamp(iso_string)

        assert isinstance(parsed, float)
        assert parsed > 0

    def test_parse_timestamp_invalid(self):
        """Test parsing invalid timestamp."""
        with pytest.raises(ValueError, match="Unable to parse timestamp"):
            self.timestamp_util.parse_timestamp("invalid-timestamp")

    def test_duration_since(self):
        """Test duration calculation."""
        past_timestamp = time.time() - 100  # 100 seconds ago

        duration = self.timestamp_util.duration_since(past_timestamp)

        assert duration >= 100
        assert duration < 105  # Should be close to 100

    def test_format_duration(self):
        """Test duration formatting."""
        assert "30.0s" in self.timestamp_util.format_duration(30)
        assert "2.0m" in self.timestamp_util.format_duration(120)
        assert "1.0h" in self.timestamp_util.format_duration(3600)

    def test_time_ago(self):
        """Test 'time ago' formatting."""
        current = time.time()

        assert "30 seconds ago" in self.timestamp_util.time_ago(current - 30)
        assert "2 minutes ago" in self.timestamp_util.time_ago(current - 120)
        assert "1 hour ago" in self.timestamp_util.time_ago(current - 3600)
        assert "1 day ago" in self.timestamp_util.time_ago(current - 86400)

    def test_is_timestamp_recent(self):
        """Test recent timestamp check."""
        current = time.time()

        assert (
            self.timestamp_util.is_timestamp_recent(current - 100, max_age_seconds=300)
            is True
        )
        assert (
            self.timestamp_util.is_timestamp_recent(current - 400, max_age_seconds=300)
            is False
        )

    def test_timestamp_date_time_conversion(self):
        """Test timestamp to date/time conversion."""
        test_timestamp = 1692000000.0  # 2023-08-14 12:00:00 UTC

        date_str = self.timestamp_util.timestamp_to_date(test_timestamp)
        time_str = self.timestamp_util.timestamp_to_time(test_timestamp)

        assert "2023-08-14" in date_str
        assert ":" in time_str  # Should contain time separators

    def test_start_end_of_day(self):
        """Test start and end of day calculations."""
        test_timestamp = 1692054321.0  # Some timestamp in the middle of a day

        start = self.timestamp_util.start_of_day(test_timestamp)
        end = self.timestamp_util.end_of_day(test_timestamp)

        assert start < test_timestamp < end
        assert end - start < 86400  # Less than 24 hours
        assert end - start > 86399  # But very close to 24 hours


class TestBaseResource:
    """Test suite for BaseResource combined functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config["TESTING"] = True

        # Create concrete implementation for testing
        class TestResource(BaseResource):
            def get_single(self, resource_id):
                return self.success_response({"id": resource_id})

            def get_list(self):
                return self.success_response([{"id": 1}, {"id": 2}])

            def create(self):
                return self.success_response({"id": "new"})

            def update(self, resource_id):
                return self.success_response({"id": resource_id, "updated": True})

            def delete_resource(self, resource_id):
                return self.success_response({"deleted": resource_id})

        self.resource_class = TestResource

    def test_base_resource_initialization(self):
        """Test BaseResource initializes with all mixins."""
        with self.app.app_context():
            resource = self.resource_class()

            # Should have all mixin capabilities
            assert hasattr(resource, "validate_ip_address")  # ValidationMixin
            assert hasattr(resource, "cache_set")  # CacheMixin
            assert hasattr(resource, "current_timestamp")  # TimestampMixin
            assert hasattr(resource, "execute_query")  # DatabaseMixin
            assert hasattr(resource, "success_response")  # BaseAPIView
            assert hasattr(resource, "get_single")  # BaseResourceView

    def test_base_resource_combined_functionality(self):
        """Test BaseResource uses all mixin functionality together."""
        with self.app.app_context():
            resource = self.resource_class()

            # Test validation
            valid_ip = resource.validate_ip_address("192.168.1.1")
            assert valid_ip is True

            # Test caching
            resource.cache_set("test_key", "test_value")
            cached = resource.cache_get("test_key")
            assert cached == "test_value"

            # Test timestamp
            timestamp = resource.current_timestamp()
            assert isinstance(timestamp, float)

            # Test response formatting
            response, status = resource.success_response({"test": "data"})
            assert status == 200

    def test_get_cached_or_fetch(self):
        """Test the get_cached_or_fetch utility method."""
        with self.app.app_context():
            resource = self.resource_class()

            # Mock fetch function
            fetch_func = Mock(return_value="fetched_value")

            # First call should fetch and cache
            result = resource.get_cached_or_fetch("test_cache_key", fetch_func)

            assert result == "fetched_value"
            fetch_func.assert_called_once()

            # Second call should use cache
            fetch_func.reset_mock()
            result = resource.get_cached_or_fetch("test_cache_key", fetch_func)

            assert result == "fetched_value"
            fetch_func.assert_not_called()  # Should not fetch again

    def test_multiple_inheritance_method_resolution(self):
        """Test that multiple inheritance method resolution works correctly."""
        with self.app.app_context():
            resource = self.resource_class()

            # Test that methods from different mixins are accessible
            # and don't conflict with each other

            # From ValidationMixin
            assert callable(resource.validate_ip_address)

            # From CacheMixin
            assert callable(resource.cache_set)

            # From TimestampMixin
            assert callable(resource.current_timestamp)

            # From DatabaseMixin
            assert callable(resource.execute_query)

            # From BaseAPIView
            assert callable(resource.success_response)

            # From BaseResourceView
            assert callable(resource.get_single)


class TestBackwardCompatibility:
    """Test suite for backward compatibility of refactored base classes."""

    def test_base_classes_import_compatibility(self):
        """Test that old imports still work with deprecation warning."""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # This should work but generate a deprecation warning
            from hwautomation.web.core.base_classes import (
                BaseResource as OldBaseResource,
            )

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message)

    def test_backward_compatible_functionality(self):
        """Test that old import provides same functionality."""
        from hwautomation.web.core.base import BaseResource as NewBaseResource
        from hwautomation.web.core.base_classes import BaseResource as OldBaseResource

        # Should be the same class
        assert OldBaseResource is NewBaseResource

        # Should have same functionality
        old_instance = OldBaseResource()
        new_instance = NewBaseResource()

        assert type(old_instance) is type(new_instance)
        assert hasattr(old_instance, "validate_ip_address")
        assert hasattr(old_instance, "cache_set")
        assert hasattr(old_instance, "current_timestamp")


if __name__ == "__main__":
    pytest.main([__file__])
