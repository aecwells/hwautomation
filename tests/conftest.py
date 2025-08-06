"""
Pytest configuration and shared fixtures.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
import yaml

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "fixtures"

@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        yield f.name
    # Cleanup
    try:
        os.unlink(f.name)
    except FileNotFoundError:
        pass

@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        'maas': {
            'url': 'http://test-maas.local:5240/MAAS/',
            'api_key': 'test-api-key',
            'timeout': 30
        },
        'database': {
            'path': ':memory:'  # In-memory database for tests
        },
        'ssh': {
            'timeout': 30,
            'retries': 3
        },
        'ipmi': {
            'timeout': 60,
            'retries': 2
        }
    }

@pytest.fixture
def config_file(temp_dir, sample_config):
    """Create a temporary config file."""
    config_path = temp_dir / "config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(sample_config, f)
    return config_path

@pytest.fixture
def mock_maas_client():
    """Mock MaaS client for testing."""
    with patch('hwautomation.maas.client.create_maas_client') as mock:
        client = Mock()
        client.get_machines.return_value = []
        client.get_machine.return_value = {}
        mock.return_value = client
        yield client

@pytest.fixture
def mock_ssh_client():
    """Mock SSH client for testing."""
    with patch('paramiko.SSHClient') as mock:
        client = Mock()
        client.exec_command.return_value = (Mock(), Mock(), Mock())
        mock.return_value = client
        yield client

@pytest.fixture
def mock_db_helper():
    """Mock database helper for testing."""
    with patch('hwautomation.database.helper.DbHelper') as mock:
        helper = Mock()
        helper.get_data.return_value = []
        helper.insert_data.return_value = True
        mock.return_value = helper
        yield helper
