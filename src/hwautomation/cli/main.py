#!/usr/bin/env python3
"""
Main CLI entry point for HWAutomation.

Provides command-line interface for hardware automation operations.
."""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from hwautomation import *
from hwautomation.database.migrations import DatabaseMigrator
from hwautomation.maas.client import create_maas_client
from hwautomation.utils.env_config import get_config, load_config

# Configure unified logging
from hwautomation.logging import setup_logging, get_logger
import os

# Set up unified logging system
environment = os.getenv('HW_AUTOMATION_ENV', 'development')
setup_logging(environment=environment)
logger = get_logger(__name__)


def init_database(config):
    """Initialize database with migrations."""
    try:
        db_helper = DbHelper(
            tablename=config["database"]["table_name"],
            db_path=config["database"]["path"],
            auto_migrate=config["database"]["auto_migrate"],
        )
        logger.info("Database initialized with migrations")
        db_helper.close()
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False


def get_maas_response(config):
    """Get response from MAAS API."""
    try:
        maas_client = create_maas_client(config["maas"])
        response = maas_client.get_machines()
        logger.info(f"Retrieved {len(response)} servers from MAAS")
        return response
    except Exception as e:
        logger.error(f"MAAS API call failed: {e}")
        return None


def run_full_workflow(config):
    """Execute full server update workflow."""
    logger.info("Starting full server update workflow...")

    # 1. Initialize database with migrations
    if not init_database(config):
        return False

    # 2. Get server data from MAAS
    machines = get_maas_response(config)
    if machines is None:
        return False

    logger.info(f"Workflow completed successfully with {len(machines)} machines")
    return True


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="HWAutomation CLI - Hardware automation and management",
        prog="hwautomation",
    )

    parser.add_argument(
        "command",
        choices=["init-db", "maas-status", "full-workflow", "version"],
        help="Command to execute",
    )

    parser.add_argument("--config", default=None, help="Path to configuration file")

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load configuration
    try:
        config = load_config(config_file=args.config)
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return 1

    # Execute command
    try:
        if args.command == "version":
            from hwautomation import __version__

            print(f"HWAutomation CLI v{__version__}")
            return 0

        elif args.command == "init-db":
            success = init_database(config)
            return 0 if success else 1

        elif args.command == "maas-status":
            machines = get_maas_response(config)
            if machines is not None:
                print(f"MAAS Status: {len(machines)} machines available")
                return 0
            return 1

        elif args.command == "full-workflow":
            success = run_full_workflow(config)
            return 0 if success else 1

        else:
            logger.error(f"Unknown command: {args.command}")
            return 1

    except Exception as e:
        logger.error(f"Command execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
