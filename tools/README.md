# Development Tools

This directory contains development and maintenance tools for the HWAutomation project.

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
