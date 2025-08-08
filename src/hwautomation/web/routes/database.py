#!/usr/bin/env python3
"""
Database routes for HWAutomation Web Interface

Handles database management, table viewing, and database operations.
"""

import logging
import os

import sqlite3
from flask import Blueprint, jsonify, render_template, request

logger = logging.getLogger(__name__)

# Create blueprint for database routes
database_bp = Blueprint("database", __name__, url_prefix="/api/database")


@database_bp.route("/info")
def api_database_info():
    """Get database information."""
    try:
        from flask import current_app

        db_helper = getattr(current_app, "_hwautomation_db_helper", None)

        if not db_helper:
            return jsonify({"success": False, "error": "Database not available"}), 500

        db_path = db_helper.db_path

        # Get database file size
        if db_path != ":memory:" and os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            if size_bytes < 1024:
                size = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                size = f"{size_bytes / 1024:.1f} KB"
            else:
                size = f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            size = "In-memory"

        # Get SQLite version
        cursor = db_helper.sql_db_worker.cursor()
        cursor.execute("SELECT sqlite_version()")
        version = cursor.fetchone()[0]

        # Count tables
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]

        # Count servers (if table exists)
        try:
            cursor.execute("SELECT COUNT(*) FROM servers")
            server_count = cursor.fetchone()[0]
        except:
            server_count = 0

        cursor.close()

        return jsonify(
            {
                "success": True,
                "info": {
                    "version": version,
                    "size": size,
                    "path": db_path if db_path != ":memory:" else None,
                    "table_count": table_count,
                    "server_count": server_count,
                },
            }
        )

    except Exception as e:
        logger.error(f"Database info API error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@database_bp.route("/tables")
def api_database_tables():
    """Get database tables and their data."""
    try:
        from flask import current_app

        db_helper = getattr(current_app, "_hwautomation_db_helper", None)

        if not db_helper:
            return jsonify({"success": False, "error": "Database not available"}), 500

        format_type = request.args.get("format", "json")
        cursor = db_helper.sql_db_worker.cursor()

        # Get all tables
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        table_names = [row[0] for row in cursor.fetchall()]

        tables_data = {}

        for table_name in table_names:
            try:
                # Get table row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]

                # Get table data (limit to first 100 rows for display)
                limit = 100
                cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()

                # Convert to list of dictionaries
                data = []
                for row in rows:
                    row_dict = {}
                    for i, value in enumerate(row):
                        row_dict[columns[i]] = value
                    data.append(row_dict)

                tables_data[table_name] = {
                    "count": count,
                    "showing": len(data),
                    "data": data,
                }

            except Exception as e:
                logger.warning(f"Error reading table {table_name}: {e}")
                tables_data[table_name] = {
                    "count": 0,
                    "showing": 0,
                    "data": [],
                    "error": str(e),
                }

        cursor.close()

        if format_type == "json" and request.args.get("download"):
            response = jsonify({"success": True, "tables": tables_data})
            response.headers["Content-Disposition"] = (
                "attachment; filename=database_export.json"
            )
            return response

        return jsonify({"success": True, "tables": tables_data})

    except Exception as e:
        logger.error(f"Database tables API error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


def init_database_routes(app, db_helper):
    """Initialize database routes with dependencies."""

    # Page routes (not part of API blueprint)
    @app.route("/database")
    def database_management():
        """Database management page."""
        return render_template("database.html")
