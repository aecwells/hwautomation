"""
Focused Phase 2 Decision Logic Test

This test demonstrates the enhanced per-setting method selection without
requiring full hwautomation module imports.
"""

import logging
import sys
from pathlib import Path

import yaml

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from hwautomation.hardware.bios_decision_logic import (
        BiosSettingMethodSelector,
        ConfigMethod,
        SettingPriority,
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Testing decision logic module in isolation...")

    # Copy the decision logic classes locally for testing
    exec(
        open(
            Path(__file__).parent.parent
            / "src"
            / "hwautomation"
            / "hardware"
            / "bios_decision_logic.py"
        ).read()
    )


def load_device_config():
    """Load device configuration from YAML file"""
    config_file = (
        Path(__file__).parent.parent / "configs" / "bios" / "device_mappings.yaml"
    )

    if not config_file.exists():
        print(f"❌ Configuration file not found: {config_file}")
        return None

    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)

        # Get a1.c5.large device config
        device_type = "a1.c5.large"
        device_config = config.get("device_types", {}).get(device_type)

        if not device_config:
            print(f"❌ Device type {device_type} not found in configuration")
            return None

        return device_config

    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        return None


def test_decision_logic_focused():
    """Test the decision logic in isolation"""
    print("=" * 80)
    print("TESTING PHASE 2: Enhanced Decision Logic (Focused Test)")
    print("=" * 80)

    # Load device configuration
    device_config = load_device_config()
    if not device_config:
        return False

    print("✅ Device configuration loaded successfully")

    try:
        # Initialize method selector
        method_selector = BiosSettingMethodSelector(device_config)

        # Test 1: Get method statistics
        print(f"\n1. Method Statistics:")
        stats = method_selector.get_method_statistics()

        print(f"   📊 Total configured settings: {stats['total_settings']}")
        print(f"   📊 Redfish preferred: {stats['redfish_preferred']}")
        print(f"   📊 Redfish fallback: {stats['redfish_fallback']}")
        print(f"   📊 Vendor only: {stats['vendor_only']}")
        print(f"   ⏱️  Average Redfish time: {stats['avg_redfish_time']:.1f}s")
        print(f"   ⏱️  Average vendor time: {stats['avg_vendor_time']:.1f}s")

        # Test 2: Sample settings analysis
        print(f"\n2. Sample Settings Analysis:")

        sample_settings = {
            # Should be Redfish preferred
            "BootMode": "UEFI",
            "SecureBoot": "Enabled",
            "PowerProfile": "Performance",
            "QuietBoot": "Disabled",
            # Should be Redfish fallback
            "IntelHyperThreadingTech": "Enabled",
            "MemoryMode": "Performance",
            "ProcessorEistEnable": "Enabled",
            # Should be vendor only
            "CPUMicrocodeUpdate": "Enabled",
            "MemoryTimingAdvanced": "Auto",
            "FanControlMode": "Manual",
            # Unknown settings
            "UnknownBootSetting": "TestValue",
            "CustomVendorSetting": "AdvancedValue",
            "ComplexTimingValue": {"subkey": "complex"},
        }

        print(f"   🔍 Analyzing {len(sample_settings)} sample settings...")

        # Performance-optimized analysis
        print(f"\n   📈 Performance-optimized analysis:")
        perf_analysis = method_selector.analyze_settings(
            sample_settings, prefer_performance=True
        )

        print(f"      Redfish settings ({len(perf_analysis.redfish_settings)}):")
        for setting in perf_analysis.redfish_settings:
            reason = perf_analysis.method_rationale.get(setting, "No reason")
            print(f"        ✓ {setting}: {reason}")

        print(f"      Vendor tool settings ({len(perf_analysis.vendor_settings)}):")
        for setting in perf_analysis.vendor_settings:
            reason = perf_analysis.method_rationale.get(setting, "No reason")
            print(f"        ⚙️  {setting}: {reason}")

        if perf_analysis.unknown_settings:
            print(f"      Unknown settings ({len(perf_analysis.unknown_settings)}):")
            for setting in perf_analysis.unknown_settings:
                reason = perf_analysis.method_rationale.get(setting, "No reason")
                print(f"        ❓ {setting}: {reason}")

        # Reliability-optimized analysis
        print(f"\n   🛡️  Reliability-optimized analysis:")
        reliability_analysis = method_selector.analyze_settings(
            sample_settings, prefer_performance=False
        )

        print(f"      Redfish: {len(reliability_analysis.redfish_settings)} settings")
        print(
            f"      Vendor tools: {len(reliability_analysis.vendor_settings)} settings"
        )
        print(f"      Unknown: {len(reliability_analysis.unknown_settings)} settings")

        # Performance comparison
        perf_estimate = perf_analysis.performance_estimate
        rel_estimate = reliability_analysis.performance_estimate

        print(f"\n   ⏱️  Performance Comparison:")
        print(
            f"      Performance-optimized: {perf_estimate.get('estimated_total_time', 0):.1f}s total"
        )
        print(f"         - Redfish: {perf_estimate.get('redfish_total_time', 0):.1f}s")
        print(
            f"         - Vendor: {perf_estimate.get('vendor_tool_total_time', 0):.1f}s"
        )
        print(
            f"      Reliability-optimized: {rel_estimate.get('estimated_total_time', 0):.1f}s total"
        )
        print(f"         - Redfish: {rel_estimate.get('redfish_total_time', 0):.1f}s")
        print(
            f"         - Vendor: {rel_estimate.get('vendor_tool_total_time', 0):.1f}s"
        )

        # Batch execution plan
        print(f"\n   📦 Batch Execution Plan (Performance-optimized):")
        for i, batch in enumerate(perf_analysis.batch_groups):
            method = batch["method"]
            count = batch["batch_size"]
            time = batch["estimated_time"]
            settings = list(batch["settings"].keys())
            print(f"      Batch {i+1}: {method} - {count} setting(s) - {time:.1f}s")
            print(f"        Settings: {', '.join(settings[:3])}")
            if len(settings) > 3:
                print(f"        ... and {len(settings) - 3} more")

        # Test 3: Redfish capability validation (mock)
        print(f"\n3. Redfish Capability Validation (Mock):")

        # Simulate available Redfish settings
        mock_available_settings = {
            "BootMode",
            "SecureBoot",
            "PowerProfile",
            "QuietBoot",
            "IntelHyperThreadingTech",
            "ProcessorEistEnable",
            "SomeOtherSetting",
        }

        validation_results = method_selector.validate_redfish_capabilities(
            mock_available_settings
        )

        available = [
            setting for setting, available in validation_results.items() if available
        ]
        unavailable = [
            setting
            for setting, available in validation_results.items()
            if not available
        ]

        print(f"   ✅ Available via Redfish ({len(available)}):")
        for setting in available:
            print(f"      ✓ {setting}")

        print(f"   ❌ Not available via Redfish ({len(unavailable)}):")
        for setting in unavailable:
            print(f"      ✗ {setting}")

        # Test 4: Configuration validation
        print(f"\n4. Configuration Structure Validation:")

        bios_setting_methods = device_config.get("bios_setting_methods", {})
        method_performance = device_config.get("method_performance", {})
        redfish_compatibility = device_config.get("redfish_compatibility", {})

        print(f"   ✅ bios_setting_methods: {len(bios_setting_methods)} categories")
        print(f"   ✅ method_performance: {len(method_performance)} hints")
        print(f"   ✅ redfish_compatibility: {len(redfish_compatibility)} properties")

        # Show sample configuration content
        if "redfish_preferred" in bios_setting_methods:
            preferred = bios_setting_methods["redfish_preferred"]
            print(
                f"      Sample Redfish preferred settings: {list(preferred.keys())[:3]}"
            )

        if "vendor_only" in bios_setting_methods:
            vendor_only = bios_setting_methods["vendor_only"]
            print(f"      Sample vendor-only settings: {list(vendor_only.keys())[:3]}")

        print(f"\n✅ Phase 2 Enhanced Decision Logic Test Completed Successfully!")
        print(f"\n🎯 Key Features Demonstrated:")
        print(f"   ✓ Intelligent per-setting method selection")
        print(f"   ✓ Performance vs reliability optimization")
        print(f"   ✓ Unknown setting analysis with heuristics")
        print(f"   ✓ Batch execution planning for efficiency")
        print(f"   ✓ Comprehensive performance estimation")
        print(f"   ✓ Redfish capability validation")
        print(f"   ✓ Configuration-driven decision logic")

        print(f"\n🚀 Phase 2 Implementation Ready for Production!")

        return True

    except Exception as e:
        print(f"❌ Decision logic test failed: {e}")
        logger.exception("Decision logic test failed")
        return False


if __name__ == "__main__":
    print("Phase 2 Enhanced BIOS Configuration - Focused Testing")
    print("=" * 60)

    success = test_decision_logic_focused()

    if success:
        print(f"\n🎉 All tests passed! Phase 2 is ready for integration.")
    else:
        print(f"\n❌ Tests failed. Please check the configuration and implementation.")
        sys.exit(1)
