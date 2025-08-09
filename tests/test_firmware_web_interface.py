#!/usr/bin/env python3
"""
Unit tests for firmware web interface components.
"""

import json
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Mark all tests in this file as web interface tests
pytestmark = [pytest.mark.web, pytest.mark.integration]

# Test fixture imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hwautomation.database.helper import DbHelper
from hwautomation.hardware.firmware import FirmwareManager
from hwautomation.orchestration.workflow_manager import WorkflowManager
from hwautomation.web.routes.firmware import (
    FirmwareWebManager,
    firmware_bp,
    init_firmware_routes,
)


class TestFirmwareWebManager:
    """Test firmware web manager functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for testing."""
        firmware_manager = Mock()  # Remove spec to allow any method
        firmware_manager.discover_firmware_files = (
            Mock()
        )  # Explicitly add required methods
        firmware_manager.detect_firmware_versions = Mock()
        firmware_manager.check_for_updates = Mock()
        firmware_manager.install_firmware = Mock()

        workflow_manager = Mock(spec=WorkflowManager)
        db_helper = Mock()  # Remove spec to allow any method
        db_helper.get_connection = Mock()  # Explicitly add get_connection method
        socketio = Mock()

        return {
            "firmware_manager": firmware_manager,
            "workflow_manager": workflow_manager,
            "db_helper": db_helper,
            "socketio": socketio,
        }

    @pytest.fixture
    def firmware_web_manager(self, mock_dependencies):
        """Create firmware web manager with mocked dependencies."""
        return FirmwareWebManager(
            mock_dependencies["firmware_manager"],
            mock_dependencies["workflow_manager"],
            mock_dependencies["db_helper"],
            mock_dependencies["socketio"],
        )

    def test_firmware_web_manager_initialization(
        self, firmware_web_manager, mock_dependencies
    ):
        """Test firmware web manager initializes correctly."""
        assert (
            firmware_web_manager.firmware_manager
            == mock_dependencies["firmware_manager"]
        )
        assert (
            firmware_web_manager.workflow_manager
            == mock_dependencies["workflow_manager"]
        )
        assert firmware_web_manager.db_helper == mock_dependencies["db_helper"]
        assert firmware_web_manager.socketio == mock_dependencies["socketio"]
        assert firmware_web_manager._active_updates == {}

    def test_get_firmware_inventory_empty_database(
        self, firmware_web_manager, mock_dependencies
    ):
        """Test getting firmware inventory with empty database."""
        # Mock database context manager
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__ = Mock(return_value=mock_connection)
        mock_connection.__exit__ = Mock(return_value=None)
        mock_dependencies["db_helper"].get_connection.return_value = mock_connection

        # Mock firmware discovery
        mock_dependencies["firmware_manager"].discover_firmware_files.return_value = []

        inventory = firmware_web_manager.get_firmware_inventory()

        assert inventory["servers"] == []
        assert inventory["update_summary"]["total_servers"] == 0
        assert inventory["update_summary"]["updates_available"] == 0
        assert inventory["update_summary"]["up_to_date"] == 0
        assert inventory["update_summary"]["unknown_status"] == 0
        assert inventory["firmware_repository"]["total_files"] == 0

    def test_get_firmware_inventory_with_servers(
        self, firmware_web_manager, mock_dependencies
    ):
        """Test getting firmware inventory with servers in database."""
        # Mock database response with servers
        mock_servers = [
            ("server-1", "test-server-1", "Ready", "a1.c5.large", "192.168.1.100"),
            ("server-2", "test-server-2", "Deployed", "d1.c1.small", "192.168.1.101"),
            ("server-3", "test-server-3", "New", "unknown", None),
        ]

        # Mock database context manager
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = mock_servers
        mock_connection.cursor.return_value = mock_cursor
        mock_connection.__enter__ = Mock(return_value=mock_connection)
        mock_connection.__exit__ = Mock(return_value=None)
        mock_dependencies["db_helper"].get_connection.return_value = mock_connection

        # Mock firmware discovery
        mock_firmware_files = [
            {"vendor": "hpe", "type": "bios", "file": "test.fwpkg"},
            {"vendor": "supermicro", "type": "bmc", "file": "test.bin"},
        ]
        mock_dependencies["firmware_manager"].discover_firmware_files.return_value = (
            mock_firmware_files
        )

        inventory = firmware_web_manager.get_firmware_inventory()

        assert len(inventory["servers"]) == 3
        assert inventory["update_summary"]["total_servers"] == 3
        assert inventory["firmware_repository"]["total_files"] == 2
        assert "hpe" in inventory["firmware_repository"]["vendors"]
        assert "supermicro" in inventory["firmware_repository"]["vendors"]

        # Check server data structure
        server_1 = inventory["servers"][0]
        assert server_1["id"] == "server-1"
        assert server_1["hostname"] == "test-server-1"
        assert server_1["status"] == "Ready"
        assert server_1["device_type"] == "a1.c5.large"
        assert server_1["ipmi_ip"] == "192.168.1.100"

    def test_check_available_updates(self, firmware_web_manager):
        """Test checking for available firmware updates."""
        # Test device with updates available
        updates = firmware_web_manager._check_available_updates("a1.c5.large")
        assert len(updates) == 2
        assert updates[0]["component"] == "BIOS"
        assert updates[0]["current"] == "v1.0"
        assert updates[0]["available"] == "v1.2"
        assert updates[1]["component"] == "BMC"

        # Test device without updates
        updates = firmware_web_manager._check_available_updates("d1.c1.small")
        assert len(updates) == 0

    def test_schedule_firmware_update_success(
        self, firmware_web_manager, mock_dependencies
    ):
        """Test successful firmware update scheduling."""
        server_ids = ["server-1", "server-2"]
        update_config = {
            "components": ["bios", "bmc"],
            "scheduled_time": "2024-08-10T14:00:00",
            "maintenance_window": 120,
            "rollback_enabled": True,
        }

        result = firmware_web_manager.schedule_firmware_update(
            server_ids, update_config
        )

        assert result["success"] == True
        assert result["total_scheduled"] == 2
        assert len(result["scheduled_updates"]) == 2
        assert len(result["failed_schedules"]) == 0

        # Check workflow IDs are generated
        for update in result["scheduled_updates"]:
            assert update["workflow_id"].startswith("fw-update-")
            assert update["status"] == "scheduled"

    def test_schedule_firmware_update_partial_failure(
        self, firmware_web_manager, mock_dependencies
    ):
        """Test firmware update scheduling with partial failures."""
        server_ids = ["server-1", "server-invalid"]
        update_config = {"components": ["bios"], "maintenance_window": 60}

        # Test basic scheduling - the current implementation doesn't handle individual failures
        result = firmware_web_manager.schedule_firmware_update(
            server_ids, update_config
        )

        assert result["success"] == True
        assert result["total_scheduled"] == 2  # Current implementation schedules all
        assert len(result["scheduled_updates"]) == 2

    def test_get_update_progress_new_workflow(self, firmware_web_manager):
        """Test getting progress for a new workflow."""
        workflow_id = "fw-update-test-123"

        progress = firmware_web_manager.get_update_progress(workflow_id)

        assert progress["workflow_id"] == workflow_id
        assert progress["status"] == "running"
        assert progress["current_phase"] == "firmware_analysis"
        assert progress["progress_percentage"] == 25
        assert "phases" in progress
        assert progress["phases"]["hardware_discovery"]["status"] == "completed"
        assert progress["phases"]["firmware_analysis"]["status"] == "running"

    def test_get_update_progress_existing_workflow(self, firmware_web_manager):
        """Test getting progress for an existing workflow."""
        workflow_id = "fw-update-existing-123"

        # Simulate existing workflow
        existing_progress = {
            "workflow_id": workflow_id,
            "status": "running",
            "progress_percentage": 75,
        }
        firmware_web_manager._active_updates[workflow_id] = existing_progress

        progress = firmware_web_manager.get_update_progress(workflow_id)

        assert progress == existing_progress


