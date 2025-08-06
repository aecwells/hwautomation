#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, '/home/ubuntu/HWAutomation/src')

from hwautomation.utils.config import load_config
from hwautomation.orchestration.workflow_manager import WorkflowManager
from hwautomation.orchestration.server_provisioning import ServerProvisioningWorkflow

def test_provision():
    try:
        print("Loading configuration...")
        config = load_config('/home/ubuntu/HWAutomation/config.yaml')
        
        # Disable auto migration to avoid hanging
        config['database']['auto_migrate'] = False
        
        print("Creating workflow manager...")
        workflow_manager = WorkflowManager(config)
        
        print("Creating provisioning workflow...")
        provisioning_workflow = ServerProvisioningWorkflow(workflow_manager)
        
        print("Starting server provisioning...")
        result = provisioning_workflow.provision_server(
            server_id='4af348',
            device_type='s2.c2.small',
            target_ipmi_ip=None,
            rack_location=None
        )
        
        print(f"Provisioning result: {result}")
        
    except Exception as e:
        print(f"Error during provisioning: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_provision()
