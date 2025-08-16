# HWAutomation User Guide

Complete user manual for the HWAutomation enterprise hardware automation platform.

## 📋 Table of Contents

- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Web Interface](#web-interface)
- [Workflow Management](#workflow-management)
- [Hardware Management](#hardware-management)
- [MaaS Integration](#maas-integration)
- [Troubleshooting](#troubleshooting)

## 🚀 Installation & Setup

### Quick Start (Docker)

The fastest way to get started is with Docker Compose:

```bash
# Clone the repository
git clone https://github.com/aecwells/hwautomation.git
cd hwautomation

# Start the application
docker compose up

# Access the web interface
open http://localhost:5000
```

### Production Deployment

For production environments, use the container-first architecture:

```bash
# Production deployment with optimizations
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Configure environment variables
cp .env.example .env
# Edit .env with your configuration
```

### Local Development

For development and testing:

```bash
# Install Python dependencies
pip install -e .[dev]

# Set up environment
export PYTHONPATH="$(pwd)/src"
export DATABASE_PATH="./hw_automation.db"

# Run the application
python -m hwautomation.web
```

### System Requirements

- **Python**: 3.9 or higher
- **Docker**: 20.10+ (for container deployment)
- **Memory**: 512MB minimum, 1GB recommended
- **Storage**: 1GB for application, additional space for firmware files
- **Network**: Access to target servers via IPMI/SSH

## ⚙️ Configuration

### Environment Configuration

Key environment variables:

```bash
# Database
DATABASE_PATH=/path/to/database.db

# MaaS Integration
MAAS_URL=http://your-maas-server:5240/MAAS
MAAS_CONSUMER_KEY=your-consumer-key
MAAS_TOKEN_KEY=your-token-key
MAAS_TOKEN_SECRET=your-token-secret

# Logging
LOG_LEVEL=INFO
LOG_FILE=/path/to/hwautomation.log
```

### Device Configuration

Configure hardware devices in `configs/devices/unified_device_config.yaml`:

```yaml
# Device type mappings
device_types:
  a1.c5.large:
    vendor: HPE
    product_family: ProLiant
    motherboard: "ProLiant RL300 Gen11"
    cpu_socket_count: 1
    memory_slot_count: 8
    storage_bay_count: 4
    network_port_count: 2

  d1.c2.medium:
    vendor: Dell
    product_family: PowerEdge
    motherboard: "PowerEdge R650"
    # ... additional configuration
```

### BIOS Templates

Create reusable BIOS configuration templates in `configs/bios/`:

- `template_rules.yaml` - Define BIOS settings by device type
- `preserve_settings.yaml` - Settings to preserve during updates
- `xml_templates/` - Device-specific XML templates

## 🖥️ Web Interface

### Dashboard Overview

The main dashboard provides:

- **Server Status**: Real-time overview of all managed servers
- **Active Workflows**: Current provisioning and configuration tasks
- **System Health**: Component status and alerts
- **Quick Actions**: Common management tasks

### Navigation

| Section | Purpose |
|---------|---------|
| **Dashboard** | System overview and status |
| **Orchestration** | Workflow management and provisioning |
| **Device Management** | Hardware configuration and discovery |
| **Database** | Server information and records |
| **Logs** | System logs and activity monitoring |

### Server Management

#### Adding Servers

1. Navigate to **Device Management**
2. Click **Add Server**
3. Enter server details:
   - Server ID
   - Device Type (from configured types)
   - IPMI IP Address
   - Credentials

#### Server Information

View comprehensive server details:
- Hardware specifications
- BIOS configuration
- Firmware versions
- Network configuration
- Provisioning history

## 🔄 Workflow Management

### Provisioning Workflow

The 7-step server provisioning process:

1. **Hardware Discovery** - Detect and classify hardware
2. **Network Configuration** - Configure IPMI and network settings
3. **BIOS Configuration** - Apply device-specific BIOS settings
4. **Firmware Updates** - Update BIOS, BMC, and other firmware
5. **MaaS Commissioning** - Register server with MaaS
6. **OS Deployment** - Deploy operating system
7. **Validation** - Verify successful deployment

### Starting a Workflow

#### Via Web Interface

1. Go to **Orchestration** → **Server Provisioning**
2. Select target server(s)
3. Choose device type
4. Configure workflow options:
   - Firmware-first mode
   - Network settings
   - Custom templates
5. Click **Start Provisioning**

#### Via API

```python
import requests

# Start provisioning workflow
response = requests.post('http://localhost:5000/api/orchestration/provision', json={
    'server_id': 'server-001',
    'device_type': 'a1.c5.large',
    'target_ipmi_ip': '192.168.1.100',
    'gateway': '192.168.1.1'
})

workflow_id = response.json()['id']
```

### Monitoring Progress

- **Real-time Updates**: WebSocket-based live progress
- **Sub-task Details**: Detailed step-by-step progress
- **Log Streaming**: Live log output from each step
- **Error Handling**: Automatic retry and error reporting

### Workflow Cancellation

Cancel running workflows safely:
- Preserves completed steps
- Graceful cleanup of resources
- Maintains system state consistency

## 🔧 Hardware Management

### Multi-Vendor Support

Supported hardware vendors:

#### HPE (Hewlett Packard Enterprise)
- **Tools**: iLORest, IPMI
- **Protocols**: Redfish, IPMI
- **Supported Models**: ProLiant Gen9, Gen10, Gen11

#### Dell Technologies
- **Tools**: RACADM, IPMI
- **Protocols**: Redfish, IPMI
- **Supported Models**: PowerEdge R640, R650, R750

#### Supermicro
- **Tools**: IPMI, vendor utilities
- **Protocols**: IPMI, Redfish
- **Supported Models**: X11, X12 series

### BIOS Configuration

#### Intelligent Method Selection

The system automatically chooses the best configuration method:

1. **Redfish API** - Modern, standardized interface
2. **Vendor Tools** - Manufacturer-specific utilities
3. **IPMI** - Universal fallback method

#### Configuration Templates

Create device-specific BIOS templates:

```yaml
# Example template rule
device_types:
  a1.c5.large:
    bios_settings:
      boot_mode: "UEFI"
      virtualization: "Enabled"
      hyper_threading: "Enabled"
      memory_patrol_scrub: "Enabled"
```

### Firmware Management

#### Update Process

1. **Discovery** - Detect current firmware versions
2. **Comparison** - Compare with available updates
3. **Download** - Retrieve firmware files
4. **Installation** - Apply updates using vendor tools
5. **Verification** - Confirm successful update

#### Supported Firmware Types

- **BIOS/UEFI** - System firmware
- **BMC/iLO** - Baseboard management controller
- **Network Cards** - NIC firmware
- **Storage Controllers** - RAID and HBA firmware

## 🌐 MaaS Integration

### Configuration

Set up MaaS integration:

```bash
# Configure MaaS endpoint
export MAAS_URL="http://maas.example.com:5240/MAAS"
export MAAS_CONSUMER_KEY="your-consumer-key"
export MAAS_TOKEN_KEY="your-token-key"
export MAAS_TOKEN_SECRET="your-token-secret"
```

### Machine Lifecycle

#### Discovery and Commissioning

1. **Hardware Discovery** - HWAutomation discovers hardware
2. **IPMI Configuration** - Set up remote management
3. **MaaS Registration** - Register machine with MaaS
4. **Commissioning** - MaaS performs hardware inventory
5. **Ready State** - Machine available for deployment

#### Deployment

1. **OS Selection** - Choose operating system image
2. **Configuration** - Apply deployment settings
3. **Installation** - MaaS installs OS
4. **Validation** - Verify successful deployment

### Batch Operations

Process multiple servers efficiently:

```python
# Batch commissioning
response = requests.post('/api/batch/commission', json={
    'server_ids': ['server-001', 'server-002', 'server-003'],
    'device_type': 'a1.c5.large',
    'ipmi_range': '192.168.1.100-102',
    'gateway': '192.168.1.1'
})
```

## 🔍 Troubleshooting

### Common Issues

#### Connection Problems

**IPMI Connection Failed**
```
Error: Unable to establish IPMI connection to 192.168.1.100
```

**Solutions:**
- Verify IPMI credentials
- Check network connectivity
- Ensure IPMI is enabled on target server
- Verify firewall settings

#### BIOS Configuration Issues

**Template Not Found**
```
Error: BIOS template for device type 'a1.c5.large' not found
```

**Solutions:**
- Check device type configuration
- Verify template files exist
- Review template syntax
- Check file permissions

#### Firmware Update Failures

**Download Failed**
```
Error: Failed to download firmware file for HPE ProLiant
```

**Solutions:**
- Check internet connectivity
- Verify firmware repository access
- Ensure sufficient disk space
- Check file permissions

### Logs and Monitoring

#### Log Locations

```bash
# Application logs
tail -f logs/hwautomation.log

# Error logs
tail -f logs/errors.log

# Workflow logs
tail -f logs/workflows.log
```

#### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python -m hwautomation.web
```

#### Health Checks

Monitor system health:

```bash
# Check application status
curl http://localhost:5000/health

# Database connectivity
curl http://localhost:5000/api/database/health

# MaaS connectivity
curl http://localhost:5000/api/maas/health
```

### Performance Optimization

#### Database Maintenance

```bash
# Database cleanup
make data-backup
make data-clean

# Optimize database
sqlite3 hw_automation.db "VACUUM;"
```

#### Memory Management

- Monitor container memory usage
- Adjust Docker memory limits
- Configure garbage collection

#### Network Optimization

- Use local firmware repositories
- Implement caching for large files
- Optimize IPMI connection pooling

## 📞 Support

### Getting Help

- **Documentation**: Check this guide and API documentation
- **Examples**: Review example scripts in `examples/` directory
- **Logs**: Check application logs for error details
- **Issues**: Report bugs on GitHub Issues

### Community Resources

- **GitHub Repository**: https://github.com/aecwells/hwautomation
- **Documentation**: Latest docs in repository
- **Examples**: Usage patterns and integrations

---

*For API integration and advanced usage, see the [API Reference](API_REFERENCE.md) and [Development Guide](DEVELOPMENT.md).*
