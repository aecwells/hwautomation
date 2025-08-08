#!/usr/bin/env python3
"""
OpenAPI/Swagger documentation for HWAutomation API endpoints.

This module provides comprehensive API documentation using Flask-RESTX,
making the API self-documenting and interactive.
"""

import logging

from flask import Blueprint
from flask_restx import Api, Namespace, Resource, fields

logger = logging.getLogger(__name__)

# Create API documentation blueprint
api_docs_bp = Blueprint("api_docs", __name__)

# Initialize Flask-RESTX API
api = Api(
    api_docs_bp,
    version="1.0.0",
    title="HWAutomation API",
    description="Hardware Automation Platform API for server provisioning, BIOS configuration, and firmware management",
    doc="/docs/",
    contact_email="admin@hwautomation.local",
    license="MIT",
    license_url="https://opensource.org/licenses/MIT",
    authorizations={
        "Bearer Auth": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Type in the *'Value'* input box below: **'Bearer &lt;JWT&gt;'**, where JWT is the token",
        }
    },
)

# Define namespaces for organized documentation
core_ns = Namespace("core", description="Core system operations and health checks")
orchestration_ns = Namespace(
    "orchestration", description="Workflow orchestration and server provisioning"
)
database_ns = Namespace("database", description="Database management and operations")
maas_ns = Namespace("maas", description="MaaS (Metal as a Service) integration")
logs_ns = Namespace("logs", description="System logging and monitoring")
firmware_ns = Namespace("firmware", description="Firmware management and updates")

api.add_namespace(core_ns, path="/api")
api.add_namespace(orchestration_ns, path="/api/orchestration")
api.add_namespace(database_ns, path="/api/database")
api.add_namespace(maas_ns, path="/api/maas")
api.add_namespace(logs_ns, path="/api/logs")
api.add_namespace(firmware_ns, path="/api/firmware")

# Common models for response consistency
health_model = api.model(
    "Health",
    {
        "status": fields.String(
            required=True, description="System health status", example="healthy"
        ),
        "service": fields.String(
            required=True, description="Service identifier", example="hwautomation-web"
        ),
        "timestamp": fields.DateTime(
            required=True, description="Health check timestamp"
        ),
        "services": fields.Raw(description="Detailed service status information"),
    },
)

error_model = api.model(
    "Error",
    {
        "success": fields.Boolean(
            required=True, description="Operation success flag", example=False
        ),
        "error": fields.String(
            required=True, description="Error message", example="Operation failed"
        ),
        "error_code": fields.String(
            description="Machine-readable error code", example="VALIDATION_ERROR"
        ),
        "details": fields.Raw(description="Additional error details"),
    },
)

success_model = api.model(
    "Success",
    {
        "success": fields.Boolean(
            required=True, description="Operation success flag", example=True
        ),
        "message": fields.String(
            description="Success message", example="Operation completed"
        ),
        "data": fields.Raw(description="Response data"),
    },
)

# Workflow models
workflow_status_model = api.model(
    "WorkflowStatus",
    {
        "id": fields.String(required=True, description="Workflow identifier"),
        "status": fields.String(
            required=True,
            description="Current workflow status",
            enum=["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"],
        ),
        "progress": fields.Integer(
            description="Completion percentage (0-100)", min=0, max=100
        ),
        "current_step": fields.String(description="Current operation step"),
        "created_at": fields.DateTime(description="Workflow creation timestamp"),
        "updated_at": fields.DateTime(description="Last update timestamp"),
        "sub_tasks": fields.List(fields.Raw(), description="Sub-task progress details"),
    },
)

workflow_list_model = api.model(
    "WorkflowList",
    {
        "workflows": fields.List(
            fields.Nested(workflow_status_model), description="List of workflows"
        ),
        "total": fields.Integer(description="Total number of workflows"),
        "active": fields.Integer(description="Number of active workflows"),
    },
)

