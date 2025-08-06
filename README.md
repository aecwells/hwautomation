# Hardware Automation Package

A comprehensive Python package for hardware automation, server management, and infrastructure operations. Originally converted from bash scripts, this package provides a clean, maintainable interface for MAAS, IPMI, and RedFish operations.

## Features

- **🖥️ Web GUI**: Modern web-based interface for hardware management
- **🔧 Vendor-Specific Tools**: Automatic installation and integration of HPE, Supermicro, and Dell management tools
- **🚀 Complete Orchestration**: 8-step automated server provisioning workflow
- **🔍 Hardware Discovery**: SSH-based system information gathering with IPMI detection
- **MAAS Integration**: Complete API client for Metal as a Service operations
- **IPMI Management**: Hardware control via IPMI protocol
- **RedFish Support**: Modern BMC management through RedFish APIs
- **BIOS Configuration**: Smart pull-edit-push BIOS configuration by device type
- **Database Migrations**: Robust schema versioning and upgrade system
- **Configuration Management**: Flexible YAML/JSON configuration with environment overrides
- **Network Utilities**: SSH operations, connectivity testing, and IP management

## Project Structure

```
HWAutomation/
├── src/hwautomation/          # Main package source code
│   ├── database/              # Database operations and migrations
│   ├── hardware/              # IPMI and RedFish management
│   ├── maas/                  # MAAS API client
│   └── utils/                 # Configuration and utilities
├── gui/                       # Web-based GUI interface
│   ├── app.py                 # Flask web application
│   ├── templates/             # HTML templates
│   └── static/                # CSS, JavaScript, assets
├── scripts/                   # Command-line tools
├── examples/                  # Usage examples
├── tests/                     # Test suite
├── docs/                      # Detailed documentation
├── tools/                     # Development and maintenance tools
├── pyproject.toml             # Package configuration
└── README.md                  # This file
```

## Installation

### From Source

```bash
# Clone the repository
git clone <your-repo-url>
cd HWAutomation

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
from hwautomation.utils.config import load_config

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

# Generate XML configuration for s2_c2_small
xml_config = bios_manager.generate_xml_config('s2_c2_small')
print("Generated BIOS configuration:")
print(xml_config)

# Apply configuration to a system (placeholder)
# bios_manager.apply_bios_config('s2_c2_small', '192.168.1.100', 'ADMIN', 'password')
```

### 4. Web GUI Usage

Launch the modern web interface:

```bash
# Quick launch (Windows)
gui\launch_gui.bat

# Manual launch
cd gui
python setup_gui.py

# Access GUI at: http://127.0.0.1:5000
```

**GUI Features:**
- 🎛️ Interactive BIOS configuration management
- 📊 Real-time dashboard with system status
- ⚡ Live progress updates via WebSocket
- 📱 Responsive design for mobile/tablet
- 🔍 Advanced filtering and search
- 📁 Download configurations and logs

### 5. Command Line Usage

```bash
# Run the main interactive interface
python main.py

# BIOS configuration management
python scripts/bios_manager.py list-types
python scripts/bios_manager.py show-config s2_c2_small
python scripts/bios_manager.py generate-xml s2_c2_small --output config.xml

# Database management
python scripts/db_manager.py status
python scripts/db_manager.py backup

# Use the examples
python examples/basic_usage.py

# Database management
python scripts/db_manager.py status
python scripts/db_manager.py migrate
python scripts/db_manager.py backup
```

## Package Structure

```
src/hwautomation/
├── __init__.py              # Main package exports
├── database/
│   ├── helper.py           # Database operations
│   └── migrations.py       # Schema migration system
├── maas/
│   └── client.py          # MAAS API client
├── hardware/
│   ├── ipmi.py           # IPMI management
│   └── redfish.py        # RedFish operations
└── utils/
    ├── config.py         # Configuration management
    └── network.py        # Network utilities
```

## Database Schema

The package includes a complete migration system with versioned schema updates:

- **Version 1**: Basic server table
- **Version 2**: Added IP address tracking
- **Version 3**: Hardware model information
- **Version 4**: Extended status fields
- **Version 5**: Metadata and tagging support

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

#### `IpmiManager`
IPMI hardware control operations.

```python
from hwautomation.hardware.ipmi import IpmiManager
ipmi_manager = IpmiManager(username="admin", timeout=30)
```

#### `RedFishManager`
RedFish API management for modern BMCs.

```python
from hwautomation.hardware.redfish import RedFishManager
redfish_manager = RedFishManager(username="admin", timeout=30)
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
- `get_system_info(ip, password)` - Get RedFish system information

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
- Interactive examples for IPMI, RedFish, and database operations

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

1. Follow the existing code structure
2. Add tests for new functionality
3. Update documentation
4. Use black for code formatting: `black src/`

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

The package maintains compatibility with existing databases through the migration system.
