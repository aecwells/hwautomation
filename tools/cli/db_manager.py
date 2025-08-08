#!/usr/bin/env python3
"""
Database management utility for hardware automation project.
Provides commands for migration, backup, and schema management.
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hwautomation.database.helper import DbHelper
from hwautomation.database.migrations import DatabaseMigrator, migrate_existing_database


def cmd_migrate(args):
    """Apply database migrations"""
    try:
        migrate_existing_database(args.database)
        print("Migration completed successfully")
    except Exception as e:
        print(f"Migration failed: {e}")
        return 1
    return 0


def cmd_backup(args):
    """Create database backup"""
    try:
        migrator = DatabaseMigrator(args.database)
        backup_path = migrator.backup_database(args.output)
        migrator.close()
        print(f"Backup created: {backup_path}")
    except Exception as e:
        print(f"Backup failed: {e}")
        return 1
    return 0


def cmd_status(args):
    """Show database status and schema information"""
    try:
        migrator = DatabaseMigrator(args.database)

        current_version = migrator.get_current_version()
        applied_migrations = migrator.get_applied_migrations()
        all_migrations = migrator.get_all_migrations()

        print(f"Database: {args.database}")
        print(f"Current version: {current_version}")
        print(f"Applied migrations: {applied_migrations}")

        print("\nAvailable migrations:")
        for version, name, _ in all_migrations:
            status = "✓" if version in applied_migrations else "○"
            print(f"  {status} {version}: {name}")

        # Export and display schema
        if args.verbose:
            schema_info = migrator.export_schema_info()
            print("\nSchema details:")
            for table_name, table_info in schema_info["tables"].items():
                print(f"  Table: {table_name}")
                for col in table_info["columns"]:
                    pk = " (PK)" if col["primary_key"] else ""
                    nn = " NOT NULL" if col["not_null"] else ""
                    default = f" DEFAULT {col['default']}" if col["default"] else ""
                    print(f"    - {col['name']} {col['type']}{pk}{nn}{default}")

        migrator.close()

    except Exception as e:
        print(f"Status check failed: {e}")
        return 1
    return 0


def cmd_export_schema(args):
    """Export schema information to JSON"""
    try:
        migrator = DatabaseMigrator(args.database)
        schema_info = migrator.export_schema_info()
        migrator.close()

        output_file = (
            args.output
            or f"schema_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(output_file, "w") as f:
            json.dump(schema_info, f, indent=2)

        print(f"Schema exported to: {output_file}")

    except Exception as e:
        print(f"Schema export failed: {e}")
        return 1
    return 0


def cmd_init(args):
    """Initialize a new database with latest schema"""
    try:
        if os.path.exists(args.database) and not args.force:
            print(f"Database {args.database} already exists. Use --force to overwrite.")
            return 1

        # Remove existing file if force is specified
        if args.force and os.path.exists(args.database):
            os.remove(args.database)

        # Create new database with migrations
        migrator = DatabaseMigrator(args.database)
        migrator.migrate_to_latest()

        print(f"Database initialized: {args.database}")
        print(f"Schema version: {migrator.get_current_version()}")

        migrator.close()

    except Exception as e:
        print(f"Database initialization failed: {e}")
        return 1
    return 0


def cmd_repair(args):
    """Attempt to repair a corrupted database"""
    try:
        # Create backup first
        migrator = DatabaseMigrator(args.database)
        backup_path = migrator.backup_database()
        print(f"Backup created before repair: {backup_path}")

        # Run PRAGMA integrity_check
        cursor = migrator.cursor
        result = cursor.execute("PRAGMA integrity_check").fetchall()

        if result == [("ok",)]:
            print("Database integrity check passed")
        else:
            print("Database integrity issues found:")
            for row in result:
                print(f"  {row[0]}")

        # Run VACUUM to rebuild database
        print("Running VACUUM to rebuild database...")
        cursor.execute("VACUUM")
        migrator.connection.commit()

        print("Database repair completed")
        migrator.close()

    except Exception as e:
        print(f"Database repair failed: {e}")
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Database management utility for hardware automation"
    )

    parser.add_argument(
        "--database",
        "-d",
        default="hw_automation.db",
        help="Database file path (default: hw_automation.db)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Migrate command
    migrate_parser = subparsers.add_parser("migrate", help="Apply database migrations")

    # Backup command
    backup_parser = subparsers.add_parser("backup", help="Create database backup")
    backup_parser.add_argument("--output", "-o", help="Backup file path")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show database status")
    status_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed schema information"
    )

    # Export schema command
    export_parser = subparsers.add_parser("export-schema", help="Export schema to JSON")
    export_parser.add_argument("--output", "-o", help="Output file path")

    # Initialize command
    init_parser = subparsers.add_parser("init", help="Initialize new database")
    init_parser.add_argument(
        "--force", "-f", action="store_true", help="Overwrite existing database"
    )

    # Repair command
    repair_parser = subparsers.add_parser("repair", help="Repair corrupted database")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Map commands to functions
    commands = {
        "migrate": cmd_migrate,
        "backup": cmd_backup,
        "status": cmd_status,
        "export-schema": cmd_export_schema,
        "init": cmd_init,
        "repair": cmd_repair,
    }

    if args.command in commands:
        return commands[args.command](args)
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
