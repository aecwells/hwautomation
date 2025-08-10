"""Vendor detection utilities for orchestration workflows.

This module provides utilities for detecting hardware vendors and
their specific characteristics during workflow execution.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from hwautomation.logging import get_logger

from ...utils.network import SSHClient

logger = get_logger(__name__)


class VendorDetector:
    """Hardware vendor detection utilities."""

    # Known vendor patterns and their characteristics
    VENDOR_PATTERNS = {
        "supermicro": {
            "patterns": [
                r"supermicro",
                r"super micro",
                r"x[0-9]+[a-z]*-[a-z0-9]+",  # Supermicro motherboard patterns
            ],
            "bios_patterns": [
                r"american megatrends",
                r"ami",
            ],
            "ipmi_default_creds": [
                {"username": "ADMIN", "password": "ADMIN"},
                {"username": "admin", "password": "admin"},
            ],
            "characteristics": {
                "has_ipmi": True,
                "redfish_support": "limited",
                "firmware_tools": ["ipmitool", "dmidecode"],
                "bios_config_method": "vendor_tool",
            },
        },
        "hp": {
            "patterns": [
                r"hewlett.?packard",
                r"hp",
                r"hpe",
                r"proliant",
                r"microserver",
            ],
            "bios_patterns": [
                r"hp",
                r"hpe",
                r"proliant",
            ],
            "ipmi_default_creds": [
                {"username": "Administrator", "password": "password"},
                {"username": "admin", "password": "admin"},
            ],
            "characteristics": {
                "has_ipmi": True,
                "has_ilo": True,
                "redfish_support": "full",
                "firmware_tools": ["hponcfg", "conrep", "ipmitool"],
                "bios_config_method": "hp_tools",
            },
        },
        "dell": {
            "patterns": [
                r"dell",
                r"poweredge",
                r"optiplex",
                r"precision",
            ],
            "bios_patterns": [
                r"dell",
                r"poweredge",
            ],
            "ipmi_default_creds": [
                {"username": "root", "password": "calvin"},
                {"username": "admin", "password": "admin"},
            ],
            "characteristics": {
                "has_ipmi": True,
                "has_idrac": True,
                "redfish_support": "full",
                "firmware_tools": ["racadm", "ipmitool"],
                "bios_config_method": "dell_tools",
            },
        },
        "lenovo": {
            "patterns": [
                r"lenovo",
                r"thinkserver",
                r"thinkstation",
                r"thinksystem",
            ],
            "bios_patterns": [
                r"lenovo",
                r"thinkserver",
            ],
            "ipmi_default_creds": [
                {"username": "USERID", "password": "PASSW0RD"},
                {"username": "admin", "password": "admin"},
            ],
            "characteristics": {
                "has_ipmi": True,
                "has_xcc": True,
                "redfish_support": "full",
                "firmware_tools": ["ipmitool", "onecli"],
                "bios_config_method": "lenovo_tools",
            },
        },
        "intel": {
            "patterns": [
                r"intel",
                r"nuc",
            ],
            "bios_patterns": [
                r"intel",
            ],
            "ipmi_default_creds": [
                {"username": "admin", "password": "admin"},
            ],
            "characteristics": {
                "has_ipmi": False,
                "redfish_support": "none",
                "firmware_tools": ["dmidecode"],
                "bios_config_method": "uefi",
            },
        },
    }

    def __init__(self, ssh_client: Optional[SSHClient] = None):
        """Initialize vendor detector."""
        self.ssh_client = ssh_client

    @classmethod
    def create_for_host(
        cls, hostname: str, username: str = "ubuntu", key_path: Optional[str] = None
    ) -> "VendorDetector":
        """Create vendor detector for a specific host."""
        ssh_client = SSHClient(hostname=hostname, username=username, key_path=key_path)
        return cls(ssh_client)

    def detect_vendor(
        self, system_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Detect hardware vendor from system information."""
        try:
            # Use provided system info or gather it
            if system_info is None:
                system_info = self._gather_vendor_detection_info()

            detection_results = {
                "vendor": "unknown",
                "confidence": 0.0,
                "method": "none",
                "characteristics": {},
                "detection_details": {},
            }

            # Try different detection methods
            methods = [
                self._detect_from_dmidecode,
                self._detect_from_bios_info,
                self._detect_from_hardware_info,
                self._detect_from_network_interfaces,
            ]

            best_result = detection_results

            for method in methods:
                try:
                    result = method(system_info)
                    if result["confidence"] > best_result["confidence"]:
                        best_result = result
                except Exception as e:
                    logger.debug(f"Detection method {method.__name__} failed: {e}")

            # Add vendor characteristics if detected
            if best_result["vendor"] != "unknown":
                vendor_config = self.VENDOR_PATTERNS.get(best_result["vendor"], {})
                best_result["characteristics"] = vendor_config.get(
                    "characteristics", {}
                )
                best_result["default_credentials"] = vendor_config.get(
                    "ipmi_default_creds", []
                )

            return best_result

        except Exception as e:
            logger.error(f"Vendor detection failed: {e}")
            return {
                "vendor": "unknown",
                "confidence": 0.0,
                "method": "error",
                "error": str(e),
                "characteristics": {},
                "detection_details": {},
            }

    def _gather_vendor_detection_info(self) -> Dict[str, Any]:
        """Gather information needed for vendor detection."""
        if not self.ssh_client:
            return {}

        info = {}

        # DMI decode information
        dmi_result = self.ssh_client.execute_command("sudo dmidecode -t system")
        if dmi_result.get("success"):
            info["dmidecode_system"] = dmi_result.get("stdout", "")

        # BIOS information
        bios_result = self.ssh_client.execute_command("sudo dmidecode -t bios")
        if bios_result.get("success"):
            info["dmidecode_bios"] = bios_result.get("stdout", "")

        # Motherboard information
        board_result = self.ssh_client.execute_command("sudo dmidecode -t baseboard")
        if board_result.get("success"):
            info["dmidecode_baseboard"] = board_result.get("stdout", "")

        # lshw information
        lshw_result = self.ssh_client.execute_command("sudo lshw -short")
        if lshw_result.get("success"):
            info["lshw_output"] = lshw_result.get("stdout", "")

        # Network interfaces (for vendor-specific patterns)
        network_result = self.ssh_client.execute_command("cat /proc/net/dev")
        if network_result.get("success"):
            info["network_interfaces"] = network_result.get("stdout", "")

        # PCI devices
        pci_result = self.ssh_client.execute_command("lspci")
        if pci_result.get("success"):
            info["pci_devices"] = pci_result.get("stdout", "")

        return info

    def _detect_from_dmidecode(self, system_info: Dict[str, Any]) -> Dict[str, Any]:
        """Detect vendor from DMI decode information."""
        dmi_data = (
            system_info.get("dmidecode_system", "")
            + " "
            + system_info.get("dmidecode_baseboard", "")
        )

        if not dmi_data.strip():
            return {"vendor": "unknown", "confidence": 0.0, "method": "dmidecode"}

        # Look for vendor patterns in DMI data
        best_vendor = "unknown"
        best_confidence = 0.0
        detection_details = {}

        for vendor, config in self.VENDOR_PATTERNS.items():
            confidence = 0.0
            matches = []

            for pattern in config["patterns"]:
                matches_found = re.findall(pattern, dmi_data, re.IGNORECASE)
                if matches_found:
                    matches.extend(matches_found)
                    confidence += 0.3  # Each pattern match adds confidence

            # Bonus for multiple matches
            if len(matches) > 1:
                confidence += 0.2

            detection_details[vendor] = {"matches": matches, "confidence": confidence}

            if confidence > best_confidence:
                best_confidence = confidence
                best_vendor = vendor

        return {
            "vendor": best_vendor,
            "confidence": min(best_confidence, 1.0),
            "method": "dmidecode",
            "detection_details": detection_details,
        }

    def _detect_from_bios_info(self, system_info: Dict[str, Any]) -> Dict[str, Any]:
        """Detect vendor from BIOS information."""
        bios_data = system_info.get("dmidecode_bios", "")

        if not bios_data.strip():
            return {"vendor": "unknown", "confidence": 0.0, "method": "bios"}

        best_vendor = "unknown"
        best_confidence = 0.0
        detection_details = {}

        for vendor, config in self.VENDOR_PATTERNS.items():
            confidence = 0.0
            matches = []

            # Check BIOS-specific patterns
            bios_patterns = config.get("bios_patterns", [])
            for pattern in bios_patterns:
                matches_found = re.findall(pattern, bios_data, re.IGNORECASE)
                if matches_found:
                    matches.extend(matches_found)
                    confidence += 0.4  # BIOS patterns are quite reliable

            detection_details[vendor] = {
                "bios_matches": matches,
                "confidence": confidence,
            }

            if confidence > best_confidence:
                best_confidence = confidence
                best_vendor = vendor

        return {
            "vendor": best_vendor,
            "confidence": min(best_confidence, 1.0),
            "method": "bios",
            "detection_details": detection_details,
        }

    def _detect_from_hardware_info(self, system_info: Dict[str, Any]) -> Dict[str, Any]:
        """Detect vendor from general hardware information."""
        hw_data = (
            system_info.get("lshw_output", "")
            + " "
            + system_info.get("pci_devices", "")
        )

        if not hw_data.strip():
            return {"vendor": "unknown", "confidence": 0.0, "method": "hardware"}

        best_vendor = "unknown"
        best_confidence = 0.0
        detection_details = {}

        for vendor, config in self.VENDOR_PATTERNS.items():
            confidence = 0.0
            matches = []

            for pattern in config["patterns"]:
                matches_found = re.findall(pattern, hw_data, re.IGNORECASE)
                if matches_found:
                    matches.extend(matches_found)
                    confidence += 0.2  # Hardware info is less reliable

            detection_details[vendor] = {
                "hardware_matches": matches,
                "confidence": confidence,
            }

            if confidence > best_confidence:
                best_confidence = confidence
                best_vendor = vendor

        return {
            "vendor": best_vendor,
            "confidence": min(best_confidence, 1.0),
            "method": "hardware",
            "detection_details": detection_details,
        }

    def _detect_from_network_interfaces(
        self, system_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect vendor from network interface patterns."""
        network_data = system_info.get("network_interfaces", "")

        if not network_data.strip():
            return {"vendor": "unknown", "confidence": 0.0, "method": "network"}

        # This is a basic implementation - could be enhanced with MAC OUI lookup
        vendor_hints = {
            "eno": "dell",  # Dell often uses eno* naming
            "em": "hp",  # HP often uses em* naming
        }

        best_vendor = "unknown"
        best_confidence = 0.0

        for interface_pattern, vendor in vendor_hints.items():
            if interface_pattern in network_data:
                return {
                    "vendor": vendor,
                    "confidence": 0.3,  # Low confidence from network interfaces alone
                    "method": "network",
                    "detection_details": {"interface_pattern": interface_pattern},
                }

        return {
            "vendor": "unknown",
            "confidence": 0.0,
            "method": "network",
            "detection_details": {},
        }

    def get_vendor_specific_tools(self, vendor: str) -> List[str]:
        """Get list of vendor-specific tools."""
        vendor_config = self.VENDOR_PATTERNS.get(vendor.lower(), {})
        return vendor_config.get("characteristics", {}).get("firmware_tools", [])

    def get_default_credentials(self, vendor: str) -> List[Dict[str, str]]:
        """Get default IPMI credentials for vendor."""
        vendor_config = self.VENDOR_PATTERNS.get(vendor.lower(), {})
        return vendor_config.get("ipmi_default_creds", [])

    def has_redfish_support(self, vendor: str) -> str:
        """Check Redfish support level for vendor."""
        vendor_config = self.VENDOR_PATTERNS.get(vendor.lower(), {})
        return vendor_config.get("characteristics", {}).get("redfish_support", "none")

    def get_bios_config_method(self, vendor: str) -> str:
        """Get preferred BIOS configuration method for vendor."""
        vendor_config = self.VENDOR_PATTERNS.get(vendor.lower(), {})
        return vendor_config.get("characteristics", {}).get(
            "bios_config_method", "generic"
        )

    def validate_vendor_detection(
        self, detected_vendor: str, additional_checks: bool = True
    ) -> Dict[str, Any]:
        """Validate vendor detection with additional checks."""
        try:
            if not self.ssh_client or detected_vendor == "unknown":
                return {"validated": False, "confidence": 0.0, "checks_performed": []}

            validation_results = {
                "validated": False,
                "confidence": 0.0,
                "checks_performed": [],
                "check_results": {},
            }

            if additional_checks:
                # Check for vendor-specific tools
                tools = self.get_vendor_specific_tools(detected_vendor)
                for tool in tools[:2]:  # Check first 2 tools
                    tool_result = self.ssh_client.execute_command(f"which {tool}")
                    tool_available = tool_result.get("success", False)

                    validation_results["checks_performed"].append(f"tool_{tool}")
                    validation_results["check_results"][f"tool_{tool}"] = tool_available

                    if tool_available:
                        validation_results["confidence"] += 0.2

                # Check for vendor-specific files or directories
                vendor_paths = {
                    "hp": ["/opt/hp", "/usr/sbin/hponcfg"],
                    "dell": ["/opt/dell", "/usr/bin/racadm"],
                    "supermicro": ["/usr/bin/ipmitool"],
                }

                paths_to_check = vendor_paths.get(detected_vendor, [])
                for path in paths_to_check:
                    path_result = self.ssh_client.execute_command(
                        f"test -e {path} && echo 'exists'"
                    )
                    path_exists = "exists" in path_result.get("stdout", "")

                    validation_results["checks_performed"].append(f"path_{path}")
                    validation_results["check_results"][f"path_{path}"] = path_exists

                    if path_exists:
                        validation_results["confidence"] += 0.15

            validation_results["validated"] = validation_results["confidence"] > 0.3

            return validation_results

        except Exception as e:
            logger.error(f"Vendor validation failed: {e}")
            return {
                "validated": False,
                "confidence": 0.0,
                "error": str(e),
                "checks_performed": [],
            }
