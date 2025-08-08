#!/usr/bin/env python3
"""
Comprehensive test suite configuration and utilities for HWAutomation.

This module provides advanced testing infrastructure including:
- Performance testing framework
- Integration testing helpers
- Mock factories for complex objects
- Test data generators
- Coverage reporting enhancements
"""

import asyncio
import os
import statistics
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import AsyncMock, Mock, patch

import pytest
import sqlite3
import yaml

# Test configuration
TEST_DATA_DIR = Path(__file__).parent / "fixtures"
PERFORMANCE_TEST_TIMEOUT = 30  # seconds
INTEGRATION_TEST_TIMEOUT = 60  # seconds


@dataclass
class PerformanceMetrics:
    """Container for performance test metrics."""

    operation_name: str
    execution_times: List[float] = field(default_factory=list)
    memory_usage: List[float] = field(default_factory=list)
    success_rate: float = 0.0
    error_count: int = 0

    @property
    def average_time(self) -> float:
        return statistics.mean(self.execution_times) if self.execution_times else 0.0

    @property
    def median_time(self) -> float:
        return statistics.median(self.execution_times) if self.execution_times else 0.0

    @property
    def p95_time(self) -> float:
        if not self.execution_times:
            return 0.0
        sorted_times = sorted(self.execution_times)
        index = int(0.95 * len(sorted_times))
        return sorted_times[index]


class PerformanceTestMixin:
    """Mixin class for performance testing capabilities."""

    def __init__(self):
        self.performance_metrics = {}

    def time_operation(self, operation_name: str, iterations: int = 10):
        """Decorator for timing operations."""

        def decorator(func):
            def wrapper(*args, **kwargs):
                if operation_name not in self.performance_metrics:
                    self.performance_metrics[operation_name] = PerformanceMetrics(
                        operation_name
                    )

                metrics = self.performance_metrics[operation_name]

                for _ in range(iterations):
                    start_time = time.time()
                    try:
                        result = func(*args, **kwargs)
                        execution_time = time.time() - start_time
                        metrics.execution_times.append(execution_time)
                    except Exception as e:
                        metrics.error_count += 1
                        raise e

                metrics.success_rate = (iterations - metrics.error_count) / iterations
                return result

            return wrapper

        return decorator

    def assert_performance_threshold(
        self,
        operation_name: str,
        max_average_time: float,
        max_p95_time: float,
        min_success_rate: float = 0.95,
    ):
        """Assert that performance metrics meet specified thresholds."""
        metrics = self.performance_metrics.get(operation_name)
        assert metrics is not None, f"No metrics found for operation: {operation_name}"

        assert (
            metrics.average_time <= max_average_time
        ), f"Average time {metrics.average_time:.3f}s exceeds threshold {max_average_time}s"

        assert (
            metrics.p95_time <= max_p95_time
        ), f"P95 time {metrics.p95_time:.3f}s exceeds threshold {max_p95_time}s"

        assert (
            metrics.success_rate >= min_success_rate
        ), f"Success rate {metrics.success_rate:.3f} below threshold {min_success_rate}"


class MockDataFactory:
    """Factory for creating realistic test data."""

    @staticmethod
    def create_server_data(
        server_id: str = "test-server-001", device_type: str = "a1.c5.large"
    ) -> Dict[str, Any]:
        """Create mock server data."""
        return {
            "id": server_id,
            "device_type": device_type,
            "status_name": "Ready",
            "ipmi_ip": "192.168.1.100",
            "ipmi_user": "ADMIN",
            "rack_location": "Rack-A-U12",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metadata": {
                "cpu_count": 24,
                "memory_gb": 128,
                "storage_gb": 1000,
                "network_interfaces": 4,
            },
        }

    @staticmethod
    def create_workflow_data(
        workflow_id: str = "wf-test-001", status: str = "RUNNING"
    ) -> Dict[str, Any]:
        """Create mock workflow data."""
        return {
            "id": workflow_id,
            "status": status,
            "progress": 45,
            "current_step": "Configuring BIOS settings",
            "created_at": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "sub_tasks": [
                {
                    "name": "IPMI Connection",
                    "status": "completed",
                    "progress": 100,
                    "message": "IPMI connection established",
                },
                {
                    "name": "BIOS Configuration",
                    "status": "running",
                    "progress": 60,
                    "message": "Applying BIOS settings...",
                },
            ],
        }

    @staticmethod
    def create_maas_machine_data(system_id: str = "node-test-001") -> Dict[str, Any]:
        """Create mock MaaS machine data."""
        return {
            "system_id": system_id,
            "hostname": f"server-{system_id}",
            "status": "Ready",
            "architecture": "amd64/generic",
            "cpu_count": 24,
            "memory": 131072,  # MB
            "storage": 1000.0,  # GB
            "power_state": "on",
            "ip_addresses": ["192.168.1.100"],
            "tags": ["hw-testing", "available"],
        }

    @staticmethod
    def create_bios_config_data(device_type: str = "a1.c5.large") -> Dict[str, Any]:
        """Create mock BIOS configuration data."""
        return {
            "device_type": device_type,
            "settings": {
                "BootMode": "UEFI",
                "VirtualizationTechnology": "Enabled",
                "HyperThreading": "Enabled",
                "TurboBoost": "Enabled",
                "PowerProfile": "Performance",
            },
            "template_version": "v1.2.0",
            "last_applied": datetime.utcnow().isoformat(),
        }


