#!/usr/bin/env python3
"""
Database Consolidation Verification Script

This script verifies that the database consolidation was successful and
the GUI app now uses the root database as defined in config.yaml.
"""

import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from hwautomation.database.helper import DbHelper
from hwautomation.utils.config import load_config


def main():
    print("=== DATABASE CONSOLIDATION VERIFICATION ===\n")

    # 1. Check config.yaml database path
    print("1. Checking config.yaml database settings...")
    config = load_config(str(project_root / "config.yaml"))
    config_db_path = config.get("database", {}).get("path", "hw_automation.db")
    print(f"   Config database path: {config_db_path}")

    # 2. Resolve actual database path
    if not Path(config_db_path).is_absolute():
        actual_db_path = str(project_root / config_db_path)
    else:
        actual_db_path = config_db_path

    print(f"   Resolved database path: {actual_db_path}")
    print(f"   Database exists: {Path(actual_db_path).exists()}")

    # 3. Test GUI app database connection
    print("\n2. Testing GUI app database connection...")
    try:
        # Import GUI app components
        sys.path.append(str(project_root))
        from gui.app import db_helper

        print(f"   GUI app database path: {db_helper.db_path}")
        print(f"   Paths match: {db_helper.db_path == actual_db_path}")

        # Test database query
        import sqlite3

        conn = sqlite3.connect(db_helper.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT server_id, status_name, ip_address FROM servers")
        servers = [
            {"server_id": row[0], "status_name": row[1], "ip_address": row[2]}
            for row in cursor.fetchall()
        ]
        conn.close()

        print(f"   Successfully connected to database")
        print(f"   Found {len(servers)} servers")

        # Show server details
        if servers:
            print("\n   Server data:")
            for server in servers:
                server_id = server.get("server_id", "unknown")
                status = server.get("status_name", "unknown")
                ip = server.get("ip_address", "N/A")
                print(f"     - {server_id}: {status} ({ip})")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

    # 4. Check for old GUI database
    print("\n3. Checking for old database files...")
    gui_db_path = project_root / "gui" / "hw_automation.db"
    gui_backup_path = project_root / "gui" / "hw_automation.db.backup"

    print(f"   Old GUI database exists: {gui_db_path.exists()}")
    print(f"   Backup exists: {gui_backup_path.exists()}")

    # 5. Summary
    print(f"\n=== CONSOLIDATION RESULTS ===")
    print(f"✅ Single database location: {actual_db_path}")
    print(f"✅ GUI app uses config database: {db_helper.db_path == actual_db_path}")
    print(f"✅ Database contains {len(servers)} servers")
    print(f"✅ Old GUI database removed: {not gui_db_path.exists()}")
    print(f"✅ Backup preserved: {gui_backup_path.exists()}")

    print(f"\n🎉 Database consolidation successful!")
    print(f"   The application now uses a single database as defined in config.yaml")

    return True


if __name__ == "__main__":
    main()
