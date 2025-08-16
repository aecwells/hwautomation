# HWAutomation Documentation

Welcome to the comprehensive documentation for HWAutomation - an enterprise-grade hardware automation platform.

## 📚 Core Documentation

### User Documentation
- **[Getting Started Guide](GETTING_STARTED.md)** - Installation, configuration, and first steps
- **[Hardware Management Guide](HARDWARE_MANAGEMENT.md)** - BIOS configuration, firmware management, and device support
- **[Workflow Guide](WORKFLOW_GUIDE.md)** - Server provisioning, batch operations, and workflow orchestration

### Technical Documentation
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Container deployment, database management, and production setup
- **[Development Guide](DEVELOPMENT_GUIDE.md)** - Architecture, development setup, testing, and contributing
- **[API Reference](API_REFERENCE.md)** - REST API endpoints, Python SDK, and WebSocket events

### Project Information
- **[Changelog & Releases](CHANGELOG_AND_RELEASES.md)** - Version history and release management

## 🗂️ Documentation Structure

The documentation is organized for different audiences:

**New Users**: Start with [Getting Started Guide](GETTING_STARTED.md)
**System Administrators**: Focus on [Hardware Management](HARDWARE_MANAGEMENT.md) and [Deployment Guide](DEPLOYMENT_GUIDE.md)
**Developers**: Begin with [Development Guide](DEVELOPMENT_GUIDE.md) and [API Reference](API_REFERENCE.md)
**DevOps Engineers**: Review [Deployment Guide](DEPLOYMENT_GUIDE.md) and [Workflow Guide](WORKFLOW_GUIDE.md)

## 🏛️ Historical Documentation

Legacy and historical documentation has been moved to the `archive/` directory to maintain project history while keeping current documentation focused and relevant.

## 🔄 Documentation Maintenance

This documentation is actively maintained and updated with each release. The consolidation effort in January 2025 reduced documentation from 39 files to 8 core files for better organization and maintainability.

For documentation issues or suggestions, please open an issue in the project repository.

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
