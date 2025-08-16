# Getting Started with HWAutomation

HWAutomation is an enterprise hardware automation platform for bare metal server provisioning, BIOS configuration, firmware management, and workflow orchestration.

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [Installation Options](#-installation-options)
- [Configuration](#-configuration)
- [Web Interface](#-web-interface)
- [Basic Workflows](#-basic-workflows)
- [Hardware Management](#-hardware-management)
- [Troubleshooting](#-troubleshooting)
- [Next Steps](#-next-steps)

## 🚀 Quick Start

### Container Deployment (Recommended)

The fastest way to get started:

```bash
# Clone the repository
git clone https://github.com/aecwells/hwautomation.git
cd hwautomation

# Start the application
docker compose up

# Access the web interface
open http://localhost:5000
```

### Local Development

For development and testing:

```bash
# Install dependencies
pip install -e .[dev]

# Set up environment
export PYTHONPATH="$(pwd)/src"
export DATABASE_PATH="./hw_automation.db"

# Run the application
python -m hwautomation.web
```

## 📦 Installation Options

### Option 1: Docker Compose (Production)

```bash
# Production deployment
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check status
docker compose ps
docker compose logs app
```

### Option 2: Python Package

```bash
# Install from PyPI
pip install hwautomation

# Or install from source
git clone https://github.com/aecwells/hwautomation.git
cd hwautomation
pip install -e .[dev]
```

### System Requirements

- **Python**: 3.9 or higher
- **Docker**: 20.10+ (for container deployment)
- **Memory**: 512MB minimum, 1GB recommended
- **Storage**: 1GB for application, additional space for firmware files
- **Network**: Access to target servers via IPMI/SSH

## ⚙️ Configuration

### Environment Setup

Create a `.env` file:

```bash
# Copy template
cp .env.example .env

# Essential configuration
DATABASE_PATH=./hw_automation.db
LOG_LEVEL=INFO

# MaaS Integration (optional)
MAAS_URL=http://your-maas-server:5240/MAAS
MAAS_CONSUMER_KEY=your-consumer-key
MAAS_TOKEN_KEY=your-token-key
MAAS_TOKEN_SECRET=your-token-secret
```

### Device Configuration

Configure hardware in `configs/devices/unified_device_config.yaml`:

```yaml
device_types:
  a1.c5.large:
    vendor: HPE
    product_family: ProLiant
    motherboard: ProLiant RL300 Gen11
    cpu_sockets: 2
    memory_slots: 32
    storage_bays: 24
```

### BIOS Templates

Set up BIOS configurations in `configs/bios/`:

- `device_mappings.yaml` - Hardware to template mappings
- `template_rules.yaml` - BIOS setting templates
- `preserve_settings.yaml` - Settings to preserve during updates

## 🌐 Web Interface

### Dashboard Overview

Access the web interface at `http://localhost:5000`:

1. **Dashboard** - System overview and quick actions
2. **Orchestration** - Workflow management and execution
3. **Hardware** - BIOS configuration and firmware management
4. **Database** - Server inventory and status
5. **Logs** - Real-time logging and activity monitoring

### Key Features

- **Real-time Progress**: Live workflow execution updates
- **Batch Operations**: Commission multiple servers simultaneously
- **Interactive Configuration**: Web-based BIOS and firmware management
- **Status Monitoring**: Track server provisioning stages
- **Log Aggregation**: Centralized logging with filtering

## 🔄 Basic Workflows

### 1. Server Commissioning

**Via Web Interface:**
1. Navigate to Orchestration → Batch Commission
2. Enter server details (IP range, credentials)
3. Select device type and configuration options
4. Start commissioning workflow

**Via API:**
```bash
curl -X POST http://localhost:5000/api/batch/commission \
  -H "Content-Type: application/json" \
  -d '{
    "servers": ["server1", "server2"],
    "device_type": "a1.c5.large",
    "ipmi_range": "192.168.1.100-110"
  }'
```

### 2. BIOS Configuration

**Web Interface:**
1. Go to Hardware → BIOS Configuration
2. Select device type and target server
3. Choose configuration template
4. Apply settings with dry-run option

**Command Line:**
```bash
# Apply BIOS configuration
make bios-config DEVICE_TYPE=a1.c5.large TARGET_IP=192.168.1.100

# Dry run (preview only)
make bios-config-dry-run DEVICE_TYPE=a1.c5.large TARGET_IP=192.168.1.100
```

### 3. Firmware Management

**Web Interface:**
1. Navigate to Hardware → Firmware Management
2. Select device type and check current versions
3. Download and apply firmware updates
4. Monitor update progress

**Python API:**
```python
from hwautomation.hardware.firmware import FirmwareManager

manager = FirmwareManager()
device_info = manager.get_vendor_info("a1.c5.large")
updates = manager.check_firmware_updates(device_info)
```

## 🔧 Hardware Management

### Supported Vendors

- **HPE**: ProLiant servers (Gen9, Gen10, Gen11)
- **Dell**: PowerEdge servers (R740, R750, etc.)
- **Supermicro**: X11, X12 series

### Management Protocols

- **IPMI**: Universal hardware management
- **Redfish**: Modern RESTful API (Phase 1 support)
- **Vendor Tools**: HPE iLORest, Dell RACADM, Supermicro IPMItool

### Device Types

Common device type examples:
- `a1.c5.large` - HPE ProLiant RL300 Gen11
- `d1.c2.medium` - Dell PowerEdge configuration
- `s2.c4.xlarge` - Supermicro high-memory configuration

## 🔍 Troubleshooting

### Common Issues

**Connection Problems:**
```bash
# Test IPMI connectivity
ipmitool -I lanplus -H 192.168.1.100 -U admin -P password chassis status

# Check network accessibility
ping 192.168.1.100
telnet 192.168.1.100 623  # IPMI port
```

**Database Issues:**
```bash
# Reset database
rm hw_automation.db
python -c "from hwautomation.database.helper import DbHelper; DbHelper().init_database()"

# Check database status
sqlite3 hw_automation.db ".tables"
```

**Configuration Problems:**
```bash
# Validate configuration
python -c "from hwautomation.config import load_unified_config; print('Config OK')"

# Check logs
tail -f logs/hwautomation.log
```

### Getting Help

1. **Documentation**: Check `docs/` directory for detailed guides
2. **Logs**: Monitor `logs/hwautomation.log` for detailed error information
3. **Debug Mode**: Set `LOG_LEVEL=DEBUG` for verbose logging
4. **GitHub Issues**: Report bugs and request features

### Debug Commands

```bash
# Show current configuration
make debug

# Run tests
make test

# Check system status
make status

# View logs
make logs
```

## 🎯 Next Steps

### For Users

1. **Read the Workflow Guide**: `docs/WORKFLOW_GUIDE.md`
2. **Explore Hardware Management**: `docs/HARDWARE_MANAGEMENT.md`
3. **Set up MaaS Integration**: Configure MaaS for larger deployments
4. **Customize BIOS Templates**: Create device-specific configurations

### For Developers

1. **Development Guide**: `docs/DEVELOPMENT_GUIDE.md`
2. **API Reference**: `docs/API_REFERENCE.md`
3. **Contributing**: See `CONTRIBUTING.md`
4. **Testing**: Run the test suite with `make test`

### Production Deployment

1. **Deployment Guide**: `docs/DEPLOYMENT_GUIDE.md`
2. **Security**: Configure authentication and access controls
3. **Monitoring**: Set up logging and alerting
4. **Backup**: Implement database backup strategies

## 📚 Additional Resources

- **Main Documentation**: `docs/README.md`
- **Changelog**: `CHANGELOG.md`
- **Examples**: `examples/` directory
- **Configuration Templates**: `configs/` directory
- **Test Cases**: `tests/` directory

---

**Need Help?** Check the troubleshooting section above or review the detailed documentation in the `docs/` directory.
