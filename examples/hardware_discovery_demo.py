#!/usr/bin/env python3
"""
Hardware Discovery Demo

This script demonstrates the hardware discovery capabilities of the HWAutomation system.
It shows how to discover hardware information without needing SSH access to remote systems.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from hwautomation.hardware.discovery import (
    HardwareDiscoveryManager,
    SystemInfo,
    IPMIInfo,
    NetworkInterface,
    HardwareDiscovery
)
from hwautomation.utils.network import SSHManager
from hwautomation.utils.config import load_config

def demo_local_hardware_info():
    """Demonstrate parsing system information from local commands"""
    print("=== Hardware Discovery Demo ===\n")
    
    # Create mock dmidecode output
    mock_dmidecode_system = """
# dmidecode 3.5
Getting SMBIOS data from sysfs.
SMBIOS 2.8 present.

Handle 0x0100, DMI type 1, 27 bytes
System Information
	Manufacturer: QEMU
	Product Name: Standard PC (i440FX + PIIX, 1996)
	Version: pc-i440fx-9.2
	Serial Number: Not Specified
	UUID: aa2801b2-3c76-4563-b55a-a8211a1a10d5
	Wake-up Type: Power Switch
	SKU Number: Not Specified
	Family: Not Specified
    """
    
    mock_ip_addr = """
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever

2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether bc:24:11:95:1e:40 brd ff:ff:ff:ff:ff:ff
    altname enp0s18
    inet 192.168.100.6/24 brd 192.168.100.255 scope global eth0
       valid_lft forever preferred_lft forever
    """
    
    mock_ipmi_lan = """
Set in Progress         : Set Complete
Auth Type Support       : NONE MD2 MD5 PASSWORD 
Auth Type Enable        : Callback :
                        : User     :
                        : Operator :
                        : Admin    :
                        : OEM      :
IP Address Source       : Static Address
IP Address              : 192.168.100.101
Subnet Mask             : 255.255.255.0
MAC Address             : bc:24:11:95:1e:41
SNMP Community String   : public
IP Header               : TTL=0x40 Flags=0x40
BMC ARP Control         : ARP Responses Enabled, Gratuitous ARP Disabled
Default Gateway IP      : 192.168.100.1
Default Gateway MAC     : 00:00:00:00:00:00
Backup Gateway IP       : 0.0.0.0
Backup Gateway MAC      : 00:00:00:00:00:00
802.1q VLAN ID          : Disabled
802.1q VLAN Priority    : 0
RMCP+ Cipher Suites     : 1,2,3,6,7,8,9,11,12
Cipher Suite Priv Max   : aaaaXXaaaXXaaXX
                        :     X=Cipher Suite Unused
                        :     c=CALLBACK
                        :     u=USER
                        :     o=OPERATOR
                        :     a=ADMIN
                        :     O=OEM