# Provision request model
provision_request_model = api.model(
    "ProvisionRequest",
    {
        "server_id": fields.String(
            required=True, description="Server identifier", example="node-123"
        ),
        "device_type": fields.String(
            required=True,
            description="Device type configuration",
            example="a1.c5.large",
        ),
        "target_ipmi_ip": fields.String(
            description="Target IPMI IP address", example="192.168.1.100"
        ),
        "gateway": fields.String(
            description="Network gateway IP", example="192.168.1.1"
        ),
        "rack_location": fields.String(
            description="Physical rack location", example="Rack-A-U12"
        ),
    },
)

provision_response_model = api.model(
    "ProvisionResponse",
    {
        "success": fields.Boolean(required=True, description="Operation success flag"),
        "workflow_id": fields.String(
            required=True, description="Created workflow identifier"
        ),
        "message": fields.String(description="Operation status message"),
        "target_ipmi_ip": fields.String(description="Assigned IPMI IP address"),
        "gateway": fields.String(description="Network gateway configuration"),
    },
)

# Database models
database_info_model = api.model(
    "DatabaseInfo",
    {
        "success": fields.Boolean(required=True, description="Operation success flag"),
        "info": fields.Raw(
            required=True,
            description="Database information",
            example={
                "path": "/data/hw_automation.db",
                "size": "2.5 MB",
                "table_count": 3,
                "server_count": 15,
                "version": "3.40.1",
            },
        ),
    },
)

# MaaS models
maas_discovery_model = api.model(
    "MaaSDiscovery",
    {
        "devices": fields.List(fields.Raw(), description="Discovered MaaS devices"),
        "available_count": fields.Integer(description="Number of available devices"),
        "total_discovered": fields.Integer(description="Total devices discovered"),
        "timestamp": fields.DateTime(description="Discovery timestamp"),
    },
)

# Log models
log_entry_model = api.model(
    "LogEntry",
    {
        "timestamp": fields.DateTime(required=True, description="Log entry timestamp"),
        "level": fields.String(
            required=True,
            description="Log level",
            enum=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        ),
        "component": fields.String(
            required=True, description="Component that generated the log"
        ),
        "message": fields.String(required=True, description="Log message content"),
    },
)

logs_response_model = api.model(
    "LogsResponse",
    {
        "logs": fields.List(fields.Nested(log_entry_model), description="Log entries"),
        "total": fields.Integer(description="Total number of log entries"),
        "filtered": fields.Integer(description="Number of entries after filtering"),
    },
)


# Core API endpoints documentation
@core_ns.route("/health")
class HealthCheck(Resource):
    @core_ns.marshal_with(health_model)
    @core_ns.doc(
        "get_health",
        description="Get system health status and service information",
        responses={
            200: "Success - System is healthy",
            503: "Service Unavailable - System has issues",
        },
    )
    def get(self):
        """Get system health status"""
        pass


@core_ns.route("/")
class Dashboard(Resource):
    @core_ns.doc(
        "get_dashboard",
        description="Get main dashboard with system statistics",
        responses={
            200: "Success - Dashboard data retrieved",
            500: "Internal Server Error",
        },
    )
    def get(self):
        """Get dashboard statistics and status"""
        pass


# Orchestration API endpoints documentation
@orchestration_ns.route("/provision")
class ProvisionServer(Resource):
    @orchestration_ns.expect(provision_request_model)
    @orchestration_ns.marshal_with(provision_response_model)
    @orchestration_ns.doc(
        "provision_server",
        description="Start server provisioning workflow",
        responses={
            200: "Success - Provisioning started",
            400: "Bad Request - Invalid parameters",
            500: "Internal Server Error",
        },
    )
    def post(self):
        """Start server provisioning workflow"""
        pass


