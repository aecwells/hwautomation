# Enhanced Workflow Sub-task Reporting

## Overview

The HWAutomation workflow system now provides detailed sub-task visibility during workflow execution. This enhancement gives users real-time insight into what specific operations are being performed within each workflow step, improving transparency and debugging capabilities.

## Features

### Real-time Sub-task Progress
- **Detailed Step Breakdown**: Each workflow step now reports its internal sub-tasks
- **Live Progress Updates**: Sub-tasks are displayed in real-time as they execute
- **Clear Status Indicators**: Visual indicators show the current operation being performed
- **Timestamped Execution**: All sub-task updates include timestamps for duration tracking

### Enhanced User Interfaces

#### Web Dashboard
- **Sub-task Display**: Current sub-task shown alongside main step progress
- **Dynamic Updates**: Real-time sub-task information updates without page refresh
- **Progress Tracking**: Both main step and sub-task progress are visible
- **Error Details**: Failed sub-tasks provide specific error context

#### CLI Tools
- **Detailed Output**: CLI workflows show step-by-step sub-task execution
- **Progress Indicators**: Visual indicators (🔄, ✅, ❌) for different states
- **Hierarchical Display**: Sub-tasks are indented under their parent steps
- **Error Reporting**: Failed sub-tasks display detailed error information

#### API Integration
- **Extended Status**: API endpoints include current sub-task information
- **WebSocket Updates**: Real-time sub-task updates via WebSocket connections
- **Structured Data**: Sub-task information available in API responses

## Implementation

### Backend Components

#### Workflow Context Enhancement
```python
@dataclass
class WorkflowContext:
    # ... existing fields ...
    sub_task_callback: Optional[Callable] = None
    
    def report_sub_task(self, sub_task_description: str):
        """Report a sub-task being executed"""
        if self.sub_task_callback:
            self.sub_task_callback(sub_task_description)
```

#### Workflow Manager Updates
- **Sub-task Tracking**: Current sub-task stored in workflow state
- **Progress Callbacks**: Enhanced progress callbacks include sub-task information
- **Status API**: Workflow status endpoints include current sub-task details

#### Server Provisioning Integration
- **Commission Step**: Reports database creation, status checking, SSH verification
- **Hardware Discovery**: Shows connection, scanning, processing, and database updates
- **BIOS Configuration**: Details sumtool installation, config extraction, file operations
- **IPMI Setup**: Reports network configuration and connectivity testing

### Frontend Components

#### JavaScript Updates
- **Sub-task Display**: Enhanced progress display includes sub-task information
- **Real-time Updates**: WebSocket handlers process sub-task progress data
- **UI Components**: Progress bars and status displays show sub-task details

#### Dashboard Templates
- **Enhanced Status**: Workflow cards show both step and sub-task information
- **Progress Modal**: Orchestration modal displays detailed sub-task progress
- **Device Cards**: Commissioning progress includes sub-task details

## Example Sub-task Flows

### Server Commissioning
```
🔄 [1/8] Commission Server
    └─ Creating database entry
    └─ Checking server status in MaaS
    └─ Verifying existing commissioning
    └─ Testing SSH connectivity to 192.168.1.100
    └─ Commissioning status: Commissioned
✅ [1/8] Commission Server - COMPLETED
```

### Hardware Discovery
```
🔄 [3/8] Discover Hardware
    └─ Connecting to server for discovery
    └─ Running hardware discovery scan
    └─ Processing discovery results
    └─ Testing IPMI connectivity to 192.168.1.101
    └─ Updating database with hardware info
✅ [3/8] Discover Hardware - COMPLETED
```

### BIOS Configuration
```
🔄 [4/8] Pull BIOS Config
    └─ Connecting to server via SSH
    └─ Detecting server vendor
    └─ Checking for sumtool availability
    └─ Installing sumtool
    └─ Extracting BIOS configuration using sumtool
    └─ Downloading BIOS configuration file
    └─ Parsing BIOS configuration file
✅ [4/8] Pull BIOS Config - COMPLETED
```

## Usage Examples

### Web Interface
1. Navigate to device commissioning or orchestration page
2. Start a workflow (commissioning, provisioning, etc.)
3. Observe real-time sub-task updates in progress displays
4. Monitor both main step progress and detailed sub-task execution

### CLI Tools
```bash
# Monitor workflow with sub-task details
python tools/cli/workflow_monitor.py monitor <workflow_id>

# Real-time monitoring of all workflows
python tools/cli/realtime_monitor.py

# Provision server with detailed progress
python tools/cli/orchestrator.py provision <server_id> --device-type s2.c2.small
```

### API Integration
```bash
# Get workflow status with sub-task information
curl http://localhost:5000/api/orchestration/workflow/<workflow_id>/status

# Response includes current_sub_task field
{
  "id": "provision_abc123_20250101",
  "status": "running",
  "current_step_name": "Pull BIOS Config",
  "current_sub_task": "Extracting BIOS configuration using sumtool",
  "steps": [...]
}
```

## Benefits

### Improved User Experience
- **Transparency**: Users can see exactly what operations are being performed
- **Progress Tracking**: Detailed progress information reduces uncertainty during long operations
- **Debugging**: Failed operations provide specific sub-task error context
- **Monitoring**: Real-time updates eliminate need for manual status checking

### Enhanced Debugging
- **Granular Errors**: Failed sub-tasks pinpoint exact failure points
- **Execution Tracking**: Timestamps help identify performance bottlenecks
- **State Visibility**: Current operation context helps with troubleshooting
- **Log Correlation**: Sub-task information correlates with detailed log entries

### Better System Monitoring
- **Operational Insight**: Administrators can monitor system operations in detail
- **Performance Analysis**: Sub-task timing helps identify optimization opportunities
- **Failure Analysis**: Detailed failure context improves incident response
- **Capacity Planning**: Execution patterns help with resource planning

## Demo

Run the included demo to see enhanced sub-task reporting:

```bash
python examples/workflow_subtasks_demo.py
```

This demo shows:
- Workflow plan with expected sub-tasks
- Example sub-task progression for each step
- Integration points across different interfaces
- Key features and benefits of the enhancement

The enhanced workflow sub-task reporting provides unprecedented visibility into HWAutomation operations, making the system more transparent, debuggable, and user-friendly.
