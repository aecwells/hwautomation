# HWAutomation Documentation

This directory contains comprehensive documentation for the HWAutomation enterprise hardware automation platform.

## 📚 Documentation Structure

### `CHANGELOG_AND_RELEASES.md`

Complete guide to changelog generation and release management:

- Conventional commits setup and best practices
- Automated changelog generation from git history
- Semantic versioning and release automation
- GitHub Actions integration for CI/CD
- Development workflow and team collaboration

### `BIOS_AND_FIRMWARE.md`

Complete guide to BIOS configuration and firmware management:

- Multi-vendor BIOS configuration with intelligent method selection
- Enterprise firmware management with real vendor tools (HPE iLORest, Supermicro IPMItool, Dell RACADM)
- Firmware-first provisioning workflows
- Real-time monitoring with WebSocket integration
- Device-specific templates and configuration management

### `WORKFLOW_ORCHESTRATION.md`

Comprehensive workflow orchestration and automation system:

- 7-step server provisioning workflow with optional firmware-first mode
- Real-time sub-task reporting and progress tracking
- Workflow lifecycle management with cancellation support
- Web interface integration with live progress updates
- API integration and direct Python usage examples

### `HARDWARE_COMMISSIONING.md`

Hardware discovery and automated commissioning capabilities:

- Automatic hardware discovery via SSH (system info, IPMI configuration)
- Enhanced 8-step commissioning workflow with hardware discovery
- Network range scanning for IPMI address discovery
- Real-time commissioning progress with visual feedback
- Multi-vendor hardware support and detection

## 🚀 Quick Start

1. **Container Deployment**: See `CONTAINER_ARCHITECTURE.md` for Docker-based setup
2. **Database Setup**: Reference `DATABASE_MIGRATIONS.md` for database initialization
3. **Hardware Configuration**: Use `BIOS_AND_FIRMWARE.md` for device configuration
4. **Workflow Management**: Follow `WORKFLOW_ORCHESTRATION.md` for automation setup
5. **Hardware Discovery**: Implement using `HARDWARE_COMMISSIONING.md` guidance

## 📖 Documentation Scope

These documents provide comprehensive coverage of:

- **Hardware Automation**: Complete BIOS and firmware management
- **Workflow Orchestration**: End-to-end server provisioning automation
- **Hardware Discovery**: Automatic detection and commissioning
- **Container Deployment**: Production-ready deployment architecture
- **Database Management**: Schema management and migrations

## 🔧 System Architecture

The HWAutomation platform consists of:

- **Container-First Architecture**: Docker-based deployment with single-container design
- **SQLite Database**: Lightweight, embedded database with migration support
- **Multi-Vendor Support**: HPE, Supermicro, Dell hardware integration
- **Real-time Monitoring**: WebSocket-based progress tracking and updates
- **Enterprise Features**: Firmware management, BIOS configuration, and workflow automation

For detailed implementation guidance, refer to the specific documentation files above.

### `PACKAGE_README.md`

Package development and distribution guidelines

### `PROJECT_ORGANIZATION.md`

Overall project structure and development guidelines

### `PROJECT_STATUS_AND_ROADMAP.md`

High-level status of implemented features and upcoming work

## Quick Links

- [Main README](../README.md) - Project overview and quick start
- [Examples](../examples/) - Usage examples
- [Tests](../tests/) - Test suite
- [Tools](../tools/) - Development tools

## API Documentation

For detailed API documentation, see the individual module docstrings in the `src/hwautomation/` directory:

- `web/` - Flask web application and UI
- `database/` - SQLite operations and migrations
- `hardware/` - IPMI and Redfish hardware management
- `maas/` - MAAS API client and operations
- `utils/` - Configuration and utility functions
- `cli/` - Command-line interface
