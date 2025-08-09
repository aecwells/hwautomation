"""
Template helpers for HWAutomation Web Interface.

This module provides utility functions and filters for Jinja2 templates
used in the web interface.
"""

import datetime
import json
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

from flask import request, url_for

from hwautomation.logging import get_logger

logger = get_logger(__name__)


class TemplateHelpers:
    """
    Collection of template helper functions and filters.

    Features:
    - Date/time formatting
    - Data formatting
    - URL generation
    - Status indicators
    """

    @staticmethod
    def register_helpers(app):
        """Register all template helpers with Flask app."""
        # Register template filters
        app.jinja_env.filters["format_timestamp"] = TemplateHelpers.format_timestamp
        app.jinja_env.filters["format_duration"] = TemplateHelpers.format_duration
        app.jinja_env.filters["format_bytes"] = TemplateHelpers.format_bytes
        app.jinja_env.filters["format_percentage"] = TemplateHelpers.format_percentage
        app.jinja_env.filters["pluralize"] = TemplateHelpers.pluralize
        app.jinja_env.filters["truncate_text"] = TemplateHelpers.truncate_text
        app.jinja_env.filters["status_badge"] = TemplateHelpers.status_badge
        app.jinja_env.filters["json_pretty"] = TemplateHelpers.json_pretty

        # Register global functions
        app.jinja_env.globals["current_time"] = TemplateHelpers.current_time
        app.jinja_env.globals["build_url"] = TemplateHelpers.build_url
        app.jinja_env.globals["get_flash_class"] = TemplateHelpers.get_flash_class
        app.jinja_env.globals["format_server_specs"] = (
            TemplateHelpers.format_server_specs
        )
        app.jinja_env.globals["get_status_icon"] = TemplateHelpers.get_status_icon
        app.jinja_env.globals["format_workflow_progress"] = (
            TemplateHelpers.format_workflow_progress
        )

    @staticmethod
    def format_timestamp(
        timestamp: Union[float, str, None], format_type: str = "human"
    ) -> str:
        """Format timestamp for display."""
        if not timestamp:
            return "Never"

        try:
            if isinstance(timestamp, str):
                if timestamp.isdigit():
                    timestamp = float(timestamp)
                else:
                    # Try to parse ISO format
                    dt = datetime.datetime.fromisoformat(
                        timestamp.replace("Z", "+00:00")
                    )
                    timestamp = dt.timestamp()

            dt = datetime.datetime.fromtimestamp(float(timestamp))

            if format_type == "human":
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            elif format_type == "relative":
                return TemplateHelpers._format_relative_time(timestamp)
            elif format_type == "date":
                return dt.strftime("%Y-%m-%d")
            elif format_type == "time":
                return dt.strftime("%H:%M:%S")
            elif format_type == "iso":
                return dt.isoformat()
            else:
                return str(timestamp)

        except (ValueError, TypeError, OSError):
            return "Invalid date"

    @staticmethod
    def _format_relative_time(timestamp: float) -> str:
        """Format timestamp as relative time (e.g., '5 minutes ago')."""
        now = time.time()
        diff = now - timestamp

        if diff < 60:
            return "Just now"
        elif diff < 3600:
            minutes = int(diff / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif diff < 86400:
            hours = int(diff / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff < 2592000:  # 30 days
            days = int(diff / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            return TemplateHelpers.format_timestamp(timestamp, "date")

    @staticmethod
    def format_duration(seconds: Union[float, int, None]) -> str:
        """Format duration in human-readable format."""
        if seconds is None:
            return "Unknown"

        try:
            seconds = float(seconds)
            if seconds < 1:
                return f"{seconds:.2f}s"
            elif seconds < 60:
                return f"{seconds:.1f}s"
            elif seconds < 3600:
                minutes = seconds / 60
                return f"{minutes:.1f}m"
            elif seconds < 86400:
                hours = seconds / 3600
                return f"{hours:.1f}h"
            else:
                days = seconds / 86400
                return f"{days:.1f}d"
        except (ValueError, TypeError):
            return "Invalid duration"

    @staticmethod
    def format_bytes(
        bytes_value: Union[int, float, None], decimal_places: int = 1
    ) -> str:
        """Format byte values in human-readable format."""
        if bytes_value is None:
            return "Unknown"

        try:
            bytes_value = float(bytes_value)

            for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
                if bytes_value < 1024.0:
                    if unit == "B":
                        return f"{int(bytes_value)} {unit}"
                    else:
                        return f"{bytes_value:.{decimal_places}f} {unit}"
                bytes_value /= 1024.0

            return f"{bytes_value:.{decimal_places}f} EB"

        except (ValueError, TypeError):
            return "Invalid size"

    @staticmethod
    def format_percentage(
        value: Union[float, int, None], decimal_places: int = 1
    ) -> str:
        """Format percentage values."""
        if value is None:
            return "Unknown"

        try:
            value = float(value)
            return f"{value:.{decimal_places}f}%"
        except (ValueError, TypeError):
            return "Invalid percentage"

    @staticmethod
    def pluralize(count: int, singular: str, plural: Optional[str] = None) -> str:
        """Pluralize words based on count."""
        if plural is None:
            plural = singular + "s"

        return singular if count == 1 else plural

    @staticmethod
    def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
        """Truncate text to maximum length."""
        if not text or len(text) <= max_length:
            return text

        return text[: max_length - len(suffix)] + suffix

    @staticmethod
    def status_badge(status: str, additional_classes: str = "") -> str:
        """Generate HTML badge for status display."""
        status_classes = {
            "online": "badge-success",
            "offline": "badge-danger",
            "pending": "badge-warning",
            "running": "badge-info",
            "completed": "badge-success",
            "failed": "badge-danger",
            "cancelled": "badge-secondary",
            "unknown": "badge-secondary",
        }

        status_lower = status.lower()
        badge_class = status_classes.get(status_lower, "badge-secondary")

        if additional_classes:
            badge_class += f" {additional_classes}"

        return f'<span class="badge {badge_class}">{status.title()}</span>'

    @staticmethod
    def json_pretty(data: Any, indent: int = 2) -> str:
        """Format data as pretty-printed JSON."""
        try:
            return json.dumps(data, indent=indent, sort_keys=True, default=str)
        except TypeError:
            return str(data)

    @staticmethod
    def current_time() -> float:
        """Get current timestamp."""
        return time.time()

    @staticmethod
    def build_url(endpoint: str, **kwargs) -> str:
        """Build URL with query parameters."""
        base_url = url_for(endpoint)

        if kwargs:
            query_string = urlencode(kwargs)
            return f"{base_url}?{query_string}"

        return base_url

    @staticmethod
    def get_flash_class(category: str) -> str:
        """Get CSS class for flash message categories."""
        flash_classes = {
            "error": "alert-danger",
            "warning": "alert-warning",
            "info": "alert-info",
            "success": "alert-success",
            "message": "alert-info",
        }

        return flash_classes.get(category, "alert-info")

    @staticmethod
    def format_server_specs(server_data: Dict[str, Any]) -> str:
        """Format server specifications for display."""
        specs = []

        # CPU information
        if server_data.get("cpu_count") and server_data.get("cpu_cores"):
            cpu_info = f"{server_data['cpu_count']}x {server_data['cpu_cores']} cores"
            if server_data.get("cpu_model"):
                cpu_info += f" ({server_data['cpu_model']})"
            specs.append(cpu_info)

        # Memory information
        if server_data.get("memory_gb"):
            memory_info = f"{server_data['memory_gb']} GB RAM"
            specs.append(memory_info)

        # Storage information
        if server_data.get("storage_capacity_gb"):
            storage_info = f"{server_data['storage_capacity_gb']} GB"
            if server_data.get("storage_type"):
                storage_info += f" {server_data['storage_type']}"
            specs.append(storage_info)

        return " | ".join(specs) if specs else "No specifications available"

    @staticmethod
    def get_status_icon(status: str) -> str:
        """Get icon for status display."""
        status_icons = {
            "online": "fas fa-circle text-success",
            "offline": "fas fa-circle text-danger",
            "pending": "fas fa-clock text-warning",
            "running": "fas fa-spinner fa-spin text-info",
            "completed": "fas fa-check-circle text-success",
            "failed": "fas fa-times-circle text-danger",
            "cancelled": "fas fa-ban text-secondary",
            "unknown": "fas fa-question-circle text-secondary",
        }

        status_lower = status.lower()
        icon_class = status_icons.get(
            status_lower, "fas fa-question-circle text-secondary"
        )

        return f'<i class="{icon_class}"></i>'

    @staticmethod
    def format_workflow_progress(workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format workflow progress for template display."""
        progress = workflow_data.get("progress_percentage", 0)
        status = workflow_data.get("status", "unknown")

        # Calculate progress bar class
        if status == "completed":
            progress_class = "progress-bar-success"
        elif status == "failed":
            progress_class = "progress-bar-danger"
        elif status == "running":
            progress_class = (
                "progress-bar-info progress-bar-striped progress-bar-animated"
            )
        else:
            progress_class = "progress-bar-secondary"

        # Format progress text
        if workflow_data.get("current_step") and workflow_data.get("total_steps"):
            progress_text = f"Step {workflow_data['current_step']} of {workflow_data['total_steps']}"
        else:
            progress_text = f"{progress}%"

        return {
            "percentage": progress,
            "class": progress_class,
            "text": progress_text,
            "message": workflow_data.get("progress_message", ""),
        }


class PaginationHelper:
    """
    Helper for pagination display in templates.

    Features:
    - Page number generation
    - Navigation links
    - Page info display
    """

    def __init__(
        self, current_page: int, total_pages: int, per_page: int, total_items: int
    ):
        self.current_page = current_page
        self.total_pages = total_pages
        self.per_page = per_page
        self.total_items = total_items

    def get_page_numbers(self, window_size: int = 5) -> List[int]:
        """Get list of page numbers to display."""
        if self.total_pages <= window_size:
            return list(range(1, self.total_pages + 1))

        # Calculate window around current page
        start = max(1, self.current_page - window_size // 2)
        end = min(self.total_pages, start + window_size - 1)

        # Adjust start if we're near the end
        if end - start < window_size - 1:
            start = max(1, end - window_size + 1)

        return list(range(start, end + 1))

    def has_previous(self) -> bool:
        """Check if there's a previous page."""
        return self.current_page > 1

    def has_next(self) -> bool:
        """Check if there's a next page."""
        return self.current_page < self.total_pages

    def get_previous_page(self) -> Optional[int]:
        """Get previous page number."""
        return self.current_page - 1 if self.has_previous() else None

    def get_next_page(self) -> Optional[int]:
        """Get next page number."""
        return self.current_page + 1 if self.has_next() else None

    def get_item_range(self) -> tuple:
        """Get range of items being displayed."""
        start = (self.current_page - 1) * self.per_page + 1
        end = min(self.current_page * self.per_page, self.total_items)
        return start, end

    def get_info_text(self) -> str:
        """Get pagination info text."""
        if self.total_items == 0:
            return "No items found"

        start, end = self.get_item_range()

        if start == end:
            return f"Showing item {start} of {self.total_items}"
        else:
            return f"Showing items {start}-{end} of {self.total_items}"


class NavigationHelper:
    """
    Helper for navigation menu generation.

    Features:
    - Active page detection
    - Breadcrumb generation
    - Menu structure
    """

    @staticmethod
    def is_active_route(endpoint: str, **kwargs) -> bool:
        """Check if current route matches given endpoint."""
        try:
            return request.endpoint == endpoint
        except (AttributeError, RuntimeError):
            return False

    @staticmethod
    def get_breadcrumbs(
        current_page: str, breadcrumb_map: Dict[str, List[Dict[str, str]]]
    ) -> List[Dict[str, str]]:
        """Generate breadcrumb navigation."""
        breadcrumbs = [{"title": "Home", "url": url_for("web.index")}]

        if current_page in breadcrumb_map:
            breadcrumbs.extend(breadcrumb_map[current_page])

        return breadcrumbs

    @staticmethod
    def get_navigation_menu() -> List[Dict[str, Any]]:
        """Get main navigation menu structure."""
        menu_items = [
            {
                "title": "Dashboard",
                "endpoint": "web.index",
                "icon": "fas fa-tachometer-alt",
                "active": NavigationHelper.is_active_route("web.index"),
            },
            {
                "title": "Servers",
                "endpoint": "web.servers",
                "icon": "fas fa-server",
                "active": NavigationHelper.is_active_route("web.servers"),
                "submenu": [
                    {
                        "title": "All Servers",
                        "endpoint": "web.servers",
                        "active": NavigationHelper.is_active_route("web.servers"),
                    },
                    {
                        "title": "Add Server",
                        "endpoint": "web.add_server",
                        "active": NavigationHelper.is_active_route("web.add_server"),
                    },
                ],
            },
            {
                "title": "Workflows",
                "endpoint": "web.workflows",
                "icon": "fas fa-tasks",
                "active": NavigationHelper.is_active_route("web.workflows"),
            },
            {
                "title": "BIOS Config",
                "endpoint": "web.bios_config",
                "icon": "fas fa-microchip",
                "active": NavigationHelper.is_active_route("web.bios_config"),
            },
            {
                "title": "Logs",
                "endpoint": "web.logs",
                "icon": "fas fa-file-alt",
                "active": NavigationHelper.is_active_route("web.logs"),
            },
        ]

        return menu_items


class FormHelper:
    """
    Helper for form rendering and validation.

    Features:
    - Field rendering
    - Validation error display
    - Form state management
    """

    @staticmethod
    def render_field_errors(field_name: str, errors: Dict[str, List[str]]) -> str:
        """Render validation errors for a field."""
        if field_name not in errors:
            return ""

        error_html = '<div class="invalid-feedback d-block">'
        for error in errors[field_name]:
            error_html += f"<div>{error}</div>"
        error_html += "</div>"

        return error_html

    @staticmethod
    def get_field_class(
        field_name: str, errors: Dict[str, List[str]], base_class: str = "form-control"
    ) -> str:
        """Get CSS class for form field including validation state."""
        classes = [base_class]

        if field_name in errors:
            classes.append("is-invalid")

        return " ".join(classes)

    @staticmethod
    def preserve_form_data(
        field_name: str, form_data: Dict[str, Any], default: str = ""
    ) -> str:
        """Preserve form data on validation errors."""
        return form_data.get(field_name, default)


def register_all_helpers(app):
    """Register all template helpers with Flask app."""
    TemplateHelpers.register_helpers(app)

    # Register helper classes as globals
    app.jinja_env.globals["PaginationHelper"] = PaginationHelper
    app.jinja_env.globals["NavigationHelper"] = NavigationHelper
    app.jinja_env.globals["FormHelper"] = FormHelper

    logger.info("All template helpers registered")
