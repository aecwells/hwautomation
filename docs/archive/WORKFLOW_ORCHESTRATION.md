# Workflow Orchestration and Management

This document describes the comprehensive workflow orchestration system for automated server provisioning and management.

## 🎯 Overview

The HWAutomation orchestration system provides end-to-end automation for server provisioning with detailed progress tracking and real-time monitoring.

## 🔄 Core Workflow Architecture

### Server Provisioning Workflow

The complete 7-step automated server deployment process:

```
🔧 1. Commission Server via MaaS     → Power on, run enlistment, gather hardware details
🌐 2. Retrieve Server IP Address     → Query MaaS API for temporary IP assignment
🛠️ 3. Pull BIOS Config via SSH       → SSH into server and export current BIOS settings
✏️ 4. Modify BIOS Configuration      → Apply device-specific templates and settings
🔄 5. Push Updated BIOS Config       → Upload and apply new BIOS configuration
🧭 6. Update IPMI Configuration      → Configure BMC with target IP and settings
✅ 7. Finalize and Tag Server        → Mark as ready and apply metadata tags
```

### Firmware-First Workflow (Optional)

Enhanced 6-step firmware-first provisioning for optimal system state:

```
🔍 1. Pre-flight Validation          → System readiness and connectivity checks
📊 2. Firmware Analysis              → Current vs. available firmware comparison
💾 3. Firmware Updates               → Priority-based updates with integrity verification
🔄 4. System Reboot                  → Controlled reboot with validation
⚙️ 5. BIOS Configuration             → Post-firmware BIOS setting application
✅ 6. Final Validation               → Complete system verification
```

## 🏗️ Architecture Components

### Core Classes

#### `WorkflowManager`
Central coordination engine providing:
- Workflow lifecycle management (PENDING → RUNNING → COMPLETED/FAILED/CANCELLED)
- Background execution with threading
- Error handling and recovery
- Cancellation support with graceful cleanup

#### `ServerProvisioningWorkflow`
Complete server provisioning implementation:
- Standard 7-step workflow execution
- Optional firmware-first mode
- Device-specific configuration application
- Integration with all system components

#### `WorkflowStep`
Individual step execution with:
- Retry logic and timeout handling
- Progress reporting and status updates
- Error capture and diagnostics
- Cancellation checkpoint support

#### `WorkflowContext`
Shared data object passed between steps:
- Server and device information
- Configuration parameters
- Progress tracking callbacks
- Error accumulation and reporting

### Integration Points

- **MaaS Client**: Server commissioning and management
- **BIOS Manager**: Configuration templates and device-specific settings
- **Firmware Manager**: Multi-vendor firmware management
- **SSH Manager**: Remote command execution and file transfer
- **IPMI Manager**: BMC configuration and network setup
- **Database**: Metadata storage and state tracking

## 📊 Enhanced Sub-task Reporting

### Real-time Progress Visibility

#### Detailed Step Breakdown
Each workflow step reports internal sub-tasks for complete operational transparency:

```python
# Example sub-task reporting
context.report_sub_task("Connecting to server via SSH...")
context.report_sub_task("Exporting current BIOS configuration...")
context.report_sub_task("Validating exported settings...")
```

#### Live Progress Updates
- **WebSocket Integration**: Real-time updates to web dashboard
- **Timestamped Execution**: All sub-tasks include execution timestamps
- **Status Indicators**: Visual indicators (🔄, ✅, ❌) for operation states
- **Progress Tracking**: Both main step and sub-task progress visible

### User Interface Enhancements

#### Web Dashboard
- **Current Operation Display**: Shows exact sub-task being performed
- **Dynamic Updates**: Real-time information without page refresh
- **Progress Hierarchy**: Main steps and sub-tasks clearly organized
- **Error Context**: Failed sub-tasks provide specific error details

#### API Integration
- **Extended Status**: API endpoints include current sub-task information
- **Structured Data**: Sub-task information available in JSON responses
- **WebSocket Updates**: Real-time sub-task updates via WebSocket connections

