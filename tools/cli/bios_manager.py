#!/usr/bin/env python3
"""
BIOS Configuration Management Tool

Command-line interface for managing BIOS configurations by device type.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import xml.etree.ElementTree as ET

from hwautomation.hardware.bios_config import BiosConfigManager


def setup_logging(verbose: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def cmd_list_types(args):
    """List available device types."""
    manager = BiosConfigManager(args.config_dir)
    device_types = manager.get_device_types()

    print("Available Device Types:")
    print("=" * 30)
    for device_type in device_types:
        config = manager.get_device_config(device_type)
        if config:
            print(f"{device_type:15} - {config.get('description', 'No description')}")
            motherboards = config.get("motherboards", [])
            if motherboards:
                print(f"{'':15}   Motherboards: {', '.join(motherboards)}")
        print()


def cmd_list_templates(args):
    """List available XML templates."""
    manager = BiosConfigManager(args.config_dir)
    templates = manager.list_templates()

    print("Available XML Templates:")
    print("=" * 30)
    for template in templates:
        print(f"  {template}")

    if not templates:
        print("  No XML templates found.")
        print(
            "  Use 'generate' command to create templates from device configurations."
        )


def cmd_show_config(args):
    """Show configuration for a device type."""
    manager = BiosConfigManager(args.config_dir)
    config = manager.get_device_config(args.device_type)

    if not config:
        print(f"Device type '{args.device_type}' not found.")
        return 1

    print(f"Configuration for {args.device_type}:")
    print("=" * 40)
    print(f"Description: {config.get('description', 'N/A')}")
    print(f"Motherboards: {', '.join(config.get('motherboards', []))}")

    print("\nCPU Configuration:")
    for key, value in config.get("cpu_configs", {}).items():
        print(f"  {key}: {value}")

    print("\nMemory Configuration:")
    for key, value in config.get("memory_configs", {}).items():
        print(f"  {key}: {value}")

    print("\nBoot Configuration:")
    for key, value in config.get("boot_configs", {}).items():
        print(f"  {key}: {value}")


def cmd_generate_xml(args):
    """Generate XML configuration for a device type."""
    manager = BiosConfigManager(args.config_dir)
    xml_config = manager.generate_xml_config(args.device_type, args.motherboard)

    if not xml_config:
        print(f"Could not generate XML for device type '{args.device_type}'")
        return 1

    if args.output:
        with open(args.output, "w") as f:
            f.write(xml_config)
        print(f"XML configuration saved to {args.output}")
    else:
        print("Generated XML Configuration:")
        print("=" * 40)
        print(xml_config)


def cmd_save_template(args):
    """Save XML template for a device type."""
    manager = BiosConfigManager(args.config_dir)

    if args.file:
        with open(args.file, "r") as f:
            xml_content = f.read()
    else:
        print("Enter XML content (press Ctrl+D when finished):")
        xml_content = sys.stdin.read()

    try:
        manager.save_xml_template(args.device_type, xml_content)
        print(f"XML template saved for device type '{args.device_type}'")
    except ValueError as e:
        print(f"Error: {e}")
        return 1


def cmd_apply_config(args):
    """Apply BIOS configuration to target system using smart pull-edit-push approach."""
    manager = BiosConfigManager(args.config_dir)

    try:
        result = manager.apply_bios_config_smart(
            args.device_type, args.target_ip, args.username, args.password, args.dry_run
        )

        print(f"BIOS Configuration Application Results:")
        print("=" * 50)
        print(f"Target IP: {result['target_ip']}")
        print(f"Device Type: {result['device_type']}")
        print(f"Success: {result['success']}")
        print(f"Dry Run: {result['dry_run']}")

        if result["success"]:
            if result.get("message"):
                print(f"Message: {result['message']}")

            if result["changes_made"]:
                print(f"\nChanges {'that would be' if args.dry_run else ''} made:")
                for change in result["changes_made"]:
                    print(f"  - {change}")
            else:
                print("\nNo changes needed - configuration already matches template")
        else:
            print(f"Error: {result.get('error', 'Unknown error')}")
            if result["validation_errors"]:
                print("\nValidation Errors:")
                for error in result["validation_errors"]:
                    print(f"  - {error}")
            return 1

        if result.get("backup_path"):
            print(f"\nBackup created: {result['backup_path']}")

    except Exception as e:
        print(f"Error applying configuration: {e}")
        return 1


def cmd_pull_config(args):
    """Pull current BIOS configuration from target system."""
    manager = BiosConfigManager(args.config_dir)

    try:
        current_config = manager.pull_current_bios_config(
            args.target_ip, args.username, args.password
        )

        if current_config is not None:
            # Pretty print the XML
            manager._indent_xml(current_config)
            config_str = ET.tostring(current_config, encoding="unicode")

            if args.output:
                with open(args.output, "w") as f:
                    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                    f.write(config_str)
                print(f"Current BIOS configuration saved to {args.output}")
            else:
                print("Current BIOS Configuration:")
                print("=" * 40)
                print('<?xml version="1.0" encoding="UTF-8"?>')
                print(config_str)
        else:
            print(f"Failed to retrieve BIOS configuration from {args.target_ip}")
            return 1

    except Exception as e:
        print(f"Error pulling configuration: {e}")
        return 1


def main():
    """Main command-line interface."""
    parser = argparse.ArgumentParser(
        description="BIOS Configuration Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list-types                    # List all device types
  %(prog)s show-config s2_c2_small       # Show config for device type
  %(prog)s generate-xml s2_c2_small      # Generate XML for device type
  %(prog)s apply-config s2_c2_small 192.168.1.100  # Apply config to system
        """,
    )

    parser.add_argument("--config-dir", help="Configuration directory path")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List device types command
    list_types_parser = subparsers.add_parser(
        "list-types", help="List available device types"
    )

    # List templates command
    list_templates_parser = subparsers.add_parser(
        "list-templates", help="List available XML templates"
    )

    # Show config command
    show_parser = subparsers.add_parser(
        "show-config", help="Show configuration for device type"
    )
    show_parser.add_argument("device_type", help="Device type name")

    # Generate XML command
    generate_parser = subparsers.add_parser(
        "generate-xml", help="Generate XML configuration"
    )
    generate_parser.add_argument("device_type", help="Device type name")
    generate_parser.add_argument("--motherboard", help="Specific motherboard model")
    generate_parser.add_argument("--output", "-o", help="Output file path")

    # Save template command
    save_parser = subparsers.add_parser(
        "save-template", help="Save XML template for device type"
    )
    save_parser.add_argument("device_type", help="Device type name")
    save_parser.add_argument("--file", "-f", help="XML file to read from")

    # Pull current config command
    pull_parser = subparsers.add_parser(
        "pull-config", help="Pull current BIOS configuration from target system"
    )
    pull_parser.add_argument("target_ip", help="Target system IP address")
    pull_parser.add_argument("--username", "-u", default="ADMIN", help="BMC username")
    pull_parser.add_argument("--password", "-p", help="BMC password")
    pull_parser.add_argument("--output", "-o", help="Output file path")

    # Apply config command
    apply_parser = subparsers.add_parser(
        "apply-config",
        help="Apply BIOS configuration to target system using smart pull-edit-push",
    )
    apply_parser.add_argument("device_type", help="Device type name")
    apply_parser.add_argument("target_ip", help="Target system IP address")
    apply_parser.add_argument("--username", "-u", default="ADMIN", help="BMC username")
    apply_parser.add_argument("--password", "-p", help="BMC password")
    apply_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without applying",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    setup_logging(args.verbose)

    # Command dispatch
    commands = {
        "list-types": cmd_list_types,
        "list-templates": cmd_list_templates,
        "show-config": cmd_show_config,
        "generate-xml": cmd_generate_xml,
        "save-template": cmd_save_template,
        "pull-config": cmd_pull_config,
        "apply-config": cmd_apply_config,
    }

    command_func = commands.get(args.command)
    if command_func:
        return command_func(args) or 0
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
