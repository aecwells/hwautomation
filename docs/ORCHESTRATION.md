# Server Orchestration System

The HWAutomation Server Orchestration System provides end-to-end automation for server provisioning, from initial commissioning through BIOS configuration to IPMI setup and finalization.

## Overview

The orchestration system implements a complete 7-step workflow that automates the entire server deployment process:

```
🔧 1. Commission Server via MaaS     → Power on, run enlistment, gather hardware details
🌐 2. Retrieve Server IP Address     → Query MaaS API for temporary IP assignment
🛠️ 3. Pull BIOS Config via SSH       → SSH into server and export current BIOS settings
✏️ 4. Modify BIOS Configuration      → Apply device-specific templates and settings
🔄 5. Push Updated BIOS Config       → Upload and apply new BIOS configuration
🧭 6. Update IPMI Configuration      → Configure BMC with target IP and settings
✅ 7. Finalize and Tag Server        → Mark as ready and apply metadata tags
```

## Architecture

### Core Components

- **WorkflowManager**: Central coordination engine
- **ServerProvisioningWorkflow**: Complete server provisioning implementation
- **WorkflowStep**: Individual step with retry logic and timeout handling
- **WorkflowContext**: Shared data object passed between steps

### Integration Points

- **MaaS Client**: Server commissioning and management
- **BIOS Manager**: Configuration templates and device-specific settings
- **SSH Manager**: Remote command execution and file transfer
- **IPMI Manager**: BMC configuration and network setup
- **Database**: Metadata storage and state tracking

## Usage Examples

### 1. Web GUI Interface

Access the orchestration system through the web interface:

```
http://127.0.0.1:5000/orchestration
```

Features:
- Start new provisioning workflows
- Monitor progress in real-time
- View active workflows
- Cancel running operations

### 2. Command Line Interface

Use the CLI for scripted operations:

```bash
# Provision a server
orchestrator provision machine-123 s2.c2.small 192.168.100.50

# With rack location
orchestrator provision machine-123 s2.c2.small 192.168.100.50 --rack-location "Rack-A-U10"

# List active workflows
orchestrator list

# Check workflow status
orchestrator status provision_machine-123_1640995200

# Cancel a workflow
orchestrator cancel provision_machine-123_1640995200
```

### 3. Python API

Integrate directly with Python applications:

```python
from hwautomation.orchestration.workflow_manager import WorkflowManager
from hwautomation.orchestration.server_provisioning import ServerProvisioningWorkflow

# Initialize
config = load_config('config.yaml')
workflow_manager = WorkflowManager(config)
provisioning = ServerProvisioningWorkflow(workflow_manager)

# Start provisioning
result = provisioning.provision_server(
    server_id='machine-123',
    device_type='s2.c2.small',
    target_ipmi_ip='192.168.100.50',
    rack_location='Rack-A-U10',
    progress_callback=lambda p: print(f"Step: {p['step_name']}")
)
```

### 4. REST API

Use HTTP endpoints for web integration:

```bash
# Start provisioning
curl -X POST http://127.0.0.1:5000/api/orchestration/provision \
  -H "Content-Type: application/json" \
  -d '{
    "server_id": "machine-123",
    "device_type": "s2.c2.small",
    "target_ipmi_ip": "192.168.100.50",
    "rack_location": "Rack-A-U10"
  }'

# Check status
curl http://127.0.0.1:5000/api/orchestration/workflow/WORKFLOW_ID/status
```

## Configuration

### Required Configuration Sections

```yaml
# config.yaml
maas:
  host: "http://192.168.100.4:5240/MAAS"
  consumer_key: "your-consumer-key"
  token_key: "your-token-key"
  token_secret: "your-token-secret"

bios:
  templates_dir: "configs/bios/xml_templates"
  device_mappings_file: "configs/bios/device_mappings.yaml"

ssh:
  default_username: "ubuntu"
  timeout: 60
  key_file: "/path/to/ssh/key"

ipmi:
  default_netmask: "255.255.255.0"
  default_gateway: "192.168.100.1"
```

### Device Templates

BIOS templates are defined per device type:

```yaml
# configs/bios/device_mappings.yaml
s2.c2.small:
  template_file: "s2_c2_small.xml"
  settings:
    virtualization_enabled: true
    boot_order: ["PXE", "HDD"]
    power_profile: "performance"
```

## Workflow Details

### Step 1: Commission Server via MaaS

- **Trigger**: API request to start provisioning
- **Action**: MaaS powers on server and runs commissioning scripts
- **Timeout**: 30 minutes
- **Retry**: 2 attempts
- **Output**: Server marked as "Commissioned" with hardware inventory

### Step 2: Retrieve Server IP Address

- **Trigger**: Commissioning completion
- **Action**: Query MaaS API for assigned IP address
- **Timeout**: 5 minutes
- **Retry**: 5 attempts (30-second intervals)
- **Output**: Server IP address for SSH access

### Step 3: Pull BIOS Config via SSH

