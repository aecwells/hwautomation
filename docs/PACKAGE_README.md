# Hardware Automation Package

A Python package for automating server hardware management through MAAS API, IPMI, and RedFish interfaces.

## 🚀 Quick Start

### 1. Validate Package Structure
```bash
# Check syntax and structure (no dependencies required)
python syntax_check.py

# Full validation with imports (requires Python modules)
python validate_package.py
```

### 2. Install Dependencies
```bash
pip install requests requests-oauthlib pyyaml
```

### 3. Configuration
```bash
# Copy example configuration
cp config.yaml.example config.yaml

# Edit config.yaml with your settings
# - MAAS server details
# - Database path
# - IPMI/SSH credentials
```

### 4. Run Examples
```bash
# Interactive examples
python examples/basic_usage.py

# Updated main script (after migration)
python main.py full_update
```

## 📁 Package Structure

```
src/hwautomation/
├── __init__.py              # Main package exports
├── database/
│   ├── __init__.py
│   ├── helper.py            # Database operations (DbHelper class)
│   └── migrations.py        # Schema migration system
├── maas/
│   ├── __init__.py
│   └── client.py           # MAAS API client with OAuth1
├── hardware/
│   ├── __init__.py
│   ├── ipmi.py             # IPMI hardware control
│   └── redfish.py          # RedFish API management
└── utils/
    ├── __init__.py
    ├── config.py           # Configuration management
    └── network.py          # Network utilities
```

## 🔄 Migration from Old Structure

If you have existing scripts using the old flat file structure:

```bash
# See migration guide
python migration_guide.py

# This will show you how to update imports and function calls
```

### Old vs New Import Pattern

**Old (flat files):**
```python
from hwautolib import *
from dbhelper import DbHelper
```

**New (package structure):**
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from hwautomation import *
from hwautomation.database.helper import DbHelper
from hwautomation.maas.client import create_maas_client
```

## 🛠 Usage Examples

### Database Operations with Auto-Migration
```python
from hwautomation import DbHelper
from hwautomation.utils.config import load_config

config = load_config()
db_helper = DbHelper(
    tablename=config['database']['table_name'],
    db_path=config['database']['path'],
    auto_migrate=True  # Automatically upgrades old databases
)

# Database is now at the latest schema version
print(f"Database version: {db_helper.get_database_version()}")
```

### MAAS Integration
```python
from hwautomation.maas.client import create_maas_client
from hwautomation.utils.config import load_config

config = load_config()
maas_client = create_maas_client(config['maas'])

# Get all machines
machines = maas_client.get_machines()
print(f"Found {len(machines)} machines")

# Commission a machine
maas_client.commission_machine(system_id)
```

### IPMI Operations
```python
from hwautomation.hardware.ipmi import IpmiManager

ipmi = IpmiManager(username="admin", timeout=30)

# Get power status
power_status = ipmi.get_power_status("192.168.1.100", "password")
print(f"Power: {power_status}")

# Power cycle
ipmi.power_cycle("192.168.1.100", "password")
```

### Redfish API
```python
from hwautomation.hardware.redfish_manager import RedfishManager

# Modern Redfish API with context manager
with RedfishManager("192.168.1.100", "admin", "password") as redfish:
    # Get system information
    system_info = redfish.get_system_info()
    if system_info:
        print(f"Manufacturer: {system_info.manufacturer}")
        print(f"Model: {system_info.model}")
        print(f"Power State: {system_info.power_state}")
    
    # Control power
    redfish.power_control("GracefulRestart")
    
    # Get BIOS settings
    bios_settings = redfish.get_bios_settings()
    if bios_settings:
        print(f"Found {len(bios_settings)} BIOS settings")

# Note: Thermal information and other advanced features
# are planned for future phases of Redfish integration
```

## 🗃 Database Schema Migration

The package includes an automatic migration system that upgrades existing databases:

### Current Schema Version: 5

**Migration History:**
- v1: Basic server information
- v2: Added IP address tracking
- v3: Added IPMI IP and status fields  
- v4: Added server metadata (model, status, OS)
- v5: Added tags and rack location

### Manual Migration
```python
from hwautomation.database.migrations import DatabaseMigrator

migrator = DatabaseMigrator("path/to/database.db")
migrator.migrate_to_latest()
print(f"Migrated to version: {migrator.get_current_version()}")
```

### Migration Features
- ✅ Automatic backup before migration
- ✅ Rollback capability
- ✅ Schema validation
- ✅ Data preservation
- ✅ Export/import functionality

## ⚙ Configuration Management

### Configuration File (config.yaml)
```yaml
maas:
  host: "http://maas.example.com:5240/MAAS"
  consumer_key: "your_consumer_key"
  token_key: "your_token_key"
  token_secret: "your_token_secret"

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

### Environment Variable Override
```bash
export MAAS_HOST="http://different-maas.com:5240/MAAS"
export DB_PATH="/custom/path/database.db"
```

## 🧪 Testing & Validation

### Syntax Check (No Dependencies)
```bash
python syntax_check.py
```

### Full Import Validation
```bash
python validate_package.py
```

### Interactive Examples
```bash
python examples/basic_usage.py
```

## 📊 Database Management

### Command Line Tool
```bash
# Check database status
python scripts/db_manager.py status

# Create backup
python scripts/db_manager.py backup

# Show schema
python scripts/db_manager.py schema

# Export data
python scripts/db_manager.py export
```

## 🔧 Development Setup

### For Package Development
```bash
# Install in development mode
pip install -e .

# Or add to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### For Script Development
```python
# Add to scripts that use the package
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))
```

## 📋 Requirements

### Core Requirements (Built-in)
- Python 3.10+
- sqlite3
- json
- subprocess
- pathlib

### Optional Requirements
```bash
pip install requests          # MAAS and RedFish APIs
pip install requests-oauthlib # MAAS OAuth authentication  
pip install pyyaml           # YAML configuration files
```

## 🚨 Troubleshooting

### Import Errors
1. Run `python syntax_check.py` to check file syntax
2. Run `python validate_package.py` to test imports
3. Check that `src/` directory is in Python path

### Database Issues
1. Check file permissions on database file
2. Run migration: `python scripts/db_manager.py migrate`
3. Check database schema: `python scripts/db_manager.py schema`

### MAAS Connection Issues
1. Verify MAAS URL and credentials in config.yaml
2. Test with: `curl -H "Authorization: OAuth ..." $MAAS_URL/api/2.0/machines/`
3. Check network connectivity to MAAS server

### IPMI Issues
1. Ensure `ipmitool` is installed on the system
2. Verify IPMI credentials and network access
3. Test manually: `ipmitool -I lanplus -H <ip> -U <user> -P <pass> power status`

## 📚 Additional Resources

- **Migration Guide**: `python migration_guide.py`
- **Database Migrations**: See `DATABASE_MIGRATIONS.md`
- **API Documentation**: See docstrings in source files
- **Examples**: See `examples/` directory

## 🏗 Architecture

The package is organized into logical modules:

- **database/**: SQLite operations with migration support
- **maas/**: MAAS API client with OAuth1 authentication
- **hardware/**: IPMI and RedFish hardware management
- **utils/**: Configuration, networking, and utility functions

Each module can be used independently or as part of the complete workflow.
