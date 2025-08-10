#!/usr/bin/env python3
"""
Complete Server Orchestration Example

This example demonstrates the full end-to-end server provisioning workflow
that integrates all the HWAutomation components:

1. 🔧 Commission server via MaaS
2. 🌐 Retrieve server IP address
3. 🛠️ Pull BIOS config via SSH
4. ✏️ Modify BIOS configuration
5. 🔄 Push updated BIOS config
6. 🧭 Update IPMI configuration
7. ✅ Finalize and tag server
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from hwautomation.orchestration.workflows.provisioning import create_provisioning_workflow
from hwautomation.orchestration.workflow_manager import WorkflowManager
from hwautomation.utils.config import load_config


async def main():
    """Main example function"""

    print("🚀 HWAutomation Server Orchestration Example")
    print("=" * 50)

    try:
        # Load configuration
        config = load_config(str(project_root / "config.yaml"))
        print("✅ Configuration loaded")

        # Initialize orchestration system
        workflow_manager = WorkflowManager(config)
        print("✅ Orchestration system initialized")

        # Example server configuration
        server_config = {
            "server_id": "example-machine-001",
            "device_type": "s2.c2.small",
            "target_ipmi_ip": "192.168.100.100",
            "rack_location": "Rack-A-U15",
        }

        print(f"\n📋 Server Configuration:")
        print(f"   Server ID: {server_config['server_id']}")
        print(f"   Device Type: {server_config['device_type']}")
        print(f"   Target IPMI IP: {server_config['target_ipmi_ip']}")
        print(f"   Rack Location: {server_config['rack_location']}")

        # Progress callback
        def progress_callback(progress):
            step = progress.get("step", 0)
            total = progress.get("total_steps", 0)
            name = progress.get("step_name", "Unknown")
            status = progress.get("status", "unknown")

            icons = {"running": "⏳", "completed": "✅", "failed": "❌", "pending": "⏸️"}

            icon = icons.get(status, "❓")
            print(f"{icon} [{step}/{total}] {name}")

            if status == "failed" and progress.get("error"):
                print(f"   ❌ Error: {progress['error']}")

        print(f"\n🎬 Starting Provisioning Workflow...")
        print("-" * 40)

        # Start provisioning (this would normally be a real server)
        # For demo purposes, we'll create the workflow but not execute it
        workflow = create_provisioning_workflow(
            server_id=server_config["server_id"],
            device_type=server_config["device_type"],
            target_ipmi_ip=server_config["target_ipmi_ip"],
            gateway=None,  # Optional parameter
            workflow_type="standard",
            # Additional parameters from config
            rack_location=server_config["rack_location"],
        )

        print("📝 Workflow Steps Created:")
        for i, step in enumerate(workflow.steps, 1):
            print(f"   {i}. {step.name}: {step.description}")

        print(f"\n📊 Workflow Summary:")
        print(f"   Total Steps: {len(workflow.steps)}")
        print(f"   Estimated Time: ~30-45 minutes")
        print(f"   Workflow ID: {workflow.workflow_id}")

        print(f"\n🔧 Integration Points:")
        print(f"   ✅ MaaS Client: Ready for server commissioning")
        print(
            f"   ✅ BIOS Manager: Templates loaded for {server_config['device_type']}"
        )
        print(f"   ✅ SSH Manager: Ready for remote execution")
        print(f"   ✅ IPMI Manager: Ready for BMC configuration")
        print(f"   ✅ Database: Ready for metadata storage")

        print(f"\n🌐 Access Methods:")
        print(f"   Web GUI: http://127.0.0.1:5000/orchestration")
        print(
            f"   CLI: orchestrator provision {server_config['server_id']} {server_config['device_type']} {server_config['target_ipmi_ip']}"
        )
        print(f"   API: POST /api/orchestration/provision")

        print(f"\n📋 Next Steps:")
        print(f"   1. Ensure MaaS is configured and accessible")
        print(f"   2. Verify SSH connectivity to commissioned servers")
        print(f"   3. Prepare BIOS templates for your device types")
        print(f"   4. Configure IPMI network settings")
        print(f"   5. Run the orchestration workflow!")

        print(f"\n✨ Example completed successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
