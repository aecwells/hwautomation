# Configuration Directory Structure

This directory contains static configuration files used by HWAutomation.

## Structure

```
configs/
├── bios/           # BIOS configuration templates by device type
├── firmware/       # Firmware repository and update configurations
├── logging/        # Logging configuration templates
└── README.md       # This file
```

## Environment vs Static Configuration

- **Static configs** (this directory): Device types, BIOS templates, firmware repositories
- **Runtime configs**: Environment variables (see `.env.example`)

## Usage

These files are:
- **Development**: Mounted as volumes in docker-compose
- **Production**: Copied into Docker images during build
- **Testing**: Mocked or using test-specific versions

## Validation

Configuration validation happens at runtime through the environment config system.
Missing files will log warnings but use sensible defaults.
