# Contributing to HWAutomation

Welcome to HWAutomation! We're excited that you're interested in contributing. This guide will help you get started with contributing to our hardware automation project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [Contributing Process](#contributing-process)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation Guidelines](#documentation-guidelines)
- [Submitting Changes](#submitting-changes)
- [Review Process](#review-process)
- [Community](#community)

## Code of Conduct

This project follows a Code of Conduct that we expect all contributors to adhere to. Please be respectful, inclusive, and professional in all interactions.

### Our Standards

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Basic understanding of hardware automation concepts
- Familiarity with IPMI, BIOS configuration, and server management

### Development Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourorg/hwautomation.git
   cd hwautomation
   ```

2. **Set up development environment:**
   ```bash
   python tools/setup/setup_dev.py
   ```

3. **Activate virtual environment:**
   ```bash
   source hwautomation-env/bin/activate  # Linux/Mac
   # or
   hwautomation-env\Scripts\activate.bat  # Windows
   ```

4. **Verify setup:**
   ```bash
   python -m pytest
   python tools/quality/code_quality.py --all
   ```

## Contributing Process

### 1. Choose an Issue

- Look for issues labeled `good first issue` for beginners
- Check issues labeled `help wanted` for areas needing contribution
- For new features, create an issue first to discuss the proposal

### 2. Fork and Branch

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/yourusername/hwautomation.git
cd hwautomation

# Add upstream remote
git remote add upstream https://github.com/yourorg/hwautomation.git

# Create a feature branch
git checkout -b feature/your-feature-name
```

### 3. Development Workflow

```bash
# Make your changes
# Run tests frequently
python -m pytest tests/

# Run code quality checks
python tools/quality/code_quality.py --all

# Format code
python tools/quality/code_quality.py --format --fix

# Commit your changes (pre-commit hooks will run automatically)
git add .
git commit -m "feat: add new BIOS configuration feature"
```

## Code Standards

### Code Style

We use automated code formatting and linting tools:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking
- **bandit** for security scanning

### Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(bios): add support for Dell iDRAC 9
fix(maas): resolve timeout issue in machine commissioning
docs(api): update endpoint documentation
test(hardware): add unit tests for discovery manager
```

### Type Hints

Use comprehensive type hints:

```python
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass

@dataclass
class ServerConfig:
    server_id: str
    device_type: str
    ipmi_ip: Optional[str] = None
    
def configure_bios(config: ServerConfig) -> Dict[str, Any]:
    """Configure BIOS settings for a server."""
    pass
```

### Error Handling

Use proper exception handling:

```python
from hwautomation.exceptions import BiosConfigurationError

try:
    result = apply_bios_config(server_config)
except BiosConfigurationError as e:
    logger.error(f"BIOS configuration failed: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise BiosConfigurationError(f"Configuration failed: {e}") from e
```

### Logging

Use structured logging:

```python
import logging

logger = logging.getLogger(__name__)

def process_server(server_id: str) -> None:
    logger.info(f"Starting server processing", extra={
        'server_id': server_id,
        'operation': 'process_server'
    })
    
    try:
        # Process server
        logger.info(f"Server processing completed", extra={
            'server_id': server_id,
            'status': 'success'
        })
    except Exception as e:
        logger.error(f"Server processing failed", extra={
            'server_id': server_id,
            'error': str(e),
            'status': 'failed'
        })
        raise
```

## Testing Guidelines

### Test Types

1. **Unit Tests** (`tests/unit/`): Test individual components in isolation
2. **Integration Tests** (`tests/integration/`): Test component interactions
3. **Performance Tests** (`tests/performance/`): Test performance characteristics

### Writing Tests

```python
import pytest
from unittest.mock import Mock, patch
from hwautomation.bios.config_manager import BiosConfigManager

class TestBiosConfigManager:
    """Test suite for BiosConfigManager."""
    
    @pytest.fixture
    def config_manager(self):
        """Create a BiosConfigManager instance for testing."""
        return BiosConfigManager()
    
    def test_load_device_mappings(self, config_manager):
        """Test loading device mappings."""
        mappings = config_manager.load_device_mappings()
        assert isinstance(mappings, dict)
        assert len(mappings) > 0
    
    @pytest.mark.integration
    def test_apply_config_integration(self, config_manager):
        """Integration test for applying BIOS configuration."""
        # This test requires actual hardware or simulation
        pass
    
    @pytest.mark.performance
    def test_config_performance(self, config_manager):
        """Test configuration application performance."""
        import time
        start_time = time.time()
        # Perform operation
        execution_time = time.time() - start_time
        assert execution_time < 30.0  # Should complete within 30 seconds
```

### Test Coverage

- Maintain at least 80% test coverage
- Write tests for all public APIs
- Include edge cases and error conditions
- Test both success and failure scenarios

### Running Tests

```bash
# Run all tests
python -m pytest

# Run unit tests only
python -m pytest -m unit

# Run with coverage
python -m pytest --cov=src/hwautomation --cov-report=html

# Run performance tests
python -m pytest -m performance
```

## Documentation Guidelines

### Code Documentation

- Write clear docstrings for all public functions and classes
- Use NumPy-style docstrings
- Include examples for complex functions

```python
def apply_bios_config(device_type: str, target_ip: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Apply BIOS configuration to a target device.
    
    This function applies the specified BIOS configuration to the target device
    using the appropriate vendor-specific tools and protocols.
    
    Parameters
    ----------
    device_type : str
        The device type identifier (e.g., 'a1.c5.large')
    target_ip : str
        The IP address of the target device
    config : Dict[str, Any]
        The BIOS configuration settings to apply
    
    Returns
    -------
    Dict[str, Any]
        Results of the configuration operation including status and any errors
    
    Raises
    ------
    BiosConfigurationError
        If the configuration operation fails
    
    Examples
    --------
    >>> config = {'boot_order': ['hdd', 'network']}
    >>> result = apply_bios_config('a1.c5.large', '192.168.1.100', config)
    >>> print(result['status'])
    'success'
    """
```

### API Documentation

- Document all REST API endpoints
- Include request/response examples
- Specify error codes and messages

### README and Guides

- Keep README.md up to date
- Create guides for common use cases
- Document configuration options

## Submitting Changes

### Pull Request Process

1. **Ensure all tests pass:**
   ```bash
   python -m pytest
   python tools/quality/code_quality.py --all
   ```

2. **Update documentation** if needed

3. **Create pull request:**
   - Use a clear, descriptive title
   - Reference related issues
   - Provide detailed description of changes
   - Include screenshots for UI changes

4. **Pull request template:**
   ```markdown
   ## Description
   Brief description of the changes
   
   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Breaking change
   - [ ] Documentation update
   
   ## Testing
   - [ ] Unit tests pass
   - [ ] Integration tests pass
   - [ ] Manual testing completed
   
   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] Tests added/updated
   ```

### Review Process

1. **Automated checks** must pass (CI/CD pipeline)
2. **Code review** by maintainers
3. **Testing** in development environment
4. **Approval** and merge

### Review Criteria

- Code quality and style
- Test coverage
- Documentation completeness
- Performance impact
- Security considerations
- Backward compatibility

## Community

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Pull Request Reviews**: Code-specific discussions

### Getting Help

- Check existing issues and documentation first
- Create detailed bug reports with reproduction steps
- Ask questions in GitHub Discussions
- Tag maintainers for urgent issues

### Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- GitHub contributor statistics

## Development Tips

### Debugging

```bash
# Enable debug logging
export HWAUTOMATION_LOG_LEVEL=DEBUG

# Run with debugging
python -m pdb script.py

# Use VS Code debugger with provided launch configuration
```

### Performance Profiling

```bash
# Profile code execution
python -m cProfile -o profile.stats script.py

# Analyze with snakeviz
pip install snakeviz
snakeviz profile.stats
```

### Local Testing

```bash
# Test with different Python versions using tox
pip install tox
tox

# Test with Docker
docker build -t hwautomation-test .
docker run --rm hwautomation-test pytest
```

## Release Process

For maintainers:

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release tag
4. GitHub Actions will automatically build and deploy

---

Thank you for contributing to HWAutomation! Your contributions help make hardware automation more accessible and reliable for everyone.
