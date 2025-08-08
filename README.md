# Hardware Automation Package

![CI/CD Pipeline](https://github.com/aecwells/hwautomation/actions/workflows/ci.yml/badge.svg?branch=main)
![Tests](https://github.com/aecwells/hwautomation/actions/workflows/test.yml/badge.svg?branch=main)
[![codecov](https://codecov.io/gh/aecwells/hwautomation/branch/main/graph/badge.svg)](https://codecov.io/gh/aecwells/hwautomation)
![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)
![Code Quality](https://img.shields.io/badge/code%20quality-black%20%7C%20isort%20%7C%20flake8%20%7C%20mypy-brightgreen)
![Security](https://img.shields.io/badge/security-bandit%20scanned-green)


A comprehensive Python package for hardware automation, server management, and infrastructure operations. Features a modern container-first architecture with production-ready web GUI, complete CLI capabilities, and enterprise-grade firmware management.

## 🎯 Key Capabilities

### **Enterprise Hardware Automation Platform**

- 🔧 **Complete Server Provisioning**: Automated workflows from commissioning to production-ready state
- 💾 **Firmware Management**: Multi-vendor firmware updates with real vendor tools (HPE iLORest, Supermicro IPMItool, Dell RACADM)
- ⚙️ **BIOS Configuration**: Intelligent configuration management with device-specific templates and monitoring
- 🌐 **MaaS Integration**: Full Metal-as-a-Service API integration for bare-metal provisioning
- 📊 **Real-time Monitoring**: Live progress tracking with WebSocket updates and comprehensive audit trails
- 🏗️ **Multi-Vendor Support**: HPE Gen10, Supermicro X11, Dell PowerEdge with optimized device-specific workflows

## 🎉 Recent Enhancements (August 2025)

### **Web Interface Modernization**
- **📐 Blueprint Architecture**: Refactored monolithic 853-line Flask app into modular blueprint structure
- **🔧 Improved Maintainability**: 6 focused route modules (56-302 lines each) for easier development and testing
- **📊 Enhanced Status Indicators**: Smart MaaS connection status with visual indicators (Connected/Disconnected/Not Configured)
- **🎨 Better UI/UX**: Redesigned status bar positioning under logo with responsive design and proper color coding
- **⚡ Zero Breaking Changes**: All existing URLs and APIs preserved during refactoring

### **Developer Experience Improvements**
- **🏗️ Team-Friendly Architecture**: Single-responsibility blueprints enable parallel development
- **🧪 Easier Testing**: Modular structure simplifies unit testing and debugging
- **📈 Scalable Foundation**: Clean architecture ready for new features and team expansion

### **Code Quality & CI/CD Enhancements**
- **🚀 Comprehensive CI/CD Pipeline**: Multi-stage GitHub Actions workflow with quality gates
- **🎨 Code Formatting**: Automated Black formatting applied to entire codebase (59+ files)
- **📦 Import Organization**: isort import sorting for consistent code structure
- **🔍 Code Analysis**: flake8 linting with project-specific configurations
- **🛡️ Security Scanning**: Bandit security analysis integrated into CI pipeline
- **📊 Type Checking**: MyPy type checking configured for gradual adoption
- **🧪 Multi-Version Testing**: Python 3.9-3.12 compatibility testing
- **📈 Test Coverage**: Automated coverage reporting with realistic baselines

## 🚀 Quick Start (Container-First)

### Prerequisites

- Docker and Docker Compose v2+
- Git

### Launch the Application

```bash
# Clone and start
git clone <your-repo-url>
cd hwautomation

# Start the application
docker compose up -d app

# Access the web interface
# Open in your browser: <http://localhost:5000>
```

The web GUI provides a modern dashboard for device management, workflow orchestration, and system monitoring with an enhanced modular architecture and improved status indicators.

## Features

### 🚀 **Firmware Management**

- **🔧 Firmware-First Provisioning**: Complete workflow with firmware updates before system configuration
- **💾 Multi-Vendor Firmware Support**: Real vendor tool integration (HPE iLORest, Supermicro IPMItool, Dell RACADM)
- **📊 Intelligent Update Management**: Priority-based firmware ordering, compatibility checking, and automated rollback
- **🌐 Firmware Repository System**: Centralized firmware storage with automated downloads and integrity validation
- **📈 Advanced Progress Monitoring**: Real-time sub-task reporting with WebSocket updates and operation tracking

### ⚙️ **BIOS Configuration Management**

- **🎯 Smart Configuration**: Device-specific BIOS templates with intelligent pull-edit-push workflows
- **📋 Template System**: Comprehensive BIOS settings templates organized by device type
- **🔍 Enhanced Monitoring**: Real-time configuration progress with detailed sub-task reporting
- **🏗️ Multi-Method Support**: Redfish API and vendor-specific tool integration with automatic fallback
- **📊 Configuration Analytics**: Success rate tracking, execution time monitoring, and error analysis

### 🏗️ **Core Platform Capabilities**

- **🌐 Container-First Architecture**: Production-ready Docker deployment with SQLite database
- **🖥️ Modern Web GUI**: Blueprint-based Flask architecture with modular route organization and real-time status indicators
- **📊 Enhanced Dashboard**: Intelligent status monitoring with MaaS connection indicators and system health visualization
- **⚡ Multi-Stage Builds**: Optimized containers for development, production, web, and CLI use cases
- **Complete Orchestration**: Multiple workflow types including standard provisioning and firmware-first workflows
- **🔍 Hardware Discovery**: SSH-based system information gathering with IPMI detection and vendor identification
- **MAAS Integration**: Complete API client for Metal as a Service operations with smart status detection
- **IPMI Management**: Hardware control via IPMI protocol
- **Redfish Support**: Modern BMC management through Redfish APIs with firmware update capabilities
- **Database Migrations**: Robust SQLite schema versioning and upgrade system
- **Configuration Management**: Flexible YAML/JSON configuration with environment overrides
- **Network Utilities**: SSH operations, connectivity testing, and IP management
- **📊 Health Monitoring**: Comprehensive service health checks and monitoring endpoints

## Architecture Overview

### Container-First Design

```text
hwautomation/
├── docker/
│   └── Dockerfile.web         # 🐳 Multi-stage container builds
├── docker-compose.yml         # 🏗️ Production service orchestration
├── docker-compose.override.yml # 🛠️ Development overrides
├── src/hwautomation/          # 📦 Main package source code
│   ├── web/                   # 🌐 Flask web application with blueprint architecture
│   │   ├── app.py             # 🏭 Clean app factory with blueprint registration
│   │   ├── routes/            # 📁 Modular blueprint organization (NEW)
│   │   │   ├── core.py        # 🏠 Dashboard and health endpoints
│   │   │   ├── database.py    # 🗄️ Database management routes
│   │   │   ├── orchestration.py # 🔄 Workflow orchestration APIs
│   │   │   ├── maas.py        # 🌐 MaaS integration endpoints
│   │   │   ├── logs.py        # 📊 System logging APIs
│   │   │   └── firmware.py    # 🔧 Firmware management routes
│   │   └── templates/         # 🎨 Enhanced UI with status indicators
│   ├── hardware/              # ⚙️ IPMI, Redfish, and Firmware management
│   │   ├── firmware_manager.py           # 🔧 Multi-vendor firmware operations
│   │   └── firmware_provisioning_workflow.py # 🚀 Firmware-first workflows
│   ├── orchestration/         # 🔄 Workflow management and server provisioning
│   ├── database/              # 🗄️ SQLite operations and migrations
│   ├── maas/                  # 🌐 MAAS API client
│   └── utils/                 # 🔧 Configuration and utilities
├── configs/
│   ├── bios/                  # 📁 BIOS configuration templates and rules
│   └── firmware/              # 📁 Firmware repository and update configurations
├── examples/                  # 📚 Usage examples including firmware demos
├── tests/                     # 🧪 Test suite
├── docs/                      # 📖 Documentation
└── tools/                     # 🛠️ Development and maintenance tools
```

### Service Architecture

| Service | Container | Port | Purpose | Health Check |
|---------|-----------|------|---------|--------------|
| **Web GUI** | `hwautomation-app` | 5000 | Primary interface | ✅ `/health` endpoint |
| **MaaS Simulator** | `hwautomation-maas-sim` | 5240 | Testing only | ✅ Optional (testing profile) |

**Database**: SQLite file-based database (`hw_automation.db`) - no separate container required

## Container Deployment

### Production Deployment

```bash
# Quick start - simplified single-container deployment
docker compose up -d app

# Manual control
docker compose build app    # Build container
docker compose ps          # Check status
docker compose logs app    # View logs
docker compose down        # Stop services
```

### Development Mode

```bash
# Development with live code reload
docker compose up -d app        # Uses override config automatically
docker compose exec app bash    # Access container shell
```

### Health Monitoring

```bash
# Check application health
curl http://localhost:5000/health

# Example response:
{
  "status": "healthy",
  "services": {
    "database": "healthy",
    "maas": "healthy",
    "bios_manager": "healthy",
    "firmware_manager": "healthy",
    "workflow_manager": "healthy",
    "bios_device_types": 87,
    "firmware_repository": "ready",
    "maas_machines": 5,
    "active_workflows": 0
  },
  "version": "1.0.0"
}
```

## Installation Options

### 🚀 Container Deployment (Recommended)

Fastest way to get started with full functionality:

```bash
# Clone and run
git clone <your-repo-url>
cd hwautomation
docker compose up -d app

# Access web GUI at http://localhost:5000
```

### 📦 Package Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd hwautomation

# Create and activate a virtual environment (recommended)
python3 -m venv hwautomation-env
source hwautomation-env/bin/activate

# Install in development mode
pip install -e .

# Or install normally
pip install .
```

> **Note for Ubuntu/Debian users**: If you encounter an "externally-managed-environment" error, you need to use a virtual environment. This is a security feature in newer Python installations. Follow these steps:

```bash
# Install required packages first
sudo apt update
sudo apt install -y python3.12-venv python3-full

# Then create and use a virtual environment
python3 -m venv hwautomation-env
source hwautomation-env/bin/activate
pip install -e .

# Test the installation
python -c 'import hwautomation; print("HWAutomation package imported successfully!")'
```

> **Important Notes**:
>
> - When testing the import in bash, always use single quotes around the Python command to avoid bash history expansion issues with exclamation marks.
> - If you get "bash: !': event not found" error, you're using double quotes instead of single quotes.
> - The virtual environment approach is required on Ubuntu/Debian systems with externally-managed Python environments.

### Requirements

- Python 3.8+
- External dependencies:
  - `ipmitool` (for IPMI operations)
  - SSH access to target servers
  - MAAS server access with API credentials

## Quick Start

### 1. Configuration

Create a `config.yaml` file:

```yaml
maas:
  host: "http://your-maas-server:5240/MAAS"
  consumer_key: "your-consumer-key"
  token_key: "your-token-key"
  token_secret: "your-token-secret"

database:
  path: "hw_automation.db"
  table_name: "servers"
  auto_migrate: true

ipmi:
  username: "admin"
  timeout: 30

ssh:
  username: "ubuntu"
  timeout: 30
```

### 2. Basic Usage

```python
from hwautomation import DbHelper
from hwautomation.maas.client import create_maas_client
from hwautomation.utils.env_config import load_config

# Load configuration
config = load_config()

# Initialize database with auto-migration
db_helper = DbHelper(
    tablename=config['database']['table_name'],
    db_path=config['database']['path'],
    auto_migrate=True
)

# Create MAAS client
maas_client = create_maas_client(config['maas'])

# Get machines from MAAS
machines = maas_client.get_machines()
print(f"Found {len(machines)} machines")

# Update database
for machine in machines:
    if not db_helper.checkifserveridexists(machine['system_id'])[0]:
        db_helper.createrowforserver(machine['system_id'])

    db_helper.updateserverinfo(
        machine['system_id'],
        'status_name',
        machine['status_name']
    )

# Show database contents
db_helper.printtableinfo()
db_helper.close()
```

### 3. BIOS Configuration Management

```python
from hwautomation.hardware.bios_config import BiosConfigManager

# Initialize BIOS configuration manager
bios_manager = BiosConfigManager()

# List available device types
device_types = bios_manager.get_device_types()
print(f"Available device types: {device_types}")

# Generate XML configuration for a1.c5.large
xml_config = bios_manager.generate_xml_config('a1.c5.large')
print("Generated BIOS configuration:")
print(xml_config)

# Apply configuration to a system (enhanced monitoring)
# result = bios_manager.apply_bios_config_smart('a1.c5.large', '192.168.1.100', 'ADMIN', 'password')
```

### 4. Firmware Management

```python
from hwautomation.hardware.firmware_manager import FirmwareManager
from hwautomation.hardware.firmware_provisioning_workflow import create_firmware_provisioning_workflow

# Initialize firmware manager
firmware_manager = FirmwareManager()

# Check firmware versions
firmware_info = await firmware_manager.check_firmware_versions(
    'a1.c5.large', '192.168.1.100', 'admin', 'password'
)

# Create firmware-first provisioning workflow
workflow = create_firmware_provisioning_workflow()
context = workflow.create_provisioning_context(
    server_id="server_001",
    device_type="a1.c5.large",
    target_ip="192.168.1.100",
    credentials={"username": "admin", "password": "password"},
    firmware_policy="recommended"
)

# Execute complete firmware-first provisioning
result = await workflow.execute_firmware_first_provisioning(context)
print(f"Provisioning completed: {result.success}")
print(f"Firmware updates applied: {result.firmware_updates_applied}")
print(f"BIOS settings applied: {result.bios_settings_applied}")
```

### 5. Web GUI Usage

Launch the modern web interface:

```bash
# Container deployment (recommended)
docker compose up -d app

# Access GUI at: <http://127.0.0.1:5000>
```

**GUI Features:**

- 🎛️ Interactive BIOS configuration management
- 🧰 Firmware Management Dashboard: Real-time firmware status, version tracking, and update scheduling
- 📊 Real-time dashboard with system status and workflow progress
- ⚡ Live progress updates via WebSocket with detailed sub-task granularity
- 🚀 **Firmware-First Provisioning**: Complete workflow orchestration from web interface
- 📱 Responsive design for mobile/tablet
- 🔍 Advanced filtering and search
- 📁 Download configurations and logs
- 💾 SQLite database management interface

**API Endpoints (Blueprint Architecture):**

**Core Routes:**
- `GET /` - Modern dashboard with enhanced status indicators
- `GET /health` - System health check endpoint

**Orchestration Routes:**
- `POST /api/orchestration/provision` - Standard server provisioning workflow
- `POST /api/orchestration/provision-firmware-first` - Firmware-first provisioning workflow
- `GET /api/orchestration/workflows/{id}/status` - Real-time workflow status with sub-task details
- `POST /api/orchestration/workflow/{id}/cancel` - Cancel running workflows with graceful cleanup

**Database Routes:**
- `GET /api/database/info` - Database statistics and information
- `GET /api/database/export` - Export database data

**MaaS Routes:**
- `GET /api/maas/discover` - Discover available MaaS machines

**Logs Routes:**
- `GET /api/logs/` - System logs with filtering capabilities

**Firmware Routes:**
- `GET /api/firmware/status` - Firmware management status

### 6. Command Line Usage

```bash
# Run CLI via console scripts
hw-cli --help
hwautomation --help

# Start web interface
hw-web

# Run examples
python examples/run.py --list
```

## Package Structure

```bash
src/hwautomation/
├── __init__.py              # Main package exports
├── web/
│   ├── app.py              # Clean Flask app factory with blueprint registration
│   ├── routes/             # Modular blueprint architecture
│   │   ├── core.py         # Dashboard and health endpoints
│   │   ├── database.py     # Database management APIs
│   │   ├── orchestration.py # Workflow orchestration APIs
│   │   ├── maas.py         # MaaS integration endpoints
│   │   ├── logs.py         # System logging APIs
│   │   └── firmware.py     # Firmware management APIs
│   └── templates/          # Enhanced web UI templates with status indicators
├── orchestration/
│   ├── workflow_manager.py       # Core workflow orchestration
│   └── server_provisioning.py   # Standard and firmware-first provisioning workflows
├── database/
│   ├── helper.py           # SQLite database operations
│   └── migrations.py       # Schema migration system
├── maas/
│   └── client.py          # MAAS API client
├── hardware/
│   ├── ipmi.py                           # IPMI management
│   ├── redfish_manager.py                # Redfish operations with firmware support
│   ├── bios_config.py                    # BIOS configuration management
│   ├── firmware_manager.py               # Multi-vendor firmware management
│   └── firmware_provisioning_workflow.py # Complete firmware-first workflow
├── utils/
│   ├── config.py         # Configuration management
│   └── network.py        # Network utilities
└── cli/
    └── main.py          # Command-line interface
```

## Database Schema

The package includes a complete SQLite migration system with versioned schema updates:

- **Version 1**: Basic server table with core fields
- **Version 2**: Added IPMI fields for hardware management
- **Version 3**: Added timestamps for tracking
- **Version 4**: Added server metadata support
- **Version 5**: Added power state tracking
- **Version 6**: Added device type and workflow fields

Migrations are applied automatically when `auto_migrate=True` in configuration.

## API Reference

### Core Classes

#### `DbHelper`

Database operations and server information management.

```python
db_helper = DbHelper(tablename="servers", db_path="hw.db", auto_migrate=True)
```

#### `MaasClient`

MAAS API operations with OAuth1 authentication.

```python
from hwautomation.maas.client import create_maas_client
maas_client = create_maas_client(config['maas'])
```

#### `FirmwareManager`

Multi-vendor firmware management with real vendor tool integration.

```python
from hwautomation.hardware.firmware_manager import FirmwareManager
firmware_manager = FirmwareManager()

# Check firmware versions across all components
firmware_info = await firmware_manager.check_firmware_versions(
    device_type='a1.c5.large', target_ip='192.168.1.100',
    username='admin', password='password'
)

# Update firmware with priority ordering (BMC → BIOS → Others)
updates_needed = [fw for fw in firmware_info.values() if fw.update_required]
results = await firmware_manager.update_firmware_batch(
    updates_needed, target_ip, username, password, operation_id
)
```

#### `FirmwareProvisioningWorkflow`

Complete firmware-first provisioning workflow.

```python
from hwautomation.hardware.firmware_provisioning_workflow import create_firmware_provisioning_workflow

workflow = create_firmware_provisioning_workflow()
context = workflow.create_provisioning_context(
    server_id="server_001", device_type="a1.c5.large",
    target_ip="192.168.1.100", credentials={"username": "admin", "password": "password"}
)
result = await workflow.execute_firmware_first_provisioning(context)
```

#### `IpmiManager`

IPMI hardware control operations.

```python
from hwautomation.hardware.ipmi import IpmiManager
ipmi_manager = IpmiManager(username="admin", timeout=30)
```

#### `RedfishManager`

Modern Redfish API management for standardized BMC operations.

```python
from hwautomation.hardware.redfish_manager import RedfishManager

# Context manager usage (recommended)
with RedfishManager("192.168.1.100", "admin", "password") as redfish:
    system_info = redfish.get_system_info()
    redfish.power_control("GracefulRestart")
```

### Key Methods

#### Database Operations

- `checkifserveridexists(server_id)` - Check if server exists
- `createrowforserver(server_id)` - Create new server record
- `updateserverinfo(server_id, field, value)` - Update server information
- `getserverswithworkingips()` - Get servers with verified IP connectivity
- `printtableinfo()` - Display database contents

#### MAAS Operations

- `get_machines()` - Retrieve all machines from MAAS
- `commission_machine(system_id)` - Commission a machine
- `deploy_machine(system_id, distro)` - Deploy OS to machine
- `release_machine(system_id)` - Release machine back to pool

#### Hardware Operations

- `get_power_status(ip, password)` - Get IPMI power status
- `power_on(ip, password)` - Power on server
- `power_off(ip, password)` - Power off server
- `get_system_info(ip, password)` - Get Redfish system information

#### Firmware Operations

- `check_firmware_versions(device_type, ip, username, password)` - Comprehensive firmware analysis
- `update_firmware_batch(updates_list, ip, username, password, operation_id)` - Batch firmware updates
- `execute_firmware_first_provisioning(context)` - Complete 6-step workflow with progress monitoring
- `get_vendor_specific_methods(device_type)` - Get optimal update methods per vendor

## Migration System

The package includes a robust database migration system:

```python
from hwautomation.database.migrations import DatabaseMigrator

# Create migrator
migrator = DatabaseMigrator("hw_automation.db")

# Check current version
current_version = migrator.get_current_version()

# Apply all pending migrations
migrator.migrate_to_latest()

# Backup database
backup_path = migrator.backup_database()
```

## Configuration

Configuration can be provided via:

1. YAML file (`config.yaml`)
2. JSON file (`config.json`)
3. Environment variables (with `HW_` prefix)

Environment variable examples:

```bash
export HW_MAAS_HOST="http://maas-server:5240/MAAS"
export HW_MAAS_CONSUMER_KEY="your-key"
export HW_DATABASE_PATH="/path/to/database.db"
```

## Examples

See the `examples/` directory for complete working examples:

- `basic_usage.py` - Complete workflow demonstration
- `firmware_manager_demo.py` - Firmware manager usage demo
- `firmware_provisioning_demo.py` - Firmware-first provisioning demonstration
- `enhanced_commissioning_demo.py` - Advanced commissioning workflows
- Interactive examples for IPMI, Redfish, and database operations

## Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=hwautomation
```

## Contributing

### Development Guidelines

1. **Blueprint Architecture**: Follow the modular blueprint structure in `src/hwautomation/web/routes/`
   - Each blueprint handles a single functional domain (core, database, orchestration, etc.)
   - Keep route modules focused and under 300 lines for maintainability
   - Use proper dependency injection via Flask app context

2. **Code Quality**:
   - Follow the existing code structure and patterns
   - Add comprehensive tests for new functionality
   - Update documentation for any changes
   - Use black for code formatting: `black src/`

3. **Web Interface Development**:
   - Status indicators should follow the established color scheme (green/red/orange)
   - Maintain responsive design principles
   - Test changes across different screen sizes
   - Preserve backward compatibility for existing URLs

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:

1. Check the examples directory
2. Review the database migration documentation
3. Open an issue on the project repository

## Migration from Legacy Scripts

If you're migrating from the original bash scripts:

1. Install the package: `pip install -e .`
2. Create configuration file: `config.yaml`
3. Run database migration: `python scripts/db_manager.py migrate`
4. Test with: `python examples/basic_usage.py`

The package maintains compatibility with existing databases through the migration system and provides a seamless upgrade path to enterprise firmware management capabilities.