- **Trigger**: IP address available
- **Action**: SSH connection and BIOS export using `sumtool`
- **Timeout**: 10 minutes
- **Retry**: 3 attempts
- **Output**: Current BIOS configuration file

### Step 4: Modify BIOS Configuration

- **Trigger**: BIOS config retrieved
- **Action**: Apply device-specific template modifications
- **Timeout**: 3 minutes
- **Retry**: 2 attempts
- **Output**: Modified BIOS configuration

### Step 5: Push Updated BIOS Config

- **Trigger**: Configuration ready
- **Action**: Upload and apply new BIOS settings, reboot server
- **Timeout**: 10 minutes
- **Retry**: 2 attempts
- **Output**: BIOS changes applied

### Step 6: Update IPMI Configuration

- **Trigger**: Server rebooted with new BIOS
- **Action**: Configure BMC with target IP and network settings
- **Timeout**: 5 minutes
- **Retry**: 3 attempts
- **Output**: IPMI configured and accessible

### Step 7: Finalize and Tag Server

- **Trigger**: IPMI configuration complete
- **Action**: Apply metadata tags and mark server as ready
- **Timeout**: 3 minutes
- **Retry**: 2 attempts
- **Output**: Server ready for deployment

## Error Handling

### Automatic Retry Logic

Each step includes configurable retry logic with exponential backoff:

```python
# Example step configuration
WorkflowStep(
    name="commission_server",
    timeout=1800,      # 30 minutes
    retry_count=2      # 2 retry attempts
)
```

### Error Recovery

- **Transient Errors**: Automatic retry with exponential backoff
- **Configuration Errors**: Immediate failure with detailed error message
- **Network Errors**: Multiple retries with connection validation
- **Timeout Errors**: Configurable timeouts per step type

### Monitoring and Alerting

- **Real-time Progress**: WebSocket updates for GUI
- **Status Tracking**: Detailed step-by-step status information
- **Error Logging**: Comprehensive error logging with context
- **Notification Hooks**: Callback system for custom alerting

## Best Practices

### Pre-Deployment Checklist

1. **MaaS Configuration**
   - Verify MaaS connectivity and credentials
   - Ensure server is enlisted but not commissioned
   - Confirm network configuration

2. **BIOS Templates**
   - Create device-specific templates
   - Test template application on reference hardware
   - Validate sumtool functionality

3. **Network Setup**
   - Configure SSH access to commissioned servers
   - Prepare IPMI network ranges
   - Test connectivity from orchestration host

4. **Monitoring**
   - Set up progress monitoring callbacks
   - Configure error notification systems
   - Prepare rollback procedures

### Production Considerations

- **Parallel Execution**: Orchestrate multiple servers simultaneously
- **Resource Management**: Monitor SSH connection pools
- **State Persistence**: Implement workflow state recovery
- **Security**: Use SSH keys and secure credential storage
- **Validation**: Add post-deployment verification steps

## Troubleshooting

### Common Issues

1. **MaaS Connection Failures**
   - Verify credentials and network connectivity
   - Check MaaS API endpoint accessibility
   - Validate OAuth token permissions

2. **SSH Connection Issues**
   - Confirm server IP accessibility
   - Verify SSH key authentication
   - Check firewall and security group settings

3. **BIOS Configuration Failures**
   - Validate sumtool installation on target servers
   - Check BIOS template format and compatibility
   - Verify hardware model compatibility

4. **IPMI Setup Problems**
   - Confirm ipmitool availability
   - Validate BMC firmware versions
   - Check IPMI network configuration

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
orchestrator --verbose provision machine-123 s2.c2.small 192.168.100.50
```

### Log Analysis

Check application logs for detailed error information:

```bash
# Web GUI logs
tail -f /var/log/hwautomation/gui.log

# Orchestration logs
tail -f /var/log/hwautomation/orchestration.log
```

## Integration Examples

### CI/CD Pipeline Integration

```yaml
# .github/workflows/server-provisioning.yml
name: Server Provisioning
on:
  workflow_dispatch:
    inputs:
      server_id:
        description: 'Server ID'
        required: true
      device_type:
        description: 'Device Type'
        required: true

jobs:
  provision:
    runs-on: self-hosted
    steps:
      - name: Provision Server
        run: |
          orchestrator provision ${{ github.event.inputs.server_id }} \
            ${{ github.event.inputs.device_type }} \
            ${{ secrets.IPMI_IP_POOL }}
```

### Monitoring Integration

```python
# Custom progress monitoring
def monitoring_callback(progress):
    # Send to monitoring system
    metrics.gauge('provisioning.progress', progress['step'] / progress['total_steps'])
    
    if progress['status'] == 'failed':
        alerts.send_alert(f"Provisioning failed: {progress['error']}")

# Use with provisioning
provisioning.provision_server(
    server_id='machine-123',
    device_type='s2.c2.small',
    target_ipmi_ip='192.168.100.50',
    progress_callback=monitoring_callback
)
```

This orchestration system provides a robust, scalable solution for automated server provisioning that integrates all the existing HWAutomation components into a cohesive workflow.