Bad Password Threshold  : Not Available
    """
    
    # Create a discovery manager instance
    ssh_config = {'timeout': 60}
    ssh_manager = SSHManager(ssh_config)
    discovery_manager = HardwareDiscoveryManager(ssh_manager)
    
    # Demonstrate parsing functions
    print("1. Parsing System Information:")
    system_info = discovery_manager._parse_dmidecode_system(mock_dmidecode_system)
    print(f"   Manufacturer: {system_info.manufacturer}")
    print(f"   Product: {system_info.product_name}")
    print(f"   Serial Number: {system_info.serial_number}")
    print(f"   UUID: {system_info.uuid}")
    
    print("\n2. Parsing Network Interfaces:")
    interfaces = discovery_manager._parse_ip_addr(mock_ip_addr)
    for interface in interfaces:
        print(f"   Interface: {interface.name}")
        print(f"     MAC: {interface.mac_address}")
        print(f"     State: {interface.state}")
        if interface.ip_address:
            print(f"     IP: {interface.ip_address}")
            print(f"     Netmask: {interface.netmask}")
        print()
    
    print("3. Parsing IPMI Configuration:")
    ipmi_info = discovery_manager._parse_ipmi_lan_config(mock_ipmi_lan)
    print(f"   IPMI IP: {ipmi_info.ip_address}")
    print(f"   IPMI MAC: {ipmi_info.mac_address}")
    print(f"   IPMI Gateway: {ipmi_info.gateway}")
    print(f"   IPMI Netmask: {ipmi_info.netmask}")
    print(f"   IPMI Channel: {ipmi_info.channel}")
    
    print("\n4. Creating Mock Hardware Discovery Result:")
    hardware_discovery = HardwareDiscovery(
        hostname="demo-server",
        system_info=system_info,
        ipmi_info=ipmi_info,
        network_interfaces=interfaces,
        discovered_at="2025-07-31T15:21:00.000000",
        discovery_errors=[]
    )
    
    print(f"✅ Discovery completed for {hardware_discovery.hostname}")
    print(f"   System: {hardware_discovery.system_info.manufacturer} {hardware_discovery.system_info.product_name}")
    print(f"   IPMI: {hardware_discovery.ipmi_info.ip_address}")
    print(f"   Interfaces: {len(hardware_discovery.network_interfaces)} found")
    
    # Show the JSON representation
    print("\n5. JSON Representation:")
    import json
    print(json.dumps(hardware_discovery.to_dict(), indent=2))

def demo_network_utilities():
    """Demonstrate network utility functions"""
    print("\n=== Network Utilities Demo ===\n")
    
    from hwautomation.utils.network import test_port_connectivity, resolve_hostname
    
    # Test port connectivity
    print("1. Testing Port Connectivity:")
    print(f"   Google DNS (8.8.8.8:53): {'✅ Open' if test_port_connectivity('8.8.8.8', 53, 2) else '❌ Closed'}")
    print(f"   Local SSH (127.0.0.1:22): {'✅ Open' if test_port_connectivity('127.0.0.1', 22, 2) else '❌ Closed'}")
    print(f"   Invalid port (127.0.0.1:9999): {'✅ Open' if test_port_connectivity('127.0.0.1', 9999, 2) else '❌ Closed'}")
    
    # Test hostname resolution
    print("\n2. Hostname Resolution:")
    google_ip = resolve_hostname('google.com')
    localhost_ip = resolve_hostname('localhost')
    invalid_ip = resolve_hostname('invalid-hostname-that-does-not-exist.com')
    
    print(f"   google.com -> {google_ip if google_ip else 'Failed to resolve'}")
    print(f"   localhost -> {localhost_ip if localhost_ip else 'Failed to resolve'}")
    print(f"   invalid-hostname -> {invalid_ip if invalid_ip else 'Failed to resolve'}")

def demo_configuration_integration():
    """Demonstrate configuration integration"""
    print("\n=== Configuration Integration Demo ===\n")
    
    try:
        # Load configuration
        config_path = project_root / 'config.yaml'
        config = load_config(str(config_path))
        
        print("1. Configuration loaded successfully:")
        print(f"   Config sections: {list(config.keys())}")
        
        if 'ssh' in config:
            print(f"   SSH config: {config['ssh']}")
        
        if 'maas' in config:
            maas_config = config['maas']
            print(f"   MaaS host: {maas_config.get('host', 'Not configured')}")
        
        # Show how hardware discovery would be integrated
        print("\n2. Hardware Discovery Integration:")
        ssh_config = config.get('ssh', {})
        ssh_manager = SSHManager(ssh_config)
        discovery_manager = HardwareDiscoveryManager(ssh_manager)
        
        print("   ✅ SSH Manager initialized")
        print("   ✅ Hardware Discovery Manager initialized")
        print("   ✅ Ready for remote hardware discovery")
        
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")

def demo_use_cases():
    """Show practical use cases"""
    print("\n=== Practical Use Cases ===\n")
    
    use_cases = [
        {
            "title": "Server Commissioning Workflow",
            "description": "Discover IPMI address during MaaS commissioning",
            "steps": [
                "1. MaaS commissions server and gets IP address",
                "2. SSH to server using ubuntu user with key-based auth",
                "3. Run hardware discovery to find IPMI address",
                "4. Configure IPMI with discovered address",
                "5. Update server tags in MaaS with hardware info"
            ]
        },
        {
            "title": "Network Infrastructure Audit",
            "description": "Scan entire subnet for hardware inventory",
            "steps": [
                "1. Scan network range (e.g., 192.168.1.0/24)",
                "2. SSH to each accessible host",
                "3. Gather system information and IPMI config",
                "4. Build comprehensive hardware inventory",
                "5. Export results to database or CSV"
            ]
        },
        {
            "title": "BIOS Configuration Management", 
            "description": "Collect system info for BIOS template selection",
            "steps": [
                "1. Discover system manufacturer and model",
                "2. Select appropriate BIOS configuration template",
                "3. Apply settings based on hardware capabilities",
                "4. Verify configuration via system information",
                "5. Log changes and maintain audit trail"
            ]
        }
    ]
    
    for i, use_case in enumerate(use_cases, 1):
        print(f"{i}. {use_case['title']}")
        print(f"   {use_case['description']}")
        for step in use_case['steps']:
            print(f"   {step}")
        print()

if __name__ == '__main__':
    print("HWAutomation Hardware Discovery System")
    print("=" * 50)
    
    demo_local_hardware_info()
    demo_network_utilities()
    demo_configuration_integration()
    demo_use_cases()
    
    print("\n" + "=" * 50)
    print("Demo completed! The hardware discovery system is ready to use.")
    print("\nNext steps:")
    print("• Use the CLI tool: ./scripts/hardware_discovery.py discover <host>")
    print("• Access the GUI: http://127.0.0.1:5000/hardware")
    print("• Use the API: POST /api/hardware/discover")
    print("• Integrate with orchestration workflows")
