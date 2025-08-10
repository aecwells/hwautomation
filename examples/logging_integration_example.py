"""
Example: Integrating Unified Logging System

This example shows how to update existing modules to use the new unified logging system.
"""

# Before: Old logging pattern in hardware/discovery.py
import logging

logger = logging.getLogger(__name__)


class OldHardwareDiscoveryManager:
    def __init__(self, ssh_manager, config=None):
        self.ssh_manager = ssh_manager
        self.config = config or {}
        self.logger = logging.getLogger(__name__)  # Inconsistent pattern

    def discover_hardware(self, hostname: str, username: str = "ubuntu"):
        self.logger.info(
            f"Starting discovery for {hostname}"
        )  # No correlation tracking
        # ... discovery logic ...


import uuid

# After: New logging pattern with unified system
from hwautomation.logging import get_logger, with_correlation


class NewHardwareDiscoveryManager:
    def __init__(self, ssh_manager, config=None):
        self.ssh_manager = ssh_manager
        self.config = config or {}
        self.logger = get_logger(__name__)  # Unified logger

    def discover_hardware(self, hostname: str, username: str = "ubuntu"):
        # Generate correlation ID for request tracking
        correlation_id = f"discovery-{uuid.uuid4().hex[:8]}"

        with with_correlation(correlation_id):
            self.logger.info(f"Starting discovery for {hostname}")

            try:
                # All nested function calls will inherit the correlation ID
                system_info = self._discover_system_info(hostname)
                ipmi_info = self._discover_ipmi_info(hostname)

                self.logger.info(f"Discovery completed successfully for {hostname}")
                return {
                    "system_info": system_info,
                    "ipmi_info": ipmi_info,
                    "correlation_id": correlation_id,
                }

            except Exception as e:
                self.logger.error(f"Discovery failed for {hostname}: {e}")
                raise

    def _discover_system_info(self, hostname: str):
        # This log will automatically include the correlation ID
        self.logger.debug(f"Discovering system info for {hostname}")
        # ... discovery logic ...
        return {}

    def _discover_ipmi_info(self, hostname: str):
        # This log will also include the correlation ID
        self.logger.debug(f"Discovering IPMI info for {hostname}")
        # ... discovery logic ...
        return {}


import uuid

# Example: Web route with correlation tracking
from flask import Flask, request

from hwautomation.logging import get_logger, set_correlation_id

app = Flask(__name__)
logger = get_logger(__name__)


@app.before_request
def before_request():
    """Set correlation ID for each request."""
    correlation_id = (
        request.headers.get("X-Correlation-ID") or f"req-{uuid.uuid4().hex[:8]}"
    )
    set_correlation_id(correlation_id)


@app.route("/api/discover", methods=["POST"])
def discover_hardware():
    """Discovery endpoint with automatic correlation tracking."""
    data = request.get_json()
    hostname = data.get("hostname")

    # This log will include the request correlation ID
    logger.info(f"Received discovery request for {hostname}")

    try:
        discovery_manager = NewHardwareDiscoveryManager(ssh_manager, config)
        result = discovery_manager.discover_hardware(hostname)

        logger.info(f"Discovery request completed for {hostname}")
        return {"success": True, "data": result}

    except Exception as e:
        logger.error(f"Discovery request failed for {hostname}: {e}")
        return {"success": False, "error": str(e)}, 500


# Example: CLI tool with logging
# !/usr/bin/env python3
"""
HWAutomation CLI with unified logging
"""

import argparse
import os

from hwautomation.logging import get_logger, setup_logging


def main():
    parser = argparse.ArgumentParser(description="HWAutomation CLI")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    parser.add_argument(
        "--env", default="development", choices=["development", "staging", "production"]
    )
    parser.add_argument("command", choices=["discover", "configure", "provision"])
    parser.add_argument("--hostname", required=True)

    args = parser.parse_args()

    # Set up logging based on environment and verbosity
    if args.verbose:
        os.environ["HW_AUTOMATION_LOG_LEVEL"] = "DEBUG"

    setup_logging(environment=args.env)
    logger = get_logger(__name__)

    logger.info(f"Starting {args.command} command for {args.hostname}")

    try:
        if args.command == "discover":
            discovery_manager = NewHardwareDiscoveryManager(ssh_manager, config)
            result = discovery_manager.discover_hardware(args.hostname)
            print(f"Discovery completed: {result}")

        logger.info(f"Command {args.command} completed successfully")

    except Exception as e:
        logger.error(f"Command {args.command} failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()


# Example: Background task with correlation
import asyncio

from hwautomation.logging import get_logger, with_correlation


async def background_firmware_update(device_id: str, firmware_path: str):
    """Background firmware update with correlation tracking."""
    correlation_id = f"firmware-{device_id}-{uuid.uuid4().hex[:8]}"

    with with_correlation(correlation_id):
        logger = get_logger(__name__)
        logger.info(f"Starting firmware update for device {device_id}")

        try:
            # Simulate firmware update steps
            await asyncio.sleep(1)
            logger.debug("Downloading firmware")

            await asyncio.sleep(2)
            logger.debug("Validating firmware")

            await asyncio.sleep(5)
            logger.debug("Installing firmware")

            logger.info(f"Firmware update completed for device {device_id}")

        except Exception as e:
            logger.error(f"Firmware update failed for device {device_id}: {e}")
            raise


# Example: Testing with logging
import pytest

from hwautomation.logging import get_logger, setup_logging


@pytest.fixture(scope="session", autouse=True)
def setup_test_logging():
    """Set up logging for tests."""
    setup_logging(environment="development")


def test_hardware_discovery():
    """Test hardware discovery with logging."""
    logger = get_logger(__name__)
    logger.info("Starting hardware discovery test")

    discovery_manager = NewHardwareDiscoveryManager(mock_ssh_manager, {})

    with with_correlation("test-discovery-001"):
        result = discovery_manager.discover_hardware("test-host")
        assert result is not None
        logger.info("Hardware discovery test completed")


# Example: Configuration for different environments

# Development: logs/hwautomation.log will contain:
# 2024-08-08 15:30:45 - test-discovery-001 - hwautomation.hardware.discovery - INFO - discover_hardware:42 - Starting discovery for test-host
# 2024-08-08 15:30:45 - test-discovery-001 - hwautomation.hardware.discovery - DEBUG - _discover_system_info:58 - Discovering system info for test-host

# Production: logs/hwautomation.log will contain JSON:
# {"timestamp": "2024-08-08 15:30:45", "level": "INFO", "logger": "hwautomation.hardware.discovery", "function": "discover_hardware", "line": 42, "message": "Starting discovery for test-host", "correlation_id": "test-discovery-001"}


# Example: Integration with existing Flask app
def update_existing_flask_app():
    """Show how to update existing Flask app to use unified logging."""

    # In src/hwautomation/web/app.py - replace existing logging setup:

    # OLD:
    # import logging
    # logging.basicConfig(level=logging.INFO)
    # logger = logging.getLogger(__name__)

    # NEW:
    import os

    from hwautomation.logging import get_logger, setup_logging

    # Set up unified logging
    environment = os.getenv("HW_AUTOMATION_ENV", "development")
    setup_logging(environment=environment)
    logger = get_logger(__name__)

    # The rest of the Flask app remains the same, but now all logging
    # will be consistent and include correlation tracking
