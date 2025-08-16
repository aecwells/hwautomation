# Development Guide

Complete guide for developing, extending, and contributing to HWAutomation.

## 📋 Table of Contents

- [Development Setup](#-development-setup)
- [Architecture Overview](#-architecture-overview)
- [Configuration](#-configuration)
- [Code Standards](#-code-standards)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [Extension Development](#-extension-development)
- [Release Process](#-release-process)

## 🚀 Development Setup

### Prerequisites

```bash
# Required tools
Python 3.9+
Node.js 18+ (for frontend)
Git
Docker (optional)
```

### Local Environment

```bash
# Clone repository
git clone https://github.com/aecwells/hwautomation.git
cd hwautomation

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -e .[dev]

# Setup pre-commit hooks
pre-commit install

# Setup conventional commits
make setup-conventional-commits
```

### Development Tools

```bash
# Code quality
make lint          # Run linting
make format        # Format code
make type-check    # Type checking

# Testing
make test          # Run all tests
make test-unit     # Unit tests only
make test-cov      # With coverage

# Frontend
make frontend-dev  # Development server
make frontend-build # Production build
```

## 🏗️ Architecture Overview

### Project Structure

```
hwautomation/
├── src/hwautomation/         # Main package
│   ├── config/              # Configuration management
│   ├── hardware/            # Hardware abstraction
│   │   ├── bios/           # BIOS configuration
│   │   ├── firmware/       # Firmware management
│   │   ├── discovery/      # Hardware discovery
│   │   ├── ipmi/           # IPMI interface
│   │   └── redfish/        # Redfish API
│   ├── orchestration/      # Workflow orchestration
│   ├── database/           # Data persistence
│   ├── maas/              # MaaS integration
│   ├── web/               # Web interface
│   └── validation/        # Data validation
├── configs/                 # Configuration files
├── docs/                   # Documentation
├── examples/               # Usage examples
├── tests/                  # Test suite
└── tools/                  # Development tools
```

### Key Components

**Configuration System:**
- Unified device configuration
- BIOS template management
- Environment configuration
- Validation and schema checking

**Hardware Management:**
- Multi-vendor BIOS configuration
- Firmware update automation
- Hardware discovery and detection
- Protocol abstraction (IPMI/Redfish)

**Workflow Orchestration:**
- Step-based workflow execution
- Real-time progress tracking
- Cancellation and error handling
- Database recording

**Web Interface:**
- Flask-based REST API
- Real-time WebSocket updates
- Frontend build system
- Asset management

## ⚙️ Configuration

### Environment Configuration

Create `.env` file:

```bash
# Database
DATABASE_PATH=./hw_automation.db

# Web Interface
FLASK_ENV=development
FLASK_DEBUG=true
PORT=5000

# MaaS Integration (optional)
MAAS_URL=http://192.168.1.240:5240/MAAS
MAAS_CONSUMER_KEY=your-consumer-key
MAAS_TOKEN_KEY=your-token-key
MAAS_TOKEN_SECRET=your-token-secret

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=logs/hwautomation.log
ACTIVITY_LOG_FILE=logs/activity.log

# Security
SECRET_KEY=your-secret-key-for-development
```

### Device Configuration

**Device Types** (`configs/devices/unified_device_config.yaml`):

```yaml
device_types:
  a1.c5.large:
    vendor: HPE
    product_family: ProLiant
    motherboard: ProLiant RL300 Gen11
    cpu_sockets: 2
    memory_slots: 32
    storage_bays: 24
    pci_slots: 8
    power_consumption: 800
    form_factor: 2U

  d1.c2.medium:
    vendor: Dell
    product_family: PowerEdge
    motherboard: PowerEdge R750
    cpu_sockets: 2
    memory_slots: 24
    storage_bays: 16
```

**BIOS Templates** (`configs/bios/template_rules.yaml`):

```yaml
templates:
  performance_optimized:
    description: "High performance server configuration"
    settings:
      - name: "CPU_Power_Management"
        value: "Maximum_Performance"
      - name: "Memory_Frequency"
        value: "Maximum_Performance"
      - name: "Turbo_Mode"
        value: "Enabled"

  power_efficient:
    description: "Energy efficient configuration"
    settings:
      - name: "CPU_Power_Management"
        value: "Power_Saving"
      - name: "C_States"
        value: "Enabled"
```

### Development Configuration

**Testing Configuration** (`test_config.yaml`):

```yaml
database:
  path: ":memory:"  # In-memory for tests

logging:
  level: WARNING

maas:
  mock_mode: true

hardware:
  simulation_mode: true
```

**Pre-commit Configuration** (`.pre-commit-config.yaml`):

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.0.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
```

## 📝 Code Standards

### Python Code Style

```python
"""Module docstring following Google style."""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ExampleClass:
    """Class docstring with purpose and usage."""

    def __init__(self, config: Dict[str, str]) -> None:
        """Initialize with configuration.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self._private_attr = None

    def public_method(self, param: str) -> Optional[str]:
        """Public method with type hints.

        Args:
            param: Input parameter

        Returns:
            Optional result string

        Raises:
            ValueError: If param is invalid
        """
        if not param:
            raise ValueError("Parameter cannot be empty")

        logger.info(f"Processing parameter: {param}")
        return self._process_param(param)

    def _process_param(self, param: str) -> str:
        """Private method for internal use."""
        return param.upper()
```

### Conventional Commits

```bash
# Feature
feat(api): add user authentication endpoint

# Bug fix
fix(database): resolve connection timeout issue

# Documentation
docs: update API documentation

# Breaking change
feat!: remove deprecated configuration format
```

### File Organization

```python
# Import order (enforced by isort)
# 1. Standard library
import os
import sys
from pathlib import Path

# 2. Third-party packages
import requests
from flask import Flask

# 3. Local imports
from hwautomation.config import load_config
from hwautomation.hardware.bios import BiosManager
```

## 🧪 Testing

### Test Structure

```
tests/
├── unit/                    # Fast unit tests
│   ├── test_config.py
│   ├── test_hardware/
│   └── test_orchestration/
├── integration/             # Integration tests
│   ├── test_workflow_integration.py
│   └── test_api_integration.py
├── fixtures/               # Test data
└── conftest.py            # Pytest configuration
```

### Writing Tests

```python
import pytest
from unittest.mock import Mock, patch

from hwautomation.hardware.bios import BiosManager


class TestBiosManager:
    """Test suite for BiosManager."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            'device_type': 'a1.c5.large',
            'vendor': 'HPE'
        }

    @pytest.fixture
    def bios_manager(self, mock_config):
        """Create BiosManager instance for testing."""
        return BiosManager(mock_config)

    def test_initialization(self, bios_manager, mock_config):
        """Test manager initialization."""
        assert bios_manager.config == mock_config
        assert bios_manager.vendor == 'HPE'

    @patch('hwautomation.hardware.bios.subprocess.run')
    def test_apply_config(self, mock_subprocess, bios_manager):
        """Test BIOS configuration application."""
        mock_subprocess.return_value.returncode = 0

        result = bios_manager.apply_config('192.168.1.100')

        assert result.success is True
        mock_subprocess.assert_called_once()

    @pytest.mark.integration
    def test_full_workflow(self, bios_manager):
        """Integration test for full BIOS workflow."""
        # This test requires actual hardware or simulation
        pass
```

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# Integration tests
make test-integration

# With coverage
make test-cov

# Specific test file
pytest tests/unit/test_config.py -v

# Specific test method
pytest tests/unit/test_config.py::TestConfig::test_load_config -v
```

## 🤝 Contributing

### Development Workflow

1. **Create Feature Branch**:
```bash
git checkout -b feat/add-new-feature
```

2. **Make Changes**:
```bash
# Write code following standards
# Add tests for new functionality
# Update documentation if needed
```

3. **Commit Changes**:
```bash
# Use conventional commits
git commit -m "feat(component): add new feature

- Detailed description of changes
- Any breaking changes noted
- References to issues: Fixes #123"
```

4. **Create Pull Request**:
- Ensure all tests pass
- Include description of changes
- Reference related issues
- Request appropriate reviewers

### Code Review Guidelines

**For Authors:**
- Ensure CI passes
- Write clear commit messages
- Add tests for new features
- Update documentation
- Keep PRs focused and small

**For Reviewers:**
- Check for security issues
- Verify test coverage
- Ensure documentation is updated
- Test functionality if possible
- Provide constructive feedback

## 🔧 Extension Development

### Adding New Hardware Vendors

1. **Create Vendor Module**:
```python
# src/hwautomation/hardware/bios/devices/newvendor.py
from .base import BaseBiosDevice

class NewVendorBiosDevice(BaseBiosDevice):
    """BIOS management for NewVendor devices."""

    def apply_config(self, target_ip: str, config: dict) -> bool:
        """Apply BIOS configuration."""
        # Implement vendor-specific logic
        pass
```

2. **Register Device**:
```python
# src/hwautomation/hardware/bios/devices/factory.py
from .newvendor import NewVendorBiosDevice

DEVICE_CLASSES = {
    'HPE': HPEBiosDevice,
    'Dell': DellBiosDevice,
    'Supermicro': SupermicroBiosDevice,
    'NewVendor': NewVendorBiosDevice,  # Add here
}
```

3. **Add Configuration**:
```yaml
# configs/devices/unified_device_config.yaml
device_types:
  nv.c1.large:
    vendor: NewVendor
    product_family: ServerSeries
    motherboard: NV-MB-100
```

### Adding New Workflow Steps

```python
# src/hwautomation/orchestration/steps/custom_step.py
from .base import BaseStep

class CustomWorkflowStep(BaseStep):
    """Custom workflow step implementation."""

    def execute(self, context):
        """Execute the custom step."""
        self.logger.info(f"Executing custom step for {context.server_id}")

        # Step implementation
        try:
            result = self._perform_custom_action(context)
            context.update_status("Custom step completed")
            return result
        except Exception as e:
            self.logger.error(f"Custom step failed: {e}")
            raise

    def _perform_custom_action(self, context):
        """Perform the custom action."""
        # Implementation details
        pass
```

## 📦 Release Process

### Version Management

```bash
# Check current version
make version

# Create releases
make release-patch    # 1.0.0 -> 1.0.1
make release-minor    # 1.0.0 -> 1.1.0
make release-major    # 1.0.0 -> 2.0.0

# Dry run (preview)
make release-dry-run
```

### Release Checklist

1. **Pre-release**:
   - [ ] All tests passing
   - [ ] Documentation updated
   - [ ] CHANGELOG.md reviewed
   - [ ] Version bumped appropriately

2. **Release**:
   - [ ] Create release tag
   - [ ] Push to repository
   - [ ] GitHub release created
   - [ ] PyPI package published

3. **Post-release**:
   - [ ] Verify deployment
   - [ ] Update documentation sites
   - [ ] Announce release

### Changelog Generation

The changelog is automatically generated from conventional commits:

```bash
# Generate changelog
make changelog

# Generate release notes
make changelog-release-notes VERSION=v1.1.0
```

## 🐛 Debugging

### Debug Tools

```bash
# Debug environment
make debug

# View logs
make logs
tail -f logs/hwautomation.log

# Database inspection
sqlite3 hw_automation.db
.tables
.schema servers
```

### Common Debug Patterns

```python
import logging
from hwautomation.utils.debug import debug_context

logger = logging.getLogger(__name__)

def debug_workflow(workflow_id: str):
    """Debug workflow execution."""
    with debug_context(workflow_id):
        logger.debug(f"Starting workflow debug: {workflow_id}")

        # Debug code here
        workflow = get_workflow(workflow_id)
        logger.debug(f"Workflow status: {workflow.status}")
        logger.debug(f"Current step: {workflow.current_step}")
```

### Performance Profiling

```python
import cProfile
import pstats

def profile_function():
    """Profile a function for performance."""
    profiler = cProfile.Profile()
    profiler.enable()

    # Code to profile
    result = expensive_operation()

    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)

    return result
```

## 📚 Additional Resources

- **API Reference**: `docs/API_REFERENCE.md`
- **Getting Started**: `docs/GETTING_STARTED.md`
- **Deployment Guide**: `docs/DEPLOYMENT_GUIDE.md`
- **Examples**: `examples/` directory
- **Tests**: `tests/` directory for usage examples
