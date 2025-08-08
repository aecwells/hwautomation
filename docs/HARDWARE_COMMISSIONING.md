# Hardware Discovery and Commissioning

This document describes the comprehensive hardware discovery and automated commissioning capabilities for multi-vendor server environments.

## 🎯 Overview

The HWAutomation system provides automated hardware discovery and intelligent commissioning workflows that:
- **Discover Hardware**: Automatic detection of system information and IPMI configuration
- **Commission Servers**: Streamlined MaaS integration with progress tracking
- **Multi-vendor Support**: Works with HPE, Supermicro, Dell, and other manufacturers
- **Real-time Monitoring**: Live progress updates during commissioning operations

## 🔍 Hardware Discovery System

### Discovery Capabilities

#### System Information Detection
Automatically discovers comprehensive system details:
- **Hardware Identity**: Manufacturer, product name, serial number, system UUID
- **BIOS Information**: Version, date, and vendor details
- **CPU Details**: Model, core count, and architecture information
- **Memory Configuration**: Total memory, module information, and speeds
- **Network Interfaces**: Interface names, MAC addresses, and IP configurations

#### IPMI Configuration Discovery
Detects BMC network configuration:
- **IPMI IP Address**: Current BMC IP assignment
- **Network Settings**: Gateway, netmask, and VLAN configuration
- **MAC Address**: BMC network interface identification
- **Access Methods**: Available IPMI channels and authentication

### Discovery Architecture

#### `HardwareDiscoveryManager`
Main discovery coordination class:
```python
class HardwareDiscoveryManager:
    def discover_system_info(self, target_ip: str, username: str, password: str) -> SystemInfo
    def discover_ipmi_info(self, target_ip: str, username: str, password: str) -> IPMIInfo
    def discover_network_interfaces(self, target_ip: str, username: str, password: str) -> List[NetworkInterface]
    def comprehensive_discovery(self, target_ip: str, username: str, password: str) -> HardwareDiscovery
```

#### Data Classes for Discovery Results
```python
@dataclass
class SystemInfo:
    manufacturer: str
    product_name: str
    serial_number: str
    bios_version: str
    cpu_model: str
    memory_total: str

@dataclass
class IPMIInfo:
    ip_address: str
    mac_address: str
    gateway: str
    netmask: str

@dataclass
class HardwareDiscovery:
    system_info: SystemInfo
    ipmi_info: IPMIInfo
    network_interfaces: List[NetworkInterface]
    discovery_timestamp: datetime
```

### Discovery Methods

#### SSH-Based Discovery
Remote discovery via SSH connections to commissioned servers:
- **System Commands**: Uses dmidecode, ipmitool, and ip commands
- **Error Handling**: Robust error handling for missing tools or permissions
- **Connection Management**: Automatic SSH connection lifecycle management
- **Timeout Handling**: Configurable timeouts for discovery operations

#### Network Scanning
Network range scanning for IPMI address discovery:
- **Port Scanning**: Tests connectivity to IPMI ports (623/udp, 22/tcp)
- **Range Scanning**: Supports CIDR notation for network ranges
- **Concurrent Discovery**: Parallel discovery for improved performance
- **Hostname Resolution**: Automatic hostname resolution for discovered systems

## 🚀 Enhanced Commissioning System

### Commissioning Workflow

#### 8-Step Enhanced Process
The complete commissioning workflow with hardware discovery:

```
🔧 1. Commission Server via MaaS     → Power on, run enlistment, gather hardware details
🌐 2. Retrieve Server IP Address     → Query MaaS API for temporary IP assignment
🔍 3. Hardware Discovery             → SSH discovery of system and IPMI information
🛠️ 4. Pull BIOS Config via SSH       → Export current BIOS settings and configuration
✏️ 5. Modify BIOS Configuration      → Apply device-specific templates and settings
🔄 6. Push Updated BIOS Config       → Upload and apply new BIOS configuration
🧭 7. Update IPMI Configuration      → Configure BMC with target IP and settings
✅ 8. Finalize and Tag Server        → Mark as ready and apply metadata tags
```

#### Firmware-First Option
Optional firmware-first commissioning for optimal system state:
- **Pre-commissioning Firmware Updates**: Update firmware before BIOS configuration
- **Vendor Tool Integration**: Real vendor tools for firmware management
- **Reboot Coordination**: Intelligent reboot handling during firmware updates
- **Validation Steps**: Complete firmware and configuration validation

