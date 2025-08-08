"""
Enhanced pytest configuration and shared fixtures for HWAutomation.

This module provides comprehensive testing infrastructure including:
- Performance testing capabilities
- Integration testing helpers
- Mock factories and data generators
- Database testing utilities
- Async testing support
"""

import asyncio
import os
import tempfile
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pytest
import sqlite3
import yaml

# Import our enhanced test framework
from test_framework import (
    AsyncTestHelper,
    DatabaseTestHelper,
    MockDataFactory,
    PerformanceTestMixin,
    TestAssertions,
)

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "fixtures"

# Ensure test data directory exists
TEST_DATA_DIR.mkdir(exist_ok=True)


# Configure pytest markers
def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")
    config.addinivalue_line("markers", "slow: mark test as slow running (>5 seconds)")
    config.addinivalue_line("markers", "api: mark test as testing API endpoints")
    config.addinivalue_line(
        "markers", "database: mark test as testing database operations"
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        yield f.name
    # Cleanup
    try:
        os.unlink(f.name)
    except FileNotFoundError:
        pass


@pytest.fixture
def test_config():
    """Provide comprehensive test configuration."""
    return {
        "database": {
            "path": ":memory:",
            "auto_migrate": True,
            "connection_timeout": 30,
        },
        "maas": {
            "host": "http://test-maas:5240",
            "consumer_key": "test-consumer-key",
            "token_key": "test-token-key",
            "token_secret": "test-token-secret",
            "timeout": 10,
        },
        "ipmi": {"username": "ADMIN", "password": "test-password", "timeout": 30},
        "bios": {"config_timeout": 300, "validation_timeout": 60, "retry_attempts": 3},
        "logging": {
            "level": "DEBUG",
            "file": None,  # No file logging in tests
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
        "web": {
            "secret_key": "test-secret-key-for-testing-only",
            "testing": True,
            "debug": True,
        },
    }


@pytest.fixture
def performance_tester():
    """Provide performance testing capabilities."""
    return PerformanceTestMixin()


@pytest.fixture
def mock_data_factory():
    """Provide mock data factory."""
    return MockDataFactory()


@pytest.fixture
def test_database():
    """Provide a temporary test database with sample data."""
    db_path = DatabaseTestHelper.create_test_database()
    DatabaseTestHelper.populate_test_data(db_path, server_count=10)
    yield db_path
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def empty_test_database():
    """Provide an empty temporary test database."""
    db_path = DatabaseTestHelper.create_test_database()
    yield db_path
    try:
        os.unlink(db_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def mock_workflow_manager():
    """Provide mock workflow manager with realistic behavior."""
    manager = Mock()

    # Configure return values
    workflow_data = MockDataFactory.create_workflow_data()
    manager.create_workflow.return_value = workflow_data
    manager.get_workflow_status.return_value = workflow_data
    manager.cancel_workflow.return_value = True
    manager.list_workflows.return_value = [workflow_data]

    # Add method to simulate workflow progress
    def simulate_progress(workflow_id, progress):
        workflow_data["progress"] = progress
        workflow_data["updated_at"] = datetime.utcnow().isoformat()
        return workflow_data

    manager.simulate_progress = simulate_progress
    return manager


@pytest.fixture
def mock_maas_client():
    """Provide mock MaaS client with comprehensive API simulation."""
    client = Mock()

    # Create sample machines
    machines = [
        MockDataFactory.create_maas_machine_data(f"node-{i:03d}") for i in range(5)
    ]

    client.get_machines.return_value = machines
    client.get_machine.return_value = machines[0]
    client.commission_machine.return_value = {"status": "commissioning"}
    client.deploy_machine.return_value = {"status": "deploying"}
    client.release_machine.return_value = {"status": "releasing"}

    # Simulate connection test
    client.test_connection.return_value = {"status": "connected", "version": "3.0.0"}

    return client


@pytest.fixture
def mock_bios_manager():
    """Provide mock BIOS configuration manager."""
    manager = Mock()

    bios_config = MockDataFactory.create_bios_config_data()
    manager.get_current_config.return_value = bios_config
    manager.apply_configuration.return_value = {
        "success": True,
        "applied_settings": len(bios_config["settings"]),
        "execution_time": 2.5,
        "validation_passed": True,
    }
    manager.validate_configuration.return_value = {
        "valid": True,
        "errors": [],
        "warnings": [],
    }

    return manager


@pytest.fixture
def mock_ipmi_manager():
    """Provide mock IPMI manager."""
    manager = Mock()

    manager.test_connection.return_value = {"status": "connected", "power_state": "on"}
    manager.power_on.return_value = {"success": True, "previous_state": "off"}
    manager.power_off.return_value = {"success": True, "previous_state": "on"}
    manager.power_cycle.return_value = {"success": True, "action": "power_cycle"}
    manager.get_system_info.return_value = {
        "manufacturer": "Supermicro",
        "model": "X11DPH-T",
        "serial_number": "TEST123456",
        "firmware_version": "3.42",
    }

    return manager


@pytest.fixture
def mock_database_helper():
    """Provide mock database helper."""
    helper = Mock()

    # Configure common database operations
    helper.checkifserveridexists.return_value = [True]
    helper.createrowforserver.return_value = True
    helper.updateserverinfo.return_value = True
    helper.getserverinfo.return_value = MockDataFactory.create_server_data()

    # Mock database connection
    mock_connection = Mock()
    mock_cursor = Mock()
    mock_connection.cursor.return_value = mock_cursor
    mock_cursor.fetchone.return_value = (10,)  # Sample count
    mock_cursor.fetchall.return_value = []

    helper.get_connection.return_value.__enter__.return_value = mock_connection
    helper.get_connection.return_value.__exit__.return_value = None

    return helper


@pytest.fixture
def mock_firmware_manager():
    """Provide mock firmware manager."""
    manager = Mock()

    # Mock firmware version checking
    firmware_info = {
        "bios": {
            "current_version": "1.2.3",
            "latest_version": "1.2.4",
            "update_required": True,
        },
        "bmc": {
            "current_version": "4.5.6",
            "latest_version": "4.5.6",
            "update_required": False,
        },
    }
    manager.check_firmware_versions.return_value = firmware_info

    # Mock firmware update
    update_result = {
        "bios": {"success": True, "requires_reboot": True, "execution_time": 120},
        "bmc": {"success": True, "requires_reboot": False, "execution_time": 60},
    }
    manager.update_firmware_batch.return_value = update_result

    return manager


@pytest.fixture
def flask_test_client(test_config):
    """Provide Flask test client for API testing."""
    # Import here to avoid circular imports
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

    from hwautomation.web.app import create_app

    app = create_app(test_config)
    app.config["TESTING"] = True

    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def sample_test_data():
    """Provide sample test data for various scenarios."""
    return {
        "servers": [
            MockDataFactory.create_server_data(f"server-{i:03d}", "a1.c5.large")
            for i in range(3)
        ],
        "workflows": [
            MockDataFactory.create_workflow_data(f"workflow-{i:03d}") for i in range(2)
        ],
        "maas_machines": [
            MockDataFactory.create_maas_machine_data(f"node-{i:03d}") for i in range(4)
        ],
        "bios_configs": {
            "a1.c5.large": MockDataFactory.create_bios_config_data("a1.c5.large"),
            "d1.c2.medium": MockDataFactory.create_bios_config_data("d1.c2.medium"),
        },
    }


@pytest.fixture
def test_assertions():
    """Provide custom test assertions."""
    return TestAssertions()


# Async testing support
@pytest.fixture
def async_test_helper():
    """Provide async testing utilities."""
    return AsyncTestHelper()


# Performance testing fixtures
@pytest.fixture
def performance_thresholds():
    """Define performance testing thresholds."""
    return {
        "api_response_time": 1.0,  # seconds
        "database_query_time": 0.5,  # seconds
        "workflow_creation_time": 2.0,  # seconds
        "bios_config_time": 30.0,  # seconds
        "success_rate_threshold": 0.95,  # 95%
    }


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_environment():
    """Automatically clean up test environment after each test."""
    yield
    # Cleanup code here if needed
    pass


# Test environment validation
def pytest_runtest_setup(item):
    """Validate test environment before running tests."""
    # Skip integration tests if not in integration test environment
    if item.get_closest_marker("integration") and not os.getenv(
        "RUN_INTEGRATION_TESTS"
    ):
        pytest.skip("Integration tests skipped (set RUN_INTEGRATION_TESTS=1 to run)")

    # Skip performance tests if not in performance test environment
    if item.get_closest_marker("performance") and not os.getenv(
        "RUN_PERFORMANCE_TESTS"
    ):
        pytest.skip("Performance tests skipped (set RUN_PERFORMANCE_TESTS=1 to run)")


# Performance monitoring
@pytest.fixture(scope="session")
def performance_monitor():
    """Monitor test performance across the session."""
    metrics = {"start_time": time.time(), "test_times": [], "slow_tests": []}

    yield metrics

    # Print performance summary
    total_time = time.time() - metrics["start_time"]
    if metrics["test_times"]:
        avg_time = sum(metrics["test_times"]) / len(metrics["test_times"])
        print(f"\n=== Performance Summary ===")
        print(f"Total session time: {total_time:.2f}s")
        print(f"Average test time: {avg_time:.3f}s")
        if metrics["slow_tests"]:
            print(f"Slow tests (>5s):")
            for test_name, duration in metrics["slow_tests"]:
                print(f"  {test_name}: {duration:.2f}s")


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "maas": {
            "url": "http://test-maas.local:5240/MAAS/",
            "api_key": "test-api-key",
            "timeout": 30,
        },
        "database": {"path": ":memory:"},  # In-memory database for tests
        "ssh": {"timeout": 30, "retries": 3},
        "ipmi": {"timeout": 60, "retries": 2},
    }


@pytest.fixture
def config_file(temp_dir, sample_config):
    """Create a temporary config file."""
    config_path = temp_dir / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(sample_config, f)
    return config_path


@pytest.fixture
def mock_maas_client():
    """Mock MaaS client for testing."""
    with patch("hwautomation.maas.client.create_maas_client") as mock:
        client = Mock()
        client.get_machines.return_value = []
        client.get_machine.return_value = {}
        mock.return_value = client
        yield client


@pytest.fixture
def mock_ssh_client():
    """Mock SSH client for testing."""
    with patch("paramiko.SSHClient") as mock:
        client = Mock()
        client.exec_command.return_value = (Mock(), Mock(), Mock())
        mock.return_value = client
        yield client


@pytest.fixture
def mock_db_helper():
    """Mock database helper for testing."""
    with patch("hwautomation.database.helper.DbHelper") as mock:
        helper = Mock()
        helper.get_data.return_value = []
        helper.insert_data.return_value = True
        mock.return_value = helper
        yield helper
