# Tests

This directory contains tests for the HWAutomation project.

## Structure

- `test_database.py` - Database operations tests
- `test_hardware.py` - Hardware management tests  
- `test_bios_config.py` - BIOS configuration tests
- `test_utils.py` - Utility function tests

### MAAS Testing Scripts

- `debug_maas.py` - Debug script for MAAS connection issues
- `test_maas_simple.py` - Simple MAAS connection test with hardcoded config
- `test_fixed_maas.py` - Test for the fixed MAAS client implementation

### Orchestration Testing Scripts

- `test_device_selection.py` - Device selection service functionality tests
- `test_flexible_workflow.py` - Flexible IPMI workflow validation tests

## Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_database.py

# Run with coverage
python -m pytest tests/ --cov=hwautomation

# Run orchestration tests specifically
python tests/test_device_selection.py
python tests/test_flexible_workflow.py
```

### Running MAAS Debug Scripts

```bash
# Debug MAAS connection issues
cd /home/ubuntu/HWAutomation
python tests/debug_maas.py

# Simple MAAS connection test
python tests/test_maas_simple.py

# Test fixed MAAS client
python tests/test_fixed_maas.py
```

## Test Requirements

Install test dependencies:
```bash
pip install pytest pytest-cov
```

## Adding Tests

When adding new functionality, please include corresponding tests in the appropriate test file.
