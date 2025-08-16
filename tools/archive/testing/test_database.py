#!/usr/bin/env python3
"""
Test cases for database functionality.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from hwautomation.database.helper import DbHelper
from hwautomation.database.migrations import DatabaseMigrator


class TestDbHelper(unittest.TestCase):
    """Test cases for DbHelper class."""

    def setUp(self):
        """Set up test fixtures with temporary database."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db_helper = DbHelper(
            tablename="test_servers", db_path=self.db_path, auto_migrate=True
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.db_helper.close()
        try:
            os.unlink(self.db_path)
        except FileNotFoundError:
            pass

    def test_initialization(self):
        """Test that DbHelper initializes correctly."""
        self.assertIsNotNone(self.db_helper)
        self.assertEqual(self.db_helper.tablename, "test_servers")
        self.assertEqual(self.db_helper.db_path, self.db_path)

    def test_table_creation(self):
        """Test that tables are created properly."""
        # Table should be created during initialization
        # Check that the table exists by querying it
        table_name = self.db_helper._get_table_name()
        result = self.db_helper.sql_db_worker.execute(
            f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
        ).fetchone()
        self.assertIsNotNone(result)

    def test_server_operations(self):
        """Test basic server operations."""
        server_id = "test_server_001"

        # Test server creation
        self.db_helper.createrowforserver(server_id)
        exists_list = self.db_helper.checkifserveridexists(server_id)
        self.assertTrue(exists_list[0])

        # Test server info update
        self.db_helper.updateserverinfo(server_id, "status_name", "Ready")

        # Test server retrieval
        server_info = self.db_helper.get_server_by_id(server_id)
        self.assertIsNotNone(server_info)


class TestDatabaseMigrator(unittest.TestCase):
    """Test cases for DatabaseMigrator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name

    def tearDown(self):
        """Clean up test fixtures."""
        try:
            os.unlink(self.db_path)
        except FileNotFoundError:
            pass

    def test_migrator_initialization(self):
        """Test that DatabaseMigrator initializes correctly."""
        migrator = DatabaseMigrator(self.db_path)
        self.assertIsNotNone(migrator)
        migrator.close()

    def test_migration_to_latest(self):
        """Test migration to latest version."""
        migrator = DatabaseMigrator(self.db_path)
        try:
            migrator.migrate_to_latest()
            # Should not raise an exception
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Migration failed: {e}")
        finally:
            migrator.close()


if __name__ == "__main__":
    unittest.main()
