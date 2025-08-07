# GitHub Copilot Instructions for HWAutomation

## Project Overview

HWAutomation is a Python-based hardware automation system for bare metal server provisioning, BIOS configuration, and hardware discovery. The project orchestrates complex workflows involving MaaS (Metal-as-a-Service), IPMI management, and vendor-specific hardware tools.

## Architecture & Core Components

### 1. **Orchestration Layer** (`src/hwautomation/orchestration/`)
- **Purpose**: Workflow management and step-by-step server provisioning
- **Key Classes**:
  - `WorkflowManager`: Main orchestration engine
  - `Workflow`: Individual workflow instances with steps
  - `WorkflowContext`: Shared context data across workflow steps
  - `ServerProvisioningWorkflow`: Complete server provisioning pipeline

### 2. **Hardware Management** (`src/hwautomation/hardware/`)
- **Purpose**: Hardware discovery, BIOS configuration, and vendor tools
- **Key Classes**:
  - `BiosConfigManager`: BIOS configuration and template management
  - `HardwareDiscoveryManager`: Hardware detection and vendor identification
  - `IpmiManager`: IPMI interface management
  - `RedfishManager`: Standardized hardware management via Redfish API (Phase 1)

### Redfish Integration (Phase 1)
- **Purpose**: Industry-standard hardware management using DMTF Redfish API
- **Capabilities**: Basic operations (power control, system info, simple BIOS settings)
- **Integration**: Hybrid approach - Redfish for standard operations, vendor tools for advanced features
- **Configuration**: Device-specific Redfish preferences in `device_mappings.yaml`

### 3. **MaaS Integration** (`src/hwautomation/maas/`)
- **Purpose**: Metal-as-a-Service API integration
- **Key Classes**:
  - `MaasClient`: REST API client for MaaS operations
  - Handles machine commissioning, deployment, and status management

### 4. **Database Layer** (`src/hwautomation/database/`)
- **Purpose**: SQLite-based data persistence with migrations
- **Key Classes**:
  - `DbHelper`: Database operations and server information management
  - `DatabaseMigrator`: Schema versioning and migrations

### 5. **Web Interface** (`src/hwautomation/web/`)
- **Purpose**: Flask-based web dashboard with real-time updates
- **Key Components**:
  - `app.py`: Main Flask application with REST API endpoints
  - Templates: Jinja2 templates for dashboard, orchestration, device management
  - Real-time WebSocket communication for workflow progress

## Configuration Management

### BIOS Configuration System
- **Device Mappings** (`configs/bios/device_mappings.yaml`): Hardware specifications by device type
- **Template Rules** (`configs/bios/template_rules.yaml`): BIOS settings templates
- **Preserve Settings** (`configs/bios/preserve_settings.yaml`): Settings to preserve during configuration

### Device Types
- **Current naming scheme**: `a1.c5.large`, `d1.c1.small`, `d1.c2.medium`, etc.
- **Legacy naming scheme**: `s2_c2_small`, `s2_c2_medium`, `s2_c2_large` (template rules only)

## API Endpoints

### Orchestration APIs
- `POST /api/orchestration/provision` - Start server provisioning workflow
- `GET /api/orchestration/workflows` - List all workflows
- `GET /api/orchestration/workflow/{id}/status` - Get workflow status
- `POST /api/orchestration/workflow/{id}/cancel` - Cancel running workflow

### Batch Operations
- `POST /api/batch/commission` - Start batch commissioning with optional IPMI/gateway

### MaaS Integration
- `GET /api/maas/discover` - Discover available machines from MaaS

## Workflow System

### Workflow Lifecycle
1. **PENDING** → **RUNNING** → **COMPLETED**/**FAILED**/**CANCELLED**
2. Sub-task reporting via `context.report_sub_task()`
3. Real-time progress updates through WebSocket
4. Cancellation support with graceful cleanup

### Key Workflow Features
- **Sub-task Progress**: Detailed operation visibility
- **Context Passing**: Shared data between workflow steps
- **Error Handling**: Comprehensive exception management
- **Cancellation**: Ability to stop long-running workflows

## Testing Structure

### Test Organization
- **Unit Tests**: `tests/unit/` - Fast, isolated component tests
- **Integration Tests**: `tests/integration/` - Full system integration tests
- **Tool Tests**: `tools/testing/` - Specific functionality tests

