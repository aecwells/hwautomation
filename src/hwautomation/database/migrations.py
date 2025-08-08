"""
Database migration system for hardware automation project.
Handles schema changes and data upgrades between versions.
."""

import json
import os
from datetime import datetime
from typing import Any, Callable, Dict, List

import sqlite3


class DatabaseMigrator:
    """Handles database schema migrations."""

    def __init__(self, db_path: str = ":memory:"):
        """
        Initialize the database migrator.

        Args:
            db_path: Path to the SQLite database file
        ."""
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

        # Ensure migrations table exists
        self._ensure_migrations_table()

    def _ensure_migrations_table(self):
        """Create the migrations tracking table if it doesn't exist."""
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                checksum TEXT
            )
        ."""
        )
        self.connection.commit()

    def get_current_version(self) -> int:
        """Get the current database schema version."""
        result = self.cursor.execute(
            "SELECT MAX(version) FROM schema_migrations"
        ).fetchone()
        return result[0] if result[0] is not None else 0

    def get_applied_migrations(self) -> List[int]:
        """Get list of all applied migration versions."""
        results = self.cursor.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
        return [row[0] for row in results]

    def record_migration(self, version: int, name: str, checksum: str = None):
        """Record that a migration has been applied."""
        self.cursor.execute(
            """
            INSERT INTO schema_migrations (version, name, checksum)
            VALUES (?, ?, ?)
        .""",
            (version, name, checksum),
        )
        self.connection.commit()

    def apply_migration(self, version: int, name: str, migration_func: Callable):
        """
        Apply a single migration.

        Args:
            version: Migration version number
            name: Human-readable migration name
            migration_func: Function that performs the migration
        ."""
        current_version = self.get_current_version()

        if version <= current_version:
            print(f"Migration {version} ({name}) already applied")
            return

        print(f"Applying migration {version}: {name}")

        try:
            # Begin transaction
            self.cursor.execute("BEGIN TRANSACTION")

            # Apply the migration
            migration_func(self.cursor)

            # Record the migration
            self.record_migration(version, name)

            # Commit transaction
            self.connection.commit()
            print(f"✓ Migration {version} applied successfully")

        except Exception as e:
            # Rollback on error
            self.connection.rollback()
            print(f"✗ Migration {version} failed: {e}")
            raise

    def migrate_to_latest(self):
        """Apply all pending migrations."""
        migrations = self.get_all_migrations()
        applied = self.get_applied_migrations()

        for version, name, migration_func in migrations:
            if version not in applied:
                self.apply_migration(version, name, migration_func)

    def get_all_migrations(self) -> List[tuple]:
        """
        Get all available migrations in order.
        Returns list of (version, name, migration_function) tuples.
        ."""
        return [
            (1, "Initial schema", self._migration_001_initial_schema),
            (2, "Add IPMI fields", self._migration_002_add_ipmi_fields),
            (3, "Add timestamps", self._migration_003_add_timestamps),
            (4, "Add server metadata", self._migration_004_add_metadata),
            (5, "Add power state tracking", self._migration_005_add_power_state),
            (
                6,
                "Add device type and workflow fields",
                self._migration_006_add_device_workflow_fields,
            ),
        ]

    # Migration functions
    def _migration_001_initial_schema(self, cursor):
        """Migration 001: Create initial schema."""
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS servers (
                server_id TEXT PRIMARY KEY,
                status_name TEXT,
                is_ready TEXT,
                server_model TEXT,
                ip_address TEXT,
                ip_address_works TEXT,
                ipmi_address TEXT,
                ipmi_address_works TEXT,
                kcs_status TEXT,
                host_interface_status TEXT
            )
        ."""
        )

    def _migration_002_add_ipmi_fields(self, cursor):
        """Migration 002: Add additional IPMI-related fields."""
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(servers)")
        columns = [row[1] for row in cursor.fetchall()]

        if "ipmi_username" not in columns:
            cursor.execute(
                "ALTER TABLE servers ADD COLUMN ipmi_username TEXT DEFAULT 'ADMIN'"
            )

        if "ipmi_password_set" not in columns:
            cursor.execute(
                "ALTER TABLE servers ADD COLUMN ipmi_password_set TEXT DEFAULT 'FALSE'"
            )

        if "bios_password_set" not in columns:
            cursor.execute(
                "ALTER TABLE servers ADD COLUMN bios_password_set TEXT DEFAULT 'FALSE'"
            )

        if "redfish_available" not in columns:
            cursor.execute(
                "ALTER TABLE servers ADD COLUMN redfish_available TEXT DEFAULT 'UNKNOWN'"
            )

    def _migration_003_add_timestamps(self, cursor):
        """Migration 003: Add timestamp tracking."""
        cursor.execute("PRAGMA table_info(servers)")
        columns = [row[1] for row in cursor.fetchall()]

        if "created_at" not in columns:
            cursor.execute(
                "ALTER TABLE servers ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            )

        if "updated_at" not in columns:
            cursor.execute(
                "ALTER TABLE servers ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            )

        if "last_seen" not in columns:
            cursor.execute("ALTER TABLE servers ADD COLUMN last_seen TIMESTAMP")

        # Create trigger to update updated_at
        cursor.execute(
            """
            CREATE TRIGGER IF NOT EXISTS update_servers_timestamp
            AFTER UPDATE ON servers
            BEGIN
                UPDATE servers SET updated_at = CURRENT_TIMESTAMP WHERE server_id = NEW.server_id;
            END
        ."""
        )

    def _migration_004_add_metadata(self, cursor):
        """Migration 004: Add server metadata fields."""
        cursor.execute("PRAGMA table_info(servers)")
        columns = [row[1] for row in cursor.fetchall()]

        new_columns = [
            ("cpu_model", "TEXT"),
            ("memory_gb", "INTEGER"),
            ("storage_info", "TEXT"),
            ("network_interfaces", "TEXT"),
            ("firmware_version", "TEXT"),
            ("rack_location", "TEXT"),
            ("tags", "TEXT"),  # JSON array of tags
        ]

        for column_name, column_type in new_columns:
            if column_name not in columns:
                cursor.execute(
                    f"ALTER TABLE servers ADD COLUMN {column_name} {column_type}"
                )

    def _migration_005_add_power_state(self, cursor):
        """Migration 005: Add power state tracking."""
        cursor.execute("PRAGMA table_info(servers)")
        columns = [row[1] for row in cursor.fetchall()]

        if "power_state" not in columns:
            cursor.execute(
                "ALTER TABLE servers ADD COLUMN power_state TEXT DEFAULT 'UNKNOWN'"
            )

        if "last_power_change" not in columns:
            cursor.execute("ALTER TABLE servers ADD COLUMN last_power_change TIMESTAMP")

        # Create power state history table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS power_state_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_id TEXT NOT NULL,
                old_state TEXT,
                new_state TEXT NOT NULL,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                changed_by TEXT,
                FOREIGN KEY (server_id) REFERENCES servers (server_id)
            )
        ."""
        )

    def _migration_006_add_device_workflow_fields(self, cursor):
        """Migration 006: Add device type and workflow-related fields."""
        cursor.execute("PRAGMA table_info(servers)")
        columns = [row[1] for row in cursor.fetchall()]

        # Core workflow fields
        workflow_fields = [
            (
                "device_type",
                "TEXT",
            ),  # Device type for BIOS config (e.g., PowerEdge R7525)
            (
                "server_type",
                "TEXT",
            ),  # Server type category (e.g., compute, storage, etc.)
            ("commissioning_status", "TEXT"),  # Current commissioning status
            ("workflow_id", "TEXT"),  # Current/last workflow ID
            (
                "workflow_status",
                "TEXT",
            ),  # Workflow status (pending, running, completed, failed)
            ("last_workflow_run", "TIMESTAMP"),  # When last workflow was executed
            ("bios_config_applied", "TEXT"),  # Which BIOS config was last applied
            ("bios_config_version", "TEXT"),  # Version of BIOS config applied
            ("ipmi_configured", "INTEGER DEFAULT 0"),  # Boolean: IPMI configured (0/1)
            ("ssh_accessible", "INTEGER DEFAULT 0"),  # Boolean: SSH accessible (0/1)
            (
                "hardware_validated",
                "INTEGER DEFAULT 0",
            ),  # Boolean: Hardware discovery completed (0/1)
            (
                "provisioning_target",
                "TEXT",
            ),  # Target environment (production, staging, etc.)
            ("assigned_role", "TEXT"),  # Server role (web, database, storage, etc.)
            ("deployment_status", "TEXT"),  # Deployment status in target environment
            ("notes", "TEXT"),  # Admin notes/comments
        ]

        for column_name, column_type in workflow_fields:
            if column_name not in columns:
                cursor.execute(
                    f"ALTER TABLE servers ADD COLUMN {column_name} {column_type}"
                )

        # Create index on workflow_id for better performance
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_servers_workflow_id
            ON servers(workflow_id)
        ."""
        )

        # Create index on device_type for filtering
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_servers_device_type
            ON servers(device_type)
        ."""
        )

        # Create workflow history table for tracking workflow executions
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS workflow_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT NOT NULL,
                server_id TEXT NOT NULL,
                device_type TEXT,
                status TEXT NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                steps_completed INTEGER DEFAULT 0,
                total_steps INTEGER DEFAULT 0,
                error_message TEXT,
                metadata TEXT, -- JSON string for additional data
                FOREIGN KEY (server_id) REFERENCES servers (server_id)
            )
        ."""
        )

        # Create index on workflow history for performance
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_workflow_history_server_id
            ON workflow_history(server_id)
        ."""
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_workflow_history_workflow_id
            ON workflow_history(workflow_id)
        ."""
        )

    def backup_database(self, backup_path: str = None):
        """Create a backup of the current database."""
        if backup_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"hw_automation_backup_{timestamp}.db"

        if self.db_path == ":memory:":
            print("Cannot backup in-memory database")
            return None

        # Create backup using SQLite's backup API
        with sqlite3.connect(backup_path) as backup_conn:
            self.connection.backup(backup_conn)

        print(f"Database backed up to: {backup_path}")
        return backup_path

    def export_schema_info(self) -> Dict[str, Any]:
        """Export current schema information for debugging."""
        schema_info: Dict[str, Any] = {
            "current_version": self.get_current_version(),
            "applied_migrations": self.get_applied_migrations(),
            "tables": {},
            "exported_at": datetime.now().isoformat(),
        }

        # Get table information
        tables = self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        ).fetchall()

        for (table_name,) in tables:
            # Get column information
            columns = self.cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
            schema_info["tables"][table_name] = {
                "columns": [
                    {
                        "name": col[1],
                        "type": col[2],
                        "not_null": bool(col[3]),
                        "default": col[4],
                        "primary_key": bool(col[5]),
                    }
                    for col in columns
                ]
            }

        return schema_info

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()


def migrate_existing_database(old_db_path: str, new_db_path: str = None):
    """
    Migrate an existing database to the latest schema.

    Args:
        old_db_path: Path to existing database
        new_db_path: Path for migrated database (optional)
    ."""
    if new_db_path is None:
        new_db_path = old_db_path

    print(f"Migrating database: {old_db_path}")

    # Create migrator instance
    migrator = DatabaseMigrator(old_db_path)

    try:
        # Show current state
        current_version = migrator.get_current_version()
        print(f"Current database version: {current_version}")

        # Create backup before migration
        if old_db_path != ":memory:":
            backup_path = migrator.backup_database()
            print(f"Backup created: {backup_path}")

        # Apply migrations
        print("Applying migrations...")
        migrator.migrate_to_latest()

        # Show final state
        final_version = migrator.get_current_version()
        print(f"Database migrated to version: {final_version}")

        # Export schema info
        schema_info = migrator.export_schema_info()
        print("\nFinal schema:")
        for table_name, table_info in schema_info["tables"].items():
            print(f"  Table: {table_name}")
            for col in table_info["columns"]:
                print(f"    - {col['name']} ({col['type']})")

    except Exception as e:
        print(f"Migration failed: {e}")
        raise
    finally:
        migrator.close()
