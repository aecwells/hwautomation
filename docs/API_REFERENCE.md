# API Reference

Comprehensive API documentation for programmatic integration with HWAutomation including REST endpoints, Python SDK, and WebSocket events.

## 📋 Table of Contents

- [Overview](#-overview)
- [REST API Endpoints](#-rest-api-endpoints)
- [Python SDK](#-python-sdk)
- [WebSocket Events](#-websocket-events)
- [Error Handling](#-error-handling)
- [Examples](#-examples)

## 🎯 Overview

HWAutomation provides multiple APIs for integration:

- **REST API**: HTTP endpoints for web and external integration
- **Python SDK**: Direct library integration for Python applications
- **WebSocket API**: Real-time updates and progress monitoring
- **CLI Interface**: Command-line tools for automation scripts

### Base URL

Default web interface: `http://localhost:5000`

### API Versioning

Current API version: `v1`
Base path: `/api/`

### Response Format

All API responses follow a consistent JSON structure:

```json
{
  "success": true,
  "data": { /* response data */ },
  "message": "Operation completed successfully",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

**Error Response:**
```json
{
  "success": false,
  "error": {
    "type": "ValidationError",
    "message": "Invalid device type",
    "details": { /* error details */ }
  },
  "timestamp": "2025-01-15T10:30:00Z"
}
```

## 🚀 Quick Start

### REST API

```bash
# Start a provisioning workflow
curl -X POST http://localhost:5000/api/orchestration/provision \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "server-001",
    "device_type": "a1.c5.large",
    "target_ipmi_ip": "192.168.1.100"
  }'
```

### Python SDK

```python
from hwautomation.orchestration import ServerProvisioningWorkflow
from hwautomation.database import DbHelper

# Initialize database
db_helper = DbHelper(auto_migrate=True)

# Create and start workflow
workflow = ServerProvisioningWorkflow(
    server_id="server-001",
    device_type="a1.c5.large",
    target_ipmi_ip="192.168.1.100"
)

# Execute workflow
result = workflow.execute()
print(f"Workflow completed: {result.success}")
```

## 🔐 Authentication

Currently, HWAutomation uses basic authentication for API access. Future versions will include:

- API key authentication
- OAuth 2.0 integration
- Role-based access control

For development and testing, authentication is optional.

## 🌐 REST API Endpoints

### Orchestration API

#### Start Provisioning Workflow

```http
POST /api/orchestration/provision
Content-Type: application/json

{
  "server_id": "string",
  "device_type": "string",
  "target_ipmi_ip": "string",
  "gateway": "string"
}
```

**Response:**
```json
{
  "success": true,
  "id": "workflow-uuid",
  "status": "PENDING",
  "server_id": "server-001",
  "target_ipmi_ip": "192.168.1.100"
}
```

#### Get Workflow Status

```http
GET /api/orchestration/workflow/{workflow_id}/status
```

**Response:**
```json
{
  "id": "workflow-uuid",
  "status": "RUNNING",
  "progress": 45,
  "current_step": "BIOS Configuration",
  "steps_completed": 3,
  "total_steps": 7,
  "sub_tasks": [
    {
      "name": "Applying BIOS template",
      "status": "IN_PROGRESS",
      "progress": 60
    }
  ]
}
```

#### List All Workflows

```http
GET /api/orchestration/workflows
```

**Response:**
```json
{
  "workflows": [
    {
      "id": "workflow-uuid",
      "server_id": "server-001",
      "status": "COMPLETED",
      "created_at": "2025-08-16T10:30:00Z",
      "completed_at": "2025-08-16T11:15:00Z"
    }
  ],
  "total": 1
}
```

#### Cancel Workflow

```http
POST /api/orchestration/workflow/{workflow_id}/cancel
```

**Response:**
```json
{
  "success": true,
  "message": "Workflow cancelled successfully"
}
```

### Batch Operations API

#### Batch Commission Servers

```http
POST /api/batch/commission
Content-Type: application/json

{
  "server_ids": ["server-001", "server-002"],
  "device_type": "a1.c5.large",
  "ipmi_range": "192.168.1.100-101",
  "gateway": "192.168.1.1"
}
```

**Response:**
```json
{
  "success": true,
  "workflows": [
    {
      "server_id": "server-001",
      "workflow_id": "workflow-uuid-1",
      "ipmi_ip": "192.168.1.100"
    },
    {
      "server_id": "server-002",
      "workflow_id": "workflow-uuid-2",
      "ipmi_ip": "192.168.1.101"
    }
  ]
}
```

### Hardware Management API

#### Get Server Information

```http
GET /api/hardware/server/{server_id}
```

**Response:**
```json
{
  "server_id": "server-001",
  "device_type": "a1.c5.large",
  "vendor": "HPE",
  "model": "ProLiant RL300 Gen11",
  "bios_version": "U32.1.2.3",
  "bmc_version": "2.85.0",
  "ipmi_ip": "192.168.1.100",
  "status": "Ready",
  "last_updated": "2025-08-16T10:30:00Z"
}
```

#### Update BIOS Configuration

```http
POST /api/hardware/server/{server_id}/bios
Content-Type: application/json

{
  "template": "a1.c5.large",
  "settings": {
    "boot_mode": "UEFI",
    "virtualization": "Enabled"
  },
  "dry_run": false
}
```

#### Get Firmware Information

```http
GET /api/hardware/server/{server_id}/firmware
```

**Response:**
```json
{
  "server_id": "server-001",
  "firmware": {
    "bios": {
      "current_version": "U32.1.2.3",
      "available_version": "U32.1.2.4",
      "update_available": true
    },
    "bmc": {
      "current_version": "2.85.0",
      "available_version": "2.85.0",
      "update_available": false
    }
  }
}
```

### MaaS Integration API

#### Discover Available Machines

```http
GET /api/maas/discover
```

**Response:**
```json
{
  "machines": [
    {
      "system_id": "abc123",
      "hostname": "server-001",
      "status": "Ready",
      "ip_addresses": ["192.168.1.100"],
      "architecture": "amd64",
      "cpu_count": 16,
      "memory": 32768
    }
  ],
  "total": 1
}
```

#### Commission Machine

```http
POST /api/maas/commission/{machine_id}
```

### Database API

#### Get All Servers

```http
GET /api/database/servers
```

#### Create Server Record

```http
POST /api/database/servers
Content-Type: application/json

{
  "server_id": "server-001",
  "device_type": "a1.c5.large",
  "ipmi_ip": "192.168.1.100"
}
```

#### Update Server Information

```http
PUT /api/database/servers/{server_id}
Content-Type: application/json

{
  "status": "Ready",
  "bios_version": "U32.1.2.4"
}
```

## 🐍 Python SDK

### Core Components

#### Database Operations

```python
from hwautomation.database import DbHelper

# Initialize database helper
db_helper = DbHelper(database_path="./hw_automation.db")

# Create server record
db_helper.createrowforserver("server-001")

# Update server information
db_helper.updateserverinfo("server-001", "status_name", "Ready")

# Get server information
server_info = db_helper.getserverinfo("server-001")
print(f"Server status: {server_info.get('status_name')}")

# Check if server exists
exists = db_helper.checkifserveridexists("server-001")
print(f"Server exists: {bool(exists)}")
```

#### Workflow Management

```python
from hwautomation.orchestration import (
    WorkflowManager,
    ServerProvisioningWorkflow
)

# Initialize workflow manager
workflow_manager = WorkflowManager(db_helper)

# Create provisioning workflow
workflow = workflow_manager.create_provisioning_workflow(
    server_id="server-001",
    device_type="a1.c5.large",
    target_ipmi_ip="192.168.1.100",
    gateway="192.168.1.1"
)

# Start workflow execution
workflow.start()

# Monitor progress
while workflow.is_running():
    status = workflow.get_status()
    print(f"Progress: {status.progress}% - {status.current_step}")
    time.sleep(5)

print(f"Workflow completed with status: {workflow.status}")
```

#### Hardware Management

```python
from hwautomation.hardware.bios import BiosConfigManager
from hwautomation.hardware.firmware import FirmwareManager

# BIOS configuration
bios_manager = BiosConfigManager()

# Apply BIOS configuration
result = bios_manager.apply_bios_config_smart(
    device_type="a1.c5.large",
    target_ip="192.168.1.100",
    username="ADMIN",
    password="password",
    dry_run=False
)

print(f"BIOS configuration result: {result.success}")

# Firmware management
firmware_manager = FirmwareManager()

# Get vendor information
vendor_info = firmware_manager.get_vendor_info("a1.c5.large")
print(f"Vendor: {vendor_info}")

# Check for firmware updates
updates = firmware_manager.check_firmware_updates(
    device_type="a1.c5.large",
    current_versions={
        "bios": "U32.1.2.3",
        "bmc": "2.85.0"
    }
)

print(f"Available updates: {len(updates)}")
```

#### MaaS Integration

```python
from hwautomation.maas import MaasClient

# Initialize MaaS client
maas_client = MaasClient(
    url="http://maas.example.com:5240/MAAS",
    consumer_key="your-consumer-key",
    token_key="your-token-key",
    token_secret="your-token-secret"
)

# Discover available machines
machines = maas_client.discover_machines()
print(f"Found {len(machines)} machines")

# Commission a machine
result = maas_client.commission_machine("machine-id")
print(f"Commission result: {result}")

# Deploy machine
deployment = maas_client.deploy_machine(
    machine_id="machine-id",
    os_image="ubuntu/focal"
)
print(f"Deployment started: {deployment}")
```

## 🔌 WebSocket Events

### Connection

```javascript
const socket = io('http://localhost:5000');

// Subscribe to workflow updates
socket.emit('subscribe_workflow', {workflow_id: 'workflow-uuid'});

// Listen for progress updates
socket.on('workflow_progress', (data) => {
    console.log('Progress:', data.progress);
    console.log('Current step:', data.current_step);
});

// Listen for workflow completion
socket.on('workflow_complete', (data) => {
    console.log('Workflow completed:', data.status);
});
```

### Event Types

#### Workflow Progress

```json
{
  "event": "workflow_progress",
  "workflow_id": "workflow-uuid",
  "progress": 65,
  "current_step": "Firmware Update",
  "sub_task": "Updating BIOS firmware"
}
```

#### Workflow Status Change

```json
{
  "event": "workflow_status",
  "workflow_id": "workflow-uuid",
  "old_status": "RUNNING",
  "new_status": "COMPLETED"
}
```

#### System Alerts

```json
{
  "event": "system_alert",
  "level": "warning",
  "message": "High memory usage detected",
  "timestamp": "2025-08-16T10:30:00Z"
}
```

## 📋 Examples

### Complete Server Provisioning

```python
import time
from hwautomation.database import DbHelper
from hwautomation.orchestration import WorkflowManager

def provision_server(server_id, device_type, ipmi_ip):
    """Complete server provisioning example."""

    # Initialize components
    db_helper = DbHelper()
    workflow_manager = WorkflowManager(db_helper)

    try:
        # Create server record
        db_helper.createrowforserver(server_id)
        print(f"Created server record for {server_id}")

        # Create and start provisioning workflow
        workflow = workflow_manager.create_provisioning_workflow(
            server_id=server_id,
            device_type=device_type,
            target_ipmi_ip=ipmi_ip
        )

        print(f"Started workflow {workflow.id} for {server_id}")

        # Monitor progress
        while workflow.is_running():
            status = workflow.get_status()
            print(f"[{server_id}] {status.progress}% - {status.current_step}")

            # Print sub-task details
            for sub_task in status.sub_tasks:
                print(f"  └─ {sub_task.name}: {sub_task.status}")

            time.sleep(10)

        # Check final status
        if workflow.status == "COMPLETED":
            print(f"✅ Server {server_id} provisioned successfully!")
            return True
        else:
            print(f"❌ Server {server_id} provisioning failed: {workflow.status}")
            return False

    except Exception as e:
        print(f"Error provisioning {server_id}: {e}")
        return False

# Usage
if __name__ == "__main__":
    success = provision_server(
        server_id="server-001",
        device_type="a1.c5.large",
        ipmi_ip="192.168.1.100"
    )

    if success:
        print("Server provisioning completed successfully!")
    else:
        print("Server provisioning failed!")
```

### Batch Hardware Discovery

```python
from hwautomation.hardware.discovery import HardwareDiscoveryManager

def discover_hardware_batch(ip_range):
    """Discover hardware across IP range."""

    discovery_manager = HardwareDiscoveryManager()
    results = []

    # Generate IP addresses from range
    start_ip, end_ip = ip_range.split('-')
    start_octets = start_ip.split('.')
    end_octets = end_ip.split('.')

    base_ip = '.'.join(start_octets[:3])
    start_num = int(start_octets[3])
    end_num = int(end_octets[3])

    for num in range(start_num, end_num + 1):
        ip = f"{base_ip}.{num}"

        try:
            # Discover hardware at this IP
            hardware_info = discovery_manager.discover_hardware(
                target_ip=ip,
                username="ADMIN",
                password="password"
            )

            if hardware_info:
                results.append({
                    'ip': ip,
                    'vendor': hardware_info.get('vendor'),
                    'model': hardware_info.get('model'),
                    'serial': hardware_info.get('serial'),
                    'bios_version': hardware_info.get('bios_version')
                })
                print(f"✅ Discovered {hardware_info.get('vendor')} at {ip}")
            else:
                print(f"❌ No hardware found at {ip}")

        except Exception as e:
            print(f"⚠️  Error discovering {ip}: {e}")

    return results

# Usage
discovered = discover_hardware_batch("192.168.1.100-110")
print(f"Discovered {len(discovered)} servers")

for server in discovered:
    print(f"Server at {server['ip']}: {server['vendor']} {server['model']}")
```

### Firmware Update Automation

```python
from hwautomation.hardware.firmware import FirmwareManager

def update_firmware_if_needed(server_id, device_type):
    """Check and update firmware if updates are available."""

    firmware_manager = FirmwareManager()

    try:
        # Get current firmware versions
        current_versions = firmware_manager.get_current_versions(
            device_type=device_type,
            target_ip="192.168.1.100"  # Get from server record
        )

        # Check for available updates
        updates = firmware_manager.check_firmware_updates(
            device_type=device_type,
            current_versions=current_versions
        )

        if not updates:
            print(f"No firmware updates available for {server_id}")
            return True

        print(f"Found {len(updates)} firmware updates for {server_id}")

        # Apply updates
        for update in updates:
            print(f"Updating {update.component} from {update.current_version} to {update.new_version}")

            result = firmware_manager.apply_firmware_update(
                device_type=device_type,
                update=update,
                target_ip="192.168.1.100"
            )

            if result.success:
                print(f"✅ {update.component} updated successfully")
            else:
                print(f"❌ Failed to update {update.component}: {result.error}")
                return False

        print(f"✅ All firmware updates completed for {server_id}")
        return True

    except Exception as e:
        print(f"Error updating firmware for {server_id}: {e}")
        return False

# Usage
success = update_firmware_if_needed("server-001", "a1.c5.large")
```

### Custom Workflow Integration

```python
from hwautomation.orchestration.workflow import BaseWorkflow
from hwautomation.orchestration.steps import WorkflowStep

class CustomMaintenanceWorkflow(BaseWorkflow):
    """Custom workflow for server maintenance tasks."""

    def __init__(self, server_id, maintenance_tasks):
        super().__init__(f"maintenance-{server_id}")
        self.server_id = server_id
        self.maintenance_tasks = maintenance_tasks

    def define_steps(self):
        """Define the workflow steps."""
        return [
            WorkflowStep("backup_config", self.backup_configuration),
            WorkflowStep("update_firmware", self.update_firmware),
            WorkflowStep("update_bios", self.update_bios),
            WorkflowStep("run_diagnostics", self.run_diagnostics),
            WorkflowStep("validate_health", self.validate_health)
        ]

    def backup_configuration(self, context):
        """Backup current configuration."""
        context.report_sub_task("Creating configuration backup...")
        # Implementation here
        return {"success": True, "backup_path": "/tmp/backup.json"}

    def update_firmware(self, context):
        """Update firmware if needed."""
        context.report_sub_task("Checking firmware updates...")
        # Implementation here
        return {"success": True, "updates_applied": 2}

    def update_bios(self, context):
        """Update BIOS configuration."""
        context.report_sub_task("Applying BIOS updates...")
        # Implementation here
        return {"success": True}

    def run_diagnostics(self, context):
        """Run hardware diagnostics."""
        context.report_sub_task("Running hardware diagnostics...")
        # Implementation here
        return {"success": True, "issues_found": 0}

    def validate_health(self, context):
        """Validate system health."""
        context.report_sub_task("Validating system health...")
        # Implementation here
        return {"success": True, "health_score": 100}

# Usage
workflow = CustomMaintenanceWorkflow(
    server_id="server-001",
    maintenance_tasks=["firmware", "bios", "diagnostics"]
)

workflow.start()
```

---

*For more examples and advanced usage patterns, see the `examples/` directory in the repository.*
