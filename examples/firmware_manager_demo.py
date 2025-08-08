#!/usr/bin/env python3
"""
Firmware Manager Implementation Example

This example demonstrates the practical implementation of the firmware manager
integrated with the existing enhanced BIOS configuration system.
"""

import asyncio
import logging
import sys
import os
import tempfile

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from hwautomation.hardware.firmware_manager import (
    FirmwareManager, FirmwareType, FirmwareInfo, UpdatePriority
)
from hwautomation.hardware.firmware_provisioning_workflow import (
    FirmwareProvisioningWorkflow, ProvisioningContext
)

# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def demonstrate_firmware_manager():
    """Demonstrate the firmware manager capabilities"""
    print("=" * 80)
    print("FIRMWARE MANAGER DEMONSTRATION")
    print("=" * 80)
    
    # Create temporary config for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        config_content = f"""
firmware_repository:
  base_path: "{temp_dir}/firmware"
  download_enabled: true
  auto_verify: true
  vendors:
    hpe:
      display_name: "Hewlett Packard Enterprise"
    supermicro:
      display_name: "Super Micro Computer Inc."
"""
        config_path = os.path.join(temp_dir, "firmware_config.yaml")
        with open(config_path, 'w') as f:
            f.write(config_content)
        
        # Initialize firmware manager with temporary config
        firmware_manager = FirmwareManager(config_path=config_path)
        
        # Test configuration
        device_type = "a1.c5.large"
        target_ip = "192.168.1.100"
        credentials = {"username": "admin", "password": "password"}
        
        print(f"\n🎯 Target Configuration:")
        print(f"   Device Type: {device_type}")
        print(f"   Target IP: {target_ip}")
        print(f"   Credentials: {credentials['username']}/***")
        
        try:
            # Step 1: Check firmware versions
            print(f"\n📋 Step 1: Checking Current Firmware Versions")
            firmware_info = await firmware_manager.check_firmware_versions(
                device_type, target_ip, credentials['username'], credentials['password']
            )
            
            print(f"   Firmware Analysis Results:")
            updates_needed = []
            for fw_type, fw_info in firmware_info.items():
                status = "🔴 UPDATE NEEDED" if fw_info.update_required else "✅ UP TO DATE"
                priority = f"(priority: {fw_info.priority.value})" if fw_info.update_required else ""
                print(f"     {fw_type.value}: {fw_info.current_version} → {fw_info.latest_version} {status} {priority}")
                
                if fw_info.update_required:
                    updates_needed.append(fw_info)
            
            # Step 2: Update firmware if needed
            if updates_needed:
                print(f"\n🔧 Step 2: Updating Firmware ({len(updates_needed)} components)")
                
                total_time = sum(fw.estimated_time for fw in updates_needed)
                print(f"   Estimated time: {total_time} seconds ({total_time/60:.1f} minutes)")
                
                results = await firmware_manager.update_firmware_batch(
                    device_type, target_ip, credentials['username'], credentials['password'],
                    updates_needed, operation_id="demo_operation"
                )
                
                print(f"\n   Update Results:")
                successful = [r for r in results if r.success]
                failed = [r for r in results if not r.success]
                
                for result in results:
                    status = "✅" if result.success else "❌"
                    print(f"     {status} {result.firmware_type.value}: {result.old_version} → {result.new_version}")
                    print(f"        Time: {result.execution_time:.1f}s, Reboot: {result.requires_reboot}")
                    if result.error_message:
                        print(f"        Error: {result.error_message}")
                
                print(f"\n   Summary: {len(successful)} successful, {len(failed)} failed")
            else:
                print(f"\n✅ Step 2: No firmware updates needed")
            
            print(f"\n🎉 Firmware Manager demonstration completed successfully!")
            return True
            
        except Exception as e:
            print(f"\n❌ Firmware Manager demonstration failed: {e}")
            logger.exception("Demonstration failed")
            return False


async def demonstrate_firmware_provisioning_workflow():
    """Demonstrate the complete firmware-first provisioning workflow"""
    print("\n" + "=" * 80)
    print("FIRMWARE-FIRST PROVISIONING WORKFLOW DEMONSTRATION")
    print("=" * 80)
    
    # Initialize workflow
    workflow = FirmwareProvisioningWorkflow()
    
    # Create provisioning context
    context = workflow.create_provisioning_context(
        server_id="server_001",
        device_type="a1.c5.large",
        target_ip="192.168.1.100",
        credentials={"username": "admin", "password": "password"},
        firmware_policy="recommended"
    )
    
    print(f"\n🚀 Provisioning Configuration:")
    print(f"   Server ID: {context.server_id}")
    print(f"   Device Type: {context.device_type}")
    print(f"   Target IP: {context.target_ip}")
    print(f"   Firmware Policy: {context.firmware_policy}")
    
    try:
        # Execute the complete workflow
        result = await workflow.execute_firmware_first_provisioning(context)
        
        if result.success:
            print(f"\n" + "=" * 60)
            print("PROVISIONING COMPLETED SUCCESSFULLY")
            print("=" * 60)
            
            print(f"\n📊 Results Summary:")
            print(f"   Operation ID: {result.operation_id}")
            print(f"   Server ID: {result.server_id}")
            print(f"   Device Type: {result.device_type}")
            print(f"   Execution Time: {result.execution_time:.1f} seconds")
            print(f"   Firmware Updates Applied: {result.firmware_updates_applied}")
            print(f"   BIOS Settings Applied: {result.bios_settings_applied}")
            
            if result.warnings:
                print(f"\n⚠️  Warnings:")
                for warning in result.warnings:
                    print(f"     • {warning}")
            
            return True
        else:
            print(f"\n❌ Provisioning failed: {result.error_message}")
            return False
            
    except Exception as e:
        print(f"\n❌ Workflow demonstration failed: {e}")
        logger.exception("Workflow demonstration failed")
        return False


async def main():
    """Main demonstration function"""
    print("Firmware Update Integration - Implementation Strategy Demonstration")
    print("=" * 90)
    
    success_count = 0
    total_demos = 2
    
    # Run all demonstrations
    if await demonstrate_firmware_manager():
        success_count += 1
    
    if await demonstrate_firmware_provisioning_workflow():
        success_count += 1
    
    # Final summary
    print("\n" + "=" * 90)
    print("IMPLEMENTATION STRATEGY SUMMARY")
    print("=" * 90)
    
    print(f"\n📊 Demonstration Results: {success_count}/{total_demos} successful")

    return success_count == total_demos


if __name__ == "__main__":
    # Run the demonstration
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