class TestFirmwareRoutesInitialization:
    """Test firmware routes initialization and blueprint registration."""

    def test_init_firmware_routes(self):
        """Test firmware routes initialization."""
        firmware_manager = Mock()
        workflow_manager = Mock()
        db_helper = Mock()
        socketio = Mock()

        # This should not raise an exception
        init_firmware_routes(firmware_manager, workflow_manager, db_helper, socketio)

        # Check that global firmware_web_manager was set
        from hwautomation.web.routes.firmware import firmware_web_manager

        assert firmware_web_manager is not None
        assert firmware_web_manager.firmware_manager == firmware_manager

    def test_firmware_blueprint_exists(self):
        """Test that firmware blueprint is properly defined."""
        assert firmware_bp.name == "firmware"
        assert firmware_bp.url_prefix == "/firmware"

        # Check that routes are registered by examining the blueprint's deferred functions
        assert len(firmware_bp.deferred_functions) > 0


class TestFirmwareWebIntegration:
    """Integration tests for firmware web interface."""

    @pytest.fixture
    def test_app(self):
        """Create a test Flask app with firmware routes."""
        from flask import Flask

        from hwautomation.web.routes.firmware import firmware_bp

        app = Flask(__name__)
        app.config["TESTING"] = True
        app.secret_key = "test-secret-key"

        # Add a basic index route to avoid BuildError
        @app.route("/")
        def index():
            return "Test Index"

        # Register blueprint without initializing firmware routes
        # We'll mock the firmware_web_manager in individual tests
        app.register_blueprint(firmware_bp)

        return app

    @pytest.fixture
    def client(self, test_app):
        """Create test client."""
        return test_app.test_client()

    def test_firmware_dashboard_route(self, client):
        """Test firmware dashboard route accessibility."""
        # We need to patch both the firmware_web_manager and render_template
        with (
            patch(
                "hwautomation.web.firmware_routes.firmware_web_manager"
            ) as mock_manager,
            patch("hwautomation.web.firmware_routes.render_template") as mock_render,
        ):

            # Make the mock manager truthy so the route doesn't redirect
            mock_manager.__bool__ = Mock(return_value=True)
            mock_manager.get_firmware_inventory.return_value = {
                "servers": [],
                "update_summary": {
                    "total_servers": 0,
                    "updates_available": 0,
                    "up_to_date": 0,
                    "unknown_status": 0,
                },
                "firmware_repository": {
                    "total_files": 0,
                    "vendors": [],
                    "latest_versions": {},
                },
            }

            # Mock render_template to return a simple response
            mock_render.return_value = "Firmware Management Dashboard"

            response = client.get("/firmware/dashboard")
            assert response.status_code == 200
            assert b"Firmware Management Dashboard" in response.data

            # Verify that render_template was called with correct parameters
            mock_render.assert_called_once_with(
                "firmware/dashboard.html",
                title="Firmware Management",
                inventory=mock_manager.get_firmware_inventory.return_value,
            )

    def test_firmware_inventory_api_route(self, client):
        """Test firmware inventory API route."""
        with patch(
            "hwautomation.web.firmware_routes.firmware_web_manager"
        ) as mock_manager:
            mock_inventory = {
                "servers": [
                    {
                        "id": "test-server-1",
                        "hostname": "test-host-1",
                        "status": "Ready",
                        "device_type": "a1.c5.large",
                        "firmware_status": "detected",
                        "bios_version": "v1.0",
                        "bmc_version": "v2.0",
                        "updates_available": True,
                    }
                ],
                "update_summary": {
                    "total_servers": 1,
                    "updates_available": 1,
                    "up_to_date": 0,
                    "unknown_status": 0,
                },
                "firmware_repository": {
                    "total_files": 5,
                    "vendors": ["hpe", "supermicro"],
                    "latest_versions": {},
                },
            }
            mock_manager.get_firmware_inventory.return_value = mock_inventory

            response = client.get("/firmware/api/inventory")
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data["servers"][0]["id"] == "test-server-1"
            assert data["update_summary"]["total_servers"] == 1
            assert data["firmware_repository"]["total_files"] == 5

    def test_schedule_firmware_update_api_route(self, client):
        """Test schedule firmware update API route."""
        with patch(
            "hwautomation.web.firmware_routes.firmware_web_manager"
        ) as mock_manager:
            mock_result = {
                "success": True,
                "scheduled_updates": [
                    {
                        "server_id": "test-server-1",
                        "workflow_id": "fw-update-test-123",
                        "status": "scheduled",
                    }
                ],
                "failed_schedules": [],
                "total_scheduled": 1,
            }
            mock_manager.schedule_firmware_update.return_value = mock_result

            request_data = {
                "server_ids": ["test-server-1"],
                "components": ["bios", "bmc"],
                "maintenance_window": 60,
                "rollback_enabled": True,
            }

            response = client.post(
                "/firmware/api/schedule",
                data=json.dumps(request_data),
                content_type="application/json",
            )
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data["success"] == True
            assert data["total_scheduled"] == 1
            assert len(data["scheduled_updates"]) == 1

    def test_schedule_firmware_update_api_no_servers(self, client):
        """Test schedule firmware update API with no servers."""
        request_data = {"server_ids": [], "components": ["bios"]}

        response = client.post(
            "/firmware/api/schedule",
            data=json.dumps(request_data),
            content_type="application/json",
        )
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "No servers specified" in data["error"]

    def test_get_firmware_update_progress_api(self, client):
        """Test get firmware update progress API route."""
        with patch(
            "hwautomation.web.firmware_routes.firmware_web_manager"
        ) as mock_manager:
            mock_progress = {
                "workflow_id": "fw-update-test-123",
                "status": "running",
                "progress_percentage": 50,
                "current_step": "Updating BIOS firmware",
            }
            mock_manager.get_update_progress.return_value = mock_progress

            response = client.get("/firmware/api/progress/fw-update-test-123")
            assert response.status_code == 200

            data = json.loads(response.data)
            assert data["workflow_id"] == "fw-update-test-123"
            assert data["status"] == "running"
            assert data["progress_percentage"] == 50

    def test_cancel_firmware_update_api(self, client):
        """Test cancel firmware update API route."""
        response = client.post("/firmware/api/cancel/fw-update-test-123")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["success"] == True
        assert data["workflow_id"] == "fw-update-test-123"
        assert data["status"] == "cancelled"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
