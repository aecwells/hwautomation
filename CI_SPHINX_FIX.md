# CI Sphinx Documentation Build Fix

## Problem
The CI was failing with this error when building documentation:
```
sphinx.errors.ExtensionError: Could not import extension myst_parser
(exception: No module named 'myst_parser')
```

## Root Cause
The CI documentation job was only installing basic Sphinx dependencies:
```yaml
pip install sphinx sphinx-rtd-theme
```

But the `docs/conf.py` configuration requires additional Sphinx extensions:
- `myst_parser` - For Markdown support
- `sphinx_copybutton` - Copy code button
- `sphinx_tabs.tabs` - Tabbed content
- `sphinx_design` - Grid layouts and design elements
- `linkify_it_py` - URL linkification

## Solution
Updated `.github/workflows/ci.yml` documentation job to:

1. **Install all dependencies**: Use `requirements.txt` which contains all required Sphinx extensions
2. **Use docs Makefile**: Changed from direct `sphinx-build` to `cd docs && make html` for consistency

### Changes Made:
```yaml
# Before
pip install sphinx sphinx-rtd-theme
sphinx-build -b html docs/ docs/_build/html -W

# After
pip install -r requirements.txt
cd docs && make html
```

## Verification
The `requirements.txt` contains all required dependencies:
```
sphinx>=7.0.0
sphinx-rtd-theme>=2.0.0
myst-parser>=2.0.0
sphinx-copybutton>=0.5.0
sphinx-tabs>=3.4.0
sphinx-design>=0.5.0
linkify-it-py>=2.0.0
```

## Result
✅ CI documentation builds should now work correctly
✅ All Sphinx extensions will be available
✅ Consistent build process between local and CI environments
✅ Professional HTML documentation generation in CI

The fix ensures that the CI environment has all the same dependencies as local development and Docker builds, eliminating the missing module errors.
