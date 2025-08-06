# Development Tools

This directory contains development, testing, and command-line tools for the HWAutomation project.

## Directory Structure

### `cli/` - Production CLI Tools
Command-line interfaces for production use:
- `bios_manager.py` - BIOS Configuration Management CLI
- `orchestrator.py` - Server Orchestration CLI
- `hardware_discovery.py` - Hardware Discovery CLI  
- `db_manager.py` - Database Management CLI
- `realtime_monitor.py` - Real-time Workflow Monitor
- `workflow_monitor.py` - Workflow Debug Monitor

### `testing/` - Test Scripts
Various test scripts for project validation:
- `test_*.py` - Unit and integration tests
- `run_tests.py` - Test runner
- `run_tests.bat` - Windows test runner
- `test_bios_system.bat` - Windows BIOS test script

### `debug/` - Debug Scripts  
Debugging and troubleshooting utilities:
- `debug_*.py` - Debug scripts for various components

### `config/` - Configuration Tools
Tools for building and managing configurations:
- `build_device_configs.py` - Build device mappings from data sources
- `merge_configs.py` - Merge configuration files

### `migration/` - Migration & Setup Tools
Tools for project migration and setup:
- `migrate_config.py` - Configuration migration utility
- `migration_guide.py` - Migration guidance and documentation
- `setup_testing.py` - Modern testing infrastructure setup

### `verification/` - Validation & Verification Tools
Tools for validating project state and packages:
- `syntax_check.py` - Python syntax validation
- `validate_package.py` - Package structure validation
- `verify_sumtool.py` - Sumtool package verification
- `verify_db_consolidation.py` - Database consolidation verification
- `fix_null_database_values.py` - Database repair utility

## External Dependencies
- `sum_2.14.0_Linux_x86_64_20240215.tar.gz` - HP SUM (Smart Update Manager) package

## Usage Examples

Run these tools from the project root directory:

### CLI Tools
```bash
# Monitor workflows in real-time
python tools/cli/realtime_monitor.py

# Debug specific workflow
python tools/cli/workflow_monitor.py <workflow_id>

# Manage BIOS configurations
python tools/cli/bios_manager.py --help
```

### Configuration Tools
```bash
# Build device configurations
python tools/config/build_device_configs.py

# Merge configuration files
python tools/config/merge_configs.py
```

### Verification Tools
```bash
# Check syntax across project
python tools/verification/syntax_check.py

# Validate package structure
python tools/verification/validate_package.py

# Verify sumtool package
python tools/verification/verify_sumtool.py
```

### Testing Tools
```bash
# Run all tests
python tools/testing/run_tests.py

# Run specific test
python tools/testing/test_bios_config.py
```

### Migration Tools
```bash
# Get migration guidance
python tools/migration/migration_guide.py

# Setup modern testing infrastructure
python tools/migration/setup_testing.py
```
