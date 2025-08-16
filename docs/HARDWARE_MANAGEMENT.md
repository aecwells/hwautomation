# Hardware Management Guide

Comprehensive guide for BIOS configuration, firmware management, and hardware commissioning in HWAutomation.

## 📋 Table of Contents

- [Overview](#-overview)
- [BIOS Configuration](#-bios-configuration)
- [Firmware Management](#-firmware-management)
- [Hardware Discovery](#-hardware-discovery)
- [Commissioning Workflows](#-commissioning-workflows)
- [Vendor Support](#-vendor-support)
- [Troubleshooting](#-troubleshooting)

## 🔧 Overview

HWAutomation provides enterprise-grade hardware management capabilities:

- **Multi-vendor BIOS configuration** with intelligent method selection
- **Automated firmware management** using real vendor tools
- **Hardware discovery and detection** across different platforms
- **Commissioning workflows** for bare metal provisioning
- **Real-time monitoring** with WebSocket integration

### Supported Hardware

| Vendor | Models | BIOS | Firmware | Discovery |
|--------|---------|------|----------|-----------|
| **HPE** | ProLiant Gen9, Gen10, Gen11 | ✅ | ✅ | ✅ |
| **Dell** | PowerEdge R740, R750, R760 | ✅ | ✅ | ✅ |
| **Supermicro** | X11, X12 series | ✅ | ✅ | ✅ |

### Management Protocols

- **IPMI**: Universal hardware management protocol
- **Redfish**: Modern RESTful API (Phase 1 support)
- **Vendor Tools**: HPE iLORest, Dell RACADM, Supermicro IPMItool
- **SSH**: Direct server access for configuration

## ⚙️ BIOS Configuration

### Configuration Methods

HWAutomation intelligently selects the best configuration method:

1. **Redfish API** (preferred when available)
2. **Vendor-specific tools** (HPE iLORest, Dell RACADM)
3. **IPMI** (universal fallback)

### Device Type Configuration

Configure devices in `configs/devices/unified_device_config.yaml`:

```yaml
device_types:
  a1.c5.large:
    vendor: HPE
    product_family: ProLiant
    motherboard: ProLiant RL300 Gen11
    redfish_preferences:
      prefer_redfish: true
      fallback_to_vendor_tools: true
    ipmi_settings:
      driver: lanplus
      cipher_suite: 3
```

### BIOS Templates

**Template Rules** (`configs/bios/template_rules.yaml`):

```yaml
templates:
  performance_optimized:
    description: "High performance server configuration"
    device_types: ["a1.c5.large", "d1.c2.medium"]
    settings:
      - name: "CPU_Power_Management"
        value: "Maximum_Performance"
      - name: "Memory_Frequency"
        value: "Maximum_Performance"
      - name: "Turbo_Mode"
        value: "Enabled"
      - name: "C_States"
        value: "Disabled"

  power_efficient:
    description: "Energy efficient configuration"
    device_types: ["a1.c5.large"]
    settings:
      - name: "CPU_Power_Management"
        value: "Power_Saving"
      - name: "C_States"
        value: "Enabled"
      - name: "P_States"
        value: "Enabled"
```

**Device Mappings** (`configs/bios/device_mappings.yaml`):

```yaml
device_mappings:
  a1.c5.large:
    vendor: HPE
    model: "ProLiant RL300 Gen11"
    management_method: "redfish_primary"
    default_template: "performance_optimized"
    bios_settings_file: "hpe_gen11_settings.yaml"
```

### Using BIOS Configuration

**Web Interface:**
1. Navigate to Hardware → BIOS Configuration
2. Select device type and target server
3. Choose configuration template
4. Enable dry-run for preview
5. Apply configuration

**Command Line:**
```bash
# Apply BIOS configuration
make bios-config DEVICE_TYPE=a1.c5.large TARGET_IP=192.168.1.100

# Dry run (preview only)
make bios-config-dry-run DEVICE_TYPE=a1.c5.large TARGET_IP=192.168.1.100

# Apply specific template
make bios-apply-template DEVICE_TYPE=a1.c5.large TARGET_IP=192.168.1.100 TEMPLATE=power_efficient
```

**Python API:**
```python
from hwautomation.hardware.bios import BiosConfigManager

manager = BiosConfigManager()

# Apply configuration with dry run
result = manager.apply_bios_config_smart(
    device_type='a1.c5.large',
    target_ip='192.168.1.100',
    username='admin',
    password='password',
    dry_run=True
)

print(f"Configuration result: {result}")
```

### Advanced BIOS Features

**Preserve Settings** (`configs/bios/preserve_settings.yaml`):

```yaml
# Settings to preserve during updates
preserve_always:
  - "Boot_Order"
  - "Network_Boot_Settings"
  - "Security_Settings"

preserve_by_vendor:
  HPE:
    - "Advanced_Memory_Protection"
    - "SR-IOV"
  Dell:
    - "Integrated_RAID_Controller"
```

## 🔄 Firmware Management

### Firmware Architecture

```
firmware/
├── hpe/                     # HPE firmware files
│   ├── bios/
│   ├── bmc/
│   └── drivers/
├── dell/                    # Dell firmware files
│   ├── bios/
│   ├── idrac/
│   └── drivers/
└── supermicro/             # Supermicro firmware files
    ├── bios/
    ├── bmc/
    └── drivers/
```

### Firmware Workflows

**Check Current Versions:**
```python
from hwautomation.hardware.firmware import FirmwareManager

manager = FirmwareManager()

# Get vendor information
device_info = manager.get_vendor_info("a1.c5.large")
print(f"Vendor: {device_info['vendor']}")
print(f"Model: {device_info['motherboard']}")

# Check current firmware versions
versions = manager.check_current_versions(
    target_ip="192.168.1.100",
    vendor="HPE"
)
```

**Download Firmware:**
```python
# Download latest firmware
download_result = manager.download_firmware(
    vendor="HPE",
    device_type="a1.c5.large",
    firmware_type="bios"
)

if download_result.success:
    print(f"Downloaded: {download_result.file_path}")
```

**Apply Firmware Updates:**
```python
# Apply firmware update
update_result = manager.apply_firmware_update(
    target_ip="192.168.1.100",
    firmware_file="/path/to/firmware.bin",
    vendor="HPE",
    update_type="bios"
)

# Monitor update progress
progress = manager.monitor_update_progress(update_result.task_id)
```

### Firmware Configuration

**Repository Configuration** (`configs/firmware/repository_config.yaml`):

```yaml
repositories:
  hpe:
    base_url: "https://support.hpe.com/firmware/"
    auth_required: false
    download_path: "firmware/hpe/"

  dell:
    base_url: "https://dl.dell.com/firmware/"
    auth_required: false
    download_path: "firmware/dell/"

local_repository:
  enabled: true
  path: "./firmware/"
  auto_cleanup: true
  retention_days: 90
```

### Web Interface Firmware Management

**Firmware Page Features:**
- Real-time firmware version checking
- Automated firmware download from vendor sites
- Batch firmware update operations
- Progress monitoring with WebSocket updates
- Firmware history and rollback capabilities

**Navigation:**
1. Go to Hardware → Firmware Management
2. Select device type and target servers
3. Check current firmware versions
4. Download available updates
5. Schedule and monitor updates

## 🔍 Hardware Discovery

### Discovery Methods

**Automated Discovery:**
```python
from hwautomation.hardware.discovery import HardwareDiscoveryManager

discovery = HardwareDiscoveryManager()

# Discover hardware via IPMI
hardware_info = discovery.discover_via_ipmi(
    target_ip="192.168.1.100",
    username="admin",
    password="password"
)

# Discover via SSH (if available)
ssh_info = discovery.discover_via_ssh(
    target_ip="192.168.1.100",
    username="root",
    private_key="/path/to/key"
)
```

**Discovery Results:**
```python
{
    "vendor": "HPE",
    "model": "ProLiant RL300 Gen11",
    "serial_number": "ABC123456",
    "bmc_version": "2.44",
    "bios_version": "U32 v2.44",
    "cpu_info": {
        "count": 2,
        "model": "Intel Xeon Gold 6226R",
        "cores_per_cpu": 16
    },
    "memory_info": {
        "total_gb": 256,
        "modules": 32,
        "speed": "3200 MHz"
    },
    "storage_info": {
        "controllers": ["Smart Array P408i"],
        "drives": [...]
    }
}
```

### Vendor-Specific Detection

**HPE Detection:**
```python
from hwautomation.hardware.discovery.vendors import HPEDiscovery

hpe_discovery = HPEDiscovery()
hpe_info = hpe_discovery.get_detailed_info(
    target_ip="192.168.1.100",
    credentials={"username": "admin", "password": "password"}
)
```

**Dell Detection:**
```python
from hwautomation.hardware.discovery.vendors import DellDiscovery

dell_discovery = DellDiscovery()
dell_info = dell_discovery.get_system_info(
    target_ip="192.168.1.100",
    credentials={"username": "root", "password": "password"}
)
```

## 🚀 Commissioning Workflows

### Commissioning Process

1. **Discovery**: Detect hardware and capabilities
2. **Configuration**: Apply BIOS and network settings
3. **Firmware**: Update to required versions
4. **Validation**: Verify configuration and functionality
5. **Registration**: Add to inventory management system

### Batch Commissioning

**Web Interface:**
1. Navigate to Orchestration → Batch Commission
2. Enter server details (IP range, credentials)
3. Select device type and configuration
4. Configure IPMI settings (optional)
5. Start commissioning workflow

**API Usage:**
```bash
curl -X POST http://localhost:5000/api/batch/commission \
  -H "Content-Type: application/json" \
  -d '{
    "servers": ["server-001", "server-002"],
    "device_type": "a1.c5.large",
    "ipmi_range": "192.168.1.100-110",
    "gateway": "192.168.1.1",
    "credentials": {
      "username": "admin",
      "password": "password"
    }
  }'
```

**Python Workflow:**
```python
from hwautomation.orchestration import WorkflowManager

workflow_manager = WorkflowManager()

# Create commissioning workflow
workflow = workflow_manager.create_commissioning_workflow(
    servers=["server-001", "server-002"],
    device_type="a1.c5.large",
    ipmi_config={
        "ip_range": "192.168.1.100-110",
        "gateway": "192.168.1.1"
    }
)

# Execute workflow
result = workflow_manager.execute_workflow(workflow.id)
```

### Commissioning Configuration

**Workflow Steps:**
1. **Hardware Discovery** - Detect vendor and model
2. **BIOS Configuration** - Apply device-specific settings
3. **IPMI Setup** - Configure management interface
4. **Network Configuration** - Set up networking
5. **Firmware Updates** - Apply required firmware
6. **MaaS Commission** - Register with MaaS (if configured)
7. **Validation** - Final configuration verification

**Custom Configuration:**
```yaml
# configs/commissioning/workflow_config.yaml
commissioning_workflow:
  steps:
    - name: "hardware_discovery"
      enabled: true
      timeout: 300

    - name: "bios_configuration"
      enabled: true
      template: "performance_optimized"
      dry_run: false

    - name: "firmware_updates"
      enabled: true
      auto_download: true
      update_bios: true
      update_bmc: true
```

## 🏭 Vendor Support

### HPE ProLiant

**Supported Models:**
- ProLiant RL300 Gen11
- ProLiant DL380 Gen10
- ProLiant ML350 Gen10

**Tools Used:**
- **iLORest**: Primary BIOS configuration tool
- **Redfish API**: Modern management interface
- **IPMI**: Fallback for basic operations

**Configuration Example:**
```python
from hwautomation.hardware.bios.devices import HPEBiosDevice

hpe_device = HPEBiosDevice()
result = hpe_device.apply_config(
    target_ip="192.168.1.100",
    config={
        "template": "performance_optimized",
        "custom_settings": {
            "Memory_Frequency": "Maximum_Performance"
        }
    }
)
```

### Dell PowerEdge

**Supported Models:**
- PowerEdge R740
- PowerEdge R750
- PowerEdge R760

**Tools Used:**
- **RACADM**: Primary configuration tool
- **Redfish API**: Management interface
- **IPMI**: Universal access

**Configuration Example:**
```python
from hwautomation.hardware.bios.devices import DellBiosDevice

dell_device = DellBiosDevice()
result = dell_device.apply_config(
    target_ip="192.168.1.100",
    config={
        "bios_settings": {
            "ProcPwrPerf": "MaxPerf",
            "MemFrequency": "MaxPerf"
        }
    }
)
```

### Supermicro

**Supported Models:**
- X11 series motherboards
- X12 series motherboards

**Tools Used:**
- **IPMItool**: Primary configuration method
- **Redfish API**: Where available
- **Web interface**: Backup method

**Configuration Example:**
```python
from hwautomation.hardware.bios.devices import SupermicroBiosDevice

sm_device = SupermicroBiosDevice()
result = sm_device.apply_config(
    target_ip="192.168.1.100",
    config={
        "bios_mode": "performance",
        "custom_settings": {
            "CPU_Power_Management": "Performance"
        }
    }
)
```

## 🔧 Troubleshooting

### Common Issues

**BIOS Configuration Failures:**
```bash
# Test IPMI connectivity
ipmitool -I lanplus -H 192.168.1.100 -U admin -P password chassis status

# Verify Redfish endpoint
curl -k https://192.168.1.100/redfish/v1/

# Check vendor tool availability
which ilorest  # HPE
which racadm   # Dell
which ipmitool # Supermicro
```

**Firmware Update Issues:**
```bash
# Check firmware file integrity
md5sum firmware/hpe/bios/firmware.bin

# Verify network connectivity
ping 192.168.1.100
telnet 192.168.1.100 443  # HTTPS
telnet 192.168.1.100 623  # IPMI
```

**Discovery Problems:**
```bash
# Test basic connectivity
nmap -p 22,80,443,623 192.168.1.100

# Check SSH access
ssh -o ConnectTimeout=10 root@192.168.1.100

# Verify IPMI access
ipmitool -I lanplus -H 192.168.1.100 -U admin -P password sensor list
```

### Debug Mode

Enable detailed logging:
```bash
# Set debug logging
export LOG_LEVEL=DEBUG

# Run with debug output
python -m hwautomation.hardware.bios.manager --debug \
  --device-type a1.c5.large \
  --target-ip 192.168.1.100
```

### Performance Optimization

**BIOS Configuration:**
- Use Redfish API when available (faster than vendor tools)
- Batch multiple settings in single operations
- Cache vendor tool outputs
- Implement connection pooling

**Firmware Management:**
- Download firmware files locally before deployment
- Use parallel updates for multiple servers
- Implement update scheduling during maintenance windows
- Monitor BMC/iLO connectivity during updates

**Hardware Discovery:**
- Cache discovery results with TTL
- Use parallel discovery for multiple targets
- Implement vendor-specific optimizations
- Prioritize faster discovery methods

## 📚 Related Documentation

- **Getting Started**: `docs/GETTING_STARTED.md`
- **Workflow Guide**: `docs/WORKFLOW_GUIDE.md`
- **API Reference**: `docs/API_REFERENCE.md`
- **Development Guide**: `docs/DEVELOPMENT_GUIDE.md`
- **Configuration Examples**: `examples/` directory
