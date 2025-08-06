#!/usr/bin/env python3
"""
Workflow Monitor - Debug utility for monitoring HW Automation workflows
"""

import requests
import json
import time
import sys
from datetime import datetime

class WorkflowMonitor:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        
    def get_workflow_status(self, workflow_id):
        """Get current workflow status"""
        try:
            response = requests.get(f"{self.base_url}/api/orchestration/workflow/{workflow_id}/status")
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'HTTP {response.status_code}: {response.text}'}
        except Exception as e:
            return {'error': str(e)}
    
    def get_workflow_debug(self, workflow_id):
        """Get detailed workflow debug information"""
        try:
            response = requests.get(f"{self.base_url}/api/orchestration/workflow/{workflow_id}/debug")
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'HTTP {response.status_code}: {response.text}'}
        except Exception as e:
            return {'error': str(e)}
    
    def list_workflows(self):
        """List all workflows"""
        try:
            response = requests.get(f"{self.base_url}/api/orchestration/workflows")
            if response.status_code == 200:
                return response.json()
            else:
                return {'error': f'HTTP {response.status_code}: {response.text}'}
        except Exception as e:
            return {'error': str(e)}
    
    def monitor_workflow(self, workflow_id, interval=5):
        """Monitor a workflow with regular status updates"""
        print(f"Monitoring workflow {workflow_id}...")
        print("Press Ctrl+C to stop monitoring\n")
        
        try:
            while True:
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                # Get basic status
                status = self.get_workflow_status(workflow_id)
                
                if 'error' in status:
                    print(f"[{timestamp}] ERROR: {status['error']}")
                    break
                
                workflow_status = status.get('status', 'unknown')
                current_step = status.get('current_step_index', 'unknown')
                
                print(f"[{timestamp}] Status: {workflow_status} | Current Step: {current_step}")
                
                # Show current sub-task if available
                if status.get('current_sub_task'):
                    print(f"    └─ Sub-task: {status['current_sub_task']}")
                
                # Show step details
                if status.get('steps'):
                    for i, step in enumerate(status['steps']):
                        step_name = step.get('name', f'step_{i}')
                        step_status = step.get('status', 'unknown')
                        indicator = "▶" if i == current_step else ("✓" if step_status == 'completed' else "○")
                        print(f"    {indicator} Step {i+1}: {step_name} ({step_status})")
                        
                        if step.get('error'):
                            print(f"      ❌ Error: {step['error']}")
                        if step.get('result'):
                            print(f"      ℹ Result: {step['result']}")
                
                # Stop monitoring if workflow is completed or failed
                if workflow_status in ['completed', 'failed', 'cancelled']:
                    print(f"\n✅ Workflow finished with status: {workflow_status}")
                    break
                
                print("-" * 60)
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n⏹ Monitoring stopped by user")
    
    def show_workflow_debug(self, workflow_id):
        """Show detailed debug information for a workflow"""
        debug_info = self.get_workflow_debug(workflow_id)
        
        if 'error' in debug_info:
            print(f"ERROR: {debug_info['error']}")
            return
        
        print(f"🔍 Debug Information for Workflow {workflow_id}")
        print("=" * 50)
        
        # Basic info
        print(f"Workflow Type: {debug_info.get('workflow_type', 'unknown')}")
        print(f"Status: {debug_info.get('status', {}).get('status', 'unknown')}")
        print(f"Is Running: {debug_info.get('is_running', 'unknown')}")
        print(f"Thread Alive: {debug_info.get('thread_alive', 'unknown')}")
        print(f"Current Step: {debug_info.get('current_step', 'unknown')}")
        print(f"Total Steps: {debug_info.get('total_steps', 'unknown')}")
        
        # Step details
        if debug_info.get('step_details'):
            print("\n📋 Step Details:")
            for step in debug_info['step_details']:
                indicator = "▶" if step['index'] == debug_info.get('current_step') else ("✓" if step['status'] == 'completed' else "○")
                print(f"  {indicator} Step {step['index'] + 1}: {step['name']} ({step['status']})")
                print(f"    Function: {step.get('function', 'unknown')}")

def main():
    monitor = WorkflowMonitor()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python workflow_monitor.py list                    - List all workflows")
        print("  python workflow_monitor.py status <workflow_id>    - Get workflow status")
        print("  python workflow_monitor.py debug <workflow_id>     - Get debug info")
        print("  python workflow_monitor.py monitor <workflow_id>   - Monitor workflow")
        return
    
    command = sys.argv[1]
    
    if command == "list":
        workflows = monitor.list_workflows()
        if 'error' in workflows:
            print(f"ERROR: {workflows['error']}")
        else:
            print("📋 Active Workflows:")
            for wf in workflows.get('workflows', []):
                print(f"  - {wf['id']}: {wf.get('status', 'unknown')} ({wf.get('type', 'unknown')})")
    
    elif command in ["status", "debug", "monitor"] and len(sys.argv) >= 3:
        workflow_id = sys.argv[2]
        
        if command == "status":
            status = monitor.get_workflow_status(workflow_id)
            print(json.dumps(status, indent=2))
        
        elif command == "debug":
            monitor.show_workflow_debug(workflow_id)
        
        elif command == "monitor":
            monitor.monitor_workflow(workflow_id)
    
    else:
        print("Invalid command or missing workflow_id")

if __name__ == "__main__":
    main()
