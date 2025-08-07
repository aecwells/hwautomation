"""
Phase 2 Enhanced BIOS Configuration - Integration Example

This example demonstrates how to use the new Phase 2 enhanced decision logic
for intelligent per-setting method selection in production workflows.
"""

import sys
from pathlib import Path
import yaml
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the src directory to the path for isolated testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def load_device_config(device_type="a1.c5.large"):
    """Load device configuration for testing"""
    config_file = Path(__file__).parent.parent / "configs" / "bios" / "device_mappings.yaml"
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    return config.get('device_types', {}).get(device_type)


def example_phase2_workflow():
    """Example of Phase 2 workflow integration"""
    print("=" * 80)
    print("PHASE 2 ENHANCED BIOS CONFIGURATION - INTEGRATION EXAMPLE")
    print("=" * 80)
    
    # Import decision logic
    try:
        from hwautomation.hardware.bios_decision_logic import BiosSettingMethodSelector
    except ImportError:
        # Load in isolation mode
        decision_logic_file = Path(__file__).parent.parent / "src" / "hwautomation" / "hardware" / "bios_decision_logic.py"
        with open(decision_logic_file, 'r') as f:
            exec(f.read(), globals())
    
    # Configuration
    device_type = "a1.c5.large"
    target_ip = "192.168.1.100"
    
    print(f"🎯 Target: {target_ip}")
    print(f"📋 Device Type: {device_type}")
    
    # Load device configuration
    device_config = load_device_config(device_type)
    if not device_config:
        print(f"❌ Device configuration not found for {device_type}")
        return False
    
    # Initialize method selector
    method_selector = BiosSettingMethodSelector(device_config)
    
    # Example BIOS settings to apply (would come from template rules in real scenario)
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
    
    # =========================================================================
    # PHASE 2 ANALYSIS: Determine optimal method for each setting
    # =========================================================================
    
    print(f"\n🧠 PHASE 2 ANALYSIS: Intelligent Method Selection")
    print("-" * 60)
    
    # Analyze for performance optimization
    analysis = method_selector.analyze_settings(
        bios_settings, 
        prefer_performance=True,
        max_redfish_batch=5
    )
    
    print(f"📊 Method Selection Results:")
    print(f"   Redfish settings: {len(analysis.redfish_settings)}")
    print(f"   Vendor tool settings: {len(analysis.vendor_settings)}")
    print(f"   Unknown settings: {len(analysis.unknown_settings)}")
    
    # Show detailed method rationale
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
    print(f"   Total estimated time: {perf.get('estimated_total_time', 0):.1f}s (parallel execution)")
    print(f"   Redfish time: {perf.get('redfish_total_time', 0):.1f}s ({perf.get('redfish_batch_count', 0)} batches)")
    print(f"   Vendor tool time: {perf.get('vendor_tool_total_time', 0):.1f}s ({perf.get('vendor_setting_count', 0)} settings)")
    
    # =========================================================================
    # PHASE 2 EXECUTION PLAN: Optimized batch execution
    # =========================================================================
    
    print(f"\n🚀 PHASE 2 EXECUTION PLAN: Optimized Batch Processing")
    print("-" * 60)
    
    print(f"📦 Batch Execution Order:")
    total_time = 0
    for i, batch in enumerate(analysis.batch_groups):
        method = batch['method']
        settings = batch['settings']
        estimated_time = batch['estimated_time']
        total_time += estimated_time
        
        print(f"   Batch {i+1}: {method.upper()}")
        print(f"      Settings: {list(settings.keys())}")
        print(f"      Estimated time: {estimated_time:.1f}s")
        print(f"      Values: {settings}")
        print()
    
    print(f"📈 Execution Benefits:")
    print(f"   ✓ Parallel Redfish + vendor tool execution")
    print(f"   ✓ Batched Redfish operations for efficiency")
    print(f"   ✓ Per-setting optimization based on characteristics")
    print(f"   ✓ Automatic fallback handling")
    
    # =========================================================================
    # PHASE 2 INTEGRATION: How to use in production code
    # =========================================================================
    
    print(f"\n🔧 PHASE 2 INTEGRATION EXAMPLE:")
    print("-" * 60)
    
    integration_code = '''
    # In your orchestration workflow:
    
    from hwautomation.hardware.bios_config import BiosConfigManager
    
    def apply_bios_configuration_phase2(device_type, target_ip, username, password):
        """Apply BIOS configuration using Phase 2 enhanced logic"""
        
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
        
        if result['success']:
            print(f"✅ BIOS configuration applied successfully")
            print(f"   Redfish results: {result['redfish_results']}")
            print(f"   Vendor results: {result['vendor_results']}")
            print(f"   Performance: {result['performance_estimate']}")
        else:
            print(f"❌ BIOS configuration failed: {result['error']}")
            
        return result
    '''
    
    print(integration_code)
    
    # =========================================================================
    # PHASE 2 VALIDATION: Capability checking
    # =========================================================================
    
    print(f"\n🔍 PHASE 2 VALIDATION: Redfish Capability Assessment")
    print("-" * 60)
    
    # Simulate available Redfish settings (in production, this would come from target system)
    mock_available_redfish = {
        "BootMode", "SecureBoot", "PowerProfile", "IntelHyperThreadingTech"
    }
    
    validation = method_selector.validate_redfish_capabilities(mock_available_redfish)
    
    print(f"🔍 Redfish Capability Validation:")
    available_count = sum(1 for available in validation.values() if available)
    total_redfish_settings = len(validation)
    
    print(f"   Available: {available_count}/{total_redfish_settings} configured Redfish settings")
    
    if available_count < total_redfish_settings:
        print(f"   ⚠️  Some configured Redfish settings are not available on target system")
        print(f"   💡 Automatic fallback to vendor tools will be used")
    
    return True