## 🌐 Usage Examples

### 1. Web GUI Interface

Access the orchestration system through the web interface:

```
http://127.0.0.1:5000/orchestration
```

Dashboard features:
- Start new provisioning workflows
- Monitor progress in real-time with sub-task details
- View active workflows and their current operations
- Cancel running operations with graceful cleanup

### 2. API Usage

Start a provisioning workflow via REST API:

```bash
curl -X POST http://localhost:5000/api/orchestration/provision \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "srv001",
    "device_type": "a1.c5.large",
    "target_ipmi_ip": "192.168.1.100",
    "firmware_first": true
  }'
```

### 3. Direct Python Integration

```python
from hwautomation.orchestration import ServerProvisioningWorkflow

# Create firmware-first provisioning workflow
workflow = ServerProvisioningWorkflow(
    server_id="srv001",
    device_type="a1.c5.large",
    target_ipmi_ip="192.168.1.100",
    firmware_first=True
)

# Execute with progress monitoring
result = workflow.execute()
```

## 🛡️ Workflow Management Features

### Lifecycle Management

#### Workflow States
- **PENDING**: Workflow queued for execution
- **RUNNING**: Currently executing with progress updates
- **COMPLETED**: Successfully finished all steps
- **FAILED**: Encountered unrecoverable error
- **CANCELLED**: Gracefully stopped by user request

#### Cancellation Support
- **Graceful Interruption**: Workflows can be safely cancelled
- **Cleanup Operations**: Partial operations are properly cleaned up
- **Safe Stopping Points**: Cancellation respects operation boundaries
- **Status Tracking**: Complete visibility throughout cancellation process

### Error Handling

#### Comprehensive Exception Management
- **Step-level Error Capture**: Each step captures and reports errors
- **Error Context**: Detailed error information with sub-task context
- **Recovery Suggestions**: System provides remediation recommendations
- **Error Aggregation**: Multiple errors collected and reported together

#### Retry Logic
- **Configurable Retries**: Steps can retry failed operations
- **Exponential Backoff**: Intelligent retry timing to avoid overwhelming systems
- **Error Classification**: Different error types handled appropriately
- **Timeout Management**: Operations have configurable timeout limits

## 🔧 Configuration Options

### Workflow Parameters

#### Standard Provisioning
```python
workflow_config = {
    "server_id": "srv001",
    "device_type": "a1.c5.large",
    "target_ipmi_ip": "192.168.1.100",  # Optional
    "gateway": "192.168.1.1",           # Optional
    "timeout": 3600,                    # Optional, seconds
    "retry_count": 3                    # Optional, default retries
}
```

#### Firmware-First Provisioning
```python
firmware_workflow_config = {
    "server_id": "srv001",
    "device_type": "a1.c5.large",
    "firmware_first": True,
    "firmware_updates": ["bios", "bmc", "nic"],
    "rollback_on_failure": True,
    "pre_flight_checks": True
}
```

### Device-Specific Settings

The orchestration system adapts behavior based on device type:
- **Hardware-specific timeouts**: Different devices have different operation times
- **Vendor tool selection**: Automatic selection of appropriate vendor tools
- **Configuration templates**: Device-specific BIOS and firmware configurations
- **Validation rules**: Hardware-appropriate validation and verification

## 📈 Monitoring and Metrics

### Real-time Monitoring
- **Operation Progress**: Live progress updates with percentage completion
- **Current Activity**: Detailed description of current sub-task
- **Performance Metrics**: Operation timing and system resource usage
- **Error Tracking**: Real-time error detection and reporting

### Audit Trail
- **Complete Workflow History**: All workflow executions logged
- **Step-by-step Tracking**: Detailed logs of each workflow step
- **Sub-task Documentation**: All sub-tasks recorded with timestamps
- **Error Analysis**: Failed operations documented for improvement

This comprehensive orchestration system provides enterprise-grade automation with complete visibility, robust error handling, and flexible configuration options for reliable bare-metal server provisioning.
