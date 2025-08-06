# Development Tools

This directory contains development, testing, and command-line tools for the HWAutomation project.

## Directory Structure

### `cli/` - Production CLI Tools
Command-line interfaces for production use:
- `bios_manager.py` - BIOS Configuration Management CLI
- `orchestrator.py` - Server Orchestration CLI
- `hardware_discovery.py` - Hardware Discovery CLI  
- `db_manager.py` - Database Management CLI

### `testing/` - Test Scripts
Various test scripts for project validation:
- `test_*.py` - Unit and integration tests
- `run_tests.py` - Test runner

### `debug/` - Debug Scripts  
Debugging and troubleshooting utilities:
- `debug_*.py` - Debug scripts for various components

### Root Level - Maintenance Tools
Development and maintenance utilities

## Tools

### `syntax_check.py`
Validates Python syntax and basic imports across the project.

Usage:
```bash
python tools/syntax_check.py
```

### `validate_package.py`
Validates the package structure and dependencies.

Usage:
```bash
python tools/validate_package.py
```

### `migration_guide.py`
Provides guidance for migrating from old flat file structure to the new package structure.

Usage:
```bash
python tools/migration_guide.py
```

### `setup_testing.py`
Sets up modern unit testing infrastructure with pytest and coverage reporting.

Usage:
```bash
python tools/setup_testing.py
```

## Usage

Run these tools from the project root directory:

```bash
# Check syntax
python tools/syntax_check.py

# Validate package structure
python tools/validate_package.py

# Get migration guidance
python tools/migration_guide.py

# Setup modern testing infrastructure
python tools/setup_testing.py
```
