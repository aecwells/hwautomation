"""Workflow helper utilities for orchestration.

This module provides common utilities and helper functions
used across orchestration workflows.
"""

import json
import time
from typing import Any, Dict, List, Optional, Union

from hwautomation.logging import get_logger

logger = get_logger(__name__)


class WorkflowHelpers:
    """Common workflow helper utilities."""

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in seconds to human-readable string."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """Format bytes to human-readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f}{unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f}PB"

    @staticmethod
    def safe_json_loads(json_string: str, default: Any = None) -> Any:
        """Safely parse JSON string with fallback."""
        try:
            return json.loads(json_string)
        except (json.JSONDecodeError, TypeError):
            return default

    @staticmethod
    def safe_json_dumps(obj: Any, default: str = "{}") -> str:
        """Safely serialize object to JSON with fallback."""
        try:
            return json.dumps(obj, indent=2)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def extract_ip_addresses(text: str) -> List[str]:
        """Extract IP addresses from text."""
        import re
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        return re.findall(ip_pattern, text)

    @staticmethod
    def extract_mac_addresses(text: str) -> List[str]:
        """Extract MAC addresses from text."""
        import re
        mac_pattern = r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})'
        matches = re.findall(mac_pattern, text)
        return [f"{match[0]}{match[1]}" for match in matches]

    @staticmethod
    def parse_key_value_output(output: str, separator: str = ":") -> Dict[str, str]:
        """Parse key-value output into dictionary."""
        result = {}
        for line in output.split('\n'):
            line = line.strip()
            if separator in line:
                key, value = line.split(separator, 1)
                result[key.strip()] = value.strip()
        return result

    @staticmethod
    def retry_operation(operation, max_retries: int = 3, delay: float = 1.0, 
                       backoff_factor: float = 2.0) -> Dict[str, Any]:
        """Retry an operation with exponential backoff."""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                result = operation()
                return {
                    "success": True,
                    "result": result,
                    "attempts": attempt + 1
                }
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    sleep_time = delay * (backoff_factor ** attempt)
                    time.sleep(sleep_time)
                    logger.debug(f"Retry attempt {attempt + 1} failed, retrying in {sleep_time}s: {e}")
        
        return {
            "success": False,
            "error": str(last_exception),
            "attempts": max_retries
        }

    @staticmethod
    def validate_ip_address(ip: str) -> bool:
        """Validate IP address format."""
        try:
            import ipaddress
            ipaddress.IPv4Address(ip)
            return True
        except ipaddress.AddressValueError:
            return False

    @staticmethod
    def validate_mac_address(mac: str) -> bool:
        """Validate MAC address format."""
        import re
        mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        return bool(re.match(mac_pattern, mac))

    @staticmethod
    def normalize_mac_address(mac: str, separator: str = ":") -> str:
        """Normalize MAC address format."""
        # Remove any existing separators and convert to uppercase
        clean_mac = ''.join(mac.split()).replace(':', '').replace('-', '').upper()
        
        # Insert separators every 2 characters
        if len(clean_mac) == 12:
            return separator.join([clean_mac[i:i+2] for i in range(0, 12, 2)])
        
        return mac  # Return original if format is unexpected

    @staticmethod
    def calculate_network_range(network: str) -> Dict[str, Any]:
        """Calculate network range information."""
        try:
            import ipaddress
            net = ipaddress.IPv4Network(network, strict=False)
            
            return {
                "network": str(net.network_address),
                "netmask": str(net.netmask),
                "broadcast": str(net.broadcast_address),
                "first_host": str(net.network_address + 1),
                "last_host": str(net.broadcast_address - 1),
                "num_hosts": net.num_addresses - 2,
                "cidr": str(net)
            }
        except Exception as e:
            logger.error(f"Network calculation failed: {e}")
            return {}

    @staticmethod
    def merge_configurations(base_config: Dict[str, Any], 
                           override_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configuration dictionaries."""
        result = base_config.copy()
        
        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = WorkflowHelpers.merge_configurations(result[key], value)
            else:
                result[key] = value
        
        return result

    @staticmethod
    def filter_sensitive_data(data: Dict[str, Any], 
                             sensitive_keys: Optional[List[str]] = None) -> Dict[str, Any]:
        """Filter sensitive data from dictionary."""
        if sensitive_keys is None:
            sensitive_keys = ['password', 'passwd', 'secret', 'key', 'token', 'auth']
        
        filtered = {}
        for key, value in data.items():
            if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                filtered[key] = "***REDACTED***"
            elif isinstance(value, dict):
                filtered[key] = WorkflowHelpers.filter_sensitive_data(value, sensitive_keys)
            elif isinstance(value, list):
                filtered[key] = [
                    WorkflowHelpers.filter_sensitive_data(item, sensitive_keys) 
                    if isinstance(item, dict) else item 
                    for item in value
                ]
            else:
                filtered[key] = value
        
        return filtered

    @staticmethod
    def create_progress_callback(context, step_name: str):
        """Create a progress callback function for long operations."""
        def progress_callback(current: int, total: int, message: str = ""):
            try:
                percentage = (current / total) * 100 if total > 0 else 0
                progress_msg = f"{step_name}: {current}/{total} ({percentage:.1f}%)"
                if message:
                    progress_msg += f" - {message}"
                
                context.add_sub_task(progress_msg)
                logger.debug(progress_msg)
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")
        
        return progress_callback

    @staticmethod
    def timeout_operation(operation, timeout: float = 300.0) -> Dict[str, Any]:
        """Execute operation with timeout."""
        import signal
        import threading
        
        result = {"success": False, "timeout": False, "result": None, "error": None}
        
        def timeout_handler():
            result["timeout"] = True
            result["error"] = f"Operation timed out after {timeout} seconds"
        
        def run_operation():
            try:
                result["result"] = operation()
                result["success"] = True
            except Exception as e:
                result["error"] = str(e)
        
        # Start operation in thread
        operation_thread = threading.Thread(target=run_operation)
        operation_thread.daemon = True
        operation_thread.start()
        
        # Start timeout timer
        timeout_timer = threading.Timer(timeout, timeout_handler)
        timeout_timer.start()
        
        # Wait for operation to complete
        operation_thread.join(timeout)
        timeout_timer.cancel()
        
        return result

    @staticmethod
    def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
        """Split list into chunks of specified size."""
        return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]

    @staticmethod
    def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(WorkflowHelpers.flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    @staticmethod
    def deep_get(dictionary: Dict[str, Any], keys: str, default: Any = None) -> Any:
        """Get nested dictionary value using dot notation."""
        try:
            value = dictionary
            for key in keys.split('.'):
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default

    @staticmethod
    def deep_set(dictionary: Dict[str, Any], keys: str, value: Any) -> None:
        """Set nested dictionary value using dot notation."""
        keys_list = keys.split('.')
        current = dictionary
        
        for key in keys_list[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys_list[-1]] = value

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for filesystem use."""
        import re
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing whitespace and dots
        sanitized = sanitized.strip(' .')
        # Limit length
        return sanitized[:255] if len(sanitized) > 255 else sanitized

    @staticmethod
    def generate_workflow_id() -> str:
        """Generate unique workflow ID."""
        import uuid
        return str(uuid.uuid4())

    @staticmethod
    def get_timestamp() -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'

    @staticmethod
    def parse_version_string(version_str: str) -> Dict[str, Union[int, str]]:
        """Parse version string into components."""
        import re
        
        # Handle common version patterns like "1.2.3", "v1.2.3", "1.2.3-beta"
        pattern = r'v?(\d+)\.(\d+)(?:\.(\d+))?(?:[.-](.+))?'
        match = re.match(pattern, version_str.strip())
        
        if match:
            major, minor, patch, suffix = match.groups()
            return {
                "major": int(major),
                "minor": int(minor),
                "patch": int(patch) if patch else 0,
                "suffix": suffix or "",
                "original": version_str
            }
        
        return {"original": version_str}

    @staticmethod
    def compare_versions(version1: str, version2: str) -> int:
        """Compare two version strings. Returns -1, 0, or 1."""
        v1 = WorkflowHelpers.parse_version_string(version1)
        v2 = WorkflowHelpers.parse_version_string(version2)
        
        # Compare major.minor.patch
        for component in ['major', 'minor', 'patch']:
            v1_comp = v1.get(component, 0)
            v2_comp = v2.get(component, 0)
            
            if v1_comp < v2_comp:
                return -1
            elif v1_comp > v2_comp:
                return 1
        
        return 0  # Versions are equal (ignoring suffix)
