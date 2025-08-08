#!/usr/bin/env python3
"""
Setup Modern Unit Testing Infrastructure

This tool sets up a comprehensive unit testing infrastructure with:
- pytest as the test runner
- pytest-cov for coverage reporting
- pytest-mock for easy mocking
- Test configuration files
- Sample unit tests to replace integration tests
- Coverage reporting configuration
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def install_testing_dependencies():
    """Install testing dependencies."""
    print("📦 Installing testing dependencies...")

    dependencies = [
        "pytest>=7.0.0",
        "pytest-cov>=4.0.0",
        "pytest-mock>=3.10.0",
        "coverage>=7.0.0",
        "pytest-xdist>=3.0.0",  # For parallel test execution
        "pytest-html>=3.1.0",  # For HTML test reports
    ]

    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade"] + dependencies
        )
        print("✅ Testing dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False


def create_pytest_config():
    """Create pytest configuration."""
    print("⚙️  Creating pytest configuration...")

    pytest_ini_content = """[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --verbose
    --tb=short
    --cov=src/hwautomation
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-report=xml
    --cov-fail-under=80
    --strict-markers
    --disable-warnings
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (slower, requires external services)
    slow: Slow tests
    network: Tests requiring network access
    database: Tests requiring database access
"""

    with open("pytest.ini", "w") as f:
        f.write(pytest_ini_content)

    print("✅ pytest.ini created!")


def create_coverage_config():
    """Create coverage configuration."""
    print("⚙️  Creating coverage configuration...")

    coverage_config = """[run]
source = src/hwautomation
omit = 
    */tests/*
    */test_*
    */__pycache__/*
    */migrations/*
    */venv/*
    */env/*
    */hwautomation-env/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if self.debug:
    if settings.DEBUG
    raise AssertionError
    raise NotImplementedError
    if 0:
    if __name__ == .__main__.:
    class .*\\bProtocol\\):
    @(abc\\.)?abstractmethod

[html]
directory = htmlcov
"""

    with open(".coveragerc", "w") as f:
        f.write(coverage_config)

    print("✅ .coveragerc created!")


def backup_old_tests():
    """Backup old test files."""
    print("💾 Backing up old test files...")

    backup_dir = Path("tests_backup")
    backup_dir.mkdir(exist_ok=True)

    tests_dir = Path("tests")
    if tests_dir.exists():
        for file_path in tests_dir.iterdir():
            if file_path.is_file() and file_path.name.startswith("test_"):
                shutil.copy2(file_path, backup_dir / file_path.name)

        print(f"✅ Old tests backed up to {backup_dir}/")


def create_modern_test_structure():
    """Create modern test structure."""
    print("🏗️  Creating modern test structure...")

    # Create new test structure
    test_dirs = ["tests/unit", "tests/integration", "tests/fixtures", "tests/mocks"]

    for dir_path in test_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        # Create __init__.py files
        (Path(dir_path) / "__init__.py").touch()

    print("✅ Test directory structure created!")


def create_conftest():
    """Create modern conftest.py."""
    print("⚙️  Creating modern conftest.py...")

    conftest_content = '''"""
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
'''

    with open("tests/conftest.py", "w") as f:
        f.write(conftest_content)

    print("✅ Modern conftest.py created!")


def create_sample_unit_tests():
    """Create sample unit tests."""
    print("🧪 Creating sample unit tests...")

    # Unit test for config loading
    config_test = '''"""
Unit tests for configuration management.
"""

import pytest
from unittest.mock import patch, mock_open
import yaml
from hwautomation.utils.config import load_config, ConfigError


class TestConfigLoader:
    """Test configuration loading functionality."""
    
    def test_load_valid_config(self, sample_config, config_file):
        """Test loading a valid configuration file."""
        config = load_config(str(config_file))
        assert config == sample_config
    
    def test_load_missing_file(self):
        """Test loading a non-existent configuration file."""
        with pytest.raises(ConfigError):
            load_config("non_existent_file.yaml")
    
    def test_load_invalid_yaml(self, temp_dir):
        """Test loading an invalid YAML file."""
        invalid_config = temp_dir / "invalid.yaml"
        invalid_config.write_text("invalid: yaml: content:")
        
        with pytest.raises(ConfigError):
            load_config(str(invalid_config))
    
    @patch('builtins.open', mock_open(read_data="key: value"))
    def test_load_config_with_mock(self):
        """Test config loading with mocked file operations."""
        with patch('yaml.safe_load') as mock_yaml:
            mock_yaml.return_value = {'key': 'value'}
            config = load_config('mock_file.yaml')
            assert config == {'key': 'value'}
'''

    with open("tests/unit/test_config.py", "w") as f:
        f.write(config_test)

    # Unit test for database helper
    db_test = '''"""
Unit tests for database helper functionality.
"""

import pytest
from unittest.mock import Mock, patch, call
import sqlite3
from hwautomation.database.helper import DbHelper


class TestDbHelper:
    """Test database helper functionality."""
    
    def test_init_with_memory_db(self):
        """Test initialization with in-memory database."""
        helper = DbHelper(db_path=':memory:', tablename='test_table')
        assert helper.db_path == ':memory:'
        assert helper.tablename == 'test_table'
    
    @patch('sqlite3.connect')
    def test_get_connection(self, mock_connect):
        """Test database connection creation."""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        helper = DbHelper(db_path='test.db', tablename='test_table')
        conn = helper.get_connection()
        
        mock_connect.assert_called_once_with('test.db')
        assert conn == mock_conn
    
    @patch('sqlite3.connect')
    def test_execute_query(self, mock_connect):
        """Test query execution."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [('test', 'data')]
        mock_connect.return_value = mock_conn
        
        helper = DbHelper(db_path='test.db', tablename='test_table')
        result = helper.get_data()
        
        assert result == [('test', 'data')]
        mock_cursor.execute.assert_called()
'''

    with open("tests/unit/test_database.py", "w") as f:
        f.write(db_test)

    # Integration test example
    integration_test = '''"""