### Real-time Progress Tracking

#### User Experience Enhancements
- **Immediate Modal Closure**: Commission modal closes immediately after starting
- **Background Processing**: Commissioning runs without blocking UI
- **Live Progress Updates**: Real-time progress on device cards and list views
- **Visual Feedback**: Progress bars, step descriptions, and status indicators

#### Progress Tracking Features

##### Visual Elements
- **Animated Progress Bar**: Shows completion percentage with pulse animation
- **Current Step Display**: Real-time display of current commissioning operation
- **Status Badge Updates**: Dynamic status changes (Pending → Commissioning → Ready)
- **Button State Management**: Commission button shows appropriate state

##### Technical Implementation
```javascript
// Real-time progress tracking
const commissioningWorkflows = new Map();

function trackCommissioningProgress(systemId, workflowId) {
    const pollStatus = () => {
        fetch(`/api/orchestration/workflow/${workflowId}/status`)
            .then(response => response.json())
            .then(data => updateProgressDisplay(systemId, data));
    };

    const interval = setInterval(pollStatus, 3000);
    commissioningWorkflows.set(systemId, { workflowId, interval });
}
```

### API Integration

#### Discovery Endpoints
```bash
# Single host hardware discovery
POST /api/hardware/discover
{
    "target_ip": "192.168.1.100",
    "username": "root",
    "password": "password"
}

# Network range IPMI scanning
POST /api/hardware/scan-network
{
    "network_range": "192.168.1.0/24",
    "ports": [623, 22]
}
```

#### Commissioning Endpoints
```bash
# Start commissioning workflow
POST /api/orchestration/provision
{
    "server_id": "srv001",
    "device_type": "a1.c5.large",
    "target_ipmi_ip": "192.168.1.100"
}

# Check commissioning progress
GET /api/orchestration/workflow/{workflow_id}/status
```

## 🛠️ CLI Tools

### Hardware Discovery Command
```bash
# Discover single host
python scripts/hardware_discovery.py \
    --target-ip 192.168.1.100 \
    --username root \
    --password password \
    --output-format json

# Scan network range
python scripts/hardware_discovery.py \
    --scan-network 192.168.1.0/24 \
    --ports 623 22 \
    --verbose
```

### Discovery Output Formats
- **JSON**: Structured data for API integration
- **YAML**: Human-readable configuration format
- **Text**: Formatted console output for debugging
- **CSV**: Tabular format for spreadsheet analysis

## 🌐 Web Interface Integration

### Discovery Dashboard
- **Device Management**: View discovered hardware information
- **Network Scanning**: Initiate network-wide IPMI discovery
- **Discovery History**: Track discovery operations and results
- **Configuration Export**: Export discovered configurations

### Commissioning Interface
- **One-click Commissioning**: Start commissioning from device list
- **Progress Monitoring**: Real-time progress with detailed step information
- **Batch Operations**: Commission multiple servers simultaneously
- **Error Reporting**: Clear error messages with suggested remediation

## 🔧 Configuration Options

### Discovery Settings
```yaml
discovery:
  ssh_timeout: 30
  command_timeout: 60
  max_concurrent_discoveries: 10
  retry_count: 3

network_scanning:
  port_timeout: 5
  concurrent_scans: 50
  default_ports: [623, 22, 443]
```

### Commissioning Settings
```yaml
commissioning:
  progress_poll_interval: 3000  # milliseconds
  max_workflow_timeout: 3600    # seconds
  auto_cleanup_completed: true
  error_retry_interval: 10000   # milliseconds
```

## 📊 Monitoring and Metrics

### Discovery Analytics
- **Discovery Success Rates**: Track successful vs failed discoveries
- **Performance Metrics**: Discovery timing and system resource usage
- **Hardware Inventory**: Maintain inventory of discovered systems
- **Change Detection**: Track hardware changes over time

### Commissioning Metrics
- **Commissioning Duration**: Track time to complete commissioning
- **Success Rates by Device Type**: Monitor device-specific success rates
- **Error Patterns**: Analyze common failure points and causes
- **Resource Utilization**: Monitor system resource usage during commissioning

This comprehensive hardware discovery and commissioning system provides enterprise-grade automation with complete visibility, intelligent discovery, and robust progress tracking for reliable bare-metal server management.
