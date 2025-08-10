"""
Orchestration routes for HWAutomation Web Interface

Handles workflow management, server provisioning, and batch operations.
."""

import logging
import threading

from flask import Blueprint, current_app, jsonify, request

from ...logging import get_logger

logger = get_logger(__name__)

# Create blueprint for orchestration routes
orchestration_bp = Blueprint("orchestration", __name__, url_prefix="/api/orchestration")


@orchestration_bp.route("/workflows")
def api_orchestration_workflows():
    """Get all workflows (active and completed)."""
    try:
        workflow_manager = getattr(current_app, "_hwautomation_workflow_manager", None)
        if not workflow_manager:
            return jsonify({"error": "Workflow manager not available"}), 500

        workflows = workflow_manager.get_all_workflows()
        return jsonify({"workflows": workflows})

    except Exception as e:
        logger.error(f"Failed to get workflows: {e}")
        return jsonify({"error": str(e)}), 500


@orchestration_bp.route("/workflow/<workflow_id>/status")
def api_orchestration_workflow_status(workflow_id):
    """Get status of a specific workflow."""
    try:
        workflow_manager = getattr(current_app, "_hwautomation_workflow_manager", None)
        if not workflow_manager:
            return jsonify({"error": "Workflow manager not available"}), 500

        workflow = workflow_manager.get_workflow(workflow_id)
        if not workflow:
            return jsonify({"error": "Workflow not found"}), 404

        return jsonify(workflow.get_status())

    except Exception as e:
        logger.error(f"Failed to get workflow status: {e}")
        return jsonify({"error": str(e)}), 500


@orchestration_bp.route("/workflow/<workflow_id>/cancel", methods=["POST"])
def api_orchestration_workflow_cancel(workflow_id):
    """Cancel a running workflow."""
    try:
        workflow_manager = getattr(current_app, "_hwautomation_workflow_manager", None)
        if not workflow_manager:
            return jsonify({"error": "Workflow manager not available"}), 500

        success = workflow_manager.cancel_workflow(workflow_id)
        if not success:
            return jsonify({"error": "Workflow not found or cannot be cancelled"}), 404

        return jsonify(
            {"success": True, "message": f"Workflow {workflow_id} cancelled"}
        )

    except Exception as e:
        logger.error(f"Failed to cancel workflow: {e}")
        return jsonify({"error": str(e)}), 500