Integration tests for workflow management.
"""

import pytest
from hwautomation.orchestration.workflow_manager import WorkflowManager


@pytest.mark.integration
class TestWorkflowIntegration:
    """Integration tests for workflow functionality."""
    
    def test_workflow_with_mocked_services(self, mock_maas_client, mock_db_helper, sample_config):
        """Test workflow execution with mocked external services."""
        # This would be a real integration test but with mocked external services
        manager = WorkflowManager(config=sample_config)
        
        # Test the workflow logic without hitting real services
        # This is faster than full integration but tests component interaction
        pass
    
    @pytest.mark.slow
    @pytest.mark.network
    def test_full_workflow_integration(self):
        """Full integration test (requires real services)."""
        # This would be a full integration test
        # Only run when external services are available
        pytest.skip("Requires external services")
'''

    with open("tests/integration/test_workflow.py", "w") as f:
        f.write(integration_test)

    print("✅ Sample unit tests created!")


def create_test_makefile():
    """Create Makefile for easy test execution."""
    print("⚙️  Creating test Makefile...")

    makefile_content = """# Testing shortcuts
.PHONY: test test-unit test-integration test-cov test-html clean-test

# Run all tests
test:
    pytest

# Run only unit tests (fast)
test-unit:
    pytest tests/unit/ -m "not slow"

# Run integration tests
test-integration:
    pytest tests/integration/ -m integration

# Run tests with coverage
test-cov:
    pytest --cov=src/hwautomation --cov-report=term-missing

# Generate HTML coverage report
test-html:
    pytest --cov=src/hwautomation --cov-report=html
    @echo "Coverage report generated in htmlcov/index.html"

# Run tests in parallel (faster)
test-parallel:
    pytest -n auto

# Clean test artifacts
clean-test:
    rm -rf .pytest_cache/
    rm -rf htmlcov/
    rm -rf .coverage
    rm -rf coverage.xml
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} +

# Install test dependencies
install-test:
    pip install -e .[dev]
"""

    with open("Makefile", "w") as f:
        f.write(makefile_content)

    print("✅ Test Makefile created!")


def update_pyproject_toml():
    """Update pyproject.toml with testing configuration."""
    print("⚙️  Updating pyproject.toml...")

    # Read current pyproject.toml
    with open("pyproject.toml", "r") as f:
        content = f.read()

    # Add testing configuration if not present
    if "[tool.pytest.ini_options]" not in content:
        pytest_config = """
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--verbose",
    "--tb=short", 
    "--cov=src/hwautomation",
    "--cov-report=html:htmlcov",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
    "--strict-markers"
]
markers = [
    "unit: Unit tests (fast, isolated)",
    "integration: Integration tests (slower, requires external services)",
    "slow: Slow tests",
    "network: Tests requiring network access",
    "database: Tests requiring database access"
]

[tool.coverage.run]
source = ["src/hwautomation"]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/__pycache__/*",
    "*/migrations/*",
    "*/venv/*",
    "*/env/*",
    "*/hwautomation-env/*"
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "if self.debug:",
    "if settings.DEBUG",
    "raise AssertionError",
    "raise NotImplementedError",
    "if 0:",
    "if __name__ == .__main__.:",
    "class .*\\bProtocol\\):",
    "@(abc\\.)?abstractmethod"
]
"""
        content += pytest_config

        with open("pyproject.toml", "w") as f:
            f.write(content)

    print("✅ pyproject.toml updated!")


def create_github_actions_workflow():
    """Create GitHub Actions workflow for testing."""
    print("⚙️  Creating GitHub Actions workflow...")

    workflow_dir = Path(".github/workflows")
    workflow_dir.mkdir(parents=True, exist_ok=True)

    workflow_content = """name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev]
    
    - name: Run unit tests
      run: |
        pytest tests/unit/ --cov=src/hwautomation --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
        fail_ci_if_error: false
"""

    with open(workflow_dir / "test.yml", "w") as f:
        f.write(workflow_content)

    print("✅ GitHub Actions workflow created!")


def main():
    """Main setup function."""
    print("🚀 Setting up modern unit testing infrastructure...\n")

    if not install_testing_dependencies():
        return False

    backup_old_tests()
    create_pytest_config()
    create_coverage_config()
    create_modern_test_structure()
    create_conftest()
    create_sample_unit_tests()
    create_test_makefile()
    update_pyproject_toml()
    create_github_actions_workflow()

    print("\n" + "=" * 60)
    print("✅ Modern testing infrastructure setup complete!")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print("1. Install development dependencies: pip install -e .[dev]")
    print("2. Run unit tests: make test-unit")
    print("3. Generate coverage report: make test-html")
    print("4. View coverage: open htmlcov/index.html")
    print("5. Replace old tests with proper unit tests")
    print("\n🎯 Testing Commands:")
    print("• pytest                    - Run all tests")
    print("• pytest tests/unit/        - Run unit tests only")
    print("• pytest -m 'not slow'     - Skip slow tests")
    print("• pytest --cov              - Run with coverage")
    print("• make test-html            - Generate HTML coverage report")

    return True


if __name__ == "__main__":
    main()
