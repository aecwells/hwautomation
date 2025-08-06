#!/usr/bin/env python3
"""
Server Orchestration CLI

Command-line interface for the hardware orchestration system.
Provides easy access to server provisioning workflows.
"""

import sys
import argparse
import json
import time
from pathlib import Path
from typing import Dict, Any

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

from hwautomation.utils.config import load_config
from hwautomation.orchestration.workflow_manager import WorkflowManager
from hwautomation.orchestration.server_provisioning import ServerProvisioningWorkflow

def progress_callback(progress: Dict[str, Any]):
    """Print progress updates"""
    step = progress.get('step', 0)
    total = progress.get('total_steps', 0)
    name = progress.get('step_name', 'Unknown')
    status = progress.get('status', 'unknown')
    sub_task = progress.get('sub_task')
    
    prefix = "✓" if status == 'completed' else "→" if status == 'running' else "✗"
    print(f"{prefix} [{step}/{total}] {name}")
    
    if sub_task and status == 'running':
        print(f"   └─ {sub_task}")
    
    if status == 'failed' and progress.get('error'):
        print(f"   Error: {progress['error']}")

def provision_server(args):
    """Provision a server using the orchestration system"""
    try:
        # Load configuration
        config_path = Path(args.config) if args.config else project_root / 'config.yaml'
        config = load_config(str(config_path))
        
        # Initialize orchestration system
        workflow_manager = WorkflowManager(config)
        provisioning_workflow = ServerProvisioningWorkflow(workflow_manager)
        
        print(f"🚀 Starting server provisioning for {args.server_id}")
        print(f"   Device Type: {args.device_type}")
        print(f"   Target IPMI IP: {args.target_ipmi_ip}")
        if args.rack_location:
            print(f"   Rack Location: {args.rack_location}")
        print()
        
        # Start provisioning
        result = provisioning_workflow.provision_server(
            server_id=args.server_id,
            device_type=args.device_type,
            target_ipmi_ip=args.target_ipmi_ip,
            rack_location=args.rack_location,
            progress_callback=progress_callback
        )
        
        # Print results
        if result['success']:
            print("\n🎉 Server provisioning completed successfully!")
            
            context = result.get('context', {})
            if context.get('server_ip'):
                print(f"   Server IP: {context['server_ip']}")
            if context.get('metadata'):
                print(f"   Metadata: {json.dumps(context['metadata'], indent=2)}")
        else:
            print(f"\n❌ Server provisioning failed: {result.get('error', 'Unknown error')}")
            return 1
            
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

def list_workflows(args):
    """List active workflows"""
    try:
        config_path = Path(args.config) if args.config else project_root / 'config.yaml'
        config = load_config(str(config_path))
        
        workflow_manager = WorkflowManager(config)
        workflow_ids = workflow_manager.list_workflows()
        
        if not workflow_ids:
            print("No active workflows")
            return 0
        
        print(f"Active workflows ({len(workflow_ids)}):")
        for workflow_id in workflow_ids:
            workflow = workflow_manager.get_workflow(workflow_id)
            if workflow:
                status = workflow.get_status()
                print(f"  {workflow_id}: {status['status']}")
                if status.get('error'):
                    print(f"    Error: {status['error']}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

def workflow_status(args):
    """Get detailed workflow status"""
    try:
        config_path = Path(args.config) if args.config else project_root / 'config.yaml'
        config = load_config(str(config_path))
        
        workflow_manager = WorkflowManager(config)
        workflow = workflow_manager.get_workflow(args.workflow_id)
        
        if not workflow:
            print(f"Workflow '{args.workflow_id}' not found")
            return 1
        
        status = workflow.get_status()
        print(f"Workflow: {status['id']}")
        print(f"Status: {status['status']}")
        
        if status.get('start_time'):
            print(f"Started: {status['start_time']}")
        if status.get('end_time'):
            print(f"Ended: {status['end_time']}")
        if status.get('error'):
            print(f"Error: {status['error']}")
        
        print("\nSteps:")
        for i, step in enumerate(status['steps'], 1):
            status_icon = "✓" if step['status'] == 'completed' else "→" if step['status'] == 'running' else "✗" if step['status'] == 'failed' else "○"
            print(f"  {status_icon} [{i}] {step['name']}: {step['status']}")
            if step.get('error'):
                print(f"      Error: {step['error']}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

def cancel_workflow(args):
    """Cancel a running workflow"""
    try:
        config_path = Path(args.config) if args.config else project_root / 'config.yaml'
        config = load_config(str(config_path))
        
        workflow_manager = WorkflowManager(config)
        workflow = workflow_manager.get_workflow(args.workflow_id)
        
        if not workflow:
            print(f"Workflow '{args.workflow_id}' not found")
            return 1
        
        workflow.cancel()
        print(f"Workflow '{args.workflow_id}' cancelled")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Hardware Orchestration CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Provision a server
  orchestrator provision machine-123 s2.c2.small 192.168.100.50

  # Provision with rack location
  orchestrator provision machine-123 s2.c2.small 192.168.100.50 --rack-location "Rack-A-U10"

  # List active workflows
  orchestrator list

  # Check workflow status
  orchestrator status provision_machine-123_1640995200

  # Cancel a workflow
  orchestrator cancel provision_machine-123_1640995200
        """
    )
    
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Provision command
    provision_parser = subparsers.add_parser('provision', help='Provision a server')
    provision_parser.add_argument('server_id', help='Server ID (MaaS machine ID)')
    provision_parser.add_argument('device_type', help='Device type (e.g., s2.c2.small)')
    provision_parser.add_argument('target_ipmi_ip', help='Target IPMI IP address')
    provision_parser.add_argument('--rack-location', help='Physical rack location')
    provision_parser.set_defaults(func=provision_server)
    
    # List command
    list_parser = subparsers.add_parser('list', help='List active workflows')
    list_parser.set_defaults(func=list_workflows)
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Get workflow status')
    status_parser.add_argument('workflow_id', help='Workflow ID')
    status_parser.set_defaults(func=workflow_status)
    
    # Cancel command
    cancel_parser = subparsers.add_parser('cancel', help='Cancel a workflow')
    cancel_parser.add_argument('workflow_id', help='Workflow ID')
    cancel_parser.set_defaults(func=cancel_workflow)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    return args.func(args)

if __name__ == '__main__':
    sys.exit(main())
