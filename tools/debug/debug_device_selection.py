#!/usr/bin/env python3
"""
Debug MaaS Connection for Device Selection

Test the MaaS connection and device retrieval specifically for the device selection service.
"""

import os
import sys
from pathlib import Path

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from hwautomation.maas.client import create_maas_client
from hwautomation.orchestration.device_selection import DeviceSelectionService
from hwautomation.utils.config import load_config


def test_maas_connection():
    """Test MaaS connection and device retrieval"""
    print("=" * 60)
    print("Debug: MaaS Connection for Device Selection")
    print("=" * 60)

    try:
        # Load configuration
        config_path = Path(__file__).parent / "config.yaml"
        print(f"Loading config from: {config_path}")

        if not config_path.exists():
            print("❌ config.yaml not found!")
            return False

        config = load_config(str(config_path))
        maas_config = config.get("maas", {})

        print(f"MaaS Host: {maas_config.get('host', 'Not configured')}")
        print(f"Consumer Key: {maas_config.get('consumer_key', 'Not configured')}")
        print(f"Token Key: {maas_config.get('token_key', 'Not configured')}")

        # Test MaaS client directly
        print("\n1. Testing MaaS Client Directly")
        print("-" * 40)

        maas_client = create_maas_client(maas_config)

        # Test basic connection
        print("Testing get_machines()...")
        machines = maas_client.get_machines()
        print(f"Raw machines from MaaS: {len(machines) if machines else 0}")

        if machines:
            print("First machine sample:")
            first_machine = machines[0]
            print(f"  System ID: {first_machine.get('system_id', 'Unknown')}")
            print(f"  Hostname: {first_machine.get('hostname', 'Unknown')}")
            print(f"  Status: {first_machine.get('status_name', 'Unknown')}")
            print(f"  Architecture: {first_machine.get('architecture', 'Unknown')}")

        # Test machine summary
        print("\nTesting get_machines_summary()...")
        summary = maas_client.get_machines_summary()
        print(f"Machine summaries: {len(summary) if summary else 0}")

        if summary:
            print("First summary sample:")
            first_summary = summary[0]
            print(f"  System ID: {first_summary.get('system_id', 'Unknown')}")
            print(f"  Hostname: {first_summary.get('hostname', 'Unknown')}")
            print(f"  Status: {first_summary.get('status', 'Unknown')}")
            print(f"  CPU Count: {first_summary.get('cpu_count', 0)}")
            print(f"  Memory: {first_summary.get('memory_display', 'Unknown')}")

        # Test available machines
        print("\nTesting get_available_machines()...")
        available = maas_client.get_available_machines()
        print(f"Available machines: {len(available) if available else 0}")

        # Test device selection service
        print("\n2. Testing Device Selection Service")
        print("-" * 40)

        device_service = DeviceSelectionService(maas_client=maas_client)

        # Test status summary
        status_summary = device_service.get_status_summary()
        print(f"Status Summary: {status_summary}")

        # Test available machines through service
        available_machines = device_service.list_available_machines()
        print(f"Available machines via service: {len(available_machines)}")

        if available_machines:
            print("Available machines details:")
            for machine in available_machines[:3]:  # Show first 3
                print(
                    f"  • {machine.get('hostname', 'Unknown')} ({machine.get('system_id', 'Unknown')})"
                )
                print(f"    Status: {machine.get('status', 'Unknown')}")
                print(
                    f"    CPU: {machine.get('cpu_count', 0)}, Memory: {machine.get('memory_display', 'Unknown')}"
                )

        # Test all machines for debugging
        print("\n3. Debugging All Machine Statuses")
        print("-" * 40)

        if machines:
            status_counts = {}
            for machine in machines:
                status = machine.get("status_name", "Unknown")
                status_counts[status] = status_counts.get(status, 0) + 1

            print("Machine status breakdown:")
            for status, count in status_counts.items():
                print(f"  {status}: {count}")

            print("\nAll machine details:")
            for machine in machines:
                print(
                    f"  • {machine.get('hostname', 'Unknown')} ({machine.get('system_id', 'Unknown')})"
                )
                print(f"    Status: {machine.get('status_name', 'Unknown')}")
                print(
                    f"    Owner: {machine.get('owner', {}).get('username', 'None') if machine.get('owner') else 'None'}"
                )
                print(f"    Power Type: {machine.get('power_type', 'Unknown')}")

        return len(machines) > 0

    except Exception as e:
        print(f"❌ Error testing MaaS connection: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("MaaS Device Selection Debug Tool")
    success = test_maas_connection()

    if success:
        print("\n✅ MaaS connection working - check status filtering logic")
    else:
        print("\n❌ MaaS connection failed - check configuration and network")
