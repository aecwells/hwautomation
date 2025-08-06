"""
Modern environment-based configuration management.

This module replaces the old YAML-based configuration with environment variables
for better containerization and deployment practices.
"""

import os
from typing import Dict, Any, Optional, Union
from pathlib import Path
import logging


class ConfigError(Exception):
    """Configuration related errors."""
    pass


class Config:
    """
    Environment-based configuration manager.
    
    Loads configuration from environment variables with sensible defaults.
    Supports type conversion and validation.
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration from environment.
        
        Args:
            env_file: Optional path to .env file to load
        """
        if env_file:
            self.load_env_file(env_file)
        
        self._config = self._load_config()
        self._validate_config()
    
    def load_env_file(self, env_file: str) -> None:
        """Load environment variables from .env file."""
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file)
        except ImportError:
            logging.warning("python-dotenv not installed. Install with: pip install python-dotenv")
        except Exception as e:
            logging.warning(f"Could not load .env file {env_file}: {e}")
    
    def _get_env(self, key: str, default: Any = None, required: bool = False, 
                 var_type: type = str) -> Any:
        """
        Get environment variable with type conversion.
        
        Args:
            key: Environment variable name
            default: Default value if not found
            required: Whether the variable is required
            var_type: Type to convert the value to
            
        Returns:
            Converted environment variable value
            
        Raises:
            ConfigError: If required variable is missing
        """
        value = os.getenv(key, default)
        
        if required and value is None:
            raise ConfigError(f"Required environment variable {key} is not set")
        
        if value is None:
            return default
            
        # Handle string values
        if isinstance(value, str):
            # Handle boolean conversion
            if var_type == bool:
                return value.lower() in ('true', '1', 'yes', 'on')
            
            # Handle numeric conversion
            if var_type in (int, float):
                try:
                    return var_type(value)
                except ValueError:
                    logging.warning(f"Could not convert {key}={value} to {var_type.__name__}, using default")
                    return default
            
            # Handle list conversion (comma-separated)
            if var_type == list:
                return [item.strip() for item in value.split(',') if item.strip()]
        
        return value
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        
        return {
            # Project Configuration
            'project': {
                'name': self._get_env('PROJECT_NAME', 'hwautomation'),
                'debug': self._get_env('DEBUG', False, var_type=bool),
                'testing': self._get_env('TESTING', False, var_type=bool),
            },
            
            # Database Configuration
            'database': {
                'path': self._get_env('DATABASE_PATH', 'hw_automation.db'),
                'table_name': self._get_env('DATABASE_TABLE_NAME', 'servers'),
                'auto_migrate': self._get_env('DATABASE_AUTO_MIGRATE', False, var_type=bool),
                'backup_before_migration': self._get_env('DATABASE_BACKUP_BEFORE_MIGRATION', True, var_type=bool),
                # PostgreSQL settings (for Docker)
                'host': self._get_env('DB_HOST', 'localhost'),
                'port': self._get_env('DB_PORT', 5432, var_type=int),
                'name': self._get_env('DB_NAME', 'hwautomation'),
                'user': self._get_env('DB_USER', 'hwautomation'),
                'password': self._get_env('DB_PASSWORD', ''),
            },
            
            # Redis Configuration
            'redis': {
                'host': self._get_env('REDIS_HOST', 'localhost'),
                'port': self._get_env('REDIS_PORT', 6379, var_type=int),
                'db': self._get_env('REDIS_DB', 0, var_type=int),
            },
            
            # MaaS Configuration
            'maas': {
                'host': self._get_env('MAAS_HOST', ''),
                'url': self._get_env('MAAS_URL', ''),
                'consumer_key': self._get_env('MAAS_CONSUMER_KEY', ''),
                'token_key': self._get_env('MAAS_TOKEN_KEY', ''),
                'token_secret': self._get_env('MAAS_TOKEN_SECRET', ''),
                'api_key': self._get_env('MAAS_API_KEY', ''),
                'admin_username': self._get_env('MAAS_ADMIN_USERNAME', 'admin'),
                'admin_password': self._get_env('MAAS_ADMIN_PASSWORD', ''),
                'verify_ssl': self._get_env('MAAS_VERIFY_SSL', False, var_type=bool),
                'timeout': self._get_env('MAAS_TIMEOUT', 30, var_type=int),
            },
            
            # IPMI Configuration
            'ipmi': {
                'username': self._get_env('IPMI_USERNAME', 'admin'),
                'password': self._get_env('IPMI_PASSWORD', ''),
                'timeout': self._get_env('IPMI_TIMEOUT', 60, var_type=int),
                'retries': self._get_env('IPMI_RETRIES', 2, var_type=int),
            },
            
            # SSH Configuration
            'ssh': {
                'username': self._get_env('SSH_USERNAME', 'ubuntu'),
                'timeout': self._get_env('SSH_TIMEOUT', 30, var_type=int),
                'retries': self._get_env('SSH_RETRIES', 3, var_type=int),
                'key_path': self._get_env('SSH_KEY_PATH'),
            },
            
            # Network Configuration
            'network': {
                'ping_timeout': self._get_env('NETWORK_PING_TIMEOUT', 5, var_type=int),
                'ping_count': self._get_env('NETWORK_PING_COUNT', 3, var_type=int),
                'ssh_timeout': self._get_env('NETWORK_SSH_TIMEOUT', 10, var_type=int),
            },
            
            # RedFish Configuration
            'redfish': {
                'timeout': self._get_env('REDFISH_TIMEOUT', 30, var_type=int),
                'verify_ssl': self._get_env('REDFISH_VERIFY_SSL', False, var_type=bool),
                'retries': self._get_env('REDFISH_RETRIES', 3, var_type=int),
            },
            
            # Logging Configuration
            'logging': {
                'level': self._get_env('LOG_LEVEL', 'INFO'),
                'file': self._get_env('LOG_FILE', 'hw_automation.log'),
                'max_size_mb': self._get_env('LOG_MAX_SIZE_MB', 10, var_type=int),
                'backup_count': self._get_env('LOG_BACKUP_COUNT', 5, var_type=int),
            },
            
            # Development Settings
            'development': {
                'debug': self._get_env('DEVELOPMENT_DEBUG', False, var_type=bool),
                'test_database': self._get_env('DEVELOPMENT_TEST_DATABASE', 'test_hw_automation.db'),
                'mock_services': self._get_env('DEVELOPMENT_MOCK_SERVICES', False, var_type=bool),
            }
        }
    
    def _validate_config(self) -> None:
        """Validate critical configuration values."""
        
        # Validate MaaS configuration if provided
        maas_config = self._config['maas']
        if maas_config['host'] or maas_config['url']:
            if not (maas_config['consumer_key'] or maas_config['api_key']):
                logging.warning("MaaS configuration provided but missing authentication credentials")
        
        # Validate logging level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self._config['logging']['level'].upper() not in valid_log_levels:
            logging.warning(f"Invalid log level: {self._config['logging']['level']}, defaulting to INFO")
            self._config['logging']['level'] = 'INFO'
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key (e.g., 'database.path', 'maas.timeout')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.
        
        Args:
            section: Section name (e.g., 'database', 'maas')
            
        Returns:
            Configuration section dictionary
        """
        return self._config.get(section, {})
    
    def to_dict(self) -> Dict[str, Any]:
        """Return entire configuration as dictionary."""
        return self._config.copy()
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access."""
        return self.get(key)


