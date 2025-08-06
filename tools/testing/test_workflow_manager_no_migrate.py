#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/ubuntu/HWAutomation/src')

from hwautomation.utils.config import load_config
from hwautomation.orchestration.workflow_manager import WorkflowManager

def test_workflow_manager_no_migrate():
    try:
        print("Loading configuration...")
        config = load_config('/home/ubuntu/HWAutomation/config.yaml')
        
        # Disable auto migration
        config['database']['auto_migrate'] = False
        
        print("Creating workflow manager without auto migration...")
        workflow_manager = WorkflowManager(config)
        
        print("Workflow manager created successfully!")
        print(f"Workflow manager type: {type(workflow_manager)}")
        
    except Exception as e:
        print(f"Error creating workflow manager: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_workflow_manager_no_migrate()
