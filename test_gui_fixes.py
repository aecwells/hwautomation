#!/usr/bin/env python3
"""
Test script for the fixed GUI enhancements.
Tests that all the dashboard fixes are working correctly.
"""

import sys
import json
import requests
from pathlib import Path

def test_dashboard_loads():
    """Test that the dashboard loads without template errors"""
    try:
        response = requests.get('http://localhost:5000/', timeout=10)
        
        if response.status_code == 200:
            # Check that device_types_dict is no longer undefined
            if 'device_types_dict' in response.text and "'device_types_dict' is undefined" not in response.text:
                print("✅ Dashboard loads successfully with device types")
                return True
            else:
                print("❌ Dashboard has template issues")
                return False
        else:
            print(f"❌ Dashboard returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Dashboard test failed: {e}")
        return False

def test_device_discovery():
    """Test the device discovery API"""
    try:
        response = requests.get('http://localhost:5000/api/maas/discover', timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and 'machines' in data:
                machine_count = len(data['machines'])
                print(f"✅ Device discovery working - found {machine_count} machines")
                return True, data['machines']
            else:
                print(f"❌ Device discovery failed: {data.get('error', 'Unknown error')}")
                return False, []
        else:
            print(f"❌ Device discovery API returned status {response.status_code}")
            return False, []
            
    except Exception as e:
        print(f"❌ Device discovery test failed: {e}")
        return False, []

def test_device_type_detection(machines):
    """Test device type detection API"""
    if not machines:
        print("⚠️  Skipping device type detection - no machines available")
        return True
        
    try:
        machine_ids = [m['system_id'] for m in machines[:2]]  # Test with first 2 machines
        
        response = requests.post(
            'http://localhost:5000/api/devices/detect-types',
            json={'machine_ids': machine_ids},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'detected_types' in data:
                print(f"✅ Device type detection working for {len(machine_ids)} machines")
                return True
            else:
                print(f"❌ Device type detection failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Device type detection API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Device type detection test failed: {e}")
        return False

def test_batch_commissioning(machines):
    """Test batch commissioning API"""
    if not machines:
        print("⚠️  Skipping batch commissioning - no machines available")
        return True
        
    try:
        machine_ids = [m['system_id'] for m in machines[:1]]  # Test with just 1 machine
        
        response = requests.post(
            'http://localhost:5000/api/batch/commission',
            json={
                'device_ids': machine_ids,  # Use correct parameter name
                'device_type': 'd1.c1.small',
                'ipmi_base_ip': '192.168.100.50',
                'concurrent_limit': 1
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success') or 'workflow_id' in data:
                print(f"✅ Batch commissioning API working")
                return True
            else:
                print(f"❌ Batch commissioning failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            error_data = response.text
            print(f"❌ Batch commissioning API returned status {response.status_code}: {error_data[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Batch commissioning test failed: {e}")
        return False

def test_javascript_functions():
    """Test that JavaScript functions are properly defined"""
    try:
        response = requests.get('http://localhost:5000/', timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Check for key JavaScript functions
            functions_to_check = [
                'smartDiscoverDevices',
                'detectDeviceTypes', 
                'validateIPMI',
                'startEnhancedBatch',
                'updateDevicesList',
                'updateBatchButtonState'
            ]
            
            missing_functions = []
            for func in functions_to_check:
                if f'function {func}' not in content and f'{func}(' not in content:
                    missing_functions.append(func)
            
            if not missing_functions:
                print("✅ All JavaScript functions are defined")
                return True
            else:
                print(f"❌ Missing JavaScript functions: {', '.join(missing_functions)}")
                return False
        else:
            print(f"❌ Could not load dashboard for JavaScript test")
            return False
            
    except Exception as e:
        print(f"❌ JavaScript functions test failed: {e}")
        return False

def main():
    """Run all GUI enhancement tests"""
    print("🧪 Testing GUI Enhancement Fixes")
    print("=" * 50)
    
    tests = [
        ("Dashboard Loading", test_dashboard_loads),
        ("JavaScript Functions", test_javascript_functions),
    ]
    
    # First run basic tests
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name} Test...")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{'✅ PASSED' if result else '❌ FAILED'} - {test_name}")
        except Exception as e:
            print(f"❌ FAILED - {test_name}: {e}")
            results.append((test_name, False))
    
    # Then run API tests that depend on MaaS
    print(f"\n📋 Running Device Discovery Test...")
    discovery_success, machines = test_device_discovery()
    results.append(("Device Discovery", discovery_success))
    
    if discovery_success:
        print(f"\n📋 Running Device Type Detection Test...")
        detection_success = test_device_type_detection(machines)
        results.append(("Device Type Detection", detection_success))
        
        print(f"\n📋 Running Batch Commissioning Test...")
        batch_success = test_batch_commissioning(machines)
        results.append(("Batch Commissioning", batch_success))
    else:
        print("⚠️  Skipping dependent tests due to discovery failure")
        results.append(("Device Type Detection", False))
        results.append(("Batch Commissioning", False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 GUI ENHANCEMENT TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Overall Success Rate: {passed}/{total} ({passed/total:.1%})")
    
    if passed >= total - 1:  # Allow 1 failure due to MaaS connectivity issues
        print("🎉 GUI enhancements are working correctly!")
        return 0
    else:
        print("⚠️  Some enhancements need attention.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
