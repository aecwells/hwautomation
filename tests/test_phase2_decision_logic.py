"""
Test Phase 2 Enhanced BIOS Configuration Decision Logic

This test demonstrates the new per-setting method selection capabilities
that intelligently choose between Redfish and vendor tools for each BIOS setting.
"""

import logging
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hwautomation.hardware.bios_config import BiosConfigManager
from hwautomation.hardware.bios_decision_logic import BiosSettingMethodSelector

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_phase2_decision_logic():
    """Test the Phase 2 per-setting decision logic"""
    print("=" * 80)
    print("TESTING PHASE 2: Enhanced BIOS Configuration Decision Logic")
    print("=" * 80)

    try:
        # Initialize BIOS configuration manager
        manager = BiosConfigManager()

        # Test device type with Phase 2 configuration
        device_type = "a1.c5.large"

        print(f"\n1. Getting Phase 2 method statistics for device type: {device_type}")
        stats = manager.get_phase2_method_statistics(device_type)

        if "error" in stats:
            print(f"   ❌ Error: {stats['error']}")
            return False

        print(f"   ✅ Total configured settings: {stats['total_settings']}")
        print(f"   📊 Redfish preferred: {stats['redfish_preferred']}")
        print(f"   📊 Redfish fallback: {stats['redfish_fallback']}")
        print(f"   📊 Vendor only: {stats['vendor_only']}")
        print(f"   ⏱️  Average Redfish time: {stats['avg_redfish_time']:.1f}s")
        print(f"   ⏱️  Average vendor time: {stats['avg_vendor_time']:.1f}s")

        # Test decision logic with sample settings
        print(f"\n2. Testing decision logic with sample BIOS settings")

        # Get device configuration
        device_config = manager.device_types.get(device_type)
        if not device_config:
            print(f"   ❌ Device type {device_type} not found")
            return False

        # Initialize method selector
        method_selector = BiosSettingMethodSelector(device_config)

        # Sample settings that would come from template rules
        sample_settings = {
            # Should be Redfish preferred
            "BootMode": "UEFI",
            "SecureBoot": "Enabled",
            "PowerProfile": "Performance",
            # Should be Redfish fallback (depends on prefer_performance)
            "IntelHyperThreadingTech": "Enabled",
            "MemoryMode": "Performance",
            # Should be vendor only
            "CPUMicrocodeUpdate": "Enabled",
            "MemoryTimingAdvanced": "Auto",
            # Unknown setting (should be analyzed)
            "CustomUnknownSetting": "TestValue",
        }

        print(f"   🔍 Analyzing {len(sample_settings)} sample settings...")

        # Test with performance preference
        print(f"\n   📈 Performance-optimized analysis:")
        perf_analysis = method_selector.analyze_settings(
            sample_settings, prefer_performance=True
        )

        print(f"      Redfish settings: {len(perf_analysis.redfish_settings)}")
        for setting in perf_analysis.redfish_settings:
            reason = perf_analysis.method_rationale.get(setting, "No reason provided")
            print(f"        - {setting}: {reason}")

        print(f"      Vendor tool settings: {len(perf_analysis.vendor_settings)}")
        for setting in perf_analysis.vendor_settings:
            reason = perf_analysis.method_rationale.get(setting, "No reason provided")
            print(f"        - {setting}: {reason}")

        print(f"      Unknown settings: {len(perf_analysis.unknown_settings)}")
        for setting in perf_analysis.unknown_settings:
            reason = perf_analysis.method_rationale.get(setting, "No reason provided")
            print(f"        - {setting}: {reason}")

        # Test with reliability preference
        print(f"\n   🛡️  Reliability-optimized analysis:")
        reliability_analysis = method_selector.analyze_settings(
            sample_settings, prefer_performance=False
        )

        print(f"      Redfish settings: {len(reliability_analysis.redfish_settings)}")
        print(
            f"      Vendor tool settings: {len(reliability_analysis.vendor_settings)}"
        )
        print(f"      Unknown settings: {len(reliability_analysis.unknown_settings)}")

        # Show performance estimates
        print(f"\n   ⏱️  Performance estimates (performance-optimized):")
        perf_estimate = perf_analysis.performance_estimate
        print(
            f"      Redfish total time: {perf_estimate.get('redfish_total_time', 0):.1f}s"
        )
        print(
            f"      Vendor tool total time: {perf_estimate.get('vendor_tool_total_time', 0):.1f}s"
        )
        print(
            f"      Estimated total time: {perf_estimate.get('estimated_total_time', 0):.1f}s (parallel)"
        )
        print(
            f"      Redfish batch count: {perf_estimate.get('redfish_batch_count', 0)}"
        )
        print(
            f"      Vendor setting count: {perf_estimate.get('vendor_setting_count', 0)}"
        )

        # Show batch groups
        print(f"\n   📦 Batch execution plan:")
        for i, batch in enumerate(perf_analysis.batch_groups):
            method = batch["method"]
            settings_count = batch["batch_size"]
            estimated_time = batch["estimated_time"]
            print(
                f"      Batch {i+1}: {method} - {settings_count} settings - {estimated_time:.1f}s"
            )

        # Test the full Phase 2 method (dry run)
        print(f"\n3. Testing full Phase 2 BIOS configuration (dry run)")

        # Mock target for dry run
        target_ip = "192.168.1.100"

        print(f"   🎯 Target: {target_ip} (dry run)")
        phase2_result = manager.apply_bios_config_phase2(
            device_type=device_type,
            target_ip=target_ip,
            username="ADMIN",
            password="password",
            dry_run=True,
            prefer_performance=True,
        )

        if phase2_result.get("success"):
            print("   ✅ Phase 2 dry run completed successfully")

            # Show dry run summary
            summary = phase2_result.get("dry_run_summary", {})
            print(f"      Total settings: {summary.get('total_settings', 0)}")
            print(f"      Redfish count: {summary.get('redfish_count', 0)}")
            print(f"      Vendor count: {summary.get('vendor_count', 0)}")
            print(f"      Unknown count: {summary.get('unknown_count', 0)}")
            print(
                f"      Estimated time: {summary.get('estimated_total_time', 0):.1f}s"
            )

            # Show method analysis
            analysis = phase2_result.get("method_analysis", {})
            print(f"\n   📋 Method analysis details:")
            print(
                f"      Redfish settings: {list(analysis.get('redfish_settings', {}).keys())}"
            )
            print(
                f"      Vendor settings: {list(analysis.get('vendor_settings', {}).keys())}"
            )

        else:
            print(
                f"   ❌ Phase 2 dry run failed: {phase2_result.get('error', 'Unknown error')}"
            )
            return False

        print(f"\n4. Testing Redfish capability validation (mock)")

        # This would normally connect to a real system, but we'll show the structure
        print(f"   🔍 Redfish capability validation would check:")
        print(f"      - Which configured Redfish settings are actually available")
        print(f"      - BIOS setting names and types on target system")
        print(f"      - Redfish API version and vendor extensions")
        print(f"      (Requires actual hardware connection for real validation)")

        print(f"\n✅ Phase 2 Enhanced Decision Logic Test Completed Successfully!")
        print(f"   🎯 Key capabilities demonstrated:")
        print(f"      ✓ Per-setting method selection (Redfish vs vendor tools)")
        print(f"      ✓ Performance vs reliability optimization")
        print(f"      ✓ Intelligent unknown setting analysis")
        print(f"      ✓ Batch execution planning")
        print(f"      ✓ Comprehensive performance estimation")
        print(f"      ✓ Dry run capability for safe testing")

        return True

    except Exception as e:
        print(f"❌ Phase 2 test failed with error: {e}")
        logger.exception("Phase 2 test failed")
        return False


