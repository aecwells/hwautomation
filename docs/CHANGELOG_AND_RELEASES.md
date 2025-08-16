# Changelog and Release Management

This document explains how to use the automated changelog generation and release management system in HWAutomation.

## Overview

The project uses:
- **Conventional Commits** for structured commit messages
- **Automated changelog generation** from git history
- **Semantic versioning** for releases
- **Automated release management** with version bumping

## Conventional Commits

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools
- `ci`: Changes to CI configuration files and scripts
- `build`: Changes that affect the build system or external dependencies

### Examples

```bash
feat(api): add user authentication endpoint
fix(database): resolve connection timeout issue
docs: update API documentation
feat!: send an email to the customer when a product is shipped
feat(lang): add polish language
fix: correct minor typos in code
```

### Breaking Changes

Add `!` after the type/scope or include `BREAKING CHANGE:` in the footer:

```bash
feat!: remove deprecated API endpoints
feat(api): add new authentication method

BREAKING CHANGE: The old authentication method is no longer supported.
```

## Setup

### 1. Configure Conventional Commits Template

```bash
make setup-conventional-commits
```

This sets up a git commit template to help you write conventional commits.

### 2. Use the Template

```bash
# Use git commit without -m to open the template
git commit

# Or continue using -m for quick commits
git commit -m "feat(api): add new endpoint"
```

## Changelog Generation

### Manual Generation

```bash
# Generate complete changelog from all commits
make changelog

# Generate changelog since a specific tag
make changelog-since TAG=v1.0.0

# Generate changelog section for a specific version
make changelog-version VERSION=v1.1.0

# Generate release notes format (for GitHub releases)
make changelog-release-notes VERSION=v1.1.0
```

### Automatic Generation

The changelog is automatically updated:
- On every push to main branch (via GitHub Actions)
- When creating a new release
- When manually triggered via GitHub Actions

## Release Management

### Check Current Version

```bash
make version
```

### Create Releases

```bash
# Dry run to see what would happen
make release-dry-run

# Create a patch release (1.0.0 -> 1.0.1)
make release-patch

# Create a minor release (1.0.0 -> 1.1.0)
make release-minor

# Create a major release (1.0.0 -> 2.0.0)
make release-major
```

### Release Process

When you run a release command, the system will:

1. **Check working directory** - Ensure no uncommitted changes
2. **Bump version** - Update `pyproject.toml` and `package.json`
3. **Generate changelog** - Create/update `CHANGELOG.md`
4. **Commit changes** - Commit version bump and changelog
5. **Create git tag** - Create annotated tag for the release
6. **Optional push** - Ask if you want to push the tag

### Manual Release Steps

If you prefer manual control:

```bash
# 1. Check current version
make version

# 2. Update version manually in pyproject.toml and package.json

# 3. Generate changelog
make changelog

# 4. Commit changes
git add .
git commit -m "chore(release): bump version to 1.1.0"

# 5. Create and push tag
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0
```

## GitHub Integration

### Automated CI/CD Workflows

The changelog generation is fully integrated into the main CI/CD pipeline (`.github/workflows/ci.yml`):

1. **Changelog Generation Job**
   - Triggers on pushes to `main` branch and on new tags
   - Automatically generates and updates `CHANGELOG.md`
   - Commits changes back to the repository (on main branch)
   - Creates pull requests for tag-based updates

2. **Release Deployment Job**
   - Uses generated changelog for GitHub release notes
   - Includes proper formatting with installation instructions
   - Attaches build artifacts to releases
   - Publishes to PyPI automatically

### Workflow Benefits

- **Automatic Updates**: CHANGELOG.md stays current with every push to main
- **Release Automation**: GitHub releases include proper release notes
- **No Manual Work**: Developers just write conventional commits
- **Professional Output**: Consistent formatting and comprehensive information

### Manual Triggers

You can also manually trigger changelog updates:
- Via GitHub Actions UI → "CI/CD Pipeline" → "Run workflow"
- The changelog job runs independently and safely

## Best Practices

### Commit Messages

```bash
# Good
feat(auth): add JWT token validation
fix(db): handle connection timeouts gracefully
docs(api): update authentication examples

# Avoid
update stuff
fix bug
WIP
```

### When to Bump Versions

- **Patch (1.0.X)**: Bug fixes, small improvements
- **Minor (1.X.0)**: New features, backward-compatible changes
- **Major (X.0.0)**: Breaking changes, major rewrites

### Changelog Maintenance

- Review generated changelog before releases
- Edit if needed for clarity
- Keep unreleased section for ongoing work
- Group related changes together

## Tools and Scripts

### `tools/generate_changelog.py`

Python script that:
- Parses git commit history
- Groups commits by conventional commit types
- Generates markdown changelog
- Supports version-specific sections

### `tools/release.py`

Python script that:
- Bumps semantic versions
- Updates multiple version files
- Generates changelog for release
- Creates git tags
- Manages release workflow

### Makefile Targets

```bash
# Changelog
make changelog              # Generate full changelog
make changelog-since TAG=v1.0.0  # Since specific tag
make changelog-version VERSION=v1.1.0  # For specific version
make changelog-release-notes VERSION=v1.1.0  # GitHub release format

# Release
make release-patch          # Patch release
make release-minor          # Minor release
make release-major          # Major release
make release-dry-run        # Show what would happen

# Utilities
make version               # Show current version
make setup-conventional-commits  # Setup commit template
```

## Troubleshooting

### No Tags Found

If you have no git tags yet:
```bash
# Create initial tag
git tag -a v1.0.0 -m "Initial release"
git push origin v1.0.0
```

### Changelog Not Generated

Check that:
- You have commit history
- Python script is executable
- Git repository is properly initialized

### Release Failed

Common issues:
- Uncommitted changes (stash or commit first)
- No git repository
- Permission issues with git operations

### Fixing Mistakes

```bash
# Remove last tag (if not pushed)
git tag -d v1.0.1

# Reset last commit (if not pushed)
git reset --hard HEAD~1

# Edit last commit message
git commit --amend
```

## Example Workflow

Here's a typical development workflow:

```bash
# 1. Make changes with conventional commits
git add .
git commit -m "feat(api): add user management endpoints"

git add .
git commit -m "fix(auth): handle expired tokens properly"

git add .
git commit -m "docs: update API documentation"

# 2. When ready for release
make release-minor

# 3. Push changes
git push origin main
git push origin v1.1.0

# 4. Create GitHub release from the tag
```

This creates a professional release workflow with proper versioning, documentation, and automation.
