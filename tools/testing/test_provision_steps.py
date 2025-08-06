#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/ubuntu/HWAutomation/src')

from hwautomation.utils.config import load_config
from hwautomation.orchestration.workflow_manager import WorkflowManager
from hwautomation.orchestration.server_provisioning import ServerProvisioningWorkflow

def test_provision_step_by_step():
    try:
        print("Step 1: Loading configuration...")
        config = load_config('/home/ubuntu/HWAutomation/config.yaml')
        config['database']['auto_migrate'] = False
        print("  Config loaded successfully")
        
        print("Step 2: Creating workflow manager...")
        workflow_manager = WorkflowManager(config)
        print("  Workflow manager created successfully")
        
        print("Step 3: Creating provisioning workflow...")
        provisioning_workflow = ServerProvisioningWorkflow(workflow_manager)
        print("  Provisioning workflow created successfully")
        
        print("Step 4: Creating workflow definition...")
        workflow = provisioning_workflow.create_provisioning_workflow(
            server_id='4af348',
            device_type='s2.c2.small',
            target_ipmi_ip=None,
            rack_location=None
        )
        print(f"  Workflow definition created: {workflow}")
        
        print("All steps completed successfully!")
        
    except Exception as e:
        print(f"Error at current step: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_provision_step_by_step()