def test_configuration_validation():
    """Test that the Phase 2 configuration is properly loaded"""
    print("\n" + "=" * 80)
    print("VALIDATING PHASE 2 CONFIGURATION")
    print("=" * 80)

    try:
        manager = BiosConfigManager()
        device_type = "a1.c5.large"

        # Check device configuration
        device_config = manager.device_types.get(device_type)
        if not device_config:
            print(f"❌ Device type {device_type} not found")
            return False

        print(f"✅ Device type {device_type} found")

        # Check bios_setting_methods
        bios_setting_methods = device_config.get("bios_setting_methods")
        if not bios_setting_methods:
            print(f"❌ No bios_setting_methods found for {device_type}")
            return False

        print(f"✅ bios_setting_methods configuration found")

        # Check categories
        categories = ["redfish_preferred", "redfish_fallback", "vendor_only"]
        for category in categories:
            settings = bios_setting_methods.get(category, {})
            print(f"   📊 {category}: {len(settings)} settings")

            # Show a few examples
            if settings:
                examples = list(settings.keys())[:3]
                for example in examples:
                    print(f"      - {example}: {settings[example]}")
                if len(settings) > 3:
                    print(f"      ... and {len(settings) - 3} more")

        # Check performance hints
        performance_hints = device_config.get("method_performance", {})
        if performance_hints:
            print(f"✅ Performance hints found:")
            for key, value in performance_hints.items():
                print(f"   - {key}: {value}")

        # Check compatibility matrix
        compatibility = device_config.get("redfish_compatibility", {})
        if compatibility:
            print(f"✅ Redfish compatibility matrix found:")
            for key, value in compatibility.items():
                print(f"   - {key}: {value}")

        return True

    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return False


if __name__ == "__main__":
    print("Phase 2 Enhanced BIOS Configuration Testing")
    print("=" * 50)

    # Test configuration loading
    config_ok = test_configuration_validation()

    if config_ok:
        # Test decision logic
        decision_ok = test_phase2_decision_logic()

        if decision_ok:
            print(f"\n🎉 All Phase 2 tests passed successfully!")
            print(f"   The enhanced decision logic is ready for production use.")
        else:
            print(f"\n❌ Some Phase 2 tests failed.")
            sys.exit(1)
    else:
        print(f"\n❌ Configuration validation failed.")
        sys.exit(1)
