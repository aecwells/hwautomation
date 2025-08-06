"""
Unit tests for database helper functionality.
"""

import pytest
from unittest.mock import Mock, patch
from hwautomation.database.helper import DbHelper


class TestDbHelper:
    """Test database helper functionality."""
    
    def test_init_with_memory_db(self):
        """Test initialization with in-memory database."""
        helper = DbHelper(db_path=':memory:', tablename='test_table')
        assert helper.db_path == ':memory:'
        assert helper.tablename == 'test_table'
    
    def test_init_with_file_db(self):
        """Test initialization with file database."""
        helper = DbHelper(db_path='test.db', tablename='servers')
        assert helper.db_path == 'test.db'
        assert helper.tablename == 'servers'
    
    def test_basic_functionality(self):
        """Test basic DbHelper functionality."""
        helper = DbHelper(db_path=':memory:', tablename='test_table')
        # Just test that the object was created successfully
        assert helper is not None
        assert hasattr(helper, 'db_path')
        assert hasattr(helper, 'tablename')