@orchestration_ns.route("/workflows")
class WorkflowList(Resource):
    @orchestration_ns.marshal_with(workflow_list_model)
    @orchestration_ns.doc(
        "list_workflows",
        description="Get list of all workflows with their status",
        responses={200: "Success - Workflows retrieved", 500: "Internal Server Error"},
    )
    def get(self):
        """Get list of all workflows"""
        pass


@orchestration_ns.route("/workflows/<string:workflow_id>/status")
class WorkflowStatus(Resource):
    @orchestration_ns.marshal_with(workflow_status_model)
    @orchestration_ns.doc(
        "get_workflow_status",
        description="Get detailed status of a specific workflow",
        params={"workflow_id": "Workflow identifier"},
        responses={
            200: "Success - Workflow status retrieved",
            404: "Not Found - Workflow does not exist",
            500: "Internal Server Error",
        },
    )
    def get(self, workflow_id):
        """Get workflow status and progress"""
        pass


@orchestration_ns.route("/workflows/<string:workflow_id>/cancel")
class WorkflowCancel(Resource):
    @orchestration_ns.marshal_with(success_model)
    @orchestration_ns.doc(
        "cancel_workflow",
        description="Cancel a running workflow",
        params={"workflow_id": "Workflow identifier"},
        responses={
            200: "Success - Workflow cancelled",
            404: "Not Found - Workflow does not exist",
            409: "Conflict - Workflow cannot be cancelled",
            500: "Internal Server Error",
        },
    )
    def post(self, workflow_id):
        """Cancel a running workflow"""
        pass


# Database API endpoints documentation
@database_ns.route("/info")
class DatabaseInfo(Resource):
    @database_ns.marshal_with(database_info_model)
    @database_ns.doc(
        "get_database_info",
        description="Get database statistics and information",
        responses={
            200: "Success - Database info retrieved",
            500: "Internal Server Error",
        },
    )
    def get(self):
        """Get database information and statistics"""
        pass


# MaaS API endpoints documentation
@maas_ns.route("/discover")
class MaaSDiscover(Resource):
    @maas_ns.marshal_with(maas_discovery_model)
    @maas_ns.doc(
        "discover_maas_devices",
        description="Discover available devices from MaaS",
        responses={
            200: "Success - Devices discovered",
            503: "Service Unavailable - MaaS not available",
            500: "Internal Server Error",
        },
    )
    def get(self):
        """Discover available devices from MaaS"""
        pass


# Logs API endpoints documentation
@logs_ns.route("/")
class SystemLogs(Resource):
    @logs_ns.marshal_with(logs_response_model)
    @logs_ns.doc(
        "get_system_logs",
        description="Get system logs with optional filtering",
        params={
            "level": "Filter by log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
            "component": "Filter by component name",
            "lines": "Number of log lines to retrieve (default: 100)",
            "since": "Show logs since timestamp (ISO format)",
        },
        responses={
            200: "Success - Logs retrieved",
            400: "Bad Request - Invalid parameters",
            500: "Internal Server Error",
        },
    )
    def get(self):
        """Get system logs with filtering options"""
        pass


# Error handlers for consistent API responses
@api.errorhandler(ValueError)
def handle_value_error(error):
    """Handle validation errors"""
    return {
        "success": False,
        "error": str(error),
        "error_code": "VALIDATION_ERROR",
    }, 400


@api.errorhandler(KeyError)
def handle_key_error(error):
    """Handle missing parameter errors"""
    return {
        "success": False,
        "error": f"Missing required parameter: {str(error)}",
        "error_code": "MISSING_PARAMETER",
    }, 400


@api.errorhandler(Exception)
def handle_generic_error(error):
    """Handle unexpected errors"""
    logger.exception("Unexpected API error")
    return {
        "success": False,
        "error": "Internal server error",
        "error_code": "INTERNAL_ERROR",
    }, 500


def init_api_docs(app):
    """Initialize API documentation with the Flask app"""
    app.register_blueprint(api_docs_bp)
    return api
