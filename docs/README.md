# HWAutomation Documentation

This directory contains detailed documentation for the HWAutomation project.

## Contents

### `ENHANCED_COMMISSIONING.md`
Complete guide to enhanced server commissioning with database integration, including:
- Automatic database tracking throughout provisioning
- SSH connectivity validation and retry logic
- Hardware discovery with vendor-specific tool integration
- Real-time status monitoring and health tracking
- Interactive device selection without manual Machine ID entry

### `DEVICE_SELECTION_SUMMARY.md`
Comprehensive documentation for the device selection enhancement, including:
- Interactive MaaS device browsing and filtering
- Hardware-aware device type suggestions
- Web interface and API integration
- User experience improvements and workflow transformation

### `FLEXIBLE_WORKFLOW_SUMMARY.md`
Documentation for the flexible IPMI workflow implementation, including:
- Optional IPMI IP during initial commissioning
- Manual post-discovery IPMI configuration
- Conditional workflow logic and database integration
- API enhancements and usage examples

### `VENDOR_DISCOVERY.md`
Comprehensive guide to vendor-specific hardware discovery, including:
- Supported vendors (HPE, Supermicro, Dell)
- Automatic tool installation (sumtool, hpssacli, omreport)
- Enhanced discovery capabilities
- Testing and troubleshooting

### `HARDWARE_DISCOVERY.md`
Complete hardware discovery system documentation, including:
- SSH-based system information gathering
- IPMI address detection and configuration
- Network interface discovery
- CLI tools and API integration

### `DATABASE_MIGRATIONS.md`
Comprehensive guide to the database migration system, including:
- Migration overview and features
- Schema evolution examples
- Command-line usage
- Troubleshooting guide

### `BIOS_CONFIGURATION.md`
BIOS configuration management system, including:
- Template-based configuration
- Device type mappings
- Pull-edit-push workflow
- XML template management

### `CONVERSION_GUIDE.md`
Guide for converting from the old flat file structure to the new package-based structure.

### `PACKAGE_README.md`
Detailed package documentation including:
- Installation instructions
- Package structure explanation
- API reference
- Development setup

### `PROJECT_ORGANIZATION.md`
Documentation of project file organization and cleanup, including:
- MAAS testing file reorganization
- Import path corrections and fixes
- Benefits of proper directory structure
- Historical record of organizational changes

## Quick Links

- [Main README](../README.md) - Project overview and quick start
- [Examples](../examples/) - Usage examples
- [Scripts](../scripts/) - Command-line tools
- [Tools](../tools/) - Development tools

## API Documentation

For detailed API documentation, see the individual module docstrings in the `src/hwautomation/` directory:

- `database/` - Database operations and migrations
- `hardware/` - IPMI and RedFish hardware management
- `maas/` - MAAS API client and operations
- `utils/` - Configuration and utility functions
