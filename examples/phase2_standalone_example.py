"""
Phase 2 Enhanced BIOS Configuration - Standalone Integration Example

This example demonstrates the Phase 2 enhanced decision logic capabilities
without requiring the full hwautomation module imports.
"""

import yaml
from pathlib import Path
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple, Set


class ConfigMethod(Enum):
    """BIOS configuration methods"""
    REDFISH = "redfish"
    VENDOR_TOOL = "vendor_tool"
    HYBRID = "hybrid"


class SettingPriority(Enum):
    """Setting priority levels for method selection"""
    REDFISH_PREFERRED = "redfish_preferred"
    REDFISH_FALLBACK = "redfish_fallback"
    VENDOR_ONLY = "vendor_only"
    UNKNOWN = "unknown"


@dataclass
class SettingMethodInfo:
    """Information about how to handle a specific BIOS setting"""
    setting_name: str
    priority: SettingPriority
    description: str
    estimated_time_redfish: float = 0.0
    estimated_time_vendor: float = 0.0
    success_rate_redfish: float = 0.0
    success_rate_vendor: float = 0.0
    requires_reboot: bool = False
    complexity_score: int = 1


@dataclass
class MethodSelectionResult:
    """Result of method selection analysis"""
    redfish_settings: Dict[str, Any]
    vendor_settings: Dict[str, Any]
    unknown_settings: Dict[str, Any]
    method_rationale: Dict[str, str]
    performance_estimate: Dict[str, float]
    batch_groups: List[Dict[str, Any]]


