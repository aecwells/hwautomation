# HWAutomation Documentation

This directory contains detailed documentation for the HWAutomation project.

## Core System Documentation

### `CONTAINER_ARCHITECTURE.md`
Complete guide to the container-first deployment architecture, including:
- Multi-stage Docker builds and deployment options
- Single-container SQLite-based architecture
- Health monitoring and service management
- Production deployment guidelines

### `DATABASE_MIGRATIONS.md`
Comprehensive guide to the SQLite database migration system, including:
- Migration overview and features
- Schema evolution from version 1 to 6
- Command-line usage and API integration
- Troubleshooting guide

### `BIOS_CONFIGURATION.md`
Complete BIOS configuration management documentation, including:
- Device type configuration and templating
- XML configuration generation and application
- Vendor-specific BIOS management
- API usage and CLI tools

## Hardware Management Documentation

### `HARDWARE_DISCOVERY.md`
Complete hardware discovery system documentation, including:
- SSH-based system information gathering
- IPMI address detection and configuration
- Network interface discovery and validation
- CLI tools and API integration

### `VENDOR_DISCOVERY.md`
Comprehensive guide to vendor-specific hardware discovery, including:
- Supported vendors (HPE, Supermicro, Dell)
- Automatic tool installation (sumtool, hpssacli, omreport)
- Enhanced discovery capabilities and system detection
- Testing and troubleshooting

## Workflow and Orchestration

### `ORCHESTRATION.md`
Complete workflow orchestration system documentation, including:
- 8-step automated server provisioning workflow
- Workflow manager and execution engine
- Status tracking and error handling
- API integration and monitoring

### `ENHANCED_COMMISSIONING.md`
Complete guide to enhanced server commissioning with database integration, including:
- Automatic database tracking throughout provisioning
- SSH connectivity validation and retry logic
- Hardware discovery with vendor-specific tool integration
- Real-time status monitoring and health tracking

### `FLEXIBLE_WORKFLOW_SUMMARY.md`
Documentation for the flexible IPMI workflow implementation, including:
- Optional IPMI IP during initial commissioning
- Manual post-discovery IPMI configuration
- Conditional workflow logic and database integration
- API enhancements and usage examples

### `COMMISSIONING_PROGRESS.md`
Real-time commissioning progress monitoring documentation, including:
- Progress tracking and status updates
- WebSocket integration for live updates
- Error handling and recovery mechanisms

## User Interface and Experience

### `DEVICE_SELECTION_SUMMARY.md`
Comprehensive documentation for the device selection enhancement, including:
- Interactive MaaS device browsing and filtering
- Hardware-aware device type suggestions
- Web interface and API integration
- User experience improvements and workflow transformation

## System Maintenance and Fixes

### `SSH_TIMEOUT_FIX.md`
Documentation for SSH timeout and connectivity improvements

### `REAL_TIME_MONITORING_FIXED.md`
Real-time monitoring system fixes and enhancements

### `CONTAINER_CLEANUP_SUMMARY.md`
Recent container architecture simplification, including:
- Removal of unused PostgreSQL and Redis containers
- SQLite-based architecture benefits
- Performance and deployment improvements

## Additional Resources

### `FILE_ORGANIZATION_UPDATE.md`
Project structure and organization guidelines

### `LOCAL_SUMTOOL_DEPLOYMENT.md`
Local deployment of vendor-specific tools

### `SUMTOOL_INSTALLATION_IMPROVEMENTS.md`
Enhanced installation procedures for vendor tools

### `PACKAGE_README.md`
Package development and distribution guidelines

### `PROJECT_ORGANIZATION.md`
Overall project structure and development guidelines

## Quick Links

- [Main README](../README.md) - Project overview and quick start
- [Examples](../examples/) - Usage examples  
- [Tests](../tests/) - Test suite
- [Tools](../tools/) - Development tools

## API Documentation

For detailed API documentation, see the individual module docstrings in the `src/hwautomation/` directory:

- `web/` - Flask web application and UI
- `database/` - SQLite operations and migrations
- `hardware/` - IPMI and RedFish hardware management
- `maas/` - MAAS API client and operations
- `utils/` - Configuration and utility functions
- `cli/` - Command-line interface
