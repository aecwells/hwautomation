#!/usr/bin/env python3
"""
Test script for workflow cancellation functionality
"""

import time
import threading
from src.hwautomation.orchestration.workflow_manager import WorkflowManager, WorkflowStatus, WorkflowStep
from src.hwautomation.database.db_helper import DatabaseHelper
from src.hwautomation.maas.maas_client import MaaSClient

def test_workflow_cancellation():
    """Test workflow cancellation end-to-end."""
    
    print("Initializing workflow manager...")
    db_helper = DatabaseHelper("hw_automation.db")
    maas_client = MaaSClient("http://localhost:5240/MAAS", "test-token")
    workflow_manager = WorkflowManager(maas_client, db_helper)
    
    # Create a test workflow with multiple steps
    steps = [
        WorkflowStep(
            name="test_step_1",
            description="Test Step 1 - Quick",
            execute_func=lambda ctx: (time.sleep(2), True)[1]
        ),
        WorkflowStep(
            name="test_step_2", 
            description="Test Step 2 - Long Running",
            execute_func=lambda ctx: (time.sleep(10), True)[1]  # Long step to cancel
        ),
        WorkflowStep(
            name="test_step_3",
            description="Test Step 3 - Should not run",
            execute_func=lambda ctx: (print("This should not execute"), True)[1]
        )
    ]
    
    workflow = workflow_manager.create_workflow(
        name="test_cancellation",
        description="Test workflow for cancellation",
        steps=steps,
        server_id="test_server"
    )
    
    print(f"Created workflow: {workflow.id}")
    
    # Progress callback to monitor workflow
    def progress_callback(progress_data):
        print(f"Progress: {progress_data}")
    
    workflow.set_progress_callback(progress_callback)
    
    # Start workflow in background thread
    from src.hwautomation.orchestration.workflow_manager import WorkflowContext
    
    context = WorkflowContext(
        server_id="test_server",
        device_type="test_device",
        maas_client=maas_client,
        db_helper=db_helper
    )
    context.workflow_id = workflow.id
    
    def execute_workflow():
        try:
            print("Starting workflow execution...")
            workflow.execute(context)
            print(f"Workflow completed. Final status: {workflow.status}")
        except Exception as e:
            print(f"Workflow execution error: {e}")
    
    # Start workflow
    thread = threading.Thread(target=execute_workflow)
    thread.daemon = True
    thread.start()
    
    # Let it run for a bit
    time.sleep(3)
    
    # Test get_active_workflows
    print("\nActive workflows:")
    active_workflows = workflow_manager.get_active_workflows()
    for wf in active_workflows:
        print(f"  - {wf['id']}: {wf['status']} - {wf['current_step_name']}")
    
    # Cancel the workflow
    print(f"\nCancelling workflow {workflow.id}...")
    success = workflow_manager.cancel_workflow(workflow.id)
    print(f"Cancellation success: {success}")
    
    # Wait a bit and check status
    time.sleep(2)
    
    print(f"\nFinal workflow status: {workflow.status}")
    print(f"Workflow cancelled: {workflow.cancelled}")
    print(f"Steps executed: {len([s for s in workflow.steps if s.status == 'completed'])}")
    
    # Test get_all_workflows
    print("\nAll workflows:")
    all_workflows = workflow_manager.get_all_workflows()
    for wf in all_workflows:
        print(f"  - {wf['id']}: {wf['status']} - {wf.get('current_step_name', 'N/A')}")

if __name__ == "__main__":
    test_workflow_cancellation()