class DatabaseTestHelper:
    """Helper class for database testing operations."""

    @staticmethod
    def create_test_database() -> str:
        """Create a temporary test database."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        return path

    @staticmethod
    def populate_test_data(db_path: str, server_count: int = 5):
        """Populate test database with sample data."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create servers table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS servers (
                id TEXT PRIMARY KEY,
                device_type TEXT,
                status_name TEXT,
                ipmi_ip TEXT,
                ipmi_user TEXT,
                rack_location TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """
        )

        # Insert test data
        for i in range(server_count):
            server_data = MockDataFactory.create_server_data(f"test-server-{i:03d}")
            cursor.execute(
                """
                INSERT INTO servers (id, device_type, status_name, ipmi_ip, ipmi_user, rack_location, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    server_data["id"],
                    server_data["device_type"],
                    server_data["status_name"],
                    server_data["ipmi_ip"],
                    "ADMIN",  # ipmi_user
                    server_data["rack_location"],
                    server_data["created_at"],
                    server_data["updated_at"],
                ),
            )

        conn.commit()
        conn.close()


class AsyncTestHelper:
    """Helper for async testing operations."""

    @staticmethod
    def run_async_test(coro):
        """Run async test with proper event loop handling."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    @staticmethod
    def create_mock_async_context_manager():
        """Create a mock async context manager."""
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_cm
        mock_cm.__aexit__.return_value = None
        return mock_cm


# Pytest fixtures for enhanced testing
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
    """Provide a temporary test database."""
    db_path = DatabaseTestHelper.create_test_database()
    DatabaseTestHelper.populate_test_data(db_path)
    yield db_path
    os.unlink(db_path)


@pytest.fixture
def test_config():
    """Provide test configuration."""
    return {
        "database": {"path": ":memory:", "auto_migrate": True},
        "maas": {
            "host": "http://test-maas:5240",
            "consumer_key": "test-key",
            "token_key": "test-token",
            "token_secret": "test-secret",
        },
        "logging": {"level": "DEBUG", "file": None},  # No file logging in tests
    }


@pytest.fixture
def mock_workflow_manager():
    """Provide mock workflow manager."""
    manager = Mock()
    manager.create_workflow.return_value = MockDataFactory.create_workflow_data()
    manager.get_workflow_status.return_value = MockDataFactory.create_workflow_data()
    manager.cancel_workflow.return_value = True
    return manager


@pytest.fixture
def mock_maas_client():
    """Provide mock MaaS client."""
    client = Mock()
    client.get_machines.return_value = [
        MockDataFactory.create_maas_machine_data(f"node-{i:03d}") for i in range(3)
    ]
    client.commission_machine.return_value = {"status": "commissioning"}
    return client


@pytest.fixture
def mock_bios_manager():
    """Provide mock BIOS configuration manager."""
    manager = Mock()
    manager.get_current_config.return_value = MockDataFactory.create_bios_config_data()
    manager.apply_configuration.return_value = {
        "success": True,
        "applied_settings": 5,
        "execution_time": 2.5,
    }
    return manager


# Custom pytest markers for test organization
pytest_marks = {
    "unit": pytest.mark.unit,
    "integration": pytest.mark.integration,
    "performance": pytest.mark.performance,
    "slow": pytest.mark.slow,
    "api": pytest.mark.api,
    "database": pytest.mark.database,
    "async_test": pytest.mark.asyncio,
}


# Test utilities
class TestAssertions:
    """Custom assertions for HWAutomation testing."""

    @staticmethod
    def assert_workflow_status(workflow_data: Dict[str, Any], expected_status: str):
        """Assert workflow has expected status."""
        assert (
            workflow_data.get("status") == expected_status
        ), f"Expected workflow status {expected_status}, got {workflow_data.get('status')}"

    @staticmethod
    def assert_server_provisioned(server_data: Dict[str, Any]):
        """Assert server is properly provisioned."""
        assert (
            server_data.get("status_name") == "Ready"
        ), f"Server not ready: {server_data.get('status_name')}"
        assert server_data.get("ipmi_ip"), "Server missing IPMI IP"
        assert server_data.get("device_type"), "Server missing device type"

    @staticmethod
    def assert_api_response_format(response_data: Dict[str, Any]):
        """Assert API response follows standard format."""
        assert "success" in response_data, "Response missing 'success' field"
        if not response_data["success"]:
            assert "error" in response_data, "Error response missing 'error' field"


def generate_performance_report(
    metrics: Dict[str, PerformanceMetrics], output_file: Optional[str] = None
) -> str:
    """Generate a performance test report."""
    report_lines = [
        "# HWAutomation Performance Test Report",
        f"Generated: {datetime.utcnow().isoformat()}",
        "",
        "## Performance Metrics Summary",
        "",
    ]

    for operation_name, metric in metrics.items():
        report_lines.extend(
            [
                f"### {operation_name}",
                f"- **Average Time**: {metric.average_time:.3f}s",
                f"- **Median Time**: {metric.median_time:.3f}s",
                f"- **P95 Time**: {metric.p95_time:.3f}s",
                f"- **Success Rate**: {metric.success_rate:.1%}",
                f"- **Total Executions**: {len(metric.execution_times)}",
                f"- **Errors**: {metric.error_count}",
                "",
            ]
        )

    report_content = "\n".join(report_lines)

    if output_file:
        with open(output_file, "w") as f:
            f.write(report_content)

    return report_content
