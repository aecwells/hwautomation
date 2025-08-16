#!/usr/bin/env python3
"""
Migration script to update old files to use the new package structure.
This will show you what changes need to be made to existing files.
"""

import sys
from pathlib import Path


def show_migration_guide():
    """Show how to migrate from old to new structure"""

    print("Migration Guide: Old Files → New Package Structure")
    print("=" * 60)

    print("\n1. OLD IMPORT PATTERN (from flat files):")
    print("   from hwautolib import *")
    print("   from dbhelper import DbHelper")
    print("   from db_migrations import migrate_existing_database")

    print("\n2. NEW IMPORT PATTERN (from package):")
    print("   # Add src to path (for development)")
    print("   import sys")
    print("   from pathlib import Path")
    print("   sys.path.insert(0, str(Path(__file__).parent / 'src'))")
    print()
    print("   # Import from package")
    print("   from hwautomation import *")
    print("   from hwautomation.database.helper import DbHelper")
    print("   from hwautomation.database.migrations import DatabaseMigrator")
    print("   from hwautomation.maas.client import create_maas_client")
    print("   from hwautomation.hardware.ipmi import IpmiManager")
    print("   from hwautomation.hardware.redfish_manager import RedfishManager")
    print("   from hwautomation.utils.config import load_config")

    print("\n3. FUNCTION MAPPING:")
    function_mapping = [
        ("Old Function", "New Location"),
        ("-" * 30, "-" * 40),
        ("pullResponseFromMaas()", "maas_client.get_machines()"),
        ("bringUpDatabase()", "DbHelper() with auto_migrate=True"),
        ("migrate_existing_database()", "DatabaseMigrator.migrate_to_latest()"),
        ("createMaasOauth1Session()", "create_maas_client()"),
        ("ping_host()", "hwautomation.utils.network.ping_host()"),
        ("All IPMI functions", "IpmiManager class methods"),
        ("All RedFish functions", "RedfishManager class methods"),
    ]

    for old, new in function_mapping:
        print(f"   {old:<30} → {new}")

    print("\n4. CONFIGURATION CHANGES:")
    print("   Old: Hardcoded values in scripts")
    print("   New: config.yaml file with load_config()")
    print("   - Copy config.yaml.example to config.yaml")
    print("   - Update values for your environment")

    print("\n5. DATABASE MIGRATION:")
    print("   Old databases will be automatically migrated when using:")
    print("   DbHelper(auto_migrate=True)")

    print("\n6. FILES TO UPDATE:")
    files_to_update = [
        ("main.py", "Update imports and function calls"),
        ("example_usage.py", "Already updated in examples/"),
        ("test-library.py", "Update imports"),
        ("Any custom scripts", "Update imports and function calls"),
    ]

    for filename, action in files_to_update:
        print(f"   {filename:<20} - {action}")