class BiosSettingMethodSelector:
    """Intelligent BIOS setting method selector (Phase 2)"""
    
    def __init__(self, device_config: Dict[str, Any]):
        self.device_config = device_config
        self.setting_methods = self._parse_setting_methods()
        self.performance_hints = device_config.get('method_performance', {})
        
    def _parse_setting_methods(self) -> Dict[str, SettingMethodInfo]:
        """Parse setting method configuration"""
        methods = {}
        bios_setting_methods = self.device_config.get('bios_setting_methods', {})
        
        # Parse redfish_preferred settings
        redfish_preferred = bios_setting_methods.get('redfish_preferred', {})
        for setting, description in redfish_preferred.items():
            methods[setting] = SettingMethodInfo(
                setting_name=setting,
                priority=SettingPriority.REDFISH_PREFERRED,
                description=description,
                estimated_time_redfish=2.0,
                estimated_time_vendor=30.0,
                success_rate_redfish=0.95,
                success_rate_vendor=0.98,
                complexity_score=2
            )
        
        # Parse redfish_fallback settings
        redfish_fallback = bios_setting_methods.get('redfish_fallback', {})
        for setting, description in redfish_fallback.items():
            methods[setting] = SettingMethodInfo(
                setting_name=setting,
                priority=SettingPriority.REDFISH_FALLBACK,
                description=description,
                estimated_time_redfish=5.0,
                estimated_time_vendor=20.0,
                success_rate_redfish=0.80,
                success_rate_vendor=0.98,
                complexity_score=4
            )
        
        # Parse vendor_only settings
        vendor_only = bios_setting_methods.get('vendor_only', {})
        for setting, description in vendor_only.items():
            methods[setting] = SettingMethodInfo(
                setting_name=setting,
                priority=SettingPriority.VENDOR_ONLY,
                description=description,
                estimated_time_redfish=0.0,
                estimated_time_vendor=60.0,
                success_rate_redfish=0.0,
                success_rate_vendor=0.95,
                requires_reboot=True,
                complexity_score=8
            )
        
        return methods
    
    def analyze_settings(self, settings_to_apply: Dict[str, Any], 
                        prefer_performance: bool = True,
                        max_redfish_batch: Optional[int] = None) -> MethodSelectionResult:
        """Analyze settings and determine optimal method for each"""
        redfish_settings = {}
        vendor_settings = {}
        unknown_settings = {}
        method_rationale = {}
        
        if max_redfish_batch is None:
            max_redfish_batch = self.performance_hints.get('redfish_batch_size', 10)
        
        for setting_name, setting_value in settings_to_apply.items():
            method_info = self.setting_methods.get(setting_name)
            
            if method_info is None:
                # Unknown setting - analyze and decide
                method, reason = self._analyze_unknown_setting(setting_name, setting_value)
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
        
        # Create batch groups
        batch_groups = self._create_batch_groups(
            redfish_settings, vendor_settings, max_redfish_batch
        )
        
        return MethodSelectionResult(
            redfish_settings=redfish_settings,
            vendor_settings=vendor_settings,
            unknown_settings=unknown_settings,
            method_rationale=method_rationale,
            performance_estimate=performance_estimate,
            batch_groups=batch_groups
        )
    
    def _select_method_for_setting(self, method_info: SettingMethodInfo, 
                                  prefer_performance: bool) -> Tuple[ConfigMethod, str]:
        """Select the best method for a known setting"""
        
        if method_info.priority == SettingPriority.REDFISH_PREFERRED:
            return ConfigMethod.REDFISH, f"Redfish preferred for {method_info.setting_name} - {method_info.description}"
        
        elif method_info.priority == SettingPriority.VENDOR_ONLY:
            return ConfigMethod.VENDOR_TOOL, f"Vendor tool required for {method_info.setting_name} - {method_info.description}"
        
        elif method_info.priority == SettingPriority.REDFISH_FALLBACK:
            if prefer_performance:
                if method_info.estimated_time_redfish < method_info.estimated_time_vendor:
                    return ConfigMethod.REDFISH, f"Redfish chosen for performance ({method_info.estimated_time_redfish}s vs {method_info.estimated_time_vendor}s)"
                else:
                    return ConfigMethod.VENDOR_TOOL, f"Vendor tool chosen for performance ({method_info.estimated_time_vendor}s vs {method_info.estimated_time_redfish}s)"
            else:
                if method_info.success_rate_redfish >= method_info.success_rate_vendor:
                    return ConfigMethod.REDFISH, f"Redfish chosen for reliability ({method_info.success_rate_redfish*100}% success rate)"
                else:
                    return ConfigMethod.VENDOR_TOOL, f"Vendor tool chosen for reliability ({method_info.success_rate_vendor*100}% success rate)"
        
        return ConfigMethod.VENDOR_TOOL, f"Default fallback to vendor tool for {method_info.setting_name}"
    
    def _analyze_unknown_setting(self, setting_name: str, setting_value: Any) -> Tuple[ConfigMethod, str]:
        """Analyze unknown setting and guess best method"""
        setting_lower = setting_name.lower()
        
        redfish_indicators = [
            'boot', 'power', 'secure', 'pxe', 'wake', 'timeout', 'turbo', 
            'speedstep', 'eist', 'profile', 'quiet'
        ]
        
        vendor_indicators = [
            'microcode', 'timing', 'advanced', 'overclock', 'fan', 'monitor',
            'update', 'complex', 'vendor', 'oem', 'proprietary'
        ]
        
        if any(indicator in setting_lower for indicator in redfish_indicators):
            return ConfigMethod.REDFISH, f"Unknown setting '{setting_name}' matches Redfish patterns"
        
        if any(indicator in setting_lower for indicator in vendor_indicators):
            return ConfigMethod.VENDOR_TOOL, f"Unknown setting '{setting_name}' matches vendor-only patterns"
        
        if isinstance(setting_value, (dict, list)):
            return ConfigMethod.VENDOR_TOOL, f"Unknown setting '{setting_name}' has complex value type"
        
        return ConfigMethod.VENDOR_TOOL, f"Unknown setting '{setting_name}' - defaulting to vendor tool for safety"
    
    def _calculate_performance_estimate(self, redfish_settings: Dict[str, Any],
                                       vendor_settings: Dict[str, Any],
                                       redfish_batch_size: int) -> Dict[str, float]:
        """Calculate estimated execution time"""
        redfish_count = len(redfish_settings)
        redfish_batches = (redfish_count + redfish_batch_size - 1) // redfish_batch_size if redfish_count > 0 else 0
        redfish_time = redfish_batches * self.performance_hints.get('redfish_timeout', 30)
        
        vendor_time = 0.0
        for setting_name in vendor_settings:
            method_info = self.setting_methods.get(setting_name)
            if method_info:
                vendor_time += method_info.estimated_time_vendor
            else:
                vendor_time += 60.0
        
        if vendor_settings:
            vendor_time += 30.0  # Tool initialization overhead
        
        return {
            'redfish_total_time': redfish_time,
            'vendor_tool_total_time': vendor_time,
            'estimated_total_time': max(redfish_time, vendor_time),
            'redfish_batch_count': redfish_batches,
            'vendor_setting_count': len(vendor_settings)
        }
    
    def _create_batch_groups(self, redfish_settings: Dict[str, Any],
                           vendor_settings: Dict[str, Any],
                           batch_size: int) -> List[Dict[str, Any]]:
        """Create optimized batch groups"""
        batch_groups = []
        
        if redfish_settings:
            redfish_items = list(redfish_settings.items())
            for i in range(0, len(redfish_items), batch_size):
                batch = dict(redfish_items[i:i + batch_size])
                batch_groups.append({
                    'method': 'redfish',
                    'settings': batch,
                    'estimated_time': self.performance_hints.get('redfish_timeout', 30),
                    'batch_size': len(batch)
                })
        
        for setting_name, setting_value in vendor_settings.items():
            method_info = self.setting_methods.get(setting_name)
            estimated_time = method_info.estimated_time_vendor if method_info else 60.0
            
            batch_groups.append({
                'method': 'vendor_tool',
                'settings': {setting_name: setting_value},
                'estimated_time': estimated_time,
                'batch_size': 1
            })
        
        return batch_groups


