"""
Configuration management for hardware automation.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from file or environment variables.

    Args:
        config_path: Path to configuration file (JSON or YAML)

    Returns:
        Configuration dictionary
    """
    config = {}

    # Try to load from file if provided
    if config_path and os.path.exists(config_path):
        config = load_config_file(config_path)

    # Override with environment variables
    env_config = load_config_from_env()
    config.update(env_config)

    # Set defaults if not provided
    config = apply_default_config(config)

    return config


def load_config_file(config_path: str) -> Dict[str, Any]:
    """Load configuration from JSON or YAML file"""
    path = Path(config_path)

    try:
        with open(path, "r") as f:
            if path.suffix.lower() in [".yaml", ".yml"]:
                return yaml.safe_load(f) or {}
            elif path.suffix.lower() == ".json":
                return json.load(f) or {}
            else:
                print(f"Unsupported config file format: {path.suffix}")
                return {}

    except Exception as e:
        print(f"Error loading config file {config_path}: {e}")
        return {}


def load_config_from_env() -> Dict[str, Any]:
    """Load configuration from environment variables"""
    config = {}

    # MAAS configuration
    if os.getenv("MAAS_HOST"):
        config.setdefault("maas", {})["host"] = os.getenv("MAAS_HOST")
    if os.getenv("MAAS_CONSUMER_KEY"):
        config.setdefault("maas", {})["consumer_key"] = os.getenv("MAAS_CONSUMER_KEY")
    if os.getenv("MAAS_CONSUMER_TOKEN"):
        config.setdefault("maas", {})["consumer_token"] = os.getenv(
            "MAAS_CONSUMER_TOKEN"
        )
    if os.getenv("MAAS_SECRET"):
        config.setdefault("maas", {})["secret"] = os.getenv("MAAS_SECRET")

    # Database configuration
    if os.getenv("DB_PATH"):
        config.setdefault("database", {})["path"] = os.getenv("DB_PATH")
    if os.getenv("DB_AUTO_MIGRATE"):
        config.setdefault("database", {})["auto_migrate"] = (
            os.getenv("DB_AUTO_MIGRATE").lower() == "true"
        )

    # IPMI configuration
    if os.getenv("IPMI_USERNAME"):
        config.setdefault("ipmi", {})["username"] = os.getenv("IPMI_USERNAME")
    if os.getenv("IPMI_PASSWORD"):
        config.setdefault("ipmi", {})["password"] = os.getenv("IPMI_PASSWORD")

    # SSH configuration
    if os.getenv("SSH_USERNAME"):
        config.setdefault("ssh", {})["username"] = os.getenv("SSH_USERNAME")
    if os.getenv("SSH_TIMEOUT"):
        config.setdefault("ssh", {})["timeout"] = int(os.getenv("SSH_TIMEOUT"))

    return config


def apply_default_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply default configuration values"""
    defaults = {
        "maas": {
            "host": "http://192.168.100.253:5240/MAAS",
            "consumer_key": "QphVRmRubLwrXFefVL",
            "consumer_token": "rHmtVanv5EyAdFTjTa",
            "secret": "HVx688TMxLtw3WgQPh4pmTCAaxajD2sP",
        },
        "database": {
            "path": "hw_automation.db",
            "auto_migrate": True,
            "table_name": "servers",
        },
        "ipmi": {"username": "ADMIN", "timeout": 30},
        "ssh": {"username": "ubuntu", "timeout": 30},
        "network": {"ping_timeout": 5, "port_timeout": 5},
        "hardware": {"sum_path": "./sum"},
    }

    # Merge defaults with provided config
    for key, default_section in defaults.items():
        if key not in config:
            config[key] = {}
        for subkey, default_value in default_section.items():
            if subkey not in config[key]:
                config[key][subkey] = default_value

    return config


def save_config(config: Dict[str, Any], config_path: str):
    """Save configuration to file"""
    path = Path(config_path)

    try:
        with open(path, "w") as f:
            if path.suffix.lower() in [".yaml", ".yml"]:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            elif path.suffix.lower() == ".json":
                json.dump(config, f, indent=2)
            else:
                # Default to JSON
                json.dump(config, f, indent=2)

        print(f"Configuration saved to {config_path}")

    except Exception as e:
        print(f"Error saving config to {config_path}: {e}")


def create_sample_config(config_path: str = "config.yaml"):
    """Create a sample configuration file"""
    sample_config = {
        "maas": {
            "host": "http://your-maas-server:5240/MAAS",
            "consumer_key": "your_consumer_key",
            "consumer_token": "your_consumer_token",
            "secret": "your_secret",
        },
        "database": {
            "path": "hw_automation.db",
            "auto_migrate": True,
            "table_name": "servers",
        },
        "ipmi": {"username": "ADMIN", "password": "your_ipmi_password", "timeout": 30},
        "ssh": {"username": "ubuntu", "timeout": 30},
        "hardware": {"sum_path": "./sum"},
    }

    save_config(sample_config, config_path)
    print(f"Sample configuration created at {config_path}")
    print("Please edit the file with your actual credentials and settings.")
