"""
Database helper module for hardware automation.
Provides database connectivity and basic operations.
"""

from typing import Dict, List, Optional

import sqlite3

from .migrations import DatabaseMigrator


class DbHelper:
    """Database helper class for managing server information"""

    def __init__(
        self,
        db_path: str = "hw_automation.db",
        tablename: str = "servers",
        auto_migrate: bool = True,
    ):
        """
        Initialize database helper.

        Args:
            db_path: Path to database file (defaults to hw_automation.db)
            tablename: Name of the main table (for backward compatibility, defaults to servers)
            auto_migrate: Whether to automatically apply migrations
        """
        self.tablename = tablename
        self.db_path = db_path
        # Enable thread-safe SQLite connections for orchestration workflows
        self.sql_database = sqlite3.connect(db_path, check_same_thread=False)
        self.sql_db_worker = self.sql_database

        # Apply migrations if requested
        if auto_migrate:
            self.migrate_database()

    def migrate_database(self):
        """Apply database migrations to ensure current schema"""
        try:
            migrator = DatabaseMigrator(self.db_path)
            migrator.migrate_to_latest()
            migrator.close()

            # Reconnect after migration with thread-safe connection
            self.sql_database = sqlite3.connect(self.db_path, check_same_thread=False)
            self.sql_db_worker = self.sql_database

        except Exception as e:
            print(f"Migration failed: {e}")
            # Fall back to old table creation if migration fails
            self.createdbtable_legacy()

    def get_connection(self):
        """Get a database connection context manager"""
        return self.sql_database

    def createdbtable_legacy(self):
        """Legacy table creation for backward compatibility"""
        self.sql_db_worker.execute(
            " CREATE TABLE IF NOT EXISTS " + self.tablename + " ("
            "server_id TEXT,"  # system_id
            "status_name TEXT,"  # status_name
            "is_ready TEXT,"  # whether server is ready for commissioning, TRUE or FALSE
            "server_model TEXT,"  # hardware_info.mainboard_product
            "ip_address TEXT,"  # ip_address
            "ip_address_works TEXT,"  # TRUE or FALSE, describes ip_address
            "ipmi_address TEXT,"  # pull from ssh connection and ipmitool
            "ipmi_address_works TEXT,"  # pull from ssh connection and ipmitool
            "kcs_status TEXT,"
            "host_interface_status TEXT,"
            "currServerModels TEXT ) "
        )

    def createdbtable(self):
        """Create table using current schema (handled by migrations)"""
        # Table creation is now handled by the migration system
        # This method exists for backward compatibility
        try:
            # Check if table exists with current schema
            self.sql_db_worker.execute(
                f"SELECT name FROM sqlite_master WHERE type='table' AND name='{self.tablename}'"
            )
            if not self.sql_db_worker.fetchone():
                # If table doesn't exist, create with legacy schema and let migrations handle upgrades
                self.createdbtable_legacy()
        except Exception as e:
            print(f"Error checking table existence: {e}")
            self.createdbtable_legacy()

    def createrowforserver(self, serverid: str):
        """Create a new row for a server"""
        table_name = self._get_table_name()
        self.sql_db_worker.execute(
            f"INSERT INTO {table_name} (server_id) VALUES (?)", (serverid,)
        )
        self.sql_db_worker.commit()

    def updateserverinfo(self, serverid: str, column: str, colval: str):
        """Update server information"""
        table_name = self._get_table_name()
        self.sql_db_worker.execute(
            f"UPDATE {table_name} SET {column} = ? WHERE server_id = ?",
            (colval, serverid),
        )
        self.sql_db_worker.commit()

    def checkifserveridexists(self, serverid: str) -> List[bool]:
        """Check if a server ID exists in the database"""
        table_name = self._get_table_name()
        check = [
            item[0]
            for item in self.sql_db_worker.execute(
                f"SELECT exists(SELECT 1 FROM {table_name} WHERE server_id = ?) AS row_exists",
                (serverid,),
            )
        ]
        return check

    def checkready(self, serverid: str):
        """Check if a server is ready"""
        table_name = self._get_table_name()
        return self.sql_db_worker.execute(
            f"SELECT is_ready FROM {table_name} WHERE server_id = ?", (serverid,)
        )

    def printtableinfo(self):
        """Print table information"""
        table_name = self._get_table_name()
        result = self.sql_db_worker.execute(f"SELECT * FROM {table_name}").fetchall()
        print(result)

    def getserverswithworkingips(self) -> List[str]:
        """Get list of server IPs that are working/reachable"""
        table_name = self._get_table_name()
        result = self.sql_db_worker.execute(
            f"SELECT ip_address FROM {table_name} WHERE ip_address_works = 'TRUE' AND ip_address != 'Unreachable'"
        ).fetchall()
        return [row[0] for row in result if row[0]]

    def _get_table_name(self) -> str:
        """Get the actual table name to use (handles migration from old to new table names)"""
        # Check if 'servers' table exists (new schema)
        result = self.sql_db_worker.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='servers'"
        ).fetchone()

        if result:
            return "servers"
        else:
            return self.tablename

    def get_database_version(self) -> int:
        """Get current database schema version"""
        try:
            result = self.sql_db_worker.execute(
                "SELECT MAX(version) FROM schema_migrations"
            ).fetchone()
            return result[0] if result[0] is not None else 0
        except sqlite3.OperationalError:
            # Migrations table doesn't exist, assume version 0
            return 0

    def update_server_metadata(self, server_id: str, **kwargs):
        """Update server with new metadata fields"""
        table_name = self._get_table_name()

        # Get available columns
        cursor = self.sql_db_worker.execute(f"PRAGMA table_info({table_name})")
        available_columns = [row[1] for row in cursor.fetchall()]

        # Filter kwargs to only include existing columns
        valid_updates = {k: v for k, v in kwargs.items() if k in available_columns}

        if valid_updates:
            set_clause = ", ".join([f"{k} = ?" for k in valid_updates.keys()])
            values = list(valid_updates.values()) + [server_id]

            self.sql_db_worker.execute(
                f"UPDATE {table_name} SET {set_clause} WHERE server_id = ?", values
            )
            self.sql_db_worker.commit()

    def get_server_by_id(self, server_id: str) -> Optional[Dict]:
        """Get complete server information by ID"""
        table_name = self._get_table_name()
        result = self.sql_db_worker.execute(
            f"SELECT * FROM {table_name} WHERE server_id = ?", (server_id,)
        ).fetchone()

        if result:
            # Get column names
            cursor = self.sql_db_worker.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]

            # Return as dictionary
            return dict(zip(columns, result))
        return None

    def close(self):
        """Close database connection"""
        if self.sql_database:
            self.sql_database.close()
