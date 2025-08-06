import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from hwautomation import *
from hwautomation.maas.client import create_maas_client
from hwautomation.utils.env_config import load_config, get_config
from hwautomation.database.migrations import DatabaseMigrator

def testfunctions(input_cmd):
    """Test various functions based on input command"""
    
    # Load configuration from environment variables
    config = load_config()
    
    match input_cmd:
        case "startdb":
            # Initialize database with the new package structure
            db_helper = DbHelper(
                tablename=config['database']['table_name'],
                db_path=config['database']['path'],
                auto_migrate=config['database']['auto_migrate']
            )
            print("Database initialized with migrations")
            db_helper.close()
            
        case "response":
            # Get response from MAAS using new structure
            maas_client = create_maas_client(config['maas'])
            response = maas_client.get_machines()
            print(f"Retrieved {len(response)} servers from MAAS")
            return response
            
        case "full_update":
            # Full workflow example with new package structure
            print("Starting full server update workflow...")
            
            # 1. Load configuration
            config = load_config()
            
            # 2. Initialize database with migrations
            db_helper = DbHelper(
                tablename=config['database']['table_name'],
                db_path=config['database']['path'],
                auto_migrate=config['database']['auto_migrate']
            )
            
            # 3. Get server data from MAAS
            maas_client = create_maas_client(config['maas'])
            response = maas_client.get_machines()
            if not response:
                print("No response from MAAS")
                db_helper.close()
                return
            
            # 4. Update server information using new methods
            for machine in response:
                system_id = machine['system_id']
                
                # Create row if doesn't exist
                if not db_helper.checkifserveridexists(system_id)[0]:
                    db_helper.createrowforserver(system_id)
                
                # Update server information
                db_helper.updateserverinfo(system_id, 'status_name', machine.get('status_name', ''))
                
                # Get IP and test connectivity
                ip_address = maas_client.get_machine_ip(system_id)
                if ip_address:
                    is_reachable = ping_host(ip_address)
                    db_helper.updateserverinfo(system_id, 'ip_address', ip_address)
                    db_helper.updateserverinfo(system_id, 'ip_address_works', 'TRUE' if is_reachable else 'FALSE')
            
            # 5. Show database contents
            db_helper.printtableinfo()
            db_helper.close()
            
        case "migrate":
            db_path = input("Enter database path to migrate: ").strip()
            if db_path:
                try:
                    migrator = DatabaseMigrator(db_path)
                    migrator.migrate_to_latest()
                    print(f"Migration completed successfully to version {migrator.get_current_version()}")
                    migrator.close()
                except Exception as e:
                    print(f"Migration failed: {e}")
            
        case "db_status":
            db_path = input("Enter database path: ").strip()
            if db_path:
                try:
                    migrator = DatabaseMigrator(db_path)
                    version = migrator.get_current_version()
                    applied = migrator.get_applied_migrations()
                    print(f"Database version: {version}")
                    print(f"Applied migrations: {applied}")
                    migrator.close()
                except Exception as e:
                    print(f"Error checking database: {e}")
                    
        case "backup":
            db_path = input("Enter database path to backup: ").strip()
            if db_path:
                try:
                    migrator = DatabaseMigrator(db_path)
                    backup_path = migrator.backup_database()
                    migrator.close()
                    print(f"Backup created: {backup_path}")
                except Exception as e:
                    print(f"Backup failed: {e}")
            
        case "commission":
            config = load_config()
            maas_client = create_maas_client(config['maas'])
            response = maas_client.get_machines()
            if response:
                # Commission ready servers using new structure
                ready_machines = [m for m in response if m.get('status_name') == 'Ready']
                for machine in ready_machines:
                    result = maas_client.commission_machine(machine['system_id'])
                    print(f"Commissioned {machine['system_id']}: {result}")
            
        case "check_ready":
            config = load_config()
            maas_client = create_maas_client(config['maas'])
            response = maas_client.get_machines()
            if response:
                ready_count = sum(1 for m in response if m.get('status_name') == 'Ready')
                print(f"{ready_count} out of {len(response)} servers are ready")
                
        case "ipmi_check":
            from hwautomation.hardware.ipmi import IpmiManager
            config = load_config()
            
            # Get servers with working IPs from database
            db_helper = DbHelper(
                tablename=config['database']['table_name'],
                db_path=config['database']['path']
            )
            server_ips = db_helper.getserverswithworkingips()
            db_helper.close()
            
            if server_ips:
                ipmi_manager = IpmiManager(
                    username=config['ipmi']['username'],
                    timeout=config['ipmi']['timeout']
                )
                ipmi_ips = ipmi_manager.get_ipmi_ips_from_servers(
                    server_ips[:3],  # Limit to first 3 for demo
                    ssh_username=config['ssh']['username']
                )
                print(f"Found {len(ipmi_ips)} IPMI IPs: {ipmi_ips}")
            else:
                print("No servers with working IPs found")
            
        case "print":
            config = load_config()
            db_helper = DbHelper(
                tablename=config['database']['table_name'],
                db_path=config['database']['path']
            )
            db_helper.printtableinfo()
            db_helper.close()
            
        case _:
            print("Available commands:")
            print("  startdb - Initialize database")
            print("  response - Get MAAS response")
            print("  full_update - Complete workflow with migrations")
            print("  commission - Commission ready servers")
            print("  check_ready - Check if servers are ready")
            print("  ipmi_check - Check IPMI IPs")
            print("  migrate - Migrate existing database")
            print("  db_status - Check database version")
            print("  backup - Create database backup")
            print("  print - Show database contents")
            print("\nDatabase management:")
            print("  Use 'python scripts/db_manager.py --help' for advanced database commands")

def main():
    print("Hardware Automation Tool - Python Version")
    print("Converted from bash scripts with improved package structure")
    print("Type 'help' or any invalid command to see available options")
    print("NOTE: Make sure to configure settings in config.yaml first")
    
    while True:
        try:
            text = input("\nEnter command (or 'quit' to exit): ").strip()
            if text.lower() in ['quit', 'exit', 'q']:
                break
            if text == "":
                continue
            testfunctions(text)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()