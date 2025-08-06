# Vendor-Specific Hardware Discovery

The HWAutomation system now includes comprehensive vendor-specific hardware discovery capabilities for HPE and Supermicro devices, with automatic tool installation and enhanced information gathering.

## Supported Vendors

### Supermicro
- **Tool**: sumtool (Supermicro Update Manager)
- **Capabilities**:
  - System information discovery
  - BIOS information and version details
  - BMC/IPMI configuration and status
  - Automatic installation from official Supermicro repositories

### HPE (Hewlett Packard Enterprise)
- **Tools**: hpssacli, ssacli
- **Capabilities**:
  - Smart Array controller information
  - Storage configuration details
  - iLO (Integrated Lights-Out) detection
  - Automatic installation from HPE repositories

### Dell
- **Tool**: Dell OpenManage (omreport)
- **Capabilities**:
  - Chassis information
  - Service tag and express service code
  - System hardware details
  - Automatic installation from Dell repositories

## Features

### Automatic Tool Installation
The system automatically detects when vendor-specific tools are not installed and attempts to install them:

```python
# Supermicro sumtool installation
- Downloads latest sumtool from Supermicro
- Installs dependencies (wget, alien)
- Configures system paths
- Verifies installation

# HPE tools installation  
- Adds HPE repository and GPG keys
- Installs hpssacli package
- Configures package sources
- Verifies tool availability

# Dell OpenManage installation
- Adds Dell System Update repository
- Installs srvadmin packages
- Starts required services
- Verifies omreport availability
```

### Enhanced Discovery Information

#### Standard Discovery (All Vendors)
- System manufacturer and model
- Serial numbers and UUIDs
- BIOS version and release date
- IPMI/BMC network configuration
- Network interface details

#### Vendor-Specific Enhancements

**Supermicro (sumtool)**:
```json
{
  "product_name": "Super Server",
  "serial_number": "S123456789",
  "manufacturer": "Supermicro",
  "uuid": "12345678-1234-1234-1234-123456789ABC",
  "bios_version": "3.4",
  "bios_date": "10/15/2023",
  "bmc_version": "1.73.14",
  "bmc_ip": "192.168.1.100"
}
```

**HPE (hpssacli)**:
```json
{
  "storage_controllers": [
    {
      "model": "Smart Array P440ar",
      "serial": "PDNLH0BRH7S0J4",
      "firmware": "2.65"
    }
  ],
  "ilo_present": true
}
```

**Dell (omreport)**:
```json
{
  "chassis_model": "PowerEdge R740",
  "service_tag": "1AB2CD3",
  "express_service_code": "12345678901"
}
```

## Usage Examples

### Programmatic Usage

```python
from hwautomation.hardware.discovery import HardwareDiscoveryManager

# Initialize discovery manager
discovery_manager = HardwareDiscoveryManager(config)

# Discover hardware with vendor-specific tools
result = discovery_manager.discover_hardware(
    hostname="server.example.com",
    username="ubuntu"
)

# Access vendor-specific information
if result.success:
    vendor_info = getattr(result, 'vendor_info', {})
    print(f"Vendor-specific info: {vendor_info}")
```

### CLI Usage

```bash
# Test vendor discovery on a specific host
python examples/vendor_discovery_test.py --host server.example.com

# Force specific manufacturer testing
python examples/vendor_discovery_test.py --host server.example.com --manufacturer supermicro

# Verbose output with custom SSH key
python examples/vendor_discovery_test.py --host server.example.com --ssh-key ~/.ssh/custom_key --verbose
```

### Web GUI Usage

The web interface automatically includes vendor-specific information in the hardware discovery results:

1. Navigate to **Hardware Discovery** page
2. Enter target hostname
3. Click **Discover Hardware**
4. View enhanced vendor-specific details in results

### REST API Usage

```bash
# Discover hardware via API
curl -X POST http://localhost:5000/api/hardware/discover \
  -H "Content-Type: application/json" \
  -d '{"hostname": "server.example.com", "username": "ubuntu"}'

# Response includes vendor_info section
{
  "success": true,
  "system_info": {...},
  "ipmi_info": {...},
  "vendor_info": {
    "product_name": "Super Server",
    "bmc_version": "1.73.14"
  }
}
```

## Installation Requirements

### System Requirements
- Ubuntu/Debian-based target systems
- SSH access with sudo privileges
- Internet connectivity for tool downloads

### Automatic Dependencies
The system automatically installs required dependencies:
- `wget` - For downloading vendor tools
- `alien` - For RPM package conversion (Supermicro)
- `apt-key` - For repository key management
- Vendor-specific packages and repositories

### Network Access
Vendor tool installation requires access to:
- `supermicro.com` - Supermicro sumtool downloads
- `downloads.linux.hpe.com` - HPE repository
- `linux.dell.com` - Dell repository

## Error Handling

The system provides comprehensive error handling:

```python
# Discovery continues even if vendor tools fail
result = discovery_manager.discover_hardware(hostname)

# Check for errors
if result.errors:
    for error in result.errors:
        print(f"Warning: {error}")

# Vendor-specific errors are non-fatal
# Standard discovery information is always available
```

## Security Considerations

### Tool Installation Security
- Tools are downloaded from official vendor repositories
- GPG keys are verified where available
- Installation uses standard package managers
- Temporary files are cleaned up

### SSH Security
- Uses SSH key-based authentication
- No password storage or transmission
- Connections are established per-operation
- Automatic connection cleanup

### Privilege Requirements
- `sudo` access required for tool installation
- Hardware information commands require elevated privileges
- BMC/IPMI access may require additional permissions

## Testing and Validation

### Test Script
Use the provided test script to validate vendor discovery:

```bash
# Run comprehensive vendor discovery test
./examples/vendor_discovery_test.py --host your-server.com --verbose

# Test specific vendor functionality
./examples/vendor_discovery_test.py --host hpe-server.com --manufacturer hpe
```

### Expected Output
```
Testing vendor-specific discovery on server.example.com...
============================================================
✅ Hardware discovery completed successfully!

System Information:
  Manufacturer: Supermicro
  Product Name: Super Server
  Serial Number: S123456789
  UUID: 12345678-1234-1234-1234-123456789ABC

🔧 Supermicro Device Detected - Testing sumtool functionality...
  • Testing sumtool installation and commands...
    ✅ sumtool is available
    ✅ System Information - Command executed successfully
    ✅ BIOS Information - Command executed successfully
    ✅ BMC Information - Command executed successfully
```

## Troubleshooting

### Common Issues

**Tool Installation Fails**:
- Check internet connectivity
- Verify sudo privileges
- Check available disk space
- Review system logs for specific errors

**Command Execution Fails**:
- Verify tool installation completed
- Check hardware compatibility
- Review command permissions
- Check for conflicting packages

**Network Discovery Issues**:
- Verify IPMI/BMC is configured and accessible
- Check network interface status
- Confirm SSH connectivity and privileges

### Debug Mode
Enable verbose logging for detailed troubleshooting:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)

# Or use CLI verbose flag
./examples/vendor_discovery_test.py --host server.com --verbose
```

## Integration with Orchestration

Vendor-specific discovery is automatically integrated into the server provisioning workflow:

1. **Step 3: Hardware Discovery** includes vendor-specific tools
2. Enhanced information is used for BIOS configuration
3. Vendor-specific IPMI details improve BMC setup
4. Storage controller information assists in disk configuration

The orchestration system seamlessly handles vendor-specific information without requiring additional configuration.