@orchestration_bp.route("/provision", methods=["POST"])
def api_orchestration_provision():
    """Start a server provisioning workflow."""
    try:
        workflow_manager = getattr(current_app, "_hwautomation_workflow_manager", None)
        socketio = getattr(current_app, "_hwautomation_socketio", None)

        if not workflow_manager:
            return jsonify({"error": "Workflow manager not available"}), 500

        data = request.get_json()

        # Validate required fields
        required_fields = ["server_id", "device_type"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        server_id = data["server_id"]
        device_type = data["device_type"]
        target_ipmi_ip = data.get("target_ipmi_ip")
        rack_location = data.get("rack_location")
        gateway = data.get("gateway")

        # Create and start provisioning workflow using modular components
        from hwautomation.orchestration.workflows.provisioning import (
            create_provisioning_workflow,
        )

        workflow = create_provisioning_workflow(
            server_id=server_id,
            device_type=device_type,
            target_ipmi_ip=target_ipmi_ip,
            gateway=gateway,
            workflow_type="standard",
        )

        # Note: Modular workflows don't support set_progress_callback yet
        # TODO: Add WebSocket progress integration to modular workflows

        # Create execution context for modular workflow
        context = workflow.create_initial_context()

        # Set additional context data from workflow manager
        if hasattr(workflow_manager, "maas_client"):
            context.set_data("maas_client", workflow_manager.maas_client)
        if hasattr(workflow_manager, "db_helper"):
            context.set_data("db_helper", workflow_manager.db_helper)

        def execute_workflow():
            try:
                result = workflow.execute(context)
                success = result.status.value == "success"
                logger.info(
                    f"Workflow {workflow.workflow_id} completed with success: {success}"
                )

                # TODO: Add WebSocket notification for completion
                if socketio:
                    socketio.emit(
                        "workflow_complete",
                        {
                            "workflow_id": workflow.workflow_id,
                            "success": success,
                            "message": result.message,
                        },
                    )

            except Exception as e:
                logger.error(f"Workflow {workflow.workflow_id} failed: {e}")

                # TODO: Add WebSocket notification for failure
                if socketio:
                    socketio.emit(
                        "workflow_failed",
                        {"workflow_id": workflow.workflow_id, "error": str(e)},
                    )

        thread = threading.Thread(target=execute_workflow)
        thread.daemon = True
        thread.start()

        response_data = {
            "success": True,
            "id": workflow.workflow_id,
            "message": f"Provisioning workflow started for {server_id}",
            "steps": [
                {"name": step.name, "description": step.description}
                for step in workflow.steps
            ],
        }

        # Include optional fields in response if provided
        if target_ipmi_ip:
            response_data["target_ipmi_ip"] = target_ipmi_ip
        if gateway:
            response_data["gateway"] = gateway

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Failed to start provisioning workflow: {e}")
        return jsonify({"error": str(e)}), 500


@orchestration_bp.route("/provision-firmware-first", methods=["POST"])
def api_start_firmware_first_provisioning():
    """Start a firmware-first server provisioning workflow."""
    try:
        workflow_manager = getattr(current_app, "_hwautomation_workflow_manager", None)
        socketio = getattr(current_app, "_hwautomation_socketio", None)

        if not workflow_manager:
            return jsonify({"error": "Workflow manager not available"}), 500

        data = request.get_json()

        # Validate required fields
        required_fields = ["server_id", "device_type"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        server_id = data["server_id"]
        device_type = data["device_type"]
        target_ipmi_ip = data.get("target_ipmi_ip")
        rack_location = data.get("rack_location")
        gateway = data.get("gateway")
        firmware_policy = data.get("firmware_policy", "recommended")

        # Validate firmware policy
        valid_policies = ["recommended", "latest", "security_only"]
        if firmware_policy not in valid_policies:
            return (
                jsonify(
                    {
                        "error": f"Invalid firmware_policy. Must be one of: {valid_policies}"
                    }
                ),
                400,
            )

        # Create and start firmware-first provisioning workflow using modular components
        from hwautomation.orchestration.workflows.provisioning import (
            create_provisioning_workflow,
        )

        workflow = create_provisioning_workflow(
            server_id=server_id,
            device_type=device_type,
            target_ipmi_ip=target_ipmi_ip,
            gateway=gateway,
            workflow_type="firmware_first",
            # Additional firmware-first specific parameters
            rack_location=rack_location,
            firmware_policy=firmware_policy,
        )

        if not workflow:
            return (
                jsonify(
                    {
                        "error": "Firmware-first provisioning not available. Firmware management not initialized."
                    }
                ),
                503,
            )

        # Note: Modular workflows don't support set_progress_callback yet
        # TODO: Add WebSocket progress integration to modular workflows

        # Create execution context for modular workflow
        context = workflow.create_initial_context()

        # Set additional context data from workflow manager
        if hasattr(workflow_manager, "maas_client"):
            context.set_data("maas_client", workflow_manager.maas_client)
        if hasattr(workflow_manager, "db_helper"):
            context.set_data("db_helper", workflow_manager.db_helper)

        # Set firmware-first specific context data
        context.set_data("rack_location", rack_location)
        context.set_data("firmware_policy", firmware_policy)

        def execute_workflow():
            try:
                result = workflow.execute(context)
                success = result.status.value == "success"
                logger.info(
                    f"Firmware-first workflow {workflow.workflow_id} completed with success: {success}"
                )

                # TODO: Add WebSocket notification for completion
                if socketio:
                    socketio.emit(
                        "workflow_complete",
                        {
                            "workflow_id": workflow.workflow_id,
                            "success": success,
                            "message": result.message,
                        },
                    )

            except Exception as e:
                logger.error(
                    f"Firmware-first workflow {workflow.workflow_id} failed: {e}"
                )

                # TODO: Add WebSocket notification for failure
                if socketio:
                    socketio.emit(
                        "workflow_failed",
                        {"workflow_id": workflow.workflow_id, "error": str(e)},
                    )

        thread = threading.Thread(target=execute_workflow)
        thread.daemon = True
        thread.start()

        response_data = {
            "success": True,
            "id": workflow.workflow_id,
            "message": f"Firmware-first provisioning workflow started for {server_id}",
            "firmware_policy": firmware_policy,
            "steps": [
                {"name": step.name, "description": step.description}
                for step in workflow.steps
            ],
        }

        # Include optional fields in response if provided
        if target_ipmi_ip:
            response_data["target_ipmi_ip"] = target_ipmi_ip
        if gateway:
            response_data["gateway"] = gateway

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Failed to start firmware-first provisioning workflow: {e}")
        return jsonify({"error": str(e)}), 500


def init_orchestration_routes(app, workflow_manager, socketio):
    """Initialize orchestration routes with dependencies."""
    # Store workflow manager in app context for blueprint route access
    app._hwautomation_workflow_manager = workflow_manager

    # Workflow status endpoint (not part of orchestration prefix)
    @app.route("/api/workflows/status")
    def api_workflows_status():
        """Get status of active workflows."""
        try:
            workflows = workflow_manager.get_active_workflows()
            return jsonify({"workflows": workflows})

        except Exception as e:
            logger.error(f"Workflow status failed: {e}")
            return jsonify({"error": str(e)}), 500

    # Batch commissioning endpoint (not part of orchestration prefix)
    @app.route("/api/batch/commission", methods=["POST"])
    def api_batch_commission():
        """Start batch commissioning workflow."""
        try:
            data = request.json
            device_type = data.get("device_type")
            device_ids = data.get("device_ids", [])
            ipmi_range = data.get("ipmi_range")
            subnet_mask = data.get("subnet_mask")
            gateway = data.get("gateway")

            if not device_type:
                return jsonify({"error": "Device type is required"}), 400

            if not device_ids:
                return jsonify({"error": "At least one device must be selected"}), 400

            # Start batch commissioning workflow for each device
            workflows = []
            for device_id in device_ids:
                from hwautomation.orchestration.workflows.provisioning import (
                    create_provisioning_workflow,
                )

                # Assign IPMI IP if range is provided
                target_ipmi_ip = None
                if ipmi_range:
                    # Get next available IP from range
                    # This would need to be implemented based on your IPMI assignment logic
                    pass

                workflow = create_provisioning_workflow(
                    server_id=device_id,
                    device_type=device_type,
                    target_ipmi_ip=target_ipmi_ip,
                    gateway=gateway,
                    workflow_type="standard",
                    # Additional batch commissioning parameters
                    subnet_mask=subnet_mask,
                )

                if workflow:
                    workflows.append(
                        {
                            "id": workflow.workflow_id,
                            "device_id": device_id,
                            "device_type": device_type,
                        }
                    )

            return jsonify(
                {
                    "success": True,
                    "message": f"Started commissioning {len(workflows)} devices",
                    "workflows": workflows,
                }
            )

        except Exception as e:
            logger.error(f"Batch commission failed: {e}")
            return jsonify({"error": str(e)}), 500
