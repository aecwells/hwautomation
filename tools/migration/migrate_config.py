#!/usr/bin/env python3
"""
Configuration Migration Tool

Migrates from YAML-based configuration to environment-based configuration.
This tool helps transition existing deployments to the new configuration system.
"""

import sys
import yaml
import os
from pathlib import Path
from typing import Dict, Any, List


def migrate_yaml_to_env(yaml_file: str, env_file: str = '.env') -> bool:
    """
    Migrate YAML configuration to .env file format.
    
    Args:
        yaml_file: Path to existing config.yaml
        env_file: Path to output .env file
        
    Returns:
        True if migration successful, False otherwise
    """
    
    if not os.path.exists(yaml_file):
        print(f"❌ YAML config file not found: {yaml_file}")
        return False
    
    try:
        # Load YAML configuration
        with open(yaml_file, 'r') as f:
            yaml_config = yaml.safe_load(f) or {}
        
        print(f"📖 Loaded configuration from {yaml_file}")
        
        # Convert to environment variables
        env_vars = convert_yaml_to_env_vars(yaml_config)
        
        # Read existing .env file if it exists
        existing_env = {}
        if os.path.exists(env_file):
            print(f"📄 Found existing {env_file}, will merge configurations")
            existing_env = read_env_file(env_file)
        
        # Merge configurations (YAML values take precedence for conflicts)
        merged_env = {**existing_env, **env_vars}
        
        # Write new .env file
        write_env_file(env_file, merged_env)
        
        print(f"✅ Configuration migrated to {env_file}")
        print(f"📊 Migrated {len(env_vars)} configuration values")
        
        # Create backup of original YAML
        backup_file = f"{yaml_file}.backup"
        if not os.path.exists(backup_file):
            import shutil
            shutil.copy2(yaml_file, backup_file)
            print(f"💾 Created backup: {backup_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False


def convert_yaml_to_env_vars(config: Dict[str, Any], prefix: str = '') -> Dict[str, str]:
    """
    Convert nested YAML configuration to flat environment variables.
    
    Args:
        config: Configuration dictionary
        prefix: Prefix for environment variable names
        
    Returns:
        Dictionary of environment variable name/value pairs
    """
    env_vars = {}
    
    for key, value in config.items():
        env_key = f"{prefix}{key}".upper()
        
        if isinstance(value, dict):
            # Recursively handle nested dictionaries
            nested_vars = convert_yaml_to_env_vars(value, f"{env_key}_")
            env_vars.update(nested_vars)
        elif isinstance(value, (list, tuple)):
            # Convert lists to comma-separated strings
            env_vars[env_key] = ','.join(str(item) for item in value)
        elif isinstance(value, bool):
            # Convert booleans to string representation
            env_vars[env_key] = 'true' if value else 'false'
        elif value is not None:
            # Convert everything else to string
            env_vars[env_key] = str(value)
    
    return env_vars


def read_env_file(env_file: str) -> Dict[str, str]:
    """
    Read existing .env file into dictionary.
    
    Args:
        env_file: Path to .env file
        
    Returns:
        Dictionary of environment variables
    """
    env_vars = {}
    
    try:
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse key=value pairs
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    
    except Exception as e:
        print(f"Warning: Could not read {env_file}: {e}")
    
    return env_vars


def write_env_file(env_file: str, env_vars: Dict[str, str]) -> None:
    """
    Write environment variables to .env file.
    
    Args:
        env_file: Path to output .env file
        env_vars: Dictionary of environment variables
    """
    
    # Group variables by section for better organization
    sections = {
        'PROJECT': ['PROJECT_NAME', 'DEBUG', 'TESTING'],
        'DATABASE': [k for k in env_vars.keys() if k.startswith('DATABASE_')],
        'MAAS': [k for k in env_vars.keys() if k.startswith('MAAS_')],
        'IPMI': [k for k in env_vars.keys() if k.startswith('IPMI_')],
        'SSH': [k for k in env_vars.keys() if k.startswith('SSH_')],
        'NETWORK': [k for k in env_vars.keys() if k.startswith('NETWORK_')],
        'REDFISH': [k for k in env_vars.keys() if k.startswith('REDFISH_')],
        'LOGGING': [k for k in env_vars.keys() if k.startswith('LOG_')],
        'DEVELOPMENT': [k for k in env_vars.keys() if k.startswith('DEVELOPMENT_')],
    }
    
    with open(env_file, 'w') as f:
        f.write("# HWAutomation Configuration\n")
        f.write("# Migrated from config.yaml\n\n")
        
        # Write organized sections
        for section_name, section_keys in sections.items():
            if section_keys:
                f.write(f"# {section_name} Configuration\n")
                
                for key in section_keys:
                    if key in env_vars:
                        value = env_vars[key]
                        f.write(f"{key}={value}\n")
                
                f.write("\n")
        
        # Write any remaining variables
        written_keys = set()
        for section_keys in sections.values():
            written_keys.update(section_keys)
        
        remaining_keys = set(env_vars.keys()) - written_keys
        if remaining_keys:
            f.write("# Additional Configuration\n")
            for key in sorted(remaining_keys):
                f.write(f"{key}={env_vars[key]}\n")


def generate_migration_summary(yaml_file: str, env_file: str) -> None:
    """Generate a summary of the migration."""
    
    print("\n" + "="*60)
    print("🎯 CONFIGURATION MIGRATION SUMMARY")
    print("="*60)
    
    print(f"\n📁 Files:")
    print(f"  • Source: {yaml_file}")
    print(f"  • Target: {env_file}")
    print(f"  • Backup: {yaml_file}.backup")
    
    print(f"\n🔄 Next Steps:")
    print(f"  1. Review the generated {env_file} file")
    print(f"  2. Update your application to use environment variables")
    print(f"  3. Test the new configuration system")
    print(f"  4. Remove the old {yaml_file} when satisfied")
    
    print(f"\n📖 Usage:")
    print(f"  • Load with: python -c \"from hwautomation.utils.env_config import load_config; print(load_config())\"")
    print(f"  • Docker: The container will automatically load {env_file}")
    print(f"  • Local: Set environment variables or use python-dotenv")
    
    print(f"\n⚠️  Important:")
    print(f"  • The old YAML system is deprecated")
    print(f"  • Update your code to use the new env_config module")
    print(f"  • Environment variables take precedence over .env file")
    
    print("="*60)


def main():
    """Main migration function."""
    
    if len(sys.argv) != 2:
        print("Usage: python migrate_config.py <config.yaml>")
        print("\nExample:")
        print("  python migrate_config.py config.yaml")
        sys.exit(1)
    
    yaml_file = sys.argv[1]
    env_file = '.env'
    
    print("🚀 Starting configuration migration...")
    print(f"   YAML Config: {yaml_file}")
    print(f"   ENV Output:  {env_file}")
    
    success = migrate_yaml_to_env(yaml_file, env_file)
    
    if success:
        generate_migration_summary(yaml_file, env_file)
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
