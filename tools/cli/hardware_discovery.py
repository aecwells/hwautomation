#!/usr/bin/env python3
"""
Hardware Discovery CLI Tool

A command-line tool for discovering hardware information from remote systems
including IPMI addresses, system specifications, and network interfaces.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from hwautomation.hardware.discovery import HardwareDiscoveryManager
from hwautomation.utils.config import load_config
from hwautomation.utils.network import SSHManager


def setup_logging(verbose: bool = False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def discover_hardware(
    host: str,
    username: str = "ubuntu",
    key_file: str = None,
    output_format: str = "json",
    verbose: bool = False,
):
    """
    Discover hardware information from a remote host

    Args:
        host: Target hostname or IP address
        username: SSH username
        key_file: SSH private key file path
        output_format: Output format (json, yaml, text)
        verbose: Enable verbose logging
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    try:
        # Initialize SSH manager
        ssh_config = {"timeout": 60}
        if key_file:
            ssh_config["key_file"] = key_file

        ssh_manager = SSHManager(ssh_config)
        discovery_manager = HardwareDiscoveryManager(ssh_manager)

        logger.info(f"Discovering hardware information for {host}")

        # Perform hardware discovery
        hardware_info = discovery_manager.discover_hardware(
            host=host, username=username, key_file=key_file
        )

        # Output results
        if output_format.lower() == "json":
            print(json.dumps(hardware_info.to_dict(), indent=2))
        elif output_format.lower() == "yaml":
            import yaml

            print(yaml.dump(hardware_info.to_dict(), default_flow_style=False))
        else:  # text format
            print_text_summary(hardware_info)

    except Exception as e:
        logger.error(f"Hardware discovery failed: {e}")
        sys.exit(1)


def print_text_summary(hardware_info):
    """Print a human-readable summary of hardware information"""
    print(f"\n=== Hardware Discovery Results for {hardware_info.hostname} ===")
    print(f"Discovery Time: {hardware_info.discovered_at}")

    # System Information
    print(f"\n--- System Information ---")
    sys_info = hardware_info.system_info
    if sys_info.manufacturer:
        print(f"Manufacturer: {sys_info.manufacturer}")
    if sys_info.product_name:
        print(f"Product: {sys_info.product_name}")
    if sys_info.serial_number:
        print(f"Serial Number: {sys_info.serial_number}")
    if sys_info.uuid:
        print(f"UUID: {sys_info.uuid}")
    if sys_info.bios_version:
        print(f"BIOS Version: {sys_info.bios_version}")
    if sys_info.bios_date:
        print(f"BIOS Date: {sys_info.bios_date}")
    if sys_info.cpu_model:
        print(f"CPU: {sys_info.cpu_model}")
    if sys_info.cpu_cores:
        print(f"CPU Cores: {sys_info.cpu_cores}")
    if sys_info.memory_total:
        print(f"Memory: {sys_info.memory_total}")

    # IPMI Information
    print(f"\n--- IPMI Information ---")
    ipmi_info = hardware_info.ipmi_info
    if ipmi_info.enabled:
        print(f"IPMI Enabled: Yes")
        if ipmi_info.ip_address:
            print(f"IPMI IP: {ipmi_info.ip_address}")
        if ipmi_info.mac_address:
            print(f"IPMI MAC: {ipmi_info.mac_address}")
        if ipmi_info.gateway:
            print(f"IPMI Gateway: {ipmi_info.gateway}")
        if ipmi_info.netmask:
            print(f"IPMI Netmask: {ipmi_info.netmask}")
        if ipmi_info.channel:
            print(f"IPMI Channel: {ipmi_info.channel}")
        if ipmi_info.vlan_id:
            print(f"IPMI VLAN: {ipmi_info.vlan_id}")
    else:
        print("IPMI: Not available or not configured")

    # Network Interfaces
    print(f"\n--- Network Interfaces ---")
    for interface in hardware_info.network_interfaces:
        print(f"Interface: {interface.name}")
        print(f"  MAC: {interface.mac_address}")
        print(f"  State: {interface.state}")
        if interface.ip_address:
            print(f"  IP: {interface.ip_address}")
        if interface.netmask:
            print(f"  Netmask: {interface.netmask}")
        print()

    # Discovery Errors
    if hardware_info.discovery_errors:
        print(f"\n--- Discovery Errors ---")
        for error in hardware_info.discovery_errors:
            print(f"  • {error}")


def scan_network(
    network_range: str,
    username: str = "ubuntu",
    key_file: str = None,
    verbose: bool = False,
):
    """
    Scan a network range for IPMI addresses

    Args:
        network_range: Network range to scan (e.g., '192.168.1.0/24')
        username: SSH username
        key_file: SSH private key file path
        verbose: Enable verbose logging
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    try:
        # Initialize SSH manager
        ssh_config = {"timeout": 30}  # Shorter timeout for network scanning
        if key_file:
            ssh_config["key_file"] = key_file

        ssh_manager = SSHManager(ssh_config)
        discovery_manager = HardwareDiscoveryManager(ssh_manager)

        logger.info(f"Scanning network range {network_range} for IPMI addresses")

        # Perform network scan
        ipmi_addresses = discovery_manager.discover_ipmi_from_network_scan(
            network_range
        )

        if ipmi_addresses:
            print(f"\n=== IPMI Discovery Results for {network_range} ===")
            for host, ipmi_ip in ipmi_addresses.items():
                print(f"{host} -> IPMI: {ipmi_ip}")
        else:
            print(f"No IPMI addresses found in {network_range}")

    except Exception as e:
        logger.error(f"Network scan failed: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Discover hardware information from remote systems",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover hardware information from a single host
  %(prog)s discover 192.168.1.100
  
  # Use specific SSH key and username
  %(prog)s discover 192.168.1.100 -u admin -k ~/.ssh/id_rsa
  
  # Output in YAML format with verbose logging
  %(prog)s discover 192.168.1.100 -f yaml -v
  
  # Scan network range for IPMI addresses
  %(prog)s scan 192.168.1.0/24
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Discover command
    discover_parser = subparsers.add_parser(
        "discover", help="Discover hardware from single host"
    )
    discover_parser.add_argument("host", help="Target hostname or IP address")
    discover_parser.add_argument(
        "-u", "--username", default="ubuntu", help="SSH username (default: ubuntu)"
    )
    discover_parser.add_argument("-k", "--key-file", help="SSH private key file path")
    discover_parser.add_argument(
        "-f",
        "--format",
        choices=["json", "yaml", "text"],
        default="json",
        help="Output format (default: json)",
    )
    discover_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    # Scan command
    scan_parser = subparsers.add_parser(
        "scan", help="Scan network range for IPMI addresses"
    )
    scan_parser.add_argument(
        "network", help="Network range to scan (e.g., 192.168.1.0/24)"
    )
    scan_parser.add_argument(
        "-u", "--username", default="ubuntu", help="SSH username (default: ubuntu)"
    )
    scan_parser.add_argument("-k", "--key-file", help="SSH private key file path")
    scan_parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "discover":
        discover_hardware(
            host=args.host,
            username=args.username,
            key_file=args.key_file,
            output_format=args.format,
            verbose=args.verbose,
        )
    elif args.command == "scan":
        scan_network(
            network_range=args.network,
            username=args.username,
            key_file=args.key_file,
            verbose=args.verbose,
        )


if __name__ == "__main__":
    main()
