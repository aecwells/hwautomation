# Firmware Repository

This directory contains firmware files and related resources for hardware automation.

## Directory Structure

```
firmware/
├── supermicro/           # Super Micro Computer firmware
│   ├── bios/            # BIOS firmware files (.rom)
│   └── bmc/             # BMC firmware files (.bin)
├── hpe/                 # Hewlett Packard Enterprise firmware
│   ├── bios/            # BIOS firmware files (.fwpkg)
│   └── bmc/             # iLO firmware files (.fwpkg)
├── dell/                # Dell Technologies firmware
│   ├── bios/            # BIOS firmware files (.exe)
│   └── bmc/             # iDRAC firmware files (.exe)
└── README.md            # This file
```

## Usage

The firmware repository is configured in `configs/firmware/firmware_repository.yaml` and supports:

- **Automatic firmware downloads** from vendor websites
- **Checksum verification** for firmware file integrity
- **Multiple update methods** (Redfish, vendor tools)
- **Firmware version caching** to avoid repeated downloads

## Firmware File Management

### Adding Firmware Files

1. **Manual Addition**: Place firmware files in the appropriate vendor/type directory
2. **Automatic Download**: Configure download URLs in `firmware_repository.yaml`
3. **Verification**: Ensure checksum files (.sha256) are present for verification

### File Naming Convention

- **BIOS files**: `{model}_{version}.{ext}` (e.g., `X11SPL_3.5.rom`)
- **BMC files**: `{model}_{version}.{ext}` (e.g., `iLO5_2.78.fwpkg`)
- **Checksum files**: `{firmware_file}.sha256`

### Supported File Types

| Vendor     | BIOS Extension | BMC Extension | Notes |
|------------|----------------|---------------|-------|
| Supermicro | .rom           | .bin          | Standard format |
| HPE        | .fwpkg         | .fwpkg        | Smart Update format |
| Dell       | .exe           | .exe          | Dell Update Package |

## Configuration

The firmware repository behavior is controlled by `configs/firmware/firmware_repository.yaml`:

- **base_path**: Location of firmware files (relative to project root)
- **download_enabled**: Enable automatic firmware downloads
- **auto_verify**: Automatically verify checksums
- **vendor configurations**: Per-vendor settings and tool paths

## Security Considerations

1. **Verify Checksums**: Always verify firmware file integrity before updates
2. **Secure Downloads**: Use HTTPS for firmware downloads when possible
3. **Access Control**: Restrict access to firmware files in production
4. **Backup**: Keep firmware backups before applying updates

## Integration

The firmware repository integrates with:

- **FirmwareManager**: Core firmware management functionality
- **Phase 4 Workflows**: Firmware-first provisioning workflows
- **Vendor Tools**: Automatic tool detection and usage
- **Redfish API**: Standardized firmware update interface

## Development

For development and testing:

1. Mock firmware files can be placed in test directories
2. The repository path is configurable via environment variables
3. Unit tests use temporary directories to avoid conflicts

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure write access to firmware directory
2. **Checksum Failures**: Re-download firmware files or update checksums
3. **Path Issues**: Verify relative paths are correct from project root
4. **Vendor Tool Issues**: Check tool installation and path configuration

### Logs

Firmware operations are logged with detailed information:
- Download progress and completion
- Checksum verification results
- Update operation status
- Error details and recovery suggestions
