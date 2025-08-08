# Examples Directory

This directory contains practical examples and demonstrations of the Hardware Automation system capabilities.

## Available Examples

### Basic Examples

- **`basic_usage.py`** - Basic hardware automation usage
- **`bios_config_example.py`** - Basic BIOS configuration examples
- **`hardware_discovery_demo.py`** - Hardware discovery capabilities
- **`vendor_discovery_test.py`** - Vendor-specific discovery testing
- **`orchestration_example.py`** - System orchestration workflows
- **`enhanced_commissioning_demo.py`** - Enhanced commissioning process
- **`workflow_subtasks_demo.py`** - Workflow subtask demonstrations

### Redfish Integration Examples

- **`redfish_example.py`** - Basic Redfish API usage examples

### BIOS Configuration Examples

- Use `bios_config_example.py` for BIOS configuration basics
- Use `redfish_example.py` for Redfish-centric flows

## BIOS Configuration Decision Logic

These examples demonstrate the advanced capabilities of the enhanced BIOS configuration system:

### Key Features Demonstrated

- ✅ **Per-setting optimization** - Each BIOS setting uses the optimal method (Redfish vs vendor tools)
- ✅ **Performance vs reliability tuning** - Choose between speed-optimized or reliability-optimized configurations  
- ✅ **Intelligent unknown setting handling** - Automatic analysis of unknown BIOS settings
- ✅ **Parallel execution** - Redfish and vendor tool operations run in parallel
- ✅ **Batch optimization** - Efficient batching of operations for better performance
- ✅ **Comprehensive performance estimation** - Detailed time estimates before execution

### Usage Example

```python
# Intelligent BIOS configuration
from hwautomation.hardware.bios_config import BiosConfigManager

manager = BiosConfigManager()
result = manager.apply_bios_config_smart_enhanced(
    device_type="a1.c5.large",
    target_ip="192.168.1.100",
    username="ADMIN", 
    password="password",
    prefer_performance=True,  # or False for reliability
    dry_run=True  # Safe testing mode
)
```

## Running Examples

### Prerequisites

```bash
# Install dependencies (if needed)
pip install -r requirements.txt

# Set Python path
export PYTHONPATH=/path/to/HWAutomation/src
```

### Standalone Examples (No Hardware Required)

```bash
# BIOS configuration demo (recommended starting point)
python3 examples/bios_config_example.py

# Basic usage examples
python3 examples/basic_usage.py
python3 examples/hardware_discovery_demo.py
```

### Hardware-Connected Examples

```bash
# BIOS configuration (requires target hardware)
python3 examples/bios_config_example.py

# Redfish examples (requires Redfish-capable BMC)
python3 examples/redfish_example.py

# Enhanced commissioning (requires full hardware setup)
python3 examples/enhanced_commissioning_demo.py
```

## Example Categories

### 🚀 **BIOS Configuration (Latest)**

Intelligent BIOS configuration with per-setting optimization.

### 🔧 **Hardware Discovery**

Examples showing hardware detection and vendor identification capabilities.

### ⚙️ **BIOS Configuration**

Traditional and enhanced BIOS configuration workflows.

### 🌐 **Redfish Integration**

Modern BMC management using Redfish API standards.

### 🎯 **Orchestration**

Complete workflow examples for production deployments.

## Unified Runner

List and run examples via a single entry point:

```bash
python -m examples.run --list
python -m examples.run firmware_manager_smoke -- --target-ip 192.168.1.100
python -m examples.run firmware_manager_demo
python -m examples.run firmware_provisioning_demo
```

Common flags (most examples accept these):

```bash
--device-type a1.c5.large
--target-ip 192.168.1.100
--username ADMIN
--password ********
--dry-run | --no-dry-run
```

## Getting Help

- See `docs/` directory for comprehensive documentation
- Check `tests/` directory for additional usage patterns
- Review `configs/` directory for configuration examples
- Each example file contains inline documentation and comments

## Contributing

When adding new examples:

1. Include comprehensive inline documentation
2. Add error handling and validation
3. Provide both standalone and integrated versions
4. Update this README with the new example
5. Add corresponding tests in `tests/` directory
