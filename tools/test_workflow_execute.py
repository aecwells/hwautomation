#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/ubuntu/HWAutomation/src')

from hwautomation.utils.config import load_config
from hwautomation.orchestration.workflow_manager import WorkflowManager, WorkflowContext
from hwautomation.orchestration.server_provisioning import ServerProvisioningWorkflow

def test_workflow_execute():
    try:
        print("Setting up workflow...")
        config = load_config('/home/ubuntu/HWAutomation/config.yaml')
        config['database']['auto_migrate'] = False
        
        workflow_manager = WorkflowManager(config)
        provisioning_workflow = ServerProvisioningWorkflow(workflow_manager)
        
        print("Creating workflow...")
        workflow = provisioning_workflow.create_provisioning_workflow(
            server_id='4af348',
            device_type='s2.c2.small',
            target_ipmi_ip=None,
            rack_location=None
        )
        
        print("Creating context...")
        context = WorkflowContext(
            server_id='4af348',
            device_type='s2.c2.small',
            target_ipmi_ip=None,
            rack_location=None,
            maas_client=workflow_manager.maas_client,
            db_helper=workflow_manager.db_helper
        )
        
        print("Starting workflow execution...")
        print("This might take a while as it will actually try to commission the server...")
        
        # Execute workflow
        success = workflow.execute(context)
        
        print(f"Workflow execution completed. Success: {success}")
        
        # Get status
        status = workflow.get_status()
        print(f"Final status: {status}")
        
    except Exception as e:
        print(f"Error during workflow execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_workflow_execute()