def create_updated_main():
    """Create an updated version of main.py"""

    updated_main_content = '''#!/usr/bin/env python3
"""
Updated main.py using the new package structure.
"""

import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from hwautomation import *
from hwautomation.maas.client import create_maas_client
from hwautomation.hardware.ipmi import IpmiManager
from hwautomation.hardware.redfish_manager import RedfishManager
from hwautomation.utils.config import load_config
from hwautomation.database.migrations import DatabaseMigrator

def testfunctions(input_cmd):
    """Test various functions based on input command - Updated for new package structure"""
    match input_cmd:
        case "startdb":
            # Updated: Use new DbHelper with auto-migration
            config = load_config()
            db_helper = DbHelper(
                tablename=config['database']['table_name'],
                db_path=config['database']['path'],
                auto_migrate=True
            )
            print(f"Database initialized with version: {db_helper.get_database_version()}")
            db_helper.close()

        case "response":
            # Updated: Use new MAAS client
            config = load_config()
            maas_client = create_maas_client(config['maas'])
            machines = maas_client.get_machines()
            print(f"Retrieved {len(machines)} servers from MAAS")
            return machines

        case "full_update":
            # Updated: Full workflow with new package structure
            print("Starting full server update workflow...")

            # 1. Load configuration
            config = load_config()

            # 2. Initialize database with migrations
            db_helper = DbHelper(
                tablename=config['database']['table_name'],
                db_path=config['database']['path'],
                auto_migrate=True
            )

            # 3. Create MAAS client
            maas_client = create_maas_client(config['maas'])

            # 4. Get server data from MAAS
            machines = maas_client.get_machines()
            if not machines:
                print("No machines found in MAAS")
                db_helper.close()
                return

            # 5. Update server information
            for machine in machines:
                system_id = machine['system_id']
                status_name = machine['status_name']

                # Check if machine exists in database
                if not db_helper.checkifserveridexists(system_id)[0]:
                    db_helper.createrowforserver(system_id)
                    print(f"Added new machine: {system_id}")

                # Update machine information
                db_helper.updateserverinfo(system_id, 'status_name', status_name)

                # Get IP address if available
                ip_address = maas_client.get_machine_ip(system_id)
                if ip_address:
                    # Test connectivity
                    is_reachable = ping_host(ip_address)
                    db_helper.updateserverinfo(system_id, 'ip_address', ip_address)
                    db_helper.updateserverinfo(system_id, 'ip_address_works', 'TRUE' if is_reachable else 'FALSE')

            # 6. Show database contents
            db_helper.printtableinfo()
            db_helper.close()

        case "migrate":
            # Updated: Use new migration system
            config = load_config()
            db_path = input(f"Enter database path to migrate (default: {config['database']['path']}): ").strip()
            if not db_path:
                db_path = config['database']['path']

            try:
                migrator = DatabaseMigrator(db_path)
                migrator.migrate_to_latest()
                print(f"Migration completed successfully. Database version: {migrator.get_current_version()}")
                migrator.close()
            except Exception as e:
                print(f"Migration failed: {e}")

        case "ipmi_test":
            # New: IPMI testing with new structure
            config = load_config()

            ipmi_manager = IpmiManager(
                username=config['ipmi']['username'],
                timeout=config['ipmi']['timeout']
            )

            db_helper = DbHelper(
                tablename=config['database']['table_name'],
                db_path=config['database']['path']
            )

            server_ips = db_helper.getserverswithworkingips()
            if server_ips:
                ipmi_ips = ipmi_manager.get_ipmi_ips_from_servers(
                    server_ips[:1],  # Test first one only
                    ssh_username=config['ssh']['username']
                )
                print(f"Found IPMI IPs: {ipmi_ips}")
            else:
                print("No servers with working IPs found")

            db_helper.close()

        case "config":
            # New: Show current configuration
            config = load_config()
            print("Current configuration:")
            for section, values in config.items():
                print(f"  [{section}]")
                for key, value in values.items():
                    # Hide passwords
                    display_value = "***" if 'password' in key.lower() else value
                    print(f"    {key}: {display_value}")
                print()

        case _:
            print("Available commands:")
            print("  startdb     - Initialize database with migrations")
            print("  response    - Get servers from MAAS")
            print("  full_update - Complete workflow with database update")
            print("  migrate     - Migrate existing database")
            print("  ipmi_test   - Test IPMI functionality")
            print("  config      - Show current configuration")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        testfunctions(command)
    else:
        print("Usage: python main.py <command>")
        testfunctions("help")
'''

    return updated_main_content


def show_examples():
    """Show example usage patterns"""

    print("\n7. EXAMPLE USAGE PATTERNS:")
    print("=" * 40)

    print("\nA. Simple MAAS Integration:")
    print(
        """
    from hwautomation.maas.client import create_maas_client
    from hwautomation.utils.config import load_config

    config = load_config()
    maas_client = create_maas_client(config['maas'])
    machines = maas_client.get_machines()
    """
    )

    print("\nB. Database with Auto-Migration:")
    print(
        """
    from hwautomation import DbHelper
    from hwautomation.utils.config import load_config

    config = load_config()
    db_helper = DbHelper(
        tablename=config['database']['table_name'],
        db_path=config['database']['path'],
        auto_migrate=True  # Automatically migrate old databases
    )
    """
    )

    print("\nC. IPMI Operations:")
    print(
        """
    from hwautomation.hardware.ipmi import IpmiManager

    ipmi = IpmiManager(username="admin", timeout=30)
    power_status = ipmi.get_power_status("192.168.1.100", "password")
    """
    )


if __name__ == "__main__":
    show_migration_guide()
    show_examples()

    print("\n" + "=" * 60)
    print("NEXT STEPS:")
    print("1. Run: python validate_package.py")
    print("2. Install dependencies: pip install requests requests-oauthlib pyyaml")
    print("3. Create config.yaml from config.yaml.example")
    print("4. Test with: python examples/basic_usage.py")

    # Offer to create updated main.py
    create_updated = input("\nCreate updated main.py? (y/N): ").strip().lower()
    if create_updated == "y":
        updated_content = create_updated_main()
        with open("main_updated.py", "w") as f:
            f.write(updated_content)
        print("Created main_updated.py - Review and replace main.py when ready")
