# Tests

This directory contains tests for the HWAutomation project.

## Structure

- `test_database.py` - Database operations tests
- `test_hardware.py` - Hardware management tests  
- `test_bios_config.py` - BIOS configuration tests
- `test_utils.py` - Utility function tests

### BIOS Configuration Tests ⭐

- **`test_phase2_focused.py`** - Comprehensive BIOS decision logic testing
- **`test_phase2_decision_logic.py`** - Detailed BIOS integration testing

### Real-time Monitoring Tests 🚀

- **`test_phase3_standalone.py`** - Complete monitoring demonstration
- **`test_phase3_monitoring.py`** - Monitoring system integration tests

### Firmware Update Tests 🔧

- **`test_firmware_manager.py`** - Firmware management and update functionality tests
- **`test_firmware_integration.py`** - Integration tests for firmware-first workflows

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

# Run BIOS configuration tests (standalone, no hardware required)
python3 tests/test_phase2_focused.py
python3 tests/test_phase2_decision_logic.py

# Run monitoring tests (standalone demonstrations)
python3 tests/test_phase3_standalone.py
python3 tests/test_phase3_monitoring.py

# Run firmware provisioning demo
python3 examples/firmware_provisioning_demo.py
python3 tests/test_firmware_manager.py
python3 tests/test_firmware_integration.py

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