def example_comparison_phase1_vs_phase2():
    """Compare Phase 1 vs Phase 2 approaches"""
    print(f"\n" + "=" * 80)
    print("PHASE 1 vs PHASE 2 COMPARISON")
    print("=" * 80)
    
    print(f"📊 PHASE 1 (Basic Redfish Integration):")
    print(f"   ❌ All-or-nothing method selection")
    print(f"   ❌ Single method for all settings")
    print(f"   ❌ No per-setting optimization")
    print(f"   ❌ Limited performance tuning")
    print(f"   ✅ Simple implementation")
    print(f"   ✅ Reliable fallback")
    
    print(f"\n📊 PHASE 2 (Enhanced Decision Logic):")
    print(f"   ✅ Per-setting method selection")
    print(f"   ✅ Intelligent optimization (performance vs reliability)")
    print(f"   ✅ Unknown setting analysis with heuristics")
    print(f"   ✅ Batch execution planning")
    print(f"   ✅ Comprehensive performance estimation")
    print(f"   ✅ Redfish capability validation")
    print(f"   ✅ Configuration-driven decision logic")
    print(f"   ✅ Parallel Redfish + vendor tool execution")
    
    print(f"\n🎯 When to Use Each Phase:")
    print(f"   Phase 1: Simple deployments, uniform hardware, basic requirements")
    print(f"   Phase 2: Complex deployments, mixed hardware, performance-critical environments")


if __name__ == "__main__":
    print("Phase 2 Enhanced BIOS Configuration Integration Example")
    print("=" * 70)
    
    try:
        # Run Phase 2 workflow example
        success = example_phase2_workflow()
        
        if success:
            # Show comparison
            example_comparison_phase1_vs_phase2()
            
            print(f"\n🎉 Phase 2 Integration Example Completed Successfully!")
            print(f"\n💡 Next Steps:")
            print(f"   1. Test with real hardware using dry_run=True")
            print(f"   2. Validate Redfish capabilities on target systems")
            print(f"   3. Customize device_mappings.yaml for your hardware")
            print(f"   4. Integrate into orchestration workflows")
            print(f"   5. Monitor performance and adjust batch sizes")
        
    except Exception as e:
        print(f"❌ Integration example failed: {e}")
        sys.exit(1)