# Global configuration instance
_config: Optional[Config] = None


def load_config(env_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    This function maintains backward compatibility with the old YAML-based system
    while providing modern environment-based configuration.
    
    Args:
        env_file: Optional path to .env file
        
    Returns:
        Configuration dictionary
    """
    global _config
    
    if _config is None:
        # Try to find .env file if not provided
        if env_file is None:
            env_file = find_env_file()
        
        _config = Config(env_file)
    
    return _config.to_dict()


def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        Config instance
    """
    global _config
    
    if _config is None:
        env_file = find_env_file()
        _config = Config(env_file)
    
    return _config


def find_env_file() -> Optional[str]:
    """
    Find .env file in project directory.
    
    Returns:
        Path to .env file if found, None otherwise
    """
    # Look for .env file starting from current directory up to project root
    current_dir = Path.cwd()
    
    # Check common locations
    for path in [
        current_dir / '.env',
        current_dir.parent / '.env',
        Path(__file__).parent.parent.parent / '.env',  # Project root
    ]:
        if path.exists():
            return str(path)
    
    return None


def reload_config(env_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Reload configuration from environment variables.
    
    Args:
        env_file: Optional path to .env file
        
    Returns:
        New configuration dictionary
    """
    global _config
    _config = None
    return load_config(env_file)


# Backward compatibility functions
def load_config_file(config_path: str) -> Dict[str, Any]:
    """Backward compatibility - loads from environment instead."""
    logging.warning("load_config_file is deprecated. Configuration now loads from environment variables.")
    return load_config()


def load_config_from_env() -> Dict[str, Any]:
    """Backward compatibility - same as load_config."""
    return load_config()


def apply_default_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Backward compatibility - defaults are now handled in Config class."""
    return config
