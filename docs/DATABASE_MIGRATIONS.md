# Database Migration System

## Overview

The hardware automation project now includes a robust database migration system that allows you to upgrade existing databases with new schema changes while preserving data. This system is essential for maintaining compatibility as the application evolves.

## Key Features

- **Automatic Migrations**: Databases are automatically upgraded when the application starts
- **Version Tracking**: Each migration is tracked with version numbers and timestamps
- **Backup Creation**: Automatic backups before applying migrations
- **Rollback Safety**: Migrations are designed to be safe and reversible
- **Schema Export**: Export current schema information for documentation
- **Data Integrity**: Maintains existing data during schema changes

## Migration System Components

### 1. `db_migrations.py`
Core migration engine that handles:
- Migration version tracking
- Applying schema changes
- Creating backups
- Exporting schema information

### 2. `db_manager.py`
Command-line utility for database management:
- Apply migrations
- Create backups
- Check database status
- Initialize new databases
- Repair corrupted databases

### 3. Enhanced `DbHelper` class
Updated database helper with:
- Automatic migration support
- Backward compatibility
- New metadata fields
- Improved error handling

## Current Migration Versions

| Version | Name | Description |
|---------|------|-------------|
| 1 | Initial schema | Basic server tracking table |
| 2 | Add IPMI fields | IPMI credentials and RedFish support |
| 3 | Add timestamps | Created/updated/last seen tracking |
| 4 | Add metadata | CPU, memory, storage, rack location |
| 5 | Add power state | Power state tracking and history |

## Usage Examples

### Automatic Migration (Recommended)
```python
from hwautolib import bringUpDatabase

# Database will be automatically migrated to latest version
bringUpDatabase('servers', 'hw_automation.db', auto_migrate=True)
```

### Manual Migration Management
```bash
# Check database status
python db_manager.py status -d hw_automation.db

# Apply migrations
python db_manager.py migrate -d hw_automation.db

# Create backup
python db_manager.py backup -d hw_automation.db

# Initialize new database
python db_manager.py init -d new_database.db
```

### Programmatic Migration
```python
from db_migrations import DatabaseMigrator

migrator = DatabaseMigrator('hw_automation.db')
current_version = migrator.get_current_version()
migrator.migrate_to_latest()
migrator.close()
```

## Schema Evolution Example

### Version 1 (Initial)
```sql
CREATE TABLE servers (
    server_id TEXT PRIMARY KEY,
    status_name TEXT,
    is_ready TEXT,
    server_model TEXT,
    ip_address TEXT,
    ip_address_works TEXT
);
```

### Version 5 (Latest)
```sql
CREATE TABLE servers (
    server_id TEXT PRIMARY KEY,
    status_name TEXT,
    is_ready TEXT,
    server_model TEXT,
    ip_address TEXT,
    ip_address_works TEXT,
    ipmi_address TEXT,
    ipmi_address_works TEXT,
    ipmi_username TEXT DEFAULT 'ADMIN',
    ipmi_password_set TEXT DEFAULT 'FALSE',
    bios_password_set TEXT DEFAULT 'FALSE',
    redfish_available TEXT DEFAULT 'UNKNOWN',
    kcs_status TEXT,
    host_interface_status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP,
    cpu_model TEXT,
    memory_gb INTEGER,
    storage_info TEXT,
    network_interfaces TEXT,
    firmware_version TEXT,
    rack_location TEXT,
    tags TEXT,
    power_state TEXT DEFAULT 'UNKNOWN',
    last_power_change TIMESTAMP
);

CREATE TABLE power_state_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_id TEXT NOT NULL,
    old_state TEXT,
    new_state TEXT NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by TEXT,
    FOREIGN KEY (server_id) REFERENCES servers (server_id)
);
```

## Migration Best Practices

### 1. Always Backup First
```bash
# Create backup before any major changes
python db_manager.py backup -d hw_automation.db --output backup_before_migration.db
```

### 2. Test Migrations
```python
# Test migration on a copy of your database
import shutil
shutil.copy('production.db', 'test_migration.db')

# Apply migration to test database
python db_manager.py migrate -d test_migration.db
```

### 3. Monitor Migration Status
```bash
# Check current version and available migrations
python db_manager.py status -d hw_automation.db --verbose
```

### 4. Use New Features Safely
```python
# Check database version before using new features
dbworker = DbHelper('servers', 'hw_automation.db')
version = dbworker.get_database_version()

if version >= 4:
    # Safe to use metadata fields
    dbworker.update_server_metadata(
        server_id,
        rack_location="Rack-A-01",
        tags='["production", "web"]'
    )
```

## Adding New Migrations

To add a new migration, update the `get_all_migrations()` method in `db_migrations.py`:

```python
def get_all_migrations(self) -> List[tuple]:
    return [
        # ... existing migrations ...
        (6, "Add your new feature", self._migration_006_your_feature),
    ]

def _migration_006_your_feature(self, cursor):
    """Migration 006: Description of your new feature"""
    # Add new columns
    cursor.execute("ALTER TABLE servers ADD COLUMN new_field TEXT")

    # Create new tables
    cursor.execute("""
        CREATE TABLE new_table (
            id INTEGER PRIMARY KEY,
            server_id TEXT,
            data TEXT,
            FOREIGN KEY (server_id) REFERENCES servers (server_id)
        )
    """)
```

## Troubleshooting

### Migration Fails
1. Check error message and backup database
2. Fix any data issues manually
3. Retry migration
4. Use `db_manager.py repair` if needed

### Corrupted Database
```bash
# Attempt repair
python db_manager.py repair -d hw_automation.db

# Or restore from backup
cp backup_file.db hw_automation.db
```

### Schema Conflicts
```bash
# Export current schema to understand structure
python db_manager.py export-schema -d hw_automation.db

# Compare with expected schema
```

## Command Reference

### db_manager.py Commands

| Command | Description | Example |
|---------|-------------|---------|
| `status` | Show database version and schema | `python db_manager.py status -d hw.db` |
| `migrate` | Apply pending migrations | `python db_manager.py migrate -d hw.db` |
| `backup` | Create database backup | `python db_manager.py backup -d hw.db` |
| `init` | Initialize new database | `python db_manager.py init -d new.db` |
| `export-schema` | Export schema to JSON | `python db_manager.py export-schema -d hw.db` |
| `repair` | Repair corrupted database | `python db_manager.py repair -d hw.db` |

### Migration API

| Method | Description |
|--------|-------------|
| `get_current_version()` | Get current schema version |
| `migrate_to_latest()` | Apply all pending migrations |
| `backup_database()` | Create database backup |
| `export_schema_info()` | Export schema information |

## Integration with Existing Code

The migration system is designed to be backward compatible. Existing code will continue to work, and databases will be automatically upgraded when `auto_migrate=True` is used (default).

### Before (Old Code)
```python
dbworker = DbHelper('test')
dbworker.createdbtable()
```

### After (New Code with Migrations)
```python
# Automatically applies migrations
dbworker = DbHelper('servers', 'hw_automation.db', auto_migrate=True)
dbworker.createdbtable()
```

This migration system ensures your hardware automation database can evolve safely over time while preserving all existing data and maintaining compatibility with your existing codebase.
