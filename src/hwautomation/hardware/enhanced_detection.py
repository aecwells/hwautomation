"""
Enhanced Hardware Detection Service

Provides intelligent device detection and matching between MaaS hardware
and BMC device types, with automated IPMI configuration validation.
."""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..maas.client import MaasClient
from ..utils.env_config import load_config
from ..utils.network import SSHClient

logger = logging.getLogger(__name__)


@dataclass
class HardwareSpec:
    """Hardware specification for device type matching."""

    cpu_model_pattern: Optional[str] = None
    cpu_count_min: Optional[int] = None
    cpu_count_max: Optional[int] = None
    memory_gb_min: Optional[float] = None
    memory_gb_max: Optional[float] = None
    storage_gb_min: Optional[float] = None
    vendor_pattern: Optional[str] = None
    model_pattern: Optional[str] = None
    architecture: Optional[str] = None


@dataclass
class BMCDeviceType:
    """BMC device type definition."""

    device_type: str
    display_name: str
    description: str
    hardware_spec: HardwareSpec
    bios_template: Optional[str] = None
    ipmi_settings: Optional[Dict] = None


@dataclass
class IPMIValidation:
    """IPMI validation results."""

    is_accessible: bool
    firmware_version: Optional[str] = None
    oob_license_active: bool = False
    kcs_control: Optional[str] = None
    host_interface: Optional[str] = None
    requires_update: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)


