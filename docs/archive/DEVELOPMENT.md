# HWAutomation Development Guide

Complete development documentation for contributing to, extending, and maintaining HWAutomation.

## 📋 Table of Contents

- [Development Setup](#development-setup)
- [Architecture Overview](#architecture-overview)
- [Code Standards](#code-standards)
- [Testing](#testing)
- [Contributing Guidelines](#contributing-guidelines)
- [Extension Development](#extension-development)
- [Debugging](#debugging)
- [Release Process](#release-process)

## 🚀 Development Setup

### Prerequisites

```bash
# System requirements
Python 3.8+
Node.js 16+ (for frontend build)
Git
Docker (optional)
```

### Local Development Environment

1. **Clone and Setup**:
```bash
git clone https://github.com/your-org/hwautomation.git
cd hwautomation

# Create virtual environment
python -m venv hwautomation-env
source hwautomation-env/bin/activate  # Linux/Mac
# hwautomation-env\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements-all.txt
pip install -e .

# Setup pre-commit hooks
pip install pre-commit
pre-commit install
```

2. **Environment Configuration**:
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
MAAS_URL=http://your-maas-server:5240/MAAS
MAAS_CONSUMER_KEY=your-consumer-key
MAAS_TOKEN_KEY=your-token-key
MAAS_TOKEN_SECRET=your-token-secret
DATABASE_PATH=./hw_automation.db
```

3. **Database Setup**:
```bash
# Initialize database
python -c "from hwautomation.database import DbHelper; DbHelper().initialize_database()"

# Run migrations
python tools/migrate_database.py
```

4. **Development Server**:
```bash
# Start development server
make dev-setup
python dev.py

# Or using Flask directly
export FLASK_ENV=development
export FLASK_DEBUG=1
flask run --host=0.0.0.0 --port=5000
```

### Docker Development

```bash
# Build and start development containers
make up

# Access development shell
make shell

# Run tests in container
make test

# View logs
make logs
```

## 🏗️ Architecture Overview

### Project Structure

```
hwautomation/
├── src/hwautomation/           # Main package
│   ├── database/              # Database operations and migrations
│   ├── hardware/              # Hardware management (BIOS, firmware, discovery)
│   ├── maas/                  # MaaS integration
│   ├── orchestration/         # Workflow management
│   ├── web/                   # Flask web interface
│   └── utils/                 # Shared utilities
├── configs/                   # Configuration files
├── tests/                     # Test suite
├── tools/                     # Development and utility scripts
├── examples/                  # Usage examples
├── docs/                      # Documentation
└── firmware/                  # Firmware files and tools
```

### Core Components

#### 1. Database Layer (`src/hwautomation/database/`)

**Purpose**: Data persistence and migrations

**Key Classes**:
```python
class DbHelper:
    """Main database interface."""

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection with context manager support."""

    def createrowforserver(self, server_id: str) -> bool:
        """Create new server record."""

    def updateserverinfo(self, server_id: str, field: str, value: str) -> bool:
        """Update server information."""

class DatabaseMigrator:
    """Handle database schema migrations."""

    def run_migrations(self) -> List[str]:
        """Execute pending migrations."""
```

**Development Patterns**:
```python
# Always use context managers
with db_helper.get_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM servers WHERE id = ?", (server_id,))
    return cursor.fetchone()

# Use transactions for multi-step operations
with db_helper.get_connection() as conn:
    conn.execute("BEGIN")
    try:
        # Multiple operations
        conn.execute("INSERT INTO servers ...")
        conn.execute("UPDATE server_status ...")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
```

#### 2. Hardware Management (`src/hwautomation/hardware/`)

**Purpose**: Hardware discovery, BIOS configuration, firmware management

**Key Classes**:
```python
class BiosConfigManager:
    """BIOS configuration management."""

    def apply_bios_config_smart(
        self,
        device_type: str,
        target_ip: str,
        dry_run: bool = False
    ) -> BiosConfigResult:
        """Apply BIOS configuration intelligently."""

class HardwareDiscoveryManager:
    """Hardware discovery and vendor identification."""

    def discover_hardware(self, target_ip: str) -> HardwareInfo:
        """Discover hardware information."""

class FirmwareManager:
    """Firmware update management."""

    def check_firmware_updates(
        self,
        device_type: str,
        current_versions: Dict[str, str]
    ) -> List[FirmwareUpdate]:
        """Check for available firmware updates."""
```

#### 3. Workflow Orchestration (`src/hwautomation/orchestration/`)

**Purpose**: Workflow management and execution

**Key Classes**:
```python
class WorkflowManager:
    """Main workflow orchestration."""

    def create_provisioning_workflow(
        self,
        server_id: str,
        device_type: str,
        **kwargs
    ) -> Workflow:
        """Create new provisioning workflow."""

class Workflow:
    """Individual workflow instance."""

    def start(self) -> None:
        """Start workflow execution."""

    def cancel(self) -> None:
        """Cancel running workflow."""

class WorkflowContext:
    """Shared context across workflow steps."""

    def report_sub_task(self, description: str) -> None:
        """Report sub-task progress."""
```

**Development Patterns**:
```python
# Always report sub-tasks for visibility
context.report_sub_task("Configuring BIOS settings...")

# Use proper status updates
workflow.status = WorkflowStatus.RUNNING
workflow.update_progress("BIOS Configuration", "Applying template...")

# Handle cancellation gracefully
if workflow.is_cancelled():
    context.report_sub_task("Workflow cancelled, cleaning up...")
    return WorkflowResult(success=False, cancelled=True)
```

#### 4. Web Interface (`src/hwautomation/web/`)

**Purpose**: Flask-based web dashboard and REST API

**Key Components**:
```python
# app.py - Main Flask application
@app.route('/api/orchestration/provision', methods=['POST'])
def start_provisioning():
    """Start server provisioning workflow."""

# serializers.py - API response formatting
class WorkflowSerializer:
    @staticmethod
    def serialize_workflow(workflow: Workflow) -> dict:
        """Convert workflow to API response."""

# templates/ - Jinja2 templates for web interface
```

### Design Principles

#### 1. Separation of Concerns
- **Database**: Pure data operations, no business logic
- **Hardware**: Hardware-specific operations only
- **Orchestration**: Workflow coordination, no hardware details
- **Web**: Presentation and API, minimal business logic

#### 2. Dependency Injection
```python
class WorkflowManager:
    def __init__(self, db_helper: DbHelper, hardware_manager: HardwareManager):
        self.db_helper = db_helper
        self.hardware_manager = hardware_manager
```

#### 3. Configuration-Driven
- Device types defined in YAML
- BIOS templates externalized
- Environment-specific configuration

#### 4. Extensibility
- Plugin architecture for vendor-specific tools
- Configurable workflow steps
- Modular hardware discovery

## 📏 Code Standards

### Python Code Style

**PEP 8 Compliance** with specific guidelines:

```python
# Type hints are required
def apply_bios_config(
    device_type: str,
    target_ip: str,
    settings: Dict[str, Any]
) -> BiosConfigResult:
    """Apply BIOS configuration with proper typing."""
    pass

# Use dataclasses for configuration objects
@dataclass
class BiosConfigResult:
    success: bool
    settings_applied: List[str]
    errors: List[str]
    duration_seconds: float

# Comprehensive docstrings
def discover_hardware(target_ip: str) -> Optional[HardwareInfo]:
    """
    Discover hardware information from target system.

    Args:
        target_ip: IP address of target system

    Returns:
        HardwareInfo object if discovery successful, None otherwise

    Raises:
        NetworkError: If target system is unreachable
        AuthenticationError: If credentials are invalid

    Example:
        >>> hardware_info = discover_hardware("192.168.1.100")
        >>> print(f"Vendor: {hardware_info.vendor}")
    """
    pass

# Error handling with custom exceptions
class HWAutomationError(Exception):
    """Base exception for HWAutomation."""
    pass

class NetworkError(HWAutomationError):
    """Network-related errors."""
    pass

class ConfigurationError(HWAutomationError):
    """Configuration-related errors."""
    pass
```

### Code Organization Patterns

#### 1. Module Structure
```python
# hardware/bios/manager.py
"""BIOS configuration management module."""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from hwautomation.utils.exceptions import ConfigurationError
from hwautomation.hardware.base import BaseHardwareManager

logger = logging.getLogger(__name__)

@dataclass
class BiosConfigResult:
    """Result of BIOS configuration operation."""
    success: bool
    settings_applied: List[str]
    errors: List[str] = None
    duration_seconds: float = 0.0

class BiosConfigManager(BaseHardwareManager):
    """Manages BIOS configuration operations."""

    def __init__(self, config_path: str = None):
        super().__init__()
        self.config_path = config_path or "configs/bios"
        self._load_configurations()

    def _load_configurations(self) -> None:
        """Load BIOS configuration templates."""
        # Implementation
        pass
```

#### 2. Configuration Management
```python
# Use YAML for configuration
@dataclass
class DeviceConfig:
    vendor: str
    model: str
    bios_vendor: str
    management_tools: List[str]

    @classmethod
    def from_yaml(cls, yaml_data: dict) -> 'DeviceConfig':
        """Create DeviceConfig from YAML data."""
        return cls(**yaml_data)

# Configuration loading utility
class ConfigLoader:
    @staticmethod
    def load_device_mappings() -> Dict[str, DeviceConfig]:
        """Load device mappings from YAML."""
        with open("configs/bios/device_mappings.yaml") as f:
            data = yaml.safe_load(f)

        return {
            device_type: DeviceConfig.from_yaml(config)
            for device_type, config in data["device_types"].items()
        }
```

#### 3. Testing Patterns
```python
# Unit tests with pytest
class TestBiosConfigManager:
    @pytest.fixture
    def bios_manager(self):
        return BiosConfigManager(config_path="test_configs")

    @pytest.fixture
    def mock_device_config(self):
        return DeviceConfig(
            vendor="HPE",
            model="ProLiant RL300 Gen11",
            bios_vendor="HPE",
            management_tools=["hponcfg"]
        )

    def test_apply_bios_config_success(self, bios_manager, mock_device_config):
        """Test successful BIOS configuration."""
        result = bios_manager.apply_bios_config_smart(
            device_type="a1.c5.large",
            target_ip="192.168.1.100",
            dry_run=True
        )

        assert result.success
        assert len(result.settings_applied) > 0
        assert result.errors == []

# Integration tests
@pytest.mark.integration
class TestWorkflowIntegration:
    def test_complete_provisioning_workflow(self):
        """Test complete server provisioning."""
        # Implementation
        pass
```

### Database Patterns

```python
# Migration pattern
class Migration_001_InitialSchema:
    """Initial database schema."""

    def up(self, connection: sqlite3.Connection) -> None:
        """Apply migration."""
        connection.execute("""
            CREATE TABLE servers (
                id TEXT PRIMARY KEY,
                device_type TEXT,
                status_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    def down(self, connection: sqlite3.Connection) -> None:
        """Reverse migration."""
        connection.execute("DROP TABLE servers")

# Database operation pattern
class ServerRepository:
    def __init__(self, db_helper: DbHelper):
        self.db_helper = db_helper

    def create(self, server: Server) -> bool:
        """Create new server record."""
        with self.db_helper.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO servers (id, device_type, status) VALUES (?, ?, ?)",
                (server.id, server.device_type, server.status)
            )
            return cursor.rowcount > 0

    def find_by_id(self, server_id: str) -> Optional[Server]:
        """Find server by ID."""
        with self.db_helper.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, device_type, status FROM servers WHERE id = ?",
                (server_id,)
            )
            row = cursor.fetchone()
            return Server(*row) if row else None
```

## 🧪 Testing

### Test Structure

```
tests/
├── unit/                      # Fast, isolated tests
│   ├── test_database/
│   ├── test_hardware/
│   ├── test_orchestration/
│   └── test_web/
├── integration/               # Full system tests
│   ├── test_workflows/
│   ├── test_api/
│   └── test_hardware_integration/
└── conftest.py               # Shared test fixtures
```

### Test Categories

#### Unit Tests
```python
# Fast, isolated, no external dependencies
@pytest.mark.unit
class TestBiosConfigManager:
    def test_load_device_mappings(self, mock_yaml_loader):
        """Test device mapping loading."""
        manager = BiosConfigManager()
        mappings = manager.load_device_mappings()
        assert "a1.c5.large" in mappings

    @patch('hwautomation.hardware.bios.subprocess.run')
    def test_apply_bios_config_dry_run(self, mock_subprocess):
        """Test BIOS config in dry run mode."""
        mock_subprocess.return_value.returncode = 0

        manager = BiosConfigManager()
        result = manager.apply_bios_config_smart(
            device_type="a1.c5.large",
            target_ip="192.168.1.100",
            dry_run=True
        )

        assert result.success
        assert not mock_subprocess.called  # No actual commands in dry run
```

#### Integration Tests
```python
# Full system tests with real components
@pytest.mark.integration
class TestServerProvisioning:
    def test_complete_provisioning_workflow(self, test_database):
        """Test complete server provisioning."""
        db_helper = DbHelper(database_path=test_database)
        workflow_manager = WorkflowManager(db_helper)

        # Create workflow
        workflow = workflow_manager.create_provisioning_workflow(
            server_id="test-server",
            device_type="a1.c5.large"
        )

        # Execute workflow
        workflow.start()

        # Wait for completion
        timeout = time.time() + 60
        while workflow.is_running() and time.time() < timeout:
            time.sleep(1)

        assert workflow.status == WorkflowStatus.COMPLETED
```

### Running Tests

```bash
# Run all tests
make test

# Run unit tests only (fast)
make test-unit

# Run with coverage
make test-cov

# Run specific test file
pytest tests/unit/test_database/test_operations.py -v

# Run tests with specific marker
pytest -m unit -v
pytest -m integration -v
pytest -m slow -v

# Run tests in parallel
pytest -n auto

# Debug test failures
pytest --pdb -x
```

### Test Configuration

```python
# conftest.py - Shared test fixtures
@pytest.fixture
def test_database():
    """Create temporary test database."""
    db_path = tempfile.mktemp(suffix=".db")
    db_helper = DbHelper(database_path=db_path)
    db_helper.initialize_database()
    yield db_path
    os.unlink(db_path)

@pytest.fixture
def mock_maas_client():
    """Mock MaaS client for testing."""
    with patch('hwautomation.maas.MaasClient') as mock:
        mock.return_value.discover_machines.return_value = [
            {"system_id": "test-machine", "hostname": "test-server"}
        ]
        yield mock

@pytest.fixture
def workflow_manager(test_database):
    """Create workflow manager with test database."""
    db_helper = DbHelper(database_path=test_database)
    return WorkflowManager(db_helper)
```

## 🤝 Contributing Guidelines

### Development Workflow

1. **Fork and Clone**:
```bash
git clone https://github.com/your-username/hwautomation.git
cd hwautomation
git remote add upstream https://github.com/original-repo/hwautomation.git
```

2. **Create Feature Branch**:
```bash
git checkout -b feature/your-feature-name
```

3. **Make Changes**:
   - Write code following style guidelines
   - Add comprehensive tests
   - Update documentation
   - Add changelog entry

4. **Commit with Conventional Commits**:
```bash
# Use conventional commit format
git commit -m "feat: add BIOS configuration for Dell PowerEdge"
git commit -m "fix: resolve database migration syntax error"
git commit -m "docs: update API documentation for workflows"
```

5. **Push and Create PR**:
```bash
git push origin feature/your-feature-name
# Create pull request on GitHub
```

### Conventional Commits

We use conventional commits for automated changelog generation:

```bash
# Format: <type>(<scope>): <description>

# Types:
feat:     # New feature
fix:      # Bug fix
docs:     # Documentation changes
style:    # Code style changes (formatting, etc.)
refactor: # Code refactoring
test:     # Adding or updating tests
chore:    # Maintenance tasks

# Examples:
feat(hardware): add support for Supermicro servers
fix(database): resolve migration syntax error
docs(api): update workflow API documentation
test(integration): add end-to-end provisioning test
```

### Code Review Process

1. **Automated Checks**:
   - All tests must pass
   - Code coverage requirements met
   - Style checks pass
   - Documentation builds successfully

2. **Manual Review**:
   - Code follows architectural principles
   - Adequate test coverage
   - Documentation is complete
   - Breaking changes are documented

3. **Approval and Merge**:
   - Requires at least one approval
   - All discussions resolved
   - CI/CD pipeline passes

## 🔧 Extension Development

### Adding New Hardware Vendors

1. **Create Vendor Module**:
```python
# src/hwautomation/hardware/vendors/newvendor.py
from hwautomation.hardware.base import BaseVendorManager

class NewVendorManager(BaseVendorManager):
    """Hardware management for NewVendor servers."""

    def discover_hardware(self, target_ip: str) -> HardwareInfo:
        """Discover NewVendor hardware."""
        # Implementation
        pass

    def apply_bios_config(self, settings: Dict[str, Any]) -> BiosConfigResult:
        """Apply BIOS configuration."""
        # Implementation
        pass
```

2. **Update Device Mappings**:
```yaml
# configs/bios/device_mappings.yaml
device_types:
  nv1.c4.large:
    vendor: NewVendor
    model: ServerModel X1
    bios_vendor: NewVendor
    management_tools:
      - newvendor-cli
```

3. **Add BIOS Templates**:
```yaml
# configs/bios/template_rules.yaml
templates:
  nv1.c4.large:
    boot_mode: UEFI
    virtualization: Enabled
    # Additional settings
```

4. **Register Vendor**:
```python
# src/hwautomation/hardware/discovery.py
VENDOR_MANAGERS = {
    'HPE': HPEManager,
    'Dell': DellManager,
    'Supermicro': SupermicroManager,
    'NewVendor': NewVendorManager,  # Add here
}
```

### Creating Custom Workflows

```python
# Custom workflow example
from hwautomation.orchestration.workflow import BaseWorkflow

class CustomMaintenanceWorkflow(BaseWorkflow):
    """Custom maintenance workflow."""

    def __init__(self, server_id: str, maintenance_type: str):
        super().__init__(f"maintenance-{server_id}")
        self.server_id = server_id
        self.maintenance_type = maintenance_type

    def define_steps(self) -> List[WorkflowStep]:
        """Define workflow steps."""
        steps = [
            WorkflowStep("validate_server", self.validate_server),
            WorkflowStep("backup_config", self.backup_configuration),
        ]

        if self.maintenance_type == "firmware":
            steps.append(WorkflowStep("update_firmware", self.update_firmware))

        if self.maintenance_type == "bios":
            steps.append(WorkflowStep("update_bios", self.update_bios))

        steps.append(WorkflowStep("verify_health", self.verify_health))
        return steps

    def validate_server(self, context: WorkflowContext) -> WorkflowResult:
        """Validate server is ready for maintenance."""
        context.report_sub_task("Validating server status...")
        # Implementation
        return WorkflowResult(success=True)
```

### Adding API Endpoints

```python
# src/hwautomation/web/api/custom.py
from flask import Blueprint, request, jsonify
from hwautomation.web.serializers import WorkflowSerializer

custom_api = Blueprint('custom_api', __name__, url_prefix='/api/custom')

@custom_api.route('/maintenance', methods=['POST'])
def start_maintenance():
    """Start custom maintenance workflow."""
    data = request.get_json()

    # Validate input
    required_fields = ['server_id', 'maintenance_type']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    # Create workflow
    workflow = CustomMaintenanceWorkflow(
        server_id=data['server_id'],
        maintenance_type=data['maintenance_type']
    )

    # Start execution
    workflow.start()

    return jsonify(WorkflowSerializer.serialize_workflow(workflow))

# Register blueprint in main app
# src/hwautomation/web/app.py
from hwautomation.web.api.custom import custom_api
app.register_blueprint(custom_api)
```

## 🐛 Debugging

### Logging Configuration

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Module-specific logging
logger = logging.getLogger('hwautomation.hardware')
logger.setLevel(logging.DEBUG)

# Log to file
import logging.handlers
handler = logging.handlers.RotatingFileHandler(
    'debug.log', maxBytes=10485760, backupCount=5
)
handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
logger.addHandler(handler)
```

### Debugging Workflows

```python
# Add debug breakpoints in workflow steps
def configure_bios(self, context: WorkflowContext) -> WorkflowResult:
    """Configure BIOS settings."""
    import pdb; pdb.set_trace()  # Debug breakpoint

    context.report_sub_task("Starting BIOS configuration...")
    # Debug workflow state
    print(f"Context data: {context.data}")
    print(f"Workflow status: {self.status}")

    # Implementation
    pass

# Monitor workflow progress
workflow = workflow_manager.create_provisioning_workflow(...)
workflow.start()

while workflow.is_running():
    status = workflow.get_status()
    print(f"Progress: {status.progress}% - {status.current_step}")

    # Debug sub-tasks
    for sub_task in status.sub_tasks:
        print(f"  Sub-task: {sub_task.name} - {sub_task.status}")

    time.sleep(5)
```

### Database Debugging

```python
# Enable SQL logging
import sqlite3
sqlite3.enable_callback_tracebacks(True)

# Debug database operations
with db_helper.get_connection() as conn:
    # Enable row factory for easier debugging
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Debug query
    cursor.execute("SELECT * FROM servers WHERE id = ?", (server_id,))
    row = cursor.fetchone()
    print(f"Server data: {dict(row) if row else None}")

    # Check table schema
    cursor.execute("PRAGMA table_info(servers)")
    schema = cursor.fetchall()
    print(f"Table schema: {[dict(col) for col in schema]}")
```

### Hardware Debugging

```python
# Debug hardware discovery
discovery_manager = HardwareDiscoveryManager()

# Enable verbose output
result = discovery_manager.discover_hardware(
    target_ip="192.168.1.100",
    timeout=30,
    verbose=True
)

print(f"Discovery result: {result}")

# Debug BIOS configuration
bios_manager = BiosConfigManager()

# Dry run for debugging
result = bios_manager.apply_bios_config_smart(
    device_type="a1.c5.large",
    target_ip="192.168.1.100",
    dry_run=True,
    verbose=True
)

print(f"BIOS config result: {result}")
print(f"Settings that would be applied: {result.settings_applied}")
```

## 🚀 Release Process

### Automated Release Workflow

The project uses automated release management with conventional commits:

1. **Version Bumping**:
```bash
# Use the release tool
python tools/release.py patch  # 1.0.0 -> 1.0.1
python tools/release.py minor  # 1.0.0 -> 1.1.0
python tools/release.py major  # 1.0.0 -> 2.0.0
```

2. **Changelog Generation**:
```bash
# Generate changelog for current version
python tools/generate_changelog.py

# Changelog is automatically updated in CI/CD
```

3. **Release Creation**:
```bash
# Tag and push release
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions will create release automatically
```

### Manual Release Process

1. **Prepare Release**:
   - Update version in `pyproject.toml`
   - Update version in `package.json`
   - Generate changelog
   - Update documentation

2. **Create Release Branch**:
```bash
git checkout -b release/v1.0.0
git commit -m "chore: prepare release v1.0.0"
git push origin release/v1.0.0
```

3. **Create Release PR**:
   - Create pull request to main
   - Ensure all tests pass
   - Get approvals

4. **Tag and Release**:
```bash
git checkout main
git pull origin main
git tag v1.0.0
git push origin v1.0.0
```

### Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] Changelog generated
- [ ] Version bumped in all files
- [ ] Migration scripts tested
- [ ] Breaking changes documented
- [ ] Security review completed
- [ ] Performance regression tests passed

---

*For more development resources and examples, see the `examples/` and `tools/` directories in the repository.*