def load_device_config(device_type="a1.c5.large"):
    """Load device configuration"""
    config_file = Path(__file__).parent.parent / "configs" / "bios" / "device_mappings.yaml"
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    return config.get('device_types', {}).get(device_type)


def main():
    """Phase 2 Integration Example"""
    print("=" * 80)
    print("PHASE 2 ENHANCED BIOS CONFIGURATION - INTEGRATION EXAMPLE")
    print("=" * 80)
    
    # Configuration
    device_type = "a1.c5.large"
    target_ip = "192.168.1.100"
    
    print(f"🎯 Target: {target_ip}")
    print(f"📋 Device Type: {device_type}")
    
    # Load device configuration
    device_config = load_device_config(device_type)
    method_selector = BiosSettingMethodSelector(device_config)
    
    # Example BIOS settings
    bios_settings = {
        "BootMode": "UEFI",
        "SecureBoot": "Enabled",
        "PowerProfile": "Performance",
        "IntelHyperThreadingTech": "Enabled",
        "CPUMicrocodeUpdate": "Enabled",
        "MemoryTimingAdvanced": "Auto",
        "CustomSetting": "TestValue"
    }
    
    print(f"\n📝 BIOS Settings to Apply ({len(bios_settings)}):")
    for setting, value in bios_settings.items():
        print(f"   - {setting}: {value}")
    
    # Phase 2 Analysis
    print(f"\n🧠 PHASE 2 ANALYSIS: Intelligent Method Selection")
    print("-" * 60)
    
    analysis = method_selector.analyze_settings(
        bios_settings, 
        prefer_performance=True,
        max_redfish_batch=5
    )
    
    print(f"📊 Method Selection Results:")
    print(f"   Redfish settings: {len(analysis.redfish_settings)}")
    print(f"   Vendor tool settings: {len(analysis.vendor_settings)}")
    print(f"   Unknown settings: {len(analysis.unknown_settings)}")
    
    # Show detailed rationale
    print(f"\n📋 Detailed Method Selection:")
    for setting, value in bios_settings.items():
        if setting in analysis.redfish_settings:
            method = "🔵 Redfish"
        elif setting in analysis.vendor_settings:
            method = "🟠 Vendor Tool"
        else:
            method = "❓ Unknown"
        
        reason = analysis.method_rationale.get(setting, "No reason provided")
        print(f"   {method} {setting}: {reason}")
    
    # Performance estimation
    perf = analysis.performance_estimate
    print(f"\n⏱️  Performance Estimation:")
    print(f"   Total estimated time: {perf.get('estimated_total_time', 0):.1f}s (parallel)")
    print(f"   Redfish time: {perf.get('redfish_total_time', 0):.1f}s ({perf.get('redfish_batch_count', 0)} batches)")
    print(f"   Vendor tool time: {perf.get('vendor_tool_total_time', 0):.1f}s ({perf.get('vendor_setting_count', 0)} settings)")
    
    # Execution plan
    print(f"\n🚀 PHASE 2 EXECUTION PLAN:")
    print("-" * 60)
    
    print(f"📦 Batch Execution Order:")
    for i, batch in enumerate(analysis.batch_groups):
        method = batch['method']
        settings = batch['settings']
        estimated_time = batch['estimated_time']
        
        print(f"   Batch {i+1}: {method.upper()}")
        print(f"      Settings: {list(settings.keys())}")
        print(f"      Estimated time: {estimated_time:.1f}s")
        print()
    
    # Integration code
    print(f"🔧 PHASE 2 INTEGRATION CODE:")
    print("-" * 60)
    
    integration_code = '''
# Production Integration Example:

def apply_bios_with_phase2(device_type, target_ip, username, password):
    """Apply BIOS configuration using Phase 2 enhanced logic"""
    
    from hwautomation.hardware.bios_config import BiosConfigManager
    
    manager = BiosConfigManager()
    
    # Phase 2: Intelligent per-setting method selection
    result = manager.apply_bios_config_phase2(
        device_type=device_type,
        target_ip=target_ip,
        username=username,
        password=password,
        dry_run=False,  # Set to True for testing
        prefer_performance=True  # Or False for reliability
    )
    
    return result
    '''
    
    print(integration_code)
    
    # Benefits summary
    print(f"🎯 PHASE 2 KEY BENEFITS:")
    print("-" * 60)
    print(f"✅ Per-setting optimization (not all-or-nothing)")
    print(f"✅ Performance vs reliability tuning")
    print(f"✅ Intelligent unknown setting handling")
    print(f"✅ Parallel execution (Redfish + vendor tools)")
    print(f"✅ Batch optimization for efficiency")
    print(f"✅ Comprehensive performance estimation")
    print(f"✅ Configuration-driven decision logic")
    print(f"✅ Automatic capability validation")
    
    print(f"\n🚀 Phase 2 is ready for production deployment!")


if __name__ == "__main__":
    main()