class EnhancedHardwareDetector:
    """Enhanced hardware detection with BMC device type matching."""

    def __init__(self, maas_client: MaasClient = None, config: Dict = None):
        """
        Initialize enhanced hardware detector

        Args:
            maas_client: MaaS client instance
            config: Configuration dictionary
        ."""
        self.maas_client = maas_client
        self.config = config or load_config()
        self.device_types = self._load_device_types()

    def _load_device_types(self) -> Dict[str, BMCDeviceType]:
        """Load BMC device type definitions from configuration."""
        device_types = {}

        # Define BMC device types based on the boarding document
        # These would typically be loaded from configuration files

        # RocketLake systems
        device_types["d1.c1.small"] = BMCDeviceType(
            device_type="d1.c1.small",
            display_name="RocketLake Small (d1.c1.small)",
            description="Small compute node with RocketLake CPU",
            hardware_spec=HardwareSpec(
                cpu_model_pattern=r"Intel.*11th Gen.*Core.*i[35]",
                cpu_count_min=1,
                cpu_count_max=1,
                memory_gb_min=8,
                memory_gb_max=32,
                vendor_pattern=r"Supermicro",
                architecture="amd64",
            ),
            ipmi_settings={
                "kcs_control": "user",
                "host_interface": "off",
                "oob_license_required": True,
            },
        )

        device_types["d1.c1.large"] = BMCDeviceType(
            device_type="d1.c1.large",
            display_name="RocketLake Large (d1.c1.large)",
            description="Large compute node with RocketLake CPU",
            hardware_spec=HardwareSpec(
                cpu_model_pattern=r"Intel.*11th Gen.*Core.*i[79]",
                cpu_count_min=1,
                cpu_count_max=1,
                memory_gb_min=16,
                memory_gb_max=128,
                vendor_pattern=r"Supermicro",
                architecture="amd64",
            ),
            ipmi_settings={
                "kcs_control": "user",
                "host_interface": "off",
                "oob_license_required": True,
            },
        )

        # CoffeeLake systems
        device_types["d2.c2.medium"] = BMCDeviceType(
            device_type="d2.c2.medium",
            display_name="CoffeeLake Medium (d2.c2.medium)",
            description="Medium compute node with CoffeeLake CPU",
            hardware_spec=HardwareSpec(
                cpu_model_pattern=r"Intel.*8th Gen.*Core.*i[57]",
                cpu_count_min=1,
                cpu_count_max=2,
                memory_gb_min=16,
                memory_gb_max=64,
                vendor_pattern=r"Supermicro",
                architecture="amd64",
            ),
            ipmi_settings={"oob_license_required": True},
        )

        # Cascadelake systems
        device_types["s2.c2.large"] = BMCDeviceType(
            device_type="s2.c2.large",
            display_name="Cascadelake Large (s2.c2.large)",
            description="Large server with Cascadelake Xeon processors",
            hardware_spec=HardwareSpec(
                cpu_model_pattern=r"Intel.*Xeon.*Platinum.*(8260Y|6258R)",
                cpu_count_min=2,
                cpu_count_max=4,
                memory_gb_min=64,
                memory_gb_max=512,
                vendor_pattern=r"Supermicro",
                architecture="amd64",
            ),
            ipmi_settings={
                "kcs_control": "user",
                "host_interface": "off",
                "oob_license_required": True,
            },
        )

        # Icelake/Sapphire Rapids systems
        device_types["s5.x6.c8.large"] = BMCDeviceType(
            device_type="s5.x6.c8.large",
            display_name="Icelake/SPR Large (s5.x6.c8.large)",
            description="Large server with Icelake/Sapphire Rapids Xeon processors",
            hardware_spec=HardwareSpec(
                cpu_model_pattern=r"Intel.*Xeon.*(6336Y|8352Y|8452Y)",
                cpu_count_min=2,
                cpu_count_max=8,
                memory_gb_min=128,
                memory_gb_max=1024,
                vendor_pattern=r"Supermicro",
                architecture="amd64",
            ),
            ipmi_settings={
                "kcs_control": "user",
                "host_interface": "off",
                "oob_license_required": True,
            },
        )

        # HP systems
        device_types["hp.ilo.arm"] = BMCDeviceType(
            device_type="hp.ilo.arm",
            display_name="HP iLO ARM Server",
            description="HP server with ARM processors and iLO management",
            hardware_spec=HardwareSpec(
                cpu_model_pattern=r"ARM|AArch64",
                vendor_pattern=r"HP|HPE|Hewlett",
                architecture="arm64",
            ),
            ipmi_settings={
                "ipmi_over_lan": "enabled",
                "require_host_auth": "enabled",
                "require_login_rbsu": "enabled",
            },
        )

        device_types["hp.ilo.intel"] = BMCDeviceType(
            device_type="hp.ilo.intel",
            display_name="HP iLO Intel Server",
            description="HP server with Intel processors and iLO management",
            hardware_spec=HardwareSpec(
                cpu_model_pattern=r"Intel.*Xeon",
                vendor_pattern=r"HP|HPE|Hewlett",
                architecture="amd64",
            ),
            ipmi_settings={
                "ipmi_over_lan": "enabled",
                "require_host_auth": "enabled",
                "require_login_rbsu": "enabled",
            },
        )

        return device_types

    def detect_matching_device_types(self, system_id: str) -> List[Tuple[str, float]]:
        """
        Detect which BMC device types match the hardware of a given machine

        Args:
            system_id: MaaS system ID

        Returns:
            List of (device_type, confidence_score) tuples, sorted by confidence
        ."""
        try:
            if self.maas_client is None:
                logger.warning("MaaS client not available")
                return []

            machine = self.maas_client.get_machine(system_id)
            if not machine:
                logger.warning(f"Machine {system_id} not found in MaaS")
                return []

            hardware_info = self._extract_hardware_info(machine)
            matches = []

            for device_type, spec in self.device_types.items():
                confidence = self._calculate_match_confidence(hardware_info, spec)
                if confidence > 0.3:  # Minimum confidence threshold
                    matches.append((device_type, confidence))

            # Sort by confidence score (highest first)
            matches.sort(key=lambda x: x[1], reverse=True)

            logger.info(f"Found {len(matches)} matching device types for {system_id}")
            return matches

        except Exception as e:
            logger.error(f"Error detecting device types for {system_id}: {e}")
            return []

    def _extract_hardware_info(self, machine: Dict) -> Dict:
        """Extract relevant hardware information from MaaS machine data."""
        hardware_info = {
            "cpu_model": "",
            "cpu_count": 0,
            "memory_gb": 0.0,
            "storage_gb": 0.0,
            "vendor": "",
            "model": "",
            "architecture": machine.get("architecture", "").split("/")[0],
        }

        try:
            # Extract CPU information
            cpu_info = machine.get("cpu_count", 0)
            hardware_info["cpu_count"] = cpu_info

            # Extract memory information (convert MB to GB)
            memory_mb = machine.get("memory", 0)
            hardware_info["memory_gb"] = memory_mb / 1024.0 if memory_mb else 0.0

            # Extract storage information
            storage_mb = 0
            for disk in machine.get("blockdevice_set", []):
                storage_mb += disk.get("size", 0) / (1024 * 1024)  # Convert bytes to MB
            hardware_info["storage_gb"] = storage_mb / 1024.0 if storage_mb else 0.0

            # Extract vendor and model from node description or tags
            node_info = (
                machine.get("description", "")
                + " "
                + " ".join(machine.get("tag_names", []))
            )

            # Try to extract vendor
            vendor_patterns = [
                r"(Supermicro)",
                r"(HP[E]?)",
                r"(Dell)",
                r"(Lenovo)",
                r"(Intel)",
            ]
            for pattern in vendor_patterns:
                match = re.search(pattern, node_info, re.IGNORECASE)
                if match:
                    hardware_info["vendor"] = match.group(1)
                    break

            # Try to extract CPU model from commissioning data if available
            commissioning_results = machine.get("commissioning_results", {})
            for script_name, result in commissioning_results.items():
                if "cpu" in script_name.lower() or "processor" in script_name.lower():
                    output = result.get("output", "")
                    # Look for Intel CPU model patterns
                    cpu_match = re.search(
                        r"Intel.*?(?:Core|Xeon).*?(?:i[0-9]|[0-9]{4}[A-Z]?)",
                        output,
                        re.IGNORECASE,
                    )
                    if cpu_match:
                        hardware_info["cpu_model"] = cpu_match.group(0)
                        break

        except Exception as e:
            logger.warning(f"Error extracting hardware info: {e}")

        return hardware_info

    def _calculate_match_confidence(
        self, hardware_info: Dict, device_spec: BMCDeviceType
    ) -> float:
        """Calculate confidence score for hardware matching a device specification."""
        confidence = 0.0
        total_criteria = 0

        spec = device_spec.hardware_spec

        # CPU model matching
        if spec.cpu_model_pattern and hardware_info.get("cpu_model"):
            total_criteria += 1
            if re.search(
                spec.cpu_model_pattern, hardware_info["cpu_model"], re.IGNORECASE
            ):
                confidence += 0.3  # High weight for CPU model match

        # CPU count matching
        if spec.cpu_count_min is not None or spec.cpu_count_max is not None:
            total_criteria += 1
            cpu_count = hardware_info.get("cpu_count", 0)
            if (spec.cpu_count_min is None or cpu_count >= spec.cpu_count_min) and (
                spec.cpu_count_max is None or cpu_count <= spec.cpu_count_max
            ):
                confidence += 0.2

        # Memory matching
        if spec.memory_gb_min is not None or spec.memory_gb_max is not None:
            total_criteria += 1
            memory_gb = hardware_info.get("memory_gb", 0)
            if (spec.memory_gb_min is None or memory_gb >= spec.memory_gb_min) and (
                spec.memory_gb_max is None or memory_gb <= spec.memory_gb_max
            ):
                confidence += 0.2

        # Vendor matching
        if spec.vendor_pattern and hardware_info.get("vendor"):
            total_criteria += 1
            if re.search(spec.vendor_pattern, hardware_info["vendor"], re.IGNORECASE):
                confidence += 0.2

        # Architecture matching
        if spec.architecture and hardware_info.get("architecture"):
            total_criteria += 1
            if spec.architecture == hardware_info["architecture"]:
                confidence += 0.1

        # Normalize confidence if we have criteria
        if total_criteria > 0:
            confidence = min(confidence, 1.0)  # Cap at 1.0

        return confidence

    def validate_ipmi_configuration(
        self, ipmi_ip: str, username: str = "ADMIN", password: str = None
    ) -> IPMIValidation:
        """
        Validate IPMI configuration according to BMC boarding requirements

        Args:
            ipmi_ip: IPMI IP address
            username: IPMI username
            password: IPMI password

        Returns:
            IPMIValidation object with validation results
        ."""
        validation = IPMIValidation(
            is_accessible=False, requires_update=[], validation_errors=[]
        )

        try:
            # Test IPMI accessibility using ipmitool
            import subprocess

            # Basic connectivity test
            cmd = ["ping", "-c", "1", "-W", "2", ipmi_ip]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)

            if result.returncode != 0:
                validation.validation_errors.append(
                    f"IPMI IP {ipmi_ip} is not reachable"
                )
                return validation

            validation.is_accessible = True

            # If password provided, test IPMI authentication
            if password:
                # Test basic IPMI command
                cmd = [
                    "ipmitool",
                    "-I",
                    "lanplus",
                    "-H",
                    ipmi_ip,
                    "-U",
                    username,
                    "-P",
                    password,
                    "mc",
                    "info",
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

                if result.returncode == 0:
                    # Parse firmware version
                    for line in result.stdout.split("\n"):
                        if "Firmware Revision" in line:
                            validation.firmware_version = line.split(":")[-1].strip()
                            break
                else:
                    validation.validation_errors.append("IPMI authentication failed")

                # Check OOB license status (this would need specific implementation per vendor)
                # For now, we'll mark it as requiring validation
                validation.requires_update.append(
                    "OOB license activation status needs verification"
                )

                # Check KCS control setting (vendor-specific implementation needed)
                validation.requires_update.append(
                    "KCS control setting verification needed"
                )

                # Check host interface setting (vendor-specific implementation needed)
                validation.requires_update.append(
                    "Host interface setting verification needed"
                )

        except subprocess.TimeoutExpired:
            validation.validation_errors.append("IPMI connection timeout")
        except Exception as e:
            validation.validation_errors.append(f"IPMI validation error: {e}")

        return validation

    def get_available_device_types_for_machines(
        self, machine_ids: List[str]
    ) -> Dict[str, List[str]]:
        """
        Get available device types for a list of machines

        Args:
            machine_ids: List of MaaS system IDs

        Returns:
            Dictionary mapping machine_id to list of compatible device types
        ."""
        machine_device_types = {}

        for machine_id in machine_ids:
            matches = self.detect_matching_device_types(machine_id)
            # Only include device types with confidence > 0.5
            compatible_types = [
                device_type for device_type, confidence in matches if confidence > 0.5
            ]
            machine_device_types[machine_id] = compatible_types

        return machine_device_types

    def get_device_type_info(self, device_type: str) -> Optional[BMCDeviceType]:
        """Get information about a specific device type."""
        return self.device_types.get(device_type)

    def list_all_device_types(self) -> List[BMCDeviceType]:
        """List all available BMC device types."""
        return list(self.device_types.values())
