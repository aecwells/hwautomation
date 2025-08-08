"""
Enhanced BIOS Configuration Decision Logic

Implements intelligent per-setting method selection for BIOS configuration,
optimizing between Redfish and vendor tools based on setting characteristics,
device capabilities, and performance considerations.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class ConfigMethod(Enum):
    """BIOS configuration methods"""

    REDFISH = "redfish"
    VENDOR_TOOL = "vendor_tool"
    HYBRID = "hybrid"


class SettingPriority(Enum):
    """Setting priority levels for method selection"""

    REDFISH_PREFERRED = "redfish_preferred"  # Fast, reliable via Redfish
    REDFISH_FALLBACK = "redfish_fallback"  # Works via Redfish but vendor is better
    VENDOR_ONLY = "vendor_only"  # Requires vendor tools
    UNKNOWN = "unknown"  # Unknown setting, needs analysis


@dataclass
class SettingMethodInfo:
    """Information about how to handle a specific BIOS setting"""

    setting_name: str
    priority: SettingPriority
    description: str
    estimated_time_redfish: float = 0.0  # Estimated time in seconds
    estimated_time_vendor: float = 0.0  # Estimated time in seconds
    success_rate_redfish: float = 0.0  # Success rate 0-1
    success_rate_vendor: float = 0.0  # Success rate 0-1
    requires_reboot: bool = False  # Whether setting requires system reboot
    complexity_score: int = 1  # 1-10, higher is more complex


@dataclass
class MethodSelectionResult:
    """Result of method selection analysis"""

    redfish_settings: Dict[str, Any]  # Settings to apply via Redfish
    vendor_settings: Dict[str, Any]  # Settings to apply via vendor tools
    unknown_settings: Dict[str, Any]  # Settings with unknown method
    method_rationale: Dict[str, str]  # Explanation for each setting's method
    performance_estimate: Dict[str, float]  # Estimated time per method
    batch_groups: List[Dict[str, Any]]  # Batched operations for efficiency


class BiosSettingMethodSelector:
    """
    Intelligent BIOS setting method selector.

    Analyzes device configuration and BIOS settings to determine the optimal
    method (Redfish vs vendor tools) for each individual setting.
    """

    def __init__(self, device_config: Dict[str, Any]):
        """
        Initialize method selector with device configuration.

        Args:
            device_config: Device configuration from device_mappings.yaml
        """
        self.device_config = device_config
        self.setting_methods = self._parse_setting_methods()
        self.performance_hints = device_config.get("method_performance", {})
        self.redfish_compatibility = device_config.get("redfish_compatibility", {})

    def _parse_setting_methods(self) -> Dict[str, SettingMethodInfo]:
        """Parse setting method configuration into structured data"""
        methods = {}
        bios_setting_methods = self.device_config.get("bios_setting_methods", {})

        # Parse redfish_preferred settings
        redfish_preferred = bios_setting_methods.get("redfish_preferred", {})
        for setting, description in redfish_preferred.items():
            methods[setting] = SettingMethodInfo(
                setting_name=setting,
                priority=SettingPriority.REDFISH_PREFERRED,
                description=description,
                estimated_time_redfish=2.0,  # Fast Redfish operations
                estimated_time_vendor=30.0,  # Slower vendor tool operations
                success_rate_redfish=0.95,
                success_rate_vendor=0.98,
                complexity_score=2,
            )

        # Parse redfish_fallback settings
        redfish_fallback = bios_setting_methods.get("redfish_fallback", {})
        for setting, description in redfish_fallback.items():
            methods[setting] = SettingMethodInfo(
                setting_name=setting,
                priority=SettingPriority.REDFISH_FALLBACK,
                description=description,
                estimated_time_redfish=5.0,  # Moderate Redfish operations
                estimated_time_vendor=20.0,  # Faster vendor tool operations
                success_rate_redfish=0.80,  # Lower success rate via Redfish
                success_rate_vendor=0.98,
                complexity_score=4,
            )

        # Parse vendor_only settings
        vendor_only = bios_setting_methods.get("vendor_only", {})
        for setting, description in vendor_only.items():
            methods[setting] = SettingMethodInfo(
                setting_name=setting,
                priority=SettingPriority.VENDOR_ONLY,
                description=description,
                estimated_time_redfish=0.0,  # Not available via Redfish
                estimated_time_vendor=60.0,  # Complex vendor operations
                success_rate_redfish=0.0,
                success_rate_vendor=0.95,
                requires_reboot=True,  # Complex settings often require reboot
                complexity_score=8,
            )

        return methods

    def analyze_settings(
        self,
        settings_to_apply: Dict[str, Any],
        prefer_performance: bool = True,
        max_redfish_batch: Optional[int] = None,
    ) -> MethodSelectionResult:
        """
        Analyze settings and determine optimal method for each.

        Args:
            settings_to_apply: Dictionary of setting names and values to apply
            prefer_performance: Whether to optimize for speed over reliability
            max_redfish_batch: Maximum settings per Redfish batch (overrides config)

        Returns:
            MethodSelectionResult with optimized method selection
        """
        redfish_settings = {}
        vendor_settings = {}
        unknown_settings = {}
        method_rationale = {}

        # Get batch size preference
        if max_redfish_batch is None:
            max_redfish_batch = self.performance_hints.get("redfish_batch_size", 10)

        for setting_name, setting_value in settings_to_apply.items():
            method_info = self.setting_methods.get(setting_name)

            if method_info is None:
                # Unknown setting - analyze and decide
                method, reason = self._analyze_unknown_setting(
                    setting_name, setting_value
                )
                if method == ConfigMethod.REDFISH:
                    redfish_settings[setting_name] = setting_value
                elif method == ConfigMethod.VENDOR_TOOL:
                    vendor_settings[setting_name] = setting_value
                else:
                    unknown_settings[setting_name] = setting_value
                method_rationale[setting_name] = reason
                continue

            # Known setting - apply configured logic
            selected_method, reason = self._select_method_for_setting(
                method_info, prefer_performance
            )

            if selected_method == ConfigMethod.REDFISH:
                redfish_settings[setting_name] = setting_value
            else:
                vendor_settings[setting_name] = setting_value

            method_rationale[setting_name] = reason

        # Calculate performance estimates
        performance_estimate = self._calculate_performance_estimate(
            redfish_settings, vendor_settings, max_redfish_batch
        )

        # Create batch groups for optimized execution
        batch_groups = self._create_batch_groups(
            redfish_settings, vendor_settings, max_redfish_batch
        )

        return MethodSelectionResult(
            redfish_settings=redfish_settings,
            vendor_settings=vendor_settings,
            unknown_settings=unknown_settings,
            method_rationale=method_rationale,
            performance_estimate=performance_estimate,
            batch_groups=batch_groups,
        )

    def _select_method_for_setting(
        self, method_info: SettingMethodInfo, prefer_performance: bool
    ) -> Tuple[ConfigMethod, str]:
        """Select the best method for a known setting"""

        if method_info.priority == SettingPriority.REDFISH_PREFERRED:
            return (
                ConfigMethod.REDFISH,
                f"Redfish preferred for {method_info.setting_name} - {method_info.description}",
            )

        elif method_info.priority == SettingPriority.VENDOR_ONLY:
            return (
                ConfigMethod.VENDOR_TOOL,
                f"Vendor tool required for {method_info.setting_name} - {method_info.description}",
            )

        elif method_info.priority == SettingPriority.REDFISH_FALLBACK:
            if prefer_performance:
                # Choose based on speed
                if (
                    method_info.estimated_time_redfish
                    < method_info.estimated_time_vendor
                ):
                    return (
                        ConfigMethod.REDFISH,
                        f"Redfish chosen for performance ({method_info.estimated_time_redfish}s vs {method_info.estimated_time_vendor}s)",
                    )
                else:
                    return (
                        ConfigMethod.VENDOR_TOOL,
                        f"Vendor tool chosen for performance ({method_info.estimated_time_vendor}s vs {method_info.estimated_time_redfish}s)",
                    )
            else:
                # Choose based on reliability
                if method_info.success_rate_redfish >= method_info.success_rate_vendor:
                    return (
                        ConfigMethod.REDFISH,
                        f"Redfish chosen for reliability ({method_info.success_rate_redfish*100}% success rate)",
                    )
                else:
                    return (
                        ConfigMethod.VENDOR_TOOL,
                        f"Vendor tool chosen for reliability ({method_info.success_rate_vendor*100}% success rate)",
                    )

        # Default fallback
        return (
            ConfigMethod.VENDOR_TOOL,
            f"Default fallback to vendor tool for {method_info.setting_name}",
        )

    def _analyze_unknown_setting(
        self, setting_name: str, setting_value: Any
    ) -> Tuple[ConfigMethod, str]:
        """Analyze unknown setting and guess best method"""
        setting_lower = setting_name.lower()

        # Heuristics for unknown settings
        redfish_indicators = [
            "boot",
            "power",
            "secure",
            "pxe",
            "wake",
            "timeout",
            "turbo",
            "speedstep",
            "eist",
            "profile",
            "quiet",
        ]

        vendor_indicators = [
            "microcode",
            "timing",
            "advanced",
            "overclock",
            "fan",
            "monitor",
            "update",
            "complex",
            "vendor",
            "oem",
            "proprietary",
        ]

        # Check for Redfish-friendly patterns
        if any(indicator in setting_lower for indicator in redfish_indicators):
            return (
                ConfigMethod.REDFISH,
                f"Unknown setting '{setting_name}' matches Redfish patterns",
            )

        # Check for vendor-only patterns
        if any(indicator in setting_lower for indicator in vendor_indicators):
            return (
                ConfigMethod.VENDOR_TOOL,
                f"Unknown setting '{setting_name}' matches vendor-only patterns",
            )

        # Check value complexity
        if isinstance(setting_value, (dict, list)):
            return (
                ConfigMethod.VENDOR_TOOL,
                f"Unknown setting '{setting_name}' has complex value type",
            )

        # Default to vendor tool for safety
        return (
            ConfigMethod.VENDOR_TOOL,
            f"Unknown setting '{setting_name}' - defaulting to vendor tool for safety",
        )

    def _calculate_performance_estimate(
        self,
        redfish_settings: Dict[str, Any],
        vendor_settings: Dict[str, Any],
        redfish_batch_size: int,
    ) -> Dict[str, float]:
        """Calculate estimated execution time for each method"""

        # Calculate Redfish time (batched operations)
        redfish_count = len(redfish_settings)
        redfish_batches = (
            (redfish_count + redfish_batch_size - 1) // redfish_batch_size
            if redfish_count > 0
            else 0
        )
        redfish_time = redfish_batches * self.performance_hints.get(
            "redfish_timeout", 30
        )

        # Calculate vendor tool time (individual operations)
        vendor_time = 0.0
        for setting_name in vendor_settings:
            method_info = self.setting_methods.get(setting_name)
            if method_info:
                vendor_time += method_info.estimated_time_vendor
            else:
                vendor_time += 60.0  # Default estimate for unknown settings

        # Add vendor tool startup/overhead time
        if vendor_settings:
            vendor_time += 30.0  # Tool initialization overhead

        return {
            "redfish_total_time": redfish_time,
            "vendor_tool_total_time": vendor_time,
            "estimated_total_time": max(
                redfish_time, vendor_time
            ),  # Parallel execution
            "redfish_batch_count": redfish_batches,
            "vendor_setting_count": len(vendor_settings),
        }

    def _create_batch_groups(
        self,
        redfish_settings: Dict[str, Any],
        vendor_settings: Dict[str, Any],
        batch_size: int,
    ) -> List[Dict[str, Any]]:
        """Create optimized batch groups for execution"""
        batch_groups = []

        # Create Redfish batches
        if redfish_settings:
            redfish_items = list(redfish_settings.items())
            for i in range(0, len(redfish_items), batch_size):
                batch = dict(redfish_items[i : i + batch_size])
                batch_groups.append(
                    {
                        "method": "redfish",
                        "settings": batch,
                        "estimated_time": self.performance_hints.get(
                            "redfish_timeout", 30
                        ),
                        "batch_size": len(batch),
                    }
                )

        # Create vendor tool batches (typically individual operations)
        for setting_name, setting_value in vendor_settings.items():
            method_info = self.setting_methods.get(setting_name)
            estimated_time = method_info.estimated_time_vendor if method_info else 60.0

            batch_groups.append(
                {
                    "method": "vendor_tool",
                    "settings": {setting_name: setting_value},
                    "estimated_time": estimated_time,
                    "batch_size": 1,
                }
            )

        return batch_groups

    def get_method_statistics(self) -> Dict[str, Any]:
        """Get statistics about configured method preferences"""
        stats = {
            "total_settings": len(self.setting_methods),
            "redfish_preferred": 0,
            "redfish_fallback": 0,
            "vendor_only": 0,
            "avg_redfish_time": 0.0,
            "avg_vendor_time": 0.0,
        }

        redfish_times = []
        vendor_times = []

        for method_info in self.setting_methods.values():
            if method_info.priority == SettingPriority.REDFISH_PREFERRED:
                stats["redfish_preferred"] += 1
            elif method_info.priority == SettingPriority.REDFISH_FALLBACK:
                stats["redfish_fallback"] += 1
            elif method_info.priority == SettingPriority.VENDOR_ONLY:
                stats["vendor_only"] += 1

            if method_info.estimated_time_redfish > 0:
                redfish_times.append(method_info.estimated_time_redfish)
            if method_info.estimated_time_vendor > 0:
                vendor_times.append(method_info.estimated_time_vendor)

        if redfish_times:
            stats["avg_redfish_time"] = sum(redfish_times) / len(redfish_times)
        if vendor_times:
            stats["avg_vendor_time"] = sum(vendor_times) / len(vendor_times)

        return stats

    def validate_redfish_capabilities(
        self, available_settings: Set[str]
    ) -> Dict[str, bool]:
        """
        Validate which configured Redfish settings are actually available.

        Args:
            available_settings: Set of BIOS setting names available via Redfish

        Returns:
            Dictionary mapping setting names to availability status
        """
        validation_results = {}

        for setting_name, method_info in self.setting_methods.items():
            if method_info.priority in [
                SettingPriority.REDFISH_PREFERRED,
                SettingPriority.REDFISH_FALLBACK,
            ]:
                validation_results[setting_name] = setting_name in available_settings

        return validation_results
