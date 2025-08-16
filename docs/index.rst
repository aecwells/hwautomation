# HWAutomation Documentation

```{toctree}
:maxdepth: 2
:caption: User Documentation

getting-started
hardware-management
workflow-guide
```

```{toctree}
:maxdepth: 2
:caption: Technical Documentation

deployment-guide
development-guide
api-reference
```

```{toctree}
:maxdepth: 2
:caption: Project Information

changelog-and-releases
```

```{toctree}
:maxdepth: 2
:caption: API Documentation

modules
```

## Welcome to HWAutomation

**Enterprise-grade hardware automation platform for bare metal server provisioning, BIOS configuration, and firmware management.**

HWAutomation provides comprehensive automation for enterprise hardware management with modern container-first architecture, production-ready web GUI, and multi-vendor hardware support.

### Quick Navigation

::::{grid} 1 1 2 2
:gutter: 3

:::{grid-item-card} 🚀 Getting Started
:link: getting-started
:link-type: doc

New to HWAutomation? Start here for installation, configuration, and first steps.
:::

:::{grid-item-card} ⚙️ Hardware Management
:link: hardware-management
:link-type: doc

Learn about BIOS configuration, firmware management, and device support.
:::

:::{grid-item-card} 🔄 Workflow Guide
:link: workflow-guide
:link-type: doc

Server provisioning, batch operations, and workflow orchestration.
:::

:::{grid-item-card} 🚀 Deployment Guide
:link: deployment-guide
:link-type: doc

Container deployment, database management, and production setup.
:::

::::

### Key Features

- **🔧 Complete Server Provisioning**: Automated workflows from commissioning to production-ready state
- **💾 Multi-Vendor Firmware Management**: Real vendor tools (HPE iLORest, Dell RACADM, Supermicro IPMItool)
- **⚙️ Intelligent BIOS Configuration**: Device-specific templates with smart method selection
- **🌐 MaaS Integration**: Full Metal-as-a-Service API integration for bare-metal provisioning
- **📊 Real-time Monitoring**: Live progress tracking with WebSocket updates and comprehensive audit trails
- **🏭 Multi-Vendor Support**: HPE Gen9/10/11, Dell PowerEdge, Supermicro X11/X12 series

### Supported Hardware

| Vendor | Models | BIOS Config | Firmware Updates | Discovery |
|--------|---------|-------------|------------------|-----------|
| **HPE** | ProLiant Gen9, Gen10, Gen11 | ✅ | ✅ | ✅ |
| **Dell** | PowerEdge R740, R750, R760 | ✅ | ✅ | ✅ |
| **Supermicro** | X11, X12 series | ✅ | ✅ | ✅ |

### Architecture Overview

HWAutomation uses a modern, modular architecture:

- **Container-First Design**: Multi-stage Docker builds with SQLite database
- **Modular Web Interface**: Flask blueprint architecture with real-time WebSocket updates
- **Enterprise Features**: Comprehensive audit trails, API-first design, extensive error handling
- **Development-Friendly**: Well-documented codebase with comprehensive test coverage

## Indices and tables

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
