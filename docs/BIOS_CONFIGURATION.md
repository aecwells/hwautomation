# BIOS Configuration System

This document describes the BIOS configuration system for managing device-specific BIOS settings using XML templates.

## Overview

The BIOS Configuration Manager allows you to:
- Define device types with specific BIOS requirements (e.g., `s2_c2_small`, `s2_c2_medium`, `s2_c2_large`)
- Create and manage XML templates for BIOS configurations
- Apply configurations to target systems via IPMI/RedFish
- Organize configurations by motherboard compatibility

## Device Types

### s2_c2_small
- **Description**: Small compute nodes - dual core, 8GB RAM
- **Motherboards**: X11SCE-F
- **Use Case**: Basic compute workloads, development environments

### s2_c2_medium  
- **Description**: Medium compute nodes - quad core, 16GB RAM
- **Motherboards**: X11DPT-B, X11DPFR-SN
- **Use Case**: Standard production workloads, virtualization

### s2_c2_large
- **Description**: Large compute nodes - 8+ core, 32GB+ RAM
- **Motherboards**: X12DPT-B, X12STE-F, X13DET-B
- **Use Case**: High-performance computing, heavy workloads

## Configuration Structure

Device configurations are stored in YAML format with the following structure:

```yaml
device_types:
  s2_c2_small:
    description: "Small compute nodes - dual core, 8GB RAM"
    motherboards: ["X11SCE-F"]
    cpu_configs:
      hyperthreading: true
      turbo_boost: true
      power_profile: "balanced"
    memory_configs:
      ecc_enabled: true
      memory_speed: "auto"
    boot_configs:
      boot_mode: "uefi"
      secure_boot: false
      pxe_boot: true
```

## XML Templates

XML templates define the actual BIOS settings that will be applied:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<BiosConfig deviceType="s2_c2_small" motherboard="X11SCE-F">
  <CPU>
    <Setting name="hyperthreading" value="enabled"/>
    <Setting name="turbo_boost" value="enabled"/>
    <Setting name="power_profile" value="balanced"/>
  </CPU>
  <Memory>
    <Setting name="ecc_enabled" value="enabled"/>
    <Setting name="memory_speed" value="auto"/>
  </Memory>
  <Boot>
    <Setting name="boot_mode" value="uefi"/>
    <Setting name="secure_boot" value="disabled"/>
    <Setting name="pxe_boot" value="enabled"/>
  </Boot>
</BiosConfig>
```

## Directory Structure

```
configs/
└── bios/
    ├── device_mappings.yaml        # Device type definitions
    └── xml_templates/              # XML configuration templates
        ├── s2_c2_small.xml
        ├── s2_c2_medium.xml
        └── s2_c2_large.xml
```

## Command-Line Usage

### List Device Types
```bash
python scripts/bios_manager.py list-types
```

### Show Configuration
```bash
python scripts/bios_manager.py show-config s2_c2_small
```

### Generate XML
```bash
python scripts/bios_manager.py generate-xml s2_c2_small --output s2_small_config.xml
```

### Apply Configuration
```bash
python scripts/bios_manager.py apply-config s2_c2_small 192.168.1.100 --username ADMIN --password mypass
```

## Python API Usage

```python
from hwautomation.hardware.bios_config import BiosConfigManager

# Initialize manager
manager = BiosConfigManager()

# Get device types
device_types = manager.get_device_types()

# Get configuration for a device type
config = manager.get_device_config('s2_c2_small')

# Generate XML configuration
xml_config = manager.generate_xml_config('s2_c2_small')

# Apply configuration to a system
manager.apply_bios_config('s2_c2_small', '192.168.1.100', 'ADMIN', 'password')
```

## Adding New Device Types

1. **Edit device_mappings.yaml**:
   ```yaml
   device_types:
     my_new_device:
       description: "Custom device type"
       motherboards: ["X13DET-B"]
       cpu_configs:
         hyperthreading: true
       memory_configs:
         ecc_enabled: true
       boot_configs:
         boot_mode: "uefi"
   ```

2. **Create XML template** (optional):
   ```bash
   python scripts/bios_manager.py generate-xml my_new_device --output configs/bios/xml_templates/my_new_device.xml
   ```

3. **Test the configuration**:
   ```bash
   python scripts/bios_manager.py show-config my_new_device
   ```

## Integration Points

The BIOS Configuration Manager integrates with:
- **IPMI Manager**: For legacy BIOS configuration application
- **RedFish Manager**: For modern BMC-based configuration
- **MAAS Client**: For automated deployment workflows
- **Database System**: For tracking applied configurations

## Best Practices

1. **Version Control**: Keep XML templates in version control
2. **Testing**: Test configurations on development systems first
3. **Documentation**: Document any custom settings or deviations
4. **Backup**: Always backup existing BIOS settings before applying new ones
5. **Validation**: Validate XML templates before saving
