#!/usr/bin/env python3
"""
Example usage of the hardware automation package.
This demonstrates the main workflows using the new structured package.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hwautomation import *
from hwautomation.database.migrations import DatabaseMigrator
from hwautomation.hardware.ipmi import IpmiManager
from hwautomation.hardware.redfish_manager import RedfishManager
from hwautomation.maas.client import create_maas_client
from hwautomation.utils.config import load_config


def example_workflow():
    """Demonstrate a complete hardware automation workflow with the new package structure"""

    print("=== Hardware Automation Workflow Example ===\n")

    # Step 1: Load configuration
    print("1. Loading configuration...")
    config = load_config()
    print(f"MAAS Host: {config['maas']['host']}")
    print(f"Database: {config['database']['path']}")

    # Step 2: Initialize database with migrations
    print("\n2. Initializing database with migrations...")
    db_helper = DbHelper(
        tablename=config["database"]["table_name"],
        db_path=config["database"]["path"],
        auto_migrate=config["database"]["auto_migrate"],
    )

    # Step 3: Create MAAS client
    print("\n3. Creating MAAS client...")
    maas_client = create_maas_client(config["maas"])

    # Step 4: Get server data from MAAS
    print("\n4. Getting server data from MAAS...")
    machines = maas_client.get_machines()
    if not machines:
        print("No machines found in MAAS. Check connectivity and credentials.")
        return

    print(f"Found {len(machines)} machines in MAAS")

    # Step 5: Update database with machine information
    print("\n5. Updating database with machine information...")
    for machine in machines:
        system_id = machine["system_id"]
        status_name = machine["status_name"]

        # Check if machine exists in database
        if not db_helper.checkifserveridexists(system_id)[0]:
            db_helper.createrowforserver(system_id)
            print(f"Added new machine: {system_id}")

        # Update machine information
        db_helper.updateserverinfo(system_id, "status_name", status_name)

        # Get IP address if available
        ip_address = maas_client.get_machine_ip(system_id)
        if ip_address:
            # Test connectivity
            is_reachable = ping_host(ip_address)
            db_helper.updateserverinfo(system_id, "ip_address", ip_address)
            db_helper.updateserverinfo(
                system_id, "ip_address_works", "TRUE" if is_reachable else "FALSE"
            )
            print(
                f"Machine {system_id}: IP {ip_address} ({'reachable' if is_reachable else 'unreachable'})"
            )

    # Step 6: Show database contents
    print("\n6. Current database state:")
    db_helper.printtableinfo()

    # Step 7: Demonstrate new metadata features
    print("\n7. Demonstrating metadata features...")
    if machines:
        system_id = machines[0]["system_id"]
        db_helper.update_server_metadata(
            system_id, tags='["example", "demo"]', rack_location="Demo-Rack-01"
        )

        server_info = db_helper.get_server_by_id(system_id)
        if server_info:
            print(f"Updated server {system_id} with metadata:")
            for key, value in server_info.items():
                if value:
                    print(f"  {key}: {value}")

    print(f"\n=== Workflow Complete ===")
    print(f"Database version: {db_helper.get_database_version()}")

    # Cleanup
    db_helper.close()


def example_ipmi_operations():
    """Example of IPMI operations using the new structure"""

    print("=== IPMI Operations Example ===\n")

    # Load configuration
    config = load_config()

    # Create IPMI manager
    ipmi_manager = IpmiManager(
        username=config["ipmi"]["username"], timeout=config["ipmi"]["timeout"]
    )

    # Get database helper
    db_helper = DbHelper(
        tablename=config["database"]["table_name"], db_path=config["database"]["path"]
    )

    # Get servers with working IPs
    server_ips = db_helper.getserverswithworkingips()

    if not server_ips:
        print("No servers with working IPs found. Run main workflow first.")
        db_helper.close()
        return

    print(f"Found {len(server_ips)} servers with working IPs")

    # Get IPMI IPs
    print("\n1. Discovering IPMI IP addresses...")
    ipmi_ips = ipmi_manager.get_ipmi_ips_from_servers(
        server_ips, ssh_username=config["ssh"]["username"]
    )

    if ipmi_ips:
        print(f"Found IPMI IPs: {ipmi_ips}")

        # Example: Get power status (requires IPMI password)
        if "password" in config["ipmi"]:
            print("\n2. Checking power status...")
            for ipmi_ip in ipmi_ips[:1]:  # Check first one only
                power_status = ipmi_manager.get_power_status(
                    ipmi_ip, config["ipmi"]["password"]
                )
                print(f"Power status for {ipmi_ip}: {power_status}")
    else:
        print("No IPMI IPs found")

    # Cleanup
    db_helper.close()

    print("\n=== IPMI Operations Complete ===")


def example_redfish_operations():
    """Example of RedFish operations using the new structure"""

    print("=== RedFish Operations Example ===\n")

    # Load configuration
    config = load_config()

    # Create RedFish manager
    # Note: You'll need to update this to use the new RedfishManager
    # redfish_manager = RedfishManager(
    #     host="<target_ip>",  # This should be set per target
    #     username=config['ipmi']['username'],
    #     password="<password>"  # This should be set per target
    # )

    # Get database helper
    db_helper = DbHelper(
        tablename=config["database"]["table_name"], db_path=config["database"]["path"]
    )

    # Get IPMI manager to discover IPMI IPs
    ipmi_manager = IpmiManager()
    server_ips = db_helper.getserverswithworkingips()

    if server_ips:
        ipmi_ips = ipmi_manager.get_ipmi_ips_from_servers(
            server_ips[:1]
        )  # Get one for demo

        if ipmi_ips and "password" in config["ipmi"]:
            ipmi_ip = ipmi_ips[0]
            password = config["ipmi"]["password"]

            print(f"Testing RedFish operations on {ipmi_ip}...")

            # NOTE: RedFish operations updated for new RedfishManager
            print("\n=== RedFish Operations (Updated for new RedfishManager) ===")
            print("This section has been updated to use the new RedfishManager.")
            print("Uncomment and modify the code below to use the new implementation:")
            print()
            print("# Example usage with new RedfishManager:")
            print("# with RedfishManager(ipmi_ip, username, password) as redfish:")
            print("#     system_info = redfish.get_system_info()")
            print("#     if system_info:")
            print(
                "#         print(f'System: {system_info.manufacturer} {system_info.model}')"
            )
            print("#         print(f'Power State: {system_info.power_state}')")
            print("#     capabilities = redfish.discover_capabilities()")
            print(
                "#     print(f'BIOS Config Support: {capabilities.supports_bios_config}')"
            )

            # # Uncomment to use new RedfishManager:
            # try:
            #     with RedfishManager(ipmi_ip, username, password) as redfish:
            #         # Get system information
            #         print("\n1. Getting system information...")
            #         system_info = redfish.get_system_info()
            #         if system_info:
            #             print(f"System Model: {system_info.model}")
            #             print(f"Power State: {system_info.power_state}")
            #             print(f"Manufacturer: {system_info.manufacturer}")
            #
            #         # Check capabilities
            #         print("\n2. Checking Redfish capabilities...")
            #         capabilities = redfish.discover_capabilities()
            #         print(f"BIOS Config: {capabilities.supports_bios_config}")
            #         print(f"Power Control: {capabilities.supports_power_control}")
            #
            #         # Note: Thermal info would need to be implemented in new RedfishManager
            #         print("\n3. Thermal information not yet implemented in new RedfishManager")
            #
            # except Exception as e:
            #     print(f"RedFish operations failed: {e}")

            print("\nRedFish operations example completed (see comments for new usage)")
        else:
            print("No IPMI IPs available or password not configured")
    else:
        print("No servers with working IPs found")

    # Cleanup
    db_helper.close()

    print("\n=== RedFish Operations Complete ===")


def example_database_migration():
    """Demonstrate database migration features"""

    print("=== Database Migration Example ===\n")

    # Create a test database file
    test_db = "migration_test.db"

    print("1. Creating test database with migrations...")

    # Create new database with migrations
    migrator = DatabaseMigrator(test_db)
    migrator.migrate_to_latest()

    print(f"Database version: {migrator.get_current_version()}")

    # Show schema information
    print("\n2. Current schema:")
    schema_info = migrator.export_schema_info()

    for table_name, table_info in schema_info["tables"].items():
        print(f"  {table_name}:")
        for col in table_info["columns"]:
            print(f"    - {col['name']} ({col['type']})")

    migrator.close()

    print(f"\n3. Test database created: {test_db}")
    print(
        "You can examine it with: python scripts/db_manager.py status -d migration_test.db"
    )

    print("\n=== Migration Example Complete ===")


def example_configuration():
    """Demonstrate configuration management"""

    print("=== Configuration Management Example ===\n")

    # Load current configuration
    config = load_config()

    print("Current configuration:")
    print(f"  MAAS Host: {config['maas']['host']}")
    print(f"  Database Path: {config['database']['path']}")
    print(f"  IPMI Username: {config['ipmi']['username']}")
    print(f"  SSH Username: {config['ssh']['username']}")

    # Create a sample configuration file
    print("\n2. Creating sample configuration file...")
    from hwautomation.utils.config import create_sample_config

    create_sample_config("sample_config.yaml")

    print("\n=== Configuration Example Complete ===")


if __name__ == "__main__":
    print("Choose an example to run:")
    print("1. Main workflow (recommended to start with)")
    print("2. IPMI operations")
    print("3. RedFish operations")
    print("4. Database migration example")
    print("5. Configuration management")

    try:
        choice = input("Enter choice (1-5): ").strip()

        if choice == "1":
            example_workflow()
        elif choice == "2":
            example_ipmi_operations()
        elif choice == "3":
            example_redfish_operations()
        elif choice == "4":
            example_database_migration()
        elif choice == "5":
            example_configuration()
        else:
            print("Invalid choice. Running main workflow...")
            example_workflow()

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
