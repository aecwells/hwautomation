#!/usr/bin/env python3
"""
Enhanced Server Commissioning with Database Integration

This script demonstrates the enhanced server commissioning workflow that includes:
- Automatic database entry creation
- SSH connectivity validation
- Hardware discovery with vendor-specific tools
- Complete database tracking throughout the process

Usage:
    python enhanced_commissioning_demo.py --server-id <server_id> --device-type <type> --ipmi-ip <ip>
"""

import argparse
import json
import sys
import time
from pathlib import Path

# Add the source directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from hwautomation.orchestration.workflow_manager import WorkflowManager
from hwautomation.orchestration.server_provisioning import ServerProvisioningWorkflow
from hwautomation.utils.config import load_config
from hwautomation.database.helper import DbHelper
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    parser = argparse.ArgumentParser(description="Enhanced server commissioning with database integration")
    parser.add_argument('--server-id', required=True, help='Server ID in MaaS')
    parser.add_argument('--device-type', required=True, help='Device type (e.g., s2.c2.small)')
    parser.add_argument('--ipmi-ip', required=True, help='Target IPMI IP address')
    parser.add_argument('--rack-location', help='Physical rack location')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    try:
        config = load_config()
        print(f"✅ Configuration loaded successfully")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        sys.exit(1)
    
    # Initialize workflow manager
    try:
        workflow_manager = WorkflowManager(config)
        print(f"✅ Workflow manager initialized")
    except Exception as e:
        print(f"❌ Failed to initialize workflow manager: {e}")
        sys.exit(1)
    
    # Check database connectivity
    try:
        db_helper = workflow_manager.db_helper
        print(f"✅ Database connection established: {db_helper.db_path}")
        
        # Show current database state for this server
        if db_helper.checkifserveridexists(args.server_id)[0]:
            print(f"ℹ️  Server {args.server_id} already exists in database")
        else:
            print(f"ℹ️  Server {args.server_id} will be added to database")
            
    except Exception as e:
        print(f"❌ Database connectivity check failed: {e}")
        sys.exit(1)
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - Showing planned workflow steps:")
        print("=" * 60)
        show_workflow_plan(args)
        return
    
    # Create and execute provisioning workflow
    print(f"\n🚀 Starting enhanced server provisioning workflow...")
    print("=" * 60)
    
    try:
        provisioning = ServerProvisioningWorkflow(workflow_manager)
        
        # Set up progress callback
        def progress_callback(step_name, status, details=None):
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {step_name}: {status}")
            if details:
                for key, value in details.items():
                    print(f"    {key}: {value}")
        
        # Execute provisioning
        result = provisioning.provision_server(
            server_id=args.server_id,
            device_type=args.device_type,
            target_ipmi_ip=args.ipmi_ip,
            rack_location=args.rack_location,
            progress_callback=progress_callback
        )
        
        print("\n" + "=" * 60)
        if result['success']:
            print("✅ Server provisioning completed successfully!")
            
            # Show database final state
            show_database_state(db_helper, args.server_id)
            
            # Show workflow results
            context = result.get('context', {})
            print(f"\n📊 Provisioning Results:")
            print(f"  Server ID: {context.get('server_id')}")
            print(f"  Device Type: {context.get('device_type')}")
            print(f"  Server IP: {context.get('server_ip')}")
            print(f"  SSH Verified: {context.get('ssh_connectivity_verified', 'Unknown')}")
            
            # Show hardware discovery results if available
            if 'hardware_discovery_result' in context:
                hardware_info = context['hardware_discovery_result']
                print(f"\n🔍 Hardware Discovery Results:")
                if hardware_info.get('system_info'):
                    sys_info = hardware_info['system_info']
                    print(f"  Manufacturer: {sys_info.get('manufacturer', 'Unknown')}")
                    print(f"  Product: {sys_info.get('product_name', 'Unknown')}")
                    print(f"  Serial: {sys_info.get('serial_number', 'Unknown')}")
                
                if hardware_info.get('ipmi_info'):
                    ipmi_info = hardware_info['ipmi_info']
                    print(f"  IPMI IP: {ipmi_info.get('ip_address', 'Not found')}")
                    print(f"  IPMI Enabled: {ipmi_info.get('enabled', False)}")
                
                vendor_info = hardware_info.get('vendor_info', {})
                if vendor_info:
                    print(f"  Vendor Info: {list(vendor_info.keys())}")
            
        else:
            print("❌ Server provisioning failed!")
            print(f"Error details: {result}")
            
            # Show database state even on failure
            show_database_state(db_helper, args.server_id)
            
    except KeyboardInterrupt:
        print("\n⚠️  Provisioning interrupted by user")
        show_database_state(db_helper, args.server_id)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error during provisioning: {e}")
        show_database_state(db_helper, args.server_id)
        sys.exit(1)

def show_workflow_plan(args):
    """Show the planned workflow steps"""
    steps = [
        ("1. Commission Server", f"Commission {args.server_id} in MaaS and create database entry"),
        ("2. Get Server IP", f"Retrieve IP address and test SSH connectivity"),
        ("3. Hardware Discovery", f"Discover hardware info including IPMI, store in database"),
        ("4. Pull BIOS Config", f"Extract current BIOS configuration via SSH"),  
        ("5. Modify BIOS Config", f"Apply device type specific BIOS settings"),
        ("6. Push BIOS Config", f"Upload modified BIOS configuration"),
        ("7. Configure IPMI", f"Set up IPMI with target IP {args.ipmi_ip}"),
        ("8. Finalize Server", f"Tag server and update database with completion status")
    ]
    
    for step_name, step_desc in steps:
        print(f"  {step_name}: {step_desc}")
    
    print(f"\nDatabase Integration:")
    print(f"  • Server entry created/updated throughout process")
    print(f"  • SSH connectivity validation and tracking")
    print(f"  • Hardware discovery results stored")
    print(f"  • IPMI configuration status tracked")
    print(f"  • Final completion status recorded")

def show_database_state(db_helper: DbHelper, server_id: str):
    """Show current database state for the server"""
    print(f"\n💾 Database State for {server_id}:")
    print("-" * 40)
    
    try:
        # Query current state (using the old interface for compatibility)
        cursor = db_helper.sql_db_worker
        cursor.execute(f"SELECT * FROM {db_helper.tablename} WHERE server_id = ?", (server_id,))
        result = cursor.fetchone()
        
        if result:
            # Get column names
            cursor.execute(f"PRAGMA table_info({db_helper.tablename})")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Show key information
            for i, column in enumerate(columns):
                if i < len(result) and result[i] is not None:
                    print(f"  {column}: {result[i]}")
        else:
            print(f"  No database entry found for server {server_id}")
            
    except Exception as e:
        print(f"  Error querying database: {e}")

if __name__ == "__main__":
    main()
