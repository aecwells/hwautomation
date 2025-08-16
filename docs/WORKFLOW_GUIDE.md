# Workflow Guide

Comprehensive guide to workflow orchestration and automation in HWAutomation for server provisioning and management.

## 📋 Table of Contents

- [Overview](#-overview)
- [Workflow Architecture](#-workflow-architecture)
- [Provisioning Workflows](#-provisioning-workflows)
- [Batch Operations](#-batch-operations)
- [Progress Monitoring](#-progress-monitoring)
- [Error Handling](#-error-handling)
- [Configuration](#-configuration)
- [Troubleshooting](#-troubleshooting)

## 🎯 Overview

HWAutomation's workflow system provides enterprise-grade automation for:

- **Server Provisioning**: Complete automated deployment from bare metal to ready state
- **Batch Operations**: Parallel processing of multiple servers
- **Progress Tracking**: Real-time visibility with sub-task reporting
- **Error Recovery**: Comprehensive error handling with retry logic
- **Cancellation Support**: Graceful workflow interruption and cleanup

### Key Features

- ✅ **Multi-vendor Support**: HPE, Dell, Supermicro hardware
- ✅ **Real-time Updates**: WebSocket-based progress monitoring
- ✅ **Flexible Configuration**: Device-specific templates and settings
- ✅ **Robust Error Handling**: Automatic retries and graceful failures
- ✅ **Cancellation Support**: Safe workflow interruption
- ✅ **Audit Trails**: Complete workflow execution history

## 🏗️ Workflow Architecture

### Core Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ WorkflowManager │    │ WorkflowContext  │    │ WorkflowStep    │
│                 │    │                  │    │                 │
│ • Lifecycle     │◄──►│ • Shared Data    │◄──►│ • Execution     │
│ • Threading     │    │ • Progress Track │    │ • Retry Logic   │
│ • Cancellation  │    │ • Error Capture  │    │ • Status Update │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Workflow States

```
PENDING ──► RUNNING ──► COMPLETED
   │           │            ▲
   │           ▼            │
   │        FAILED ─────────┘
   │           │
   └──► CANCELLED
```

**State Descriptions:**
- **PENDING**: Workflow queued for execution
- **RUNNING**: Currently executing with progress updates
- **COMPLETED**: Successfully finished all steps
- **FAILED**: Encountered unrecoverable error
- **CANCELLED**: Gracefully stopped by user request

### Integration Points

- **MaaS Client**: Server commissioning and management
- **BIOS Manager**: Configuration templates and device-specific settings
- **Firmware Manager**: Multi-vendor firmware management
- **SSH Manager**: Remote command execution and file transfer
- **IPMI Manager**: BMC configuration and network setup
- **Database**: Metadata storage and state tracking

## 🚀 Provisioning Workflows

### Standard Server Provisioning

Complete 7-step automated server deployment:

```
🔧 1. Commission Server via MaaS     → Power on, run enlistment, gather hardware details
🌐 2. Retrieve Server IP Address     → Query MaaS API for temporary IP assignment
🛠️ 3. Pull BIOS Config via SSH       → SSH into server and export current BIOS settings
✏️ 4. Modify BIOS Configuration      → Apply device-specific templates and settings
🔄 5. Push Updated BIOS Config       → Upload and apply new BIOS configuration
🧭 6. Update IPMI Configuration      → Configure BMC with target IP and settings
✅ 7. Finalize and Tag Server        → Mark as ready and apply metadata tags
```

**Web Interface Usage:**
1. Navigate to Orchestration → Server Provisioning
2. Enter server ID and select device type
3. Configure IPMI settings (optional)
4. Start provisioning workflow
5. Monitor real-time progress

**API Usage:**
```bash
curl -X POST http://localhost:5000/api/orchestration/provision \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "srv001",
    "device_type": "a1.c5.large",
    "target_ipmi_ip": "192.168.1.100",
    "gateway": "192.168.1.1"
  }'
```

**Python Integration:**
```python
from hwautomation.orchestration import ServerProvisioningWorkflow

# Create provisioning workflow
workflow = ServerProvisioningWorkflow(
    server_id="srv001",
    device_type="a1.c5.large",
    target_ipmi_ip="192.168.1.100"
)

# Execute with progress monitoring
result = workflow.execute()
print(f"Workflow completed: {result.success}")
```

### Firmware-First Provisioning

Enhanced 6-step firmware-first workflow for optimal system state:

```
🔍 1. Pre-flight Validation          → System readiness and connectivity checks
📊 2. Firmware Analysis              → Current vs. available firmware comparison
💾 3. Firmware Updates               → Priority-based updates with integrity verification
🔄 4. System Reboot                  → Controlled reboot with validation
⚙️ 5. BIOS Configuration             → Post-firmware BIOS setting application
✅ 6. Final Validation               → Complete system verification
```

**Enable Firmware-First Mode:**
```python
workflow = ServerProvisioningWorkflow(
    server_id="srv001",
    device_type="a1.c5.large",
    firmware_first=True,  # Enable firmware-first mode
    firmware_updates=["bios", "bmc", "nic"],
    rollback_on_failure=True
)
```

## 📦 Batch Operations

### Batch Commissioning

Process multiple servers simultaneously with parallel execution:

**Web Interface:**
1. Navigate to Orchestration → Batch Commission
2. Enter server list or CSV file
3. Configure common settings (device type, IPMI range)
4. Set parallelism level
5. Start batch operation

**API Usage:**
```bash
curl -X POST http://localhost:5000/api/batch/commission \
  -H "Content-Type: application/json" \
  -d '{
    "servers": ["server-001", "server-002", "server-003"],
    "device_type": "a1.c5.large",
    "ipmi_range": "192.168.1.100-110",
    "gateway": "192.168.1.1",
    "max_parallel": 3
  }'
```

**Python Implementation:**
```python
from hwautomation.orchestration import WorkflowManager

workflow_manager = WorkflowManager()

# Create batch commissioning workflow
batch_workflow = workflow_manager.create_batch_commissioning_workflow(
    servers=["server-001", "server-002", "server-003"],
    device_type="a1.c5.large",
    ipmi_config={
        "ip_range": "192.168.1.100-110",
        "gateway": "192.168.1.1"
    },
    max_parallel=3
)

# Execute with progress monitoring
result = workflow_manager.execute_workflow(batch_workflow.id)
```

### Batch Configuration

**Parallel Execution:**
- Configure maximum parallel workflows
- Automatic load balancing across servers
- Progress aggregation for overall visibility
- Error isolation between parallel operations

**IPMI Range Assignment:**
- Automatic IP assignment from range
- Gateway configuration for network setup
- Collision detection and resolution
- Rollback on configuration failures

## 📊 Progress Monitoring

### Real-time Sub-task Reporting

Detailed progress visibility with sub-task tracking:

```python
# Example sub-task progression
context.report_sub_task("Connecting to server via SSH...")
context.report_sub_task("Exporting current BIOS configuration...")
context.report_sub_task("Validating exported settings...")
context.report_sub_task("Applying device-specific template...")
context.report_sub_task("Uploading modified configuration...")
```

### Web Dashboard Features

**Live Progress Updates:**
- **Current Operation Display**: Shows exact sub-task being performed
- **Dynamic Updates**: Real-time information without page refresh
- **Progress Hierarchy**: Main steps and sub-tasks clearly organized
- **Status Indicators**: Visual indicators (🔄, ✅, ❌) for operation states

**Workflow Management:**
- View all active workflows
- Monitor progress across multiple operations
- Cancel running workflows
- Review completed workflow history

### API Progress Monitoring

**Get Workflow Status:**
```bash
curl http://localhost:5000/api/orchestration/workflow/123/status
```

**Response:**
```json
{
  "id": 123,
  "status": "RUNNING",
  "progress": 45,
  "current_step": "Modify BIOS Configuration",
  "current_sub_task": "Applying performance template...",
  "steps_completed": 3,
  "total_steps": 7,
  "started_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:30Z"
}
```

### WebSocket Integration

**Real-time Updates:**
```javascript
// Connect to workflow updates
const ws = new WebSocket('ws://localhost:5000/ws/workflow/123');

ws.onmessage = function(event) {
    const update = JSON.parse(event.data);
    console.log(`Sub-task: ${update.sub_task}`);
    console.log(`Progress: ${update.progress}%`);
};
```

## 🛡️ Error Handling

### Comprehensive Exception Management

**Error Categories:**
- **Connection Errors**: Network, SSH, IPMI connectivity issues
- **Configuration Errors**: Invalid settings, template problems
- **Hardware Errors**: Device-specific failures, timeout issues
- **System Errors**: Resource constraints, permission problems

**Error Response Structure:**
```json
{
  "error": true,
  "error_type": "ConnectionError",
  "message": "SSH connection failed",
  "details": {
    "target_ip": "192.168.1.100",
    "port": 22,
    "timeout": 30
  },
  "step": "Pull BIOS Config via SSH",
  "sub_task": "Establishing SSH connection",
  "suggestions": [
    "Verify target IP is reachable",
    "Check SSH service is running",
    "Validate credentials"
  ]
}
```

### Retry Logic

**Configurable Retry Strategies:**
```python
# Configure retry behavior
workflow_config = {
    "retry_config": {
        "max_retries": 3,
        "retry_delay": 30,  # seconds
        "exponential_backoff": True,
        "retry_on_errors": ["ConnectionError", "TimeoutError"]
    }
}
```

**Error-Specific Handling:**
- **Connection Errors**: Automatic retry with exponential backoff
- **Configuration Errors**: Immediate failure with detailed diagnostics
- **Hardware Errors**: Limited retries with extended timeouts
- **System Errors**: Context-dependent retry or failure

### Recovery Strategies

**Automatic Recovery:**
- Connection pool refresh
- Alternative method fallback (Redfish → vendor tools → IPMI)
- Configuration validation and correction
- Resource cleanup and retry

**Manual Recovery:**
- Detailed error diagnostics
- Step-by-step recovery instructions
- Configuration validation tools
- Manual intervention points

## ⚙️ Configuration

### Workflow Parameters

**Standard Configuration:**
```yaml
# configs/workflows/provisioning_config.yaml
provisioning_workflow:
  default_timeout: 3600  # seconds
  max_retries: 3
  retry_delay: 30

  steps:
    - name: "commission_server"
      timeout: 600
      retries: 2

    - name: "bios_configuration"
      timeout: 1200
      retries: 3
      fallback_methods: ["redfish", "vendor_tools", "ipmi"]
```

**Device-Specific Settings:**
```yaml
# Device-specific timeouts and configurations
device_configurations:
  a1.c5.large:
    bios_config_timeout: 900
    ipmi_config_timeout: 300
    vendor_tools: ["ilorest"]

  d1.c2.medium:
    bios_config_timeout: 1200
    ipmi_config_timeout: 600
    vendor_tools: ["racadm"]
```

### Batch Operation Settings

**Parallelism Configuration:**
```yaml
batch_operations:
  max_parallel_workflows: 5
  queue_size: 20
  timeout_per_server: 3600

  failure_handling:
    continue_on_error: true
    max_failed_percentage: 20
    rollback_on_critical_failure: true
```

### Progress Reporting Configuration

**Sub-task Reporting:**
```yaml
progress_reporting:
  enable_sub_tasks: true
  websocket_updates: true
  update_interval: 5  # seconds

  detail_levels:
    minimal: ["step_start", "step_complete"]
    standard: ["step_start", "sub_task", "step_complete"]
    verbose: ["step_start", "sub_task", "command", "step_complete"]
```

## 🔧 Troubleshooting

### Common Issues

**Workflow Stuck in RUNNING State:**
```bash
# Check workflow status
curl http://localhost:5000/api/orchestration/workflow/123/status

# Cancel if necessary
curl -X POST http://localhost:5000/api/orchestration/workflow/123/cancel

# Review logs
tail -f logs/hwautomation.log | grep "workflow_123"
```

**Connection Timeouts:**
```bash
# Test connectivity
ping 192.168.1.100
telnet 192.168.1.100 22   # SSH
telnet 192.168.1.100 623  # IPMI

# Check SSH access
ssh -o ConnectTimeout=10 root@192.168.1.100

# Verify IPMI
ipmitool -I lanplus -H 192.168.1.100 -U admin -P password chassis status
```

**BIOS Configuration Failures:**
```bash
# Check vendor tools
which ilorest  # HPE
which racadm   # Dell
which ipmitool # Universal

# Test Redfish endpoint
curl -k https://192.168.1.100/redfish/v1/

# Verify device type mapping
python -c "
from hwautomation.hardware.bios import BiosConfigManager
manager = BiosConfigManager()
print(manager.get_device_config('a1.c5.large'))
"
```

### Debug Mode

**Enable Debug Logging:**
```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Run with debug output
python -m hwautomation.orchestration.workflow_manager --debug
```

**Debug Workflow Execution:**
```python
from hwautomation.orchestration import WorkflowManager

# Enable debug mode
workflow_manager = WorkflowManager(debug=True)

# Create workflow with verbose logging
workflow = workflow_manager.create_provisioning_workflow(
    server_id="srv001",
    device_type="a1.c5.large",
    debug=True
)
```

### Performance Optimization

**Workflow Performance:**
- Reduce timeout values for faster operations
- Increase parallelism for batch operations
- Use connection pooling for multiple servers
- Cache device configurations and templates

**Resource Management:**
- Monitor memory usage during large batch operations
- Implement connection limits for IPMI/SSH
- Use background processing for long-running workflows
- Configure appropriate worker thread pools

## 📚 Related Documentation

- **Getting Started**: `docs/GETTING_STARTED.md`
- **Hardware Management**: `docs/HARDWARE_MANAGEMENT.md`
- **API Reference**: `docs/API_REFERENCE.md`
- **Development Guide**: `docs/DEVELOPMENT_GUIDE.md`
- **Example Workflows**: `examples/` directory
