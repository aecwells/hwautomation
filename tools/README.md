# HWAutomation Tools - Reorganized Structure

This directory contains development, debugging, validation, and maintenance tools for the HWAutomation project.

## 📁 Directory Structure

### `active/` - Working Tools
All functional, maintained tools organized by purpose:

#### `active/cli/` - Command Line Interfaces
- `legacy/` - CLI tools that need import fixes

#### `active/debug/` - Debugging & Analysis
- `debug_config_paths.py` - Configuration path debugging ✅
- `config_analysis.py` - Configuration analysis
- `unified_config_integration_analysis.py` - Unified config analysis
- `legacy/` - Legacy debug tools (may need fixes)

#### `active/maintenance/` - Project Maintenance
- `release.py` - Release management ✅
- `generate_changelog.py` - Git-based changelog generator ✅
- `cleanup_tools.sh` - Tool management script ✅
- `add_device_type.py` - Add new device types ✅
- `batch_add_flex_devices.py` - Batch device operations ✅
- `setup/` - Development environment setup
- `config/` - Configuration management tools

#### `active/reports/` - Report Generation
- (Empty - for future report tools)

#### `active/validation/` - Testing & Quality
- `verification/` - Package and system validation
- `testing/` - Test runners and scripts
- `quality/` - Code quality tools

### `obsolete/` - Deprecated Tools
Tools that are no longer needed or depend on missing files:
- `consolidate_device_configs.py` - Completed (unified config exists)
- `update_firmware_repository.py` - Missing Excel dependency
- `integration_summary.py` - Missing Excel dependency
- `parse_excel_motherboards.py` - Missing Excel dependency
- `migration/` - Migration scripts (likely completed)
- `clean_legacy_theme.js` - Legacy cleanup
- `sum_2.14.0_Linux_x86_64_20240215.tar.gz` - Binary file

## 🔧 Usage

### Working Tools (Ready to Use)
```bash
# Configuration debugging
python tools/active/debug/debug_config_paths.py

# Project maintenance
python tools/active/maintenance/generate_changelog.py --help
python tools/active/maintenance/release.py --help
bash tools/active/maintenance/cleanup_tools.sh

# Device management
python tools/active/maintenance/add_device_type.py --help
```

### Tools Needing Fixes
See "Step 6: Fix Broken Tools" section below.

## 🚧 Next Steps

1. **Fix broken CLI tools** - Update import paths
2. **Fix validation tools** - Update file paths and imports
3. **Test legacy tools** - Determine which are still useful
4. **Remove truly obsolete tools** - Clean up obsolete directory

## 📝 Tool Status Legend
- ✅ Working and tested
- ⚠️ Needs minor fixes
- ❌ Broken/needs major fixes
- 🗑️ Obsolete/deprecated

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
