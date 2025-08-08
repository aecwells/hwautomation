#!/usr/bin/env python3
"""
Fix NULL values in the database for servers that were commissioned
through direct MaaS operations instead of the orchestration workflow.
"""

import logging
import sys
from pathlib import Path

import sqlite3

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from hwautomation.database.helper import DbHelper
from hwautomation.maas.client import MaasClient
from hwautomation.utils.config import load_config

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def fix_null_values():
    """Fix NULL values in the database"""
    try:
        # Load configuration
        config = load_config()

        # Initialize clients
        maas_client = MaasClient(config["maas"])
        db_helper = DbHelper("servers", "hw_automation.db")

        # Get servers with NULL values
        conn = sqlite3.connect("hw_automation.db")
        cursor = conn.cursor()

        # Find servers with NULL device_type or workflow_id
        cursor.execute(
            """
            SELECT server_id, device_type, workflow_id, commissioning_status, status_name
            FROM servers 
            WHERE device_type IS NULL OR workflow_id IS NULL OR commissioning_status IS NULL
            ORDER BY created_at DESC
        """
        )

        null_servers = cursor.fetchall()

        if not null_servers:
            logger.info("No servers with NULL values found")
            return

        logger.info(f"Found {len(null_servers)} servers with NULL values")

        for (
            server_id,
            device_type,
            workflow_id,
            commissioning_status,
            status_name,
        ) in null_servers:
            logger.info(f"Processing server: {server_id}")
            logger.info(
                f"  Current values - device_type: {device_type}, workflow_id: {workflow_id}, commissioning_status: {commissioning_status}, status_name: {status_name}"
            )

            try:
                # Get machine info from MaaS to determine device type
                machine_info = maas_client.get_machine(server_id)
                if not machine_info:
                    logger.warning(f"  Server {server_id} not found in MaaS, skipping")
                    continue

                # Determine device type based on machine info
                hardware_info = machine_info.get("hardware_info", {})
                memory_gb = (
                    hardware_info.get("memory", 0) / (1024**3)
                    if hardware_info.get("memory")
                    else 0
                )
                cpu_count = hardware_info.get("cpu_count", 0)

                # Simple heuristic to determine device type
                if memory_gb >= 64 and cpu_count >= 16:
                    inferred_device_type = "s2.c2.large"
                elif memory_gb >= 32 and cpu_count >= 8:
                    inferred_device_type = "s2.c2.medium"
                else:
                    inferred_device_type = "s2.c2.small"

                # Generate a workflow ID for tracking
                import time

                inferred_workflow_id = f"repair_{server_id}_{int(time.time())}"

                # Determine commissioning status based on MaaS status
                maas_status = machine_info.get("status_name", "")
                if maas_status in ["Ready", "Commissioned"]:
                    inferred_commissioning_status = "Basic Commissioning Complete"
                elif maas_status == "Commissioning":
                    inferred_commissioning_status = "In Progress"
                elif "Failed" in maas_status:
                    inferred_commissioning_status = "Failed"
                else:
                    inferred_commissioning_status = "Unknown"

                logger.info(
                    f"  Inferred values - device_type: {inferred_device_type}, workflow_id: {inferred_workflow_id}, commissioning_status: {inferred_commissioning_status}"
                )

                # Update NULL values only
                updates_made = []

                if device_type is None:
                    db_helper.updateserverinfo(
                        server_id, "device_type", inferred_device_type
                    )
                    updates_made.append(f"device_type -> {inferred_device_type}")

                if workflow_id is None:
                    db_helper.updateserverinfo(
                        server_id, "workflow_id", inferred_workflow_id
                    )
                    updates_made.append(f"workflow_id -> {inferred_workflow_id}")

                if commissioning_status is None:
                    db_helper.updateserverinfo(
                        server_id, "commissioning_status", inferred_commissioning_status
                    )
                    updates_made.append(
                        f"commissioning_status -> {inferred_commissioning_status}"
                    )

                # Update additional missing fields from MaaS data
                if machine_info.get("ip_addresses"):
                    ip_address = machine_info["ip_addresses"][0]
                    db_helper.updateserverinfo(server_id, "ip_address", ip_address)
                    db_helper.updateserverinfo(server_id, "ip_address_works", "TRUE")
                    updates_made.append(f"ip_address -> {ip_address}")

                # Update server model if available
                server_model = hardware_info.get("mainboard_product", "Unknown")
                db_helper.updateserverinfo(server_id, "server_model", server_model)
                updates_made.append(f"server_model -> {server_model}")

                # Update hardware info
                if hardware_info.get("cpu_count"):
                    cpu_model = f"{hardware_info.get('cpu_model', 'Unknown')} ({cpu_count} cores)"
                    db_helper.updateserverinfo(server_id, "cpu_model", cpu_model)
                    updates_made.append(f"cpu_model -> {cpu_model}")

                if memory_gb > 0:
                    db_helper.updateserverinfo(server_id, "memory_gb", int(memory_gb))
                    updates_made.append(f"memory_gb -> {int(memory_gb)}")

                logger.info(f"  Updates made: {', '.join(updates_made)}")

            except Exception as e:
                logger.error(f"  Error processing server {server_id}: {e}")
                continue

        conn.close()
        logger.info("Database repair completed")

        # Show final statistics
        conn = sqlite3.connect("hw_automation.db")
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM servers WHERE device_type IS NULL")
        null_device_type = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM servers WHERE workflow_id IS NULL")
        null_workflow_id = cursor.fetchone()[0]

        cursor.execute(
            "SELECT COUNT(*) FROM servers WHERE commissioning_status IS NULL"
        )
        null_commissioning_status = cursor.fetchone()[0]

        logger.info(
            f"Remaining NULL values: device_type={null_device_type}, workflow_id={null_workflow_id}, commissioning_status={null_commissioning_status}"
        )

        conn.close()

    except Exception as e:
        logger.error(f"Error fixing NULL values: {e}")
        raise


if __name__ == "__main__":
    fix_null_values()
