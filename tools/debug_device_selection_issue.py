#!/usr/bin/env python3
"""
Debug MaaS Device Selection Issue

Investigate why device selection shows 0 available machines when 5 are expected.
"""

import sys
import os
from pathlib import Path

# Add the source directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from hwautomation.utils.config import load_config
from hwautomation.maas.client import create_maas_client
from hwautomation.orchestration.device_selection import DeviceSelectionService

def debug_maas_device_selection():
    """Debug MaaS connection and device filtering"""
    print("=" * 60)
    print("Debug: MaaS Device Selection Issue")
    print("=" * 60)
    
    try:
        # Load configuration
        config_path = Path(__file__).parent.parent / 'config.yaml'
        print(f"Loading config from: {config_path}")
        
        if not config_path.exists():
            print("❌ config.yaml not found!")
            return False
            
        config = load_config(str(config_path))
        maas_config = config.get('maas', {})
        
        print(f"MaaS Host: {maas_config.get('host', 'Not configured')}")
        print(f"Consumer Key: {maas_config.get('consumer_key', 'Not configured')}")
        
        # Test MaaS client directly
        print("\n1. Testing Raw MaaS Connection")
        print("-" * 40)
        
        maas_client = create_maas_client(maas_config)
        
        # Test basic connection
        print("Calling maas_client.get_machines()...")
        machines = maas_client.get_machines()
        print(f"✅ Raw machines returned: {len(machines) if machines else 0}")
        
        if not machines:
            print("❌ No machines returned from MaaS - check connection/credentials")
            return False
        
        # Analyze machine statuses
        print("\n2. Analyzing Machine Statuses")
        print("-" * 40)
        
        status_counts = {}
        for machine in machines:
            status = machine.get('status_name', 'Unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        print("Machine status breakdown:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
        
        # Show all machines with details
        print("\nAll machines in MaaS:")
        for i, machine in enumerate(machines, 1):
            hostname = machine.get('hostname', machine.get('fqdn', 'Unknown'))
            status = machine.get('status_name', 'Unknown')
            
            # Handle owner field safely
            owner_info = machine.get('owner')
            if isinstance(owner_info, dict):
                owner = owner_info.get('username', 'None')
            elif isinstance(owner_info, str):
                owner = owner_info
            else:
                owner = 'None'
                
            power_type = machine.get('power_type', 'Unknown')
            print(f"  {i}. {hostname} ({machine.get('system_id', 'Unknown')})")
            print(f"     Status: {status}, Owner: {owner}, Power: {power_type}")
        
        # Test get_available_machines method
        print("\n3. Testing get_available_machines()")
        print("-" * 40)
        
        available = maas_client.get_available_machines()
        print(f"Available machines: {len(available) if available else 0}")
        
        # Check what statuses are considered "available"
        available_statuses = ['Ready', 'New', 'Failed commissioning', 'Failed testing']
        print(f"Looking for statuses: {available_statuses}")
        
        matching_machines = []
        for machine in machines:
            status = machine.get('status_name', '')
            if status in available_statuses:
                matching_machines.append(machine)
        
        print(f"Machines matching available statuses: {len(matching_machines)}")
        for machine in matching_machines:
            print(f"  • {machine.get('hostname', 'Unknown')} - {machine.get('status_name', 'Unknown')}")
        
        # Test get_machines_summary method
        print("\n4. Testing get_machines_summary()")
        print("-" * 40)
        
        try:
            summary = maas_client.get_machines_summary()
            print(f"Machine summaries created: {len(summary) if summary else 0}")
            
            if summary:
                print("First summary sample:")
                first_summary = summary[0]
                print(f"  System ID: {first_summary.get('system_id', 'Unknown')}")
                print(f"  Hostname: {first_summary.get('hostname', 'Unknown')}")
                print(f"  Status: {first_summary.get('status', 'Unknown')}")
                print(f"  CPU Count: {first_summary.get('cpu_count', 0)}")
                print(f"  Memory: {first_summary.get('memory_display', 'Unknown')}")
        except Exception as e:
            print(f"❌ Error in get_machines_summary(): {e}")
            import traceback
            traceback.print_exc()
        
        # Test DeviceSelectionService
        print("\n5. Testing DeviceSelectionService")
        print("-" * 40)
        
        try:
            device_service = DeviceSelectionService(maas_client=maas_client)
            
            # Test status summary
            status_summary = device_service.get_status_summary()
            print(f"Status Summary: {status_summary}")
            
            # Test list_available_machines
            available_machines = device_service.list_available_machines()
            print(f"Available machines via service: {len(available_machines)}")
            
            if available_machines:
                print("Available machines:")
                for machine in available_machines:
                    print(f"  • {machine.get('hostname', 'Unknown')} ({machine.get('system_id', 'Unknown')})")
                    print(f"    Status: {machine.get('status', 'Unknown')}")
            else:
                print("No available machines returned by service")
                
        except Exception as e:
            print(f"❌ Error in DeviceSelectionService: {e}")
            import traceback
            traceback.print_exc()
        
        return True
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_gui_integration():
    """Check if GUI is properly configured"""
    print("\n" + "=" * 60)
    print("Checking GUI Integration")
    print("=" * 60)
    
    try:
        gui_app_path = Path(__file__).parent.parent / 'gui' / 'app.py'
        
        if gui_app_path.exists():
            # Check if device_selection_service is initialized
            content = gui_app_path.read_text()
            
            if 'device_selection_service' in content:
                print("✅ device_selection_service found in GUI app")
            else:
                print("❌ device_selection_service not found in GUI app")
            
            if 'DeviceSelectionService' in content:
                print("✅ DeviceSelectionService imported in GUI")
            else:
                print("❌ DeviceSelectionService not imported in GUI")
                
            if '/api/devices/available' in content:
                print("✅ Device selection API endpoints found")
            else:
                print("❌ Device selection API endpoints missing")
        else:
            print("❌ GUI app.py not found")
            
    except Exception as e:
        print(f"❌ Error checking GUI integration: {e}")

if __name__ == '__main__':
    print("MaaS Device Selection Debug Tool")
    print("Investigating why 0 machines show as available when 5 are expected")
    
    success = debug_maas_device_selection()
    check_gui_integration()
    
    if success:
        print("\n🔍 Debug complete. Check the output above for issues.")
        print("\nCommon issues:")
        print("1. Machine statuses not matching expected 'available' statuses")
        print("2. Machines owned by users (not available for commissioning)")
        print("3. get_machines_summary() method encountering errors")
        print("4. DeviceSelectionService filtering logic issues") 
    else:
        print("\n❌ Debug failed - check MaaS configuration and connectivity")