### Test Configuration
- Uses `pytest` with coverage reporting
- Markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
- Examples directory excluded from test runs

## Development Guidelines

### Code Style & Patterns
1. **Type Hints**: Use comprehensive type annotations
2. **Dataclasses**: Prefer dataclasses for configuration objects
3. **Context Managers**: Use for database connections and resource management
4. **Async/Threading**: Background workflow execution with threading
5. **Error Handling**: Comprehensive exception hierarchy

### Database Patterns
```python
# Always use context managers for database operations
with db_helper.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM servers WHERE id = ?", (server_id,))
    result = cursor.fetchone()
```

### Workflow Patterns
```python
# Always report sub-tasks for user visibility
context.report_sub_task("Configuring BIOS settings...")

# Use proper status updates
workflow.status = WorkflowStatus.RUNNING
workflow.update_progress(step_name, "In progress...")
```

### API Response Patterns
```python
# Include optional fields conditionally
response_data = {'success': True, 'id': workflow_id}
if target_ipmi_ip:
    response_data['target_ipmi_ip'] = target_ipmi_ip
if gateway:
    response_data['gateway'] = gateway
```

## Environment & Configuration

### Required Environment Variables
- `MAAS_URL`: MaaS server URL
- `MAAS_CONSUMER_KEY`: OAuth consumer key
- `MAAS_TOKEN_KEY`: OAuth token key  
- `MAAS_TOKEN_SECRET`: OAuth token secret
- `DATABASE_PATH`: SQLite database file path

### Configuration Files
- `.env`: Environment variables (not in git)
- `config.yaml`: Application configuration
- `docker-compose.yml`: Docker services configuration

## Common Operations

### Starting a Workflow
```python
workflow = provisioning_workflow.create_provisioning_workflow(
    server_id=server_id,
    device_type=device_type,
    target_ipmi_ip=target_ipmi_ip,  # Optional
    gateway=gateway  # Optional
)
```

### BIOS Configuration
```python
result = manager.apply_bios_config_smart(
    device_type='a1.c5.large',
    target_ip='192.168.1.100',
    username='ADMIN',
    password='password',
    dry_run=True  # For testing
)
```

### Database Operations
```python
# Create server record
db_helper.createrowforserver(server_id)

# Check existence
exists_list = db_helper.checkifserveridexists(server_id)
server_exists = exists_list[0] if exists_list else False

# Update server info
db_helper.updateserverinfo(server_id, 'status_name', 'Ready')
```

## Security Considerations

1. **IPMI Credentials**: Store securely, never log
2. **SSH Keys**: Use key-based authentication where possible
3. **API Authentication**: Implement proper authentication for web endpoints
4. **Input Validation**: Sanitize all user inputs, especially IP addresses

## Performance Guidelines

1. **Database**: Use connection pooling and proper indexing
2. **Workflows**: Run in background threads to avoid blocking
3. **API**: Implement pagination for large datasets
4. **Caching**: Cache BIOS configurations and device mappings

## Debugging & Logging

### Logging Patterns
```python
logger = logging.getLogger(__name__)
logger.info(f"Starting workflow {workflow_id} for {server_id}")
logger.error(f"Workflow {workflow_id} failed: {e}")
```

### Debug Information
- Use `make debug` to print environment variables
- Check workflow status via API endpoints
- Monitor logs via `make logs` for Docker deployments

## Recent Enhancements

### Workflow Sub-task Reporting
- Added `context.report_sub_task()` throughout workflows
- Real-time progress updates in web interface
- Detailed operation visibility for debugging

### Optional IPMI Configuration
- IPMI IPs only assigned when range provided
- Gateway parameter support for network configuration
- Flexible batch commissioning options

### Workflow Cancellation
- Complete cancellation infrastructure
- Graceful workflow interruption
- Status tracking and cleanup

## Makefile Targets

- `make test` - Run all tests locally
- `make test-unit` - Fast unit tests only
- `make test-cov` - Tests with coverage
- `make dev-setup` - Setup development environment
- `make up` - Start Docker containers
- `make shell` - Access container shell

When working on this project, always consider the workflow-centric architecture, maintain comprehensive logging, and ensure proper error handling throughout the system.
