# Documentation Build System

## Sphinx Documentation

This directory contains both Markdown documentation files and Sphinx configuration for generating HTML documentation.

### Building HTML Documentation

```bash
# Install documentation dependencies
pip install -r ../requirements-all.txt

# Build HTML documentation
make html

# Serve documentation locally
make serve

# Clean build artifacts
make clean
```

### Documentation Structure

- **Markdown Files**: Source documentation in Markdown format
- **Sphinx Configuration**: `conf.py` for Sphinx settings
- **Templates**: Custom themes and templates in `_templates/`
- **Static Files**: CSS and assets in `_static/`
- **Build Output**: Generated HTML in `_build/html/`

### Integration with Web GUI

The built HTML documentation is automatically served by the Flask application at `/docs/` when available.

### Auto-generated API Documentation

Sphinx automatically generates API documentation from Python docstrings using the `autodoc` extension.
