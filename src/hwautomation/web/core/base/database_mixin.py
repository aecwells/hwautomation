"""
Database operations mixin for HWAutomation web interface.

This module provides DatabaseMixin with connection management,
transaction handling, query helpers, and comprehensive error handling.
"""

import os
from typing import Any, Dict, List, Tuple

from hwautomation.database import DbHelper
from hwautomation.logging import get_logger

logger = get_logger(__name__)


class DatabaseMixin:
    """
    Mixin providing database operations and connection management.

    Features:
    - Connection management
    - Transaction handling
    - Query helpers
    - Error handling
    """

    def __init__(self):
        if not hasattr(self, "db_helper"):
            # Use DATABASE_PATH from environment, defaulting to data/hw_automation.db
            db_path = os.getenv("DATABASE_PATH", "data/hw_automation.db")
            self.db_helper = DbHelper(db_path)

    def with_connection(self, func, *args, **kwargs):
        """Execute function with database connection."""
        try:
            with self.db_helper.get_connection() as conn:
                return func(conn, *args, **kwargs)
        except Exception as e:
            logger.error(f"Database operation failed: {e}", exc_info=True)
            raise

    def execute_query(
        self,
        query: str,
        params: Tuple = (),
        fetch_one: bool = False,
        fetch_all: bool = True,
    ):
        """Execute a database query with error handling."""

        def _execute(conn):
            cursor = conn.cursor()
            cursor.execute(query, params)

            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return cursor.rowcount

        return self.with_connection(_execute)

    def execute_many(self, query: str, params_list: List[Tuple]):
        """Execute a query with multiple parameter sets."""

        def _execute_many(conn):
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount

        return self.with_connection(_execute_many)

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information."""
        query = f"PRAGMA table_info({table_name})"
        rows = self.execute_query(query)

        return [
            {
                "column_id": row[0],
                "name": row[1],
                "type": row[2],
                "not_null": bool(row[3]),
                "default_value": row[4],
                "primary_key": bool(row[5]),
            }
            for row in rows
        ]
