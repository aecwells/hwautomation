#!/usr/bin/env python3
"""
Real-time Workflow Monitor - Continuously monitor for new workflows
"""

import json
import sys
import time
from datetime import datetime

import requests


def monitor_all_workflows():
    """Monitor all workflows continuously"""
    monitored_workflows = set()

    print("🔍 Real-time Workflow Monitor Started")
    print("Monitoring for new workflows...")
    print("Press Ctrl+C to stop\n")

    try:
        while True:
            try:
                # Get current workflows
                response = requests.get(
                    "http://localhost:5000/api/orchestration/workflows"
                )
                if response.status_code == 200:
                    data = response.json()
                    current_workflows = set(
                        wf["id"] for wf in data.get("workflows", [])
                    )

                    # Check for new workflows
                    new_workflows = current_workflows - monitored_workflows
                    for workflow_id in new_workflows:
                        print(f"🆕 NEW WORKFLOW DETECTED: {workflow_id}")
                        monitored_workflows.add(workflow_id)

                    # Monitor existing workflows
                    for workflow in data.get("workflows", []):
                        workflow_id = workflow["id"]
                        status = workflow.get("status", "unknown")
                        timestamp = datetime.now().strftime("%H:%M:%S")

                        # Get detailed status
                        status_response = requests.get(
                            f"http://localhost:5000/api/orchestration/workflow/{workflow_id}/status"
                        )
                        if status_response.status_code == 200:
                            detailed_status = status_response.json()
                            current_step_index = detailed_status.get(
                                "current_step_index"
                            )
                            current_step_name = detailed_status.get(
                                "current_step_name", "unknown"
                            )

                            # Display current step more clearly
                            if current_step_index is not None:
                                step_display = (
                                    f"{current_step_index + 1}: {current_step_name}"
                                )
                            else:
                                step_display = "unknown"

                            print(
                                f"[{timestamp}] {workflow_id}: {status} (Step: {step_display})"
                            )

                            # Show sub-task if available
                            if detailed_status.get("current_sub_task"):
                                print(
                                    f"    └─ Sub-task: {detailed_status['current_sub_task']}"
                                )

                            # Show step details
                            if detailed_status.get("steps"):
                                for i, step in enumerate(detailed_status["steps"]):
                                    step_name = step.get("name", f"step_{i}")
                                    step_status = step.get("status", "unknown")

                                    # Choose indicator based on step status and current position
                                    if i == current_step_index:
                                        indicator = "▶"  # Currently running
                                    elif step_status == "completed":
                                        indicator = "✅"  # Completed
                                    elif step_status == "failed":
                                        indicator = "❌"  # Failed
                                    else:
                                        indicator = "⏸"  # Pending

                                    print(
                                        f"    {indicator} Step {i+1}: {step_name} ({step_status})"
                                    )

                                    if step.get("error"):
                                        print(f"      ❌ Error: {step['error']}")
                                    if (
                                        step.get("result")
                                        and len(str(step["result"])) < 100
                                    ):
                                        print(f"      ℹ Result: {step['result']}")

                            # Check if workflow completed or failed
                            if status in ["completed", "failed", "cancelled"]:
                                print(
                                    f"🏁 Workflow {workflow_id} finished with status: {status}"
                                )
                                if workflow_id in monitored_workflows:
                                    monitored_workflows.remove(workflow_id)

                        print("-" * 60)

                else:
                    print(f"❌ API Error: {response.status_code}")

            except requests.exceptions.RequestException as e:
                print(f"🔌 Connection error: {e}")
            except Exception as e:
                print(f"❌ Error: {e}")

            time.sleep(3)  # Check every 3 seconds

    except KeyboardInterrupt:
        print("\n⏹ Real-time monitoring stopped")


if __name__ == "__main__":
    monitor_all_workflows()
