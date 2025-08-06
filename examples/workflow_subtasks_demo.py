#!/usr/bin/env python3
"""
Workflow Sub-task Demo

This example demonstrates the enhanced workflow output that shows
detailed sub-task execution for each workflow step.
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.hwautomation.utils.config import load_config
from src.hwautomation.orchestration.workflow_manager import WorkflowManager
from src.hwautomation.orchestration.server_provisioning import ServerProvisioningWorkflow

def progress_callback(progress):
    """Enhanced progress callback that shows sub-tasks"""
    step = progress.get('step', 0)
    total = progress.get('total_steps', 0)
    name = progress.get('step_name', 'Unknown')
    status = progress.get('status', 'unknown')
    sub_task = progress.get('sub_task')
    
    timestamp = time.strftime("%H:%M:%S")
    
    if status == 'running':
        prefix = "🔄"
        if sub_task:
            print(f"[{timestamp}] {prefix} [{step}/{total}] {name}")
            print(f"            └─ {sub_task}")
        else:
            print(f"[{timestamp}] {prefix} [{step}/{total}] {name}")
    elif status == 'completed':
        prefix = "✅"
        print(f"[{timestamp}] {prefix} [{step}/{total}] {name} - COMPLETED")
    elif status == 'failed':
        prefix = "❌"
        print(f"[{timestamp}] {prefix} [{step}/{total}] {name} - FAILED")
        if progress.get('error'):
            print(f"            Error: {progress['error']}")

def demo_workflow_subtasks():
    """Demonstrate workflow with sub-task visibility"""
    
    print("🚀 Enhanced Workflow Sub-task Demo")
    print("=" * 50)
    print()
    print("This demo shows the improved workflow output that displays:")
    print("• Main workflow steps")
    print("• Detailed sub-tasks within each step")
    print("• Real-time progress updates")
    print("• Timestamp for each operation")
    print()
    
    # Load configuration
    try:
        config_path = project_root / 'config.yaml'
        config = load_config(str(config_path))
        config['database']['auto_migrate'] = False
        
        print(f"📋 Configuration loaded from: {config_path}")
        print()
        
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return 1
    
    # Initialize workflow manager
    try:
        print("🔧 Initializing workflow manager...")
        workflow_manager = WorkflowManager(config)
        provisioning_workflow = ServerProvisioningWorkflow(workflow_manager)
        print("✅ Workflow manager initialized")
        print()
        
    except Exception as e:
        print(f"❌ Failed to initialize workflow manager: {e}")
        return 1
    
    # Create a sample workflow
    print("📝 Creating sample provisioning workflow...")
    server_id = 'demo123'
    device_type = 's2.c2.small'
    
    try:
        workflow = provisioning_workflow.create_provisioning_workflow(
            server_id=server_id,
            device_type=device_type,
            target_ipmi_ip=None,
            rack_location=None
        )
        
        # Set up progress callback
        workflow.set_progress_callback(progress_callback)
        
        print(f"✅ Created workflow for server: {server_id}")
        print(f"   Device type: {device_type}")
        print(f"   Workflow steps: {len(workflow.steps)}")
        print()
        
    except Exception as e:
        print(f"❌ Failed to create workflow: {e}")
        return 1
    
    # Show workflow plan
    print("📊 Workflow Plan with Sub-task Visibility:")
    print("-" * 45)
    for i, step in enumerate(workflow.steps, 1):
        print(f"{i}. {step.name}")
        print(f"   └─ {step.description}")
        
        # Show example sub-tasks for each step
        if 'commission' in step.name.lower():
            print(f"      • Creating database entry")
            print(f"      • Checking server status in MaaS")
            print(f"      • Verifying existing commissioning")
            print(f"      • Testing SSH connectivity")
            print(f"      • Waiting for commissioning to complete")
        elif 'hardware' in step.name.lower():
            print(f"      • Connecting to server for discovery")
            print(f"      • Running hardware discovery scan")
            print(f"      • Processing discovery results")
            print(f"      • Testing IPMI connectivity")
            print(f"      • Updating database with hardware info")
        elif 'bios' in step.name.lower() and 'pull' in step.name.lower():
            print(f"      • Connecting to server via SSH")
            print(f"      • Detecting server vendor")
            print(f"      • Checking for sumtool availability")
            print(f"      • Extracting BIOS configuration using sumtool")
            print(f"      • Downloading BIOS configuration file")
        print()
    
    print("🎯 Key Features of Enhanced Output:")
    print("• Real-time sub-task progress within each step")
    print("• Detailed status messages for complex operations")
    print("• Timestamps for tracking execution duration")
    print("• Clear visual indicators for progress status")
    print("• Failed sub-task identification for debugging")
    print()
    
    print("🔗 Integration Points:")
    print("• Web dashboard shows sub-task details")
    print("• CLI tools display sub-task progress")
    print("• API endpoints include sub-task information")
    print("• Database logging captures sub-task events")
    print()
    
    print("💡 Example Usage:")
    print("To see this in action, commission a server through:")
    print("• Web GUI: Enhanced commissioning with progress tracking")
    print("• CLI: tools/cli/orchestrator.py provision <server_id>")
    print("• API: /api/orchestration/provision endpoint")
    print()
    
    return 0

if __name__ == "__main__":
    exit_code = demo_workflow_subtasks()
    sys.exit(exit_code)
