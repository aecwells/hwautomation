# Hardware Automation Package

![CI/CD Pipeline](https://github.com/aecwells/hwautomation/actions/workflows/ci.yml/badge.svg?branch=main)
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

### **Web Interface Modernization & Modular Architecture**
- **📐 Blueprint Architecture**: Refactored monolithic 853-line Flask app into modular blueprint structure
- **🔧 Improved Maintainability**: 6 focused route modules (56-302 lines each) for easier development and testing
- **📊 Enhanced Status Indicators**: Smart MaaS connection status with visual indicators (Connected/Disconnected/Not Configured)
- **🎨 Better UI/UX**: Redesigned status bar positioning under logo with responsive design and proper color coding
- **⚡ Zero Breaking Changes**: All existing URLs and APIs preserved during refactoring

### **Hardware System Modularization**
- **🏗️ Modular Hardware Discovery**: Complete restructuring of 859-line discovery system into focused modules
- **⚙️ BIOS Configuration Modules**: Separated BIOS management into config, devices, operations, and parsers
- **🔍 Vendor-Specific Logic**: Dedicated vendor modules for Supermicro, Dell, HPE with extensible architecture
- **📦 Clean Module Structure**: Better separation of concerns and easier testing/maintenance

### **Frontend Build System Integration**
- **⚡ Vite Build System**: Modern JavaScript bundling with hot module replacement
- **🎨 Component Architecture**: Modular frontend components with SCSS styling
- **📱 Enhanced Responsive Design**: Mobile-first CSS with theme support
- **🗜️ Asset Optimization**: Automatic minification, hashing, and build optimization

### **Developer Experience Improvements**
- **🏗️ Team-Friendly Architecture**: Single-responsibility modules enable parallel development
- **🧪 Easier Testing**: Modular structure simplifies unit testing and debugging
- **📈 Scalable Foundation**: Clean architecture ready for new features and team expansion
- **🛠️ Modern Tooling**: Pre-commit hooks, automated quality checks, and comprehensive CI/CD

### **Code Quality & CI/CD Enhancements**
- **🚀 Comprehensive CI/CD Pipeline**: Multi-stage GitHub Actions workflow with quality gates
- **🎨 Code Formatting**: Automated Black formatting applied to entire codebase (59+ files)
- **📦 Import Organization**: isort import sorting for consistent code structure
- **🔍 Code Analysis**: flake8 linting with project-specific configurations
- **🛡️ Security Scanning**: Bandit security analysis integrated into CI pipeline
- **📊 Type Checking**: MyPy type checking configured for gradual adoption
- **🧪 Multi-Version Testing**: Python 3.9-3.12 compatibility testing
- **📈 Test Coverage**: Automated coverage reporting with realistic baselines
- **🪝 Pre-commit Hooks**: Comprehensive quality gates with 15+ automated checks
- **⚡ Async Testing**: Full pytest-asyncio support for async/await test patterns
- **🔧 Performance Testing**: Dedicated performance test suite with controlled execution

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

### Container-First Design with Modern Modular Structure

```text
hwautomation/
├── docker/
│   └── Dockerfile.web         # 🐳 Multi-stage container builds
├── docker-compose.yml         # 🏗️ Production service orchestration
├── docker-compose.override.yml # 🛠️ Development overrides
├── package.json               # 📦 Node.js dependencies for frontend build
├── vite.config.js             # ⚡ Vite build configuration
├── src/hwautomation/          # 📦 Main package source code
│   ├── web/                   # 🌐 Flask web application with blueprint architecture
│   │   ├── app.py             # 🏭 Clean app factory with blueprint registration
│   │   ├── core/              # 🔧 Web application core functionality
│   │   ├── routes/            # 📁 Modular blueprint organization
│   │   │   ├── core.py        # 🏠 Dashboard and health endpoints
│   │   │   ├── database.py    # 🗄️ Database management routes
│   │   │   ├── orchestration.py # 🔄 Workflow orchestration APIs
│   │   │   ├── maas.py        # 🌐 MaaS integration endpoints
│   │   │   ├── logs.py        # 📊 System logging APIs
│   │   │   └── firmware.py    # 🔧 Firmware management routes
│   │   ├── frontend/          # 🎨 Modern frontend build system
│   │   │   ├── js/            # JavaScript modules (core, services, components, utils)
│   │   │   └── css/           # SCSS stylesheets with component organization
│   │   ├── static/            # 📁 Static assets and build output
│   │   │   └── dist/          # 🏗️ Built frontend assets (gitignored)
│   │   └── templates/         # 🎨 Enhanced UI templates with status indicators
│   ├── hardware/              # ⚙️ Modular hardware management system
│   │   ├── bios/              # 🔧 BIOS configuration management (modularized)
│   │   │   ├── config/        # Configuration template management
│   │   │   ├── devices/       # Device-specific implementations
│   │   │   ├── operations/    # BIOS operation handlers
│   │   │   └── parsers/       # Configuration file parsers
│   │   ├── discovery/         # 🔍 Hardware discovery system (modularized)
│   │   │   ├── parsers/       # System information parsers
│   │   │   ├── vendors/       # Vendor-specific discovery logic
│   │   │   └── utils/         # Discovery utilities
│   │   ├── firmware_manager.py           # 🔧 Multi-vendor firmware operations
│   │   └── firmware_provisioning_workflow.py # 🚀 Firmware-first workflows
│   ├── orchestration/         # 🔄 Workflow management and server provisioning
│   ├── database/              # 🗄️ SQLite operations and migrations
│   ├── maas/                  # 🌐 MAAS API client
│   ├── logging/               # 📊 Centralized logging infrastructure
│   ├── validation/            # ✅ Data validation utilities
│   └── utils/                 # 🔧 Configuration and utilities
├── configs/
│   ├── bios/                  # 📁 BIOS configuration templates and rules
│   └── firmware/              # 📁 Firmware repository and update configurations
├── examples/                  # 📚 Usage examples including firmware demos
├── tests/                     # 🧪 Comprehensive test suite
│   ├── unit/                  # Fast unit tests
│   ├── integration/           # Integration tests
│   ├── fixtures/              # Test data and fixtures
│   └── mocks/                 # Mock objects for testing
├── docs/                      # 📖 Comprehensive documentation
├── tools/                     # 🛠️ Development and maintenance tools
│   ├── cli/                   # Production CLI tools
│   ├── testing/               # Test scripts and utilities
│   ├── debug/                 # Debug and troubleshooting scripts
│   ├── config/                # Configuration management tools
│   ├── migration/             # Migration and setup tools
│   ├── verification/          # Validation and verification tools
│   └── quality/               # Code quality tools
└── firmware/                  # 📁 Firmware repository structure
    ├── dell/                  # Dell firmware files
    ├── hpe/                   # HPE firmware files
    └── supermicro/            # Supermicro firmware files
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

## Frontend Build System

### Modern JavaScript/CSS Build Pipeline

The project includes a modern frontend build system using **Vite** for optimal development experience and production builds:

```bash
# Install frontend dependencies (Node.js required)
npm install

# Development mode with hot reloading
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

**Build System Features:**
- ⚡ **Vite-powered**: Lightning-fast HMR (Hot Module Replacement)
- 📦 **Modular JavaScript**: ES6 modules with dynamic imports
- 🎨 **SCSS Support**: Advanced CSS with variables and mixins
- 🗜️ **Asset Optimization**: Automatic minification and compression
- 🔍 **Source Maps**: Enhanced debugging capabilities
- 📱 **Responsive Design**: Mobile-first CSS architecture

**Frontend Architecture:**
```text
src/hwautomation/web/frontend/
├── js/
│   ├── core/
│   │   ├── app.js                 # Main application entry point
│   │   └── module-loader.js       # Dynamic module loading system
│   ├── services/
│   │   ├── api.js                # HTTP client and API abstraction
│   │   ├── state.js              # Centralized state management
│   │   └── notifications.js      # User notification system
│   ├── components/
│   │   ├── theme-manager.js       # Light/dark theme switching
│   │   ├── connection-status.js   # WebSocket/API status indicator
│   │   └── device-selection.js    # Device listing and selection
│   └── utils/
│       ├── dom.js                # DOM manipulation utilities
│       └── format.js             # Data formatting functions
└── css/
    ├── base.css                  # CSS variables and theme foundations
    ├── main.css                  # Main stylesheet with imports
    └── components/
        ├── navbar.css            # Navigation bar styles
        └── device-selection.css  # Device selection component styles
```

**Built Assets:**
- Output directory: `src/hwautomation/web/static/dist/`
- Automatic asset hashing for cache busting
- Manifest file for Flask template integration
- Optimized CSS and JavaScript bundles

## Installation Options

### 🚀 Container Deployment (Recommended)

Fastest way to get started with full functionality:

```bash
# Clone and run
git clone <your-repo-url>
cd hwautomation

# Build frontend assets (optional - container handles this)
npm install && npm run build

# Start the application
docker compose up -d app

# Access web GUI at http://localhost:5000
```

**Note**: The container includes Node.js and automatically builds frontend assets during the build process, so the npm commands are optional for container deployment.

### 📦 Package Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd hwautomation

# Create and activate a virtual environment (recommended)
python3 -m venv hwautomation-env
source hwautomation-env/bin/activate

# Install Python package in development mode
pip install -e .

# Install Node.js dependencies for frontend development
npm install

# Build frontend assets
npm run build

# Or install normally (without development features)
pip install .
```

> **Note for Ubuntu/Debian users**: If you encounter an "externally-managed-environment" error, you need to use a virtual environment. This is a security feature in newer Python installations. Follow these steps:

```bash
# Install required packages first
sudo apt update
sudo apt install -y python3.12-venv python3-full nodejs npm

# Then create and use a virtual environment
python3 -m venv hwautomation-env
source hwautomation-env/bin/activate
pip install -e .

# Setup frontend build system
npm install
npm run build

# Test the installation
python -c 'import hwautomation; print("HWAutomation package imported successfully!")'
```

> **Important Notes**:
>
> - When testing the import in bash, always use single quotes around the Python command to avoid bash history expansion issues with exclamation marks.
> - If you get "bash: !': event not found" error, you're using double quotes instead of single quotes.
> - The virtual environment approach is required on Ubuntu/Debian systems with externally-managed Python environments.
> - Node.js 14+ and npm 6+ are required for the frontend build system.

### Requirements

**Python Environment:**
- Python 3.8+
- Virtual environment recommended (required on Ubuntu/Debian)

**Node.js Environment (for frontend development):**
- Node.js 14+
- npm 6+

**External dependencies:**
- `ipmitool` (for IPMI operations)
- SSH access to target servers
- MAAS server access with API credentials

**Optional for development:**
- Docker and Docker Compose (for containerized deployment)
- Git (for version control)

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

### 3. Modular Hardware Management

The hardware management system has been completely modularized for better maintainability and extensibility:

```python
from hwautomation.hardware.discovery import HardwareDiscoveryManager
from hwautomation.hardware.bios.config import BiosConfigManager

# Initialize modular discovery system
discovery_manager = HardwareDiscoveryManager()

# Discover hardware with vendor-specific parsing
discovery_result = discovery_manager.discover_system(
    target_ip='192.168.1.100',
    username='admin',
    password='password'
)

print(f"Detected vendor: {discovery_result.vendor}")
print(f"Device type: {discovery_result.device_type}")
print(f"IPMI configuration: {discovery_result.ipmi_config}")

# Use modular BIOS configuration system
bios_manager = BiosConfigManager()

# Apply device-specific BIOS configuration
result = bios_manager.apply_configuration(
    device_type=discovery_result.device_type,
    target_ip='192.168.1.100',
    config_template='production',
    dry_run=False
)

print(f"BIOS configuration applied: {result.success}")
```

### 4. BIOS Configuration Management

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

### 5. Firmware Management

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

### 6. Web GUI Usage

Launch the modern web interface:

```bash
# Container deployment (recommended)
docker compose up -d app

# Local development with frontend build system
source hwautomation-env/bin/activate
npm run build  # Build frontend assets
hw-web         # Start Flask application

# Development mode with hot reloading
npm run dev    # Start Vite dev server (port 3000)
hw-web         # Start Flask backend (port 5000)

# Access GUI at: <http://127.0.0.1:5000>
```

**Modern GUI Features:**

- 🎛️ **Interactive BIOS Configuration**: Real-time configuration management with live validation
- 🧰 **Firmware Management Dashboard**: Real-time firmware status, version tracking, and update scheduling
- 📊 **Enhanced Dashboard**: System status monitoring with intelligent MaaS connection indicators
- ⚡ **Live Progress Updates**: WebSocket-powered real-time workflow progress with detailed sub-task granularity
- 🚀 **Firmware-First Provisioning**: Complete workflow orchestration from web interface
- 🎨 **Modern UI/UX**: Component-based architecture with theme switching and responsive design
- 📱 **Mobile-Friendly**: Responsive design optimized for mobile/tablet devices
- 🔍 **Advanced Filtering**: Smart search and filtering capabilities
- 📁 **Export Capabilities**: Download configurations, logs, and reports
- 💾 **Database Management**: Comprehensive SQLite database interface
- 🌙 **Theme Support**: Light/dark mode switching with user preferences
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

### 7. Command Line Usage

```bash
# Run CLI via console scripts
hw-cli --help
hwautomation --help

# Start web interface
hw-web

# Run examples
python examples/run.py --list
```

## Development Workflow

### 🛠️ Complete Development Environment Setup

```bash
# Initial setup
git clone <your-repo-url>
cd hwautomation

# Python environment
python3 -m venv hwautomation-env
source hwautomation-env/bin/activate
pip install -e .

# Frontend environment
npm install

# Development tools setup
make setup-precommit    # Install pre-commit hooks
make install-test       # Install testing dependencies

# Verify setup
make test-unit          # Quick test verification
npm run build           # Verify frontend builds
```

### 🔄 Daily Development Workflow

```bash
# Frontend development with hot reloading
npm run dev             # Start Vite dev server (localhost:3000)
# In another terminal:
hw-web                  # Start Flask backend (localhost:5000)

# Code quality checks
make test-unit          # Fast unit tests during development
make test-quality       # Code quality validation
git commit              # Pre-commit hooks run automatically

# Full validation before PR
make test               # Complete test suite
make test-cov           # Coverage verification
npm run build           # Production build test
```

### 🏗️ Build System Commands

```bash
# Frontend development
npm run dev             # Development server with HMR
npm run build           # Production build
npm run preview         # Preview production build
npm run lint            # Frontend code linting

# Python development
make test               # Full test suite
make test-unit          # Fast unit tests
make test-integration   # Integration tests
make test-cov           # Test coverage
make dev-setup          # Complete dev environment setup
```

## Package Structure

```bash
src/hwautomation/
├── __init__.py              # Main package exports
├── web/
│   ├── app.py              # Clean Flask app factory with blueprint registration
│   ├── core/               # Web application core functionality
│   ├── routes/             # Modular blueprint architecture
│   │   ├── core.py         # Dashboard and health endpoints
│   │   ├── database.py     # Database management APIs
│   │   ├── orchestration.py # Workflow orchestration APIs
│   │   ├── maas.py         # MaaS integration endpoints
│   │   ├── logs.py         # System logging APIs
│   │   └── firmware.py     # Firmware management APIs
│   ├── frontend/           # Modern frontend build system
│   │   ├── js/
│   │   │   ├── core/       # Core application logic (app.js, module-loader.js)
│   │   │   ├── services/   # API client, state management, notifications
│   │   │   ├── components/ # Reusable UI components (theme, status, device selection)
│   │   │   └── utils/      # DOM utilities and formatting functions
│   │   └── css/
│   │       ├── base.css    # CSS variables and theme foundations
│   │       ├── main.css    # Main stylesheet with imports
│   │       ├── components/ # Component-specific styles
│   │       └── themes/     # Theme variations
│   ├── static/             # Static assets and build output
│   │   ├── css/            # Legacy static CSS files
│   │   ├── js/             # Legacy static JavaScript files
│   │   └── dist/           # Built frontend assets (auto-generated)
│   │       ├── js/         # Compiled JavaScript modules
│   │       ├── css/        # Compiled stylesheets
│   │       └── manifest.json # Build manifest for asset loading
│   └── templates/          # Enhanced web UI templates with status indicators
│       ├── base.html       # Base template with build system integration
│       ├── dashboard.html  # Main dashboard
│       └── firmware/       # Firmware management templates
├── orchestration/
│   ├── workflow_manager.py       # Core workflow orchestration
│   └── server_provisioning.py   # Standard and firmware-first provisioning workflows
├── database/
│   ├── helper.py           # SQLite database operations
│   └── migrations.py       # Schema migration system
├── maas/
│   └── client.py          # MAAS API client
├── hardware/
│   ├── bios/                             # Modular BIOS management system
│   │   ├── __init__.py                   # BIOS module exports
│   │   ├── config/
│   │   │   ├── manager.py                # Configuration template management
│   │   │   └── templates.py              # Template processing logic
│   │   ├── devices/
│   │   │   ├── base.py                   # Base device classes
│   │   │   ├── supermicro.py             # Supermicro-specific implementations
│   │   │   └── vendors.py                # Multi-vendor device support
│   │   ├── operations/
│   │   │   ├── executor.py               # BIOS operation execution
│   │   │   └── monitoring.py             # Real-time monitoring
│   │   └── parsers/
│   │       ├── xml_parser.py             # XML configuration parsing
│   │       └── redfish_parser.py         # Redfish response parsing
│   ├── discovery/                        # Modular hardware discovery system
│   │   ├── __init__.py                   # Discovery module exports
│   │   ├── manager.py                    # Main discovery orchestration
│   │   ├── parsers/
│   │   │   ├── dmidecode.py              # DMI decode parsing
│   │   │   ├── ipmi.py                   # IPMI configuration parsing
│   │   │   └── network.py                # Network interface parsing
│   │   ├── vendors/
│   │   │   ├── base.py                   # Base vendor discovery class
│   │   │   ├── supermicro.py             # Supermicro-specific discovery
│   │   │   ├── dell.py                   # Dell-specific discovery
│   │   │   └── hpe.py                    # HPE-specific discovery
│   │   └── utils/
│   │       ├── ssh.py                    # SSH utilities for discovery
│   │       └── validation.py             # Discovery data validation
│   ├── ipmi.py                           # IPMI management
│   ├── redfish_manager.py                # Redfish operations with firmware support
│   ├── bios_config.py                    # Legacy BIOS configuration (being phased out)
│   ├── firmware_manager.py               # Multi-vendor firmware management
│   └── firmware_provisioning_workflow.py # Complete firmware-first workflow
├── utils/
│   ├── config.py         # Configuration management
│   └── network.py        # Network utilities
├── logging/
│   ├── __init__.py       # Logging module exports
│   ├── config.py         # Logging configuration
│   └── handlers.py       # Custom log handlers
├── validation/
│   ├── __init__.py       # Validation module exports
│   ├── schemas.py        # Data validation schemas
│   └── validators.py     # Custom validators
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

### 🧪 Comprehensive Testing Suite

The project includes a robust testing infrastructure with multiple testing approaches:

```bash
# Quick setup - install all development dependencies
make install-test

# Basic testing
make test              # Run all tests
make test-unit         # Fast unit tests only
make test-integration  # Integration tests
make test-cov         # Tests with coverage report
make test-html        # Generate HTML coverage report

# Advanced testing
make test-async       # Async tests with pytest-asyncio
make test-performance # Performance tests (set RUN_PERFORMANCE_TESTS=1)
make test-parallel    # Run tests in parallel for speed
make test-security    # Security scanning with bandit

# Code quality
make test-quality     # Run all quality checks (black, isort, flake8, mypy, bandit)
make setup-precommit  # Install pre-commit hooks
make precommit-all    # Run pre-commit on all files
```

### 🪝 Pre-commit Hooks

Automated code quality enforcement on every commit:

```bash
# Setup once
make setup-precommit

# Hooks automatically run on git commit and include:
# ✅ Code formatting (black)      ✅ Import sorting (isort)
# ✅ Linting (flake8)           ✅ Type checking (mypy)
# ✅ Security scanning (bandit)  ✅ Docstring style (pydocstyle)
# ✅ Spell checking (typos)      ✅ File validation
# ✅ Shell script linting       ✅ YAML/JSON/TOML validation
```

### 🐳 Docker Testing

```bash
# Test inside containers
make test-docker       # All tests in Docker
make test-docker-unit  # Unit tests in Docker
make test-docker-cov   # Coverage tests in Docker
```

### 📊 Test Coverage & Reporting

- **Coverage Targets**: Realistic baselines with room for improvement
- **HTML Reports**: Detailed coverage analysis in `htmlcov/index.html`
- **CI Integration**: Automated coverage reporting in GitHub Actions
- **Multi-format Output**: Terminal, HTML, and XML coverage reports

## Contributing

### Development Guidelines

1. **Modular Architecture**: Follow the established modular structure
   - **Blueprint Architecture**: Each web route blueprint handles a single functional domain
   - **Hardware Modules**: Use the modular hardware system (`/hardware/bios/`, `/hardware/discovery/`)
   - **Frontend Components**: Follow the component-based frontend architecture
   - Keep modules focused and under 300-400 lines for maintainability

2. **Modern Frontend Development**:
   - **Build System**: Use Vite for frontend development with `npm run dev`
   - **Component Architecture**: Create reusable JavaScript components in `/frontend/js/components/`
   - **Styling**: Use SCSS in `/frontend/css/` with component-specific organization
   - **Asset Management**: Built assets go to `/static/dist/` (auto-generated)

3. **Code Quality & Testing**:
   - **Pre-commit Hooks**: Automatically enforced on every commit (`make setup-precommit`)
   - **Testing Requirements**: Add tests for new functionality with pytest
   - **Async Support**: Use `@pytest.mark.asyncio` for async test functions
   - **Performance Tests**: Gate performance tests behind `RUN_PERFORMANCE_TESTS=1`
   - **Security**: All code automatically scanned with bandit for security issues
   - **Frontend Quality**: Use `npm run lint` for JavaScript/CSS quality checks

4. **Development Workflow**:
   ```bash
   # Initial setup
   make dev-setup          # Setup complete development environment
   make setup-precommit    # Install quality gates
   npm install             # Frontend dependencies

   # Daily development
   npm run dev             # Frontend development server
   make test-unit          # Fast feedback during development
   make test-quality       # Check code quality before commit
   git commit              # Pre-commit hooks run automatically

   # Before PR
   make test               # Full test suite
   make test-cov           # Verify coverage
   npm run build           # Verify frontend builds
   ```

5. **Hardware Module Development**:
   - Follow the modular structure in `/hardware/bios/` and `/hardware/discovery/`
   - Create vendor-specific implementations in respective `/vendors/` directories
   - Use base classes for consistent interfaces
   - Add comprehensive parsing and validation logic

6. **Web Interface Development**:
   - Status indicators should follow the established color scheme (green/red/orange)
   - Maintain responsive design principles and test across screen sizes
   - Use the component system for reusable UI elements
   - Preserve backward compatibility for existing URLs
   - Integrate with the build system for optimized assets

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
