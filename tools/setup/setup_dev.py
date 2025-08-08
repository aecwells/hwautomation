#!/usr/bin/env python3
"""
Development environment setup script for HWAutomation.

This script automates the setup of a complete development environment
including pre-commit hooks, code quality tools, and testing infrastructure.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional


# ANSI color codes for output formatting
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_colored(message: str, color: str = Colors.ENDC):
    """Print colored message to terminal."""
    print(f"{color}{message}{Colors.ENDC}")


def run_command(cmd: List[str], description: str, check: bool = True) -> bool:
    """Run a command and return success status."""
    print_colored(f"🔧 {description}...", Colors.OKBLUE)
    print_colored(f"Command: {' '.join(cmd)}", Colors.OKBLUE)

    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)

        if result.returncode == 0:
            print_colored(f"✅ {description} completed successfully", Colors.OKGREEN)
            if result.stdout.strip():
                print(result.stdout.strip())
            return True
        else:
            print_colored(f"❌ {description} failed", Colors.FAIL)
            if result.stderr.strip():
                print_colored(f"Error: {result.stderr.strip()}", Colors.FAIL)
            return False

    except subprocess.CalledProcessError as e:
        print_colored(f"❌ {description} failed: {e}", Colors.FAIL)
        return False
    except FileNotFoundError:
        print_colored(f"❌ Command not found: {cmd[0]}", Colors.FAIL)
        return False


def check_python_version() -> bool:
    """Check if Python version is compatible."""
    print_colored("🐍 Checking Python version...", Colors.HEADER)

    version = sys.version_info
    if version.major != 3 or version.minor < 8:
        print_colored(
            f"❌ Python 3.8+ required, found {version.major}.{version.minor}",
            Colors.FAIL,
        )
        return False

    print_colored(
        f"✅ Python {version.major}.{version.minor}.{version.micro} detected",
        Colors.OKGREEN,
    )
    return True


def check_git_repo() -> bool:
    """Check if we're in a git repository."""
    print_colored("📦 Checking git repository...", Colors.HEADER)

    if not Path(".git").exists():
        print_colored("❌ Not in a git repository", Colors.FAIL)
        print_colored(
            "💡 Run 'git init' to initialize a git repository", Colors.WARNING
        )
        return False

    print_colored("✅ Git repository detected", Colors.OKGREEN)
    return True


def setup_virtual_environment(venv_name: str = "hwautomation-env") -> bool:
    """Set up Python virtual environment."""
    print_colored("🔧 Setting up virtual environment...", Colors.HEADER)

    venv_path = Path(venv_name)

    if venv_path.exists():
        print_colored(
            f"📁 Virtual environment '{venv_name}' already exists", Colors.WARNING
        )
        response = input("Do you want to recreate it? (y/N): ").lower().strip()
        if response in ["y", "yes"]:
            print_colored(
                f"🗑️  Removing existing virtual environment...", Colors.WARNING
            )
            shutil.rmtree(venv_path)
        else:
            print_colored("✅ Using existing virtual environment", Colors.OKGREEN)
            return True

    # Create virtual environment
    if not run_command(
        [sys.executable, "-m", "venv", venv_name],
        f"Creating virtual environment '{venv_name}'",
    ):
        return False

    # Determine activate script path
    if os.name == "nt":  # Windows
        activate_script = venv_path / "Scripts" / "activate.bat"
        python_exe = venv_path / "Scripts" / "python.exe"
    else:  # Unix-like
        activate_script = venv_path / "bin" / "activate"
        python_exe = venv_path / "bin" / "python"

    print_colored(f"💡 To activate the virtual environment:", Colors.WARNING)
    if os.name == "nt":
        print_colored(f"   {activate_script}", Colors.WARNING)
    else:
        print_colored(f"   source {activate_script}", Colors.WARNING)

    return True


def install_dev_dependencies(use_venv: bool = True) -> bool:
    """Install development dependencies."""
    print_colored("📦 Installing development dependencies...", Colors.HEADER)

    # Determine Python executable
    if use_venv:
        if os.name == "nt":  # Windows
            python_exe = "hwautomation-env/Scripts/python.exe"
        else:  # Unix-like
            python_exe = "hwautomation-env/bin/python"
    else:
        python_exe = sys.executable

    # Upgrade pip first
    if not run_command(
        [python_exe, "-m", "pip", "install", "--upgrade", "pip"], "Upgrading pip"
    ):
        return False

    # Install project in development mode with dev dependencies
    if not run_command(
        [python_exe, "-m", "pip", "install", "-e", ".[dev]"],
        "Installing project with development dependencies",
    ):
        return False

    return True


def setup_pre_commit_hooks() -> bool:
    """Set up pre-commit hooks."""
    print_colored("🪝 Setting up pre-commit hooks...", Colors.HEADER)

    # Install pre-commit hooks
    if not run_command(["pre-commit", "install"], "Installing pre-commit hooks"):
        print_colored(
            "💡 Make sure pre-commit is installed: pip install pre-commit",
            Colors.WARNING,
        )
        return False

    # Install commit-msg hook for conventional commits
    if not run_command(
        ["pre-commit", "install", "--hook-type", "commit-msg"],
        "Installing commit-msg hooks",
    ):
        return False

    # Run pre-commit on all files to test setup
    print_colored("🧪 Testing pre-commit setup...", Colors.OKBLUE)
    result = run_command(
        ["pre-commit", "run", "--all-files"],
        "Running pre-commit on all files",
        check=False,
    )

    if result:
        print_colored("✅ Pre-commit hooks configured successfully", Colors.OKGREEN)
    else:
        print_colored(
            "⚠️  Pre-commit found issues (this is normal for first run)", Colors.WARNING
        )
        print_colored(
            "💡 Run 'pre-commit run --all-files' again to see if issues are fixed",
            Colors.WARNING,
        )

    return True


def create_dev_scripts() -> bool:
    """Create development helper scripts."""
    print_colored("📝 Creating development scripts...", Colors.HEADER)

    scripts_dir = Path("scripts")
    scripts_dir.mkdir(exist_ok=True)

    # Development script for common tasks
    dev_script_content = '''#!/usr/bin/env python3
"""Development helper script for common tasks."""

import sys
import subprocess
from pathlib import Path

def run_tests():
    """Run the test suite."""
    return subprocess.run([sys.executable, "-m", "pytest"], cwd=Path(__file__).parent.parent).returncode

def run_linting():
    """Run code quality checks."""
    tools_dir = Path(__file__).parent.parent / "tools" / "quality"
    script_path = tools_dir / "code_quality.py"
    return subprocess.run([sys.executable, str(script_path), "--all"], 
                         cwd=Path(__file__).parent.parent).returncode

def run_format():
    """Run code formatting."""
    tools_dir = Path(__file__).parent.parent / "tools" / "quality"
    script_path = tools_dir / "code_quality.py"
    return subprocess.run([sys.executable, str(script_path), "--format", "--fix"], 
                         cwd=Path(__file__).parent.parent).returncode

def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python dev.py [test|lint|format]")
        return 1
    
    command = sys.argv[1]
    
    if command == "test":
        return run_tests()
    elif command == "lint":
        return run_linting()
    elif command == "format":
        return run_format()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: test, lint, format")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''

    dev_script_path = scripts_dir / "dev.py"
    with open(dev_script_path, "w") as f:
        f.write(dev_script_content)

    # Make script executable on Unix-like systems
    if os.name != "nt":
        os.chmod(dev_script_path, 0o755)

    print_colored(f"✅ Development script created: {dev_script_path}", Colors.OKGREEN)

    return True


def setup_vscode_settings() -> bool:
    """Set up VS Code workspace settings."""
    print_colored("🔧 Setting up VS Code workspace settings...", Colors.HEADER)

    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)

    # VS Code settings
    settings = {
        "python.defaultInterpreterPath": "./hwautomation-env/bin/python",
        "python.linting.enabled": True,
        "python.linting.flake8Enabled": True,
        "python.linting.mypyEnabled": True,
        "python.formatting.provider": "black",
        "python.sortImports.args": ["--profile", "black"],
        "editor.formatOnSave": True,
        "editor.codeActionsOnSave": {"source.organizeImports": True},
        "files.exclude": {
            "**/__pycache__": True,
            "**/*.pyc": True,
            "**/.pytest_cache": True,
            "**/.mypy_cache": True,
            "**/htmlcov": True,
            "**/.coverage": True,
        },
        "python.testing.pytestEnabled": True,
        "python.testing.unittestEnabled": False,
        "python.testing.pytestArgs": ["tests"],
    }

    import json

    settings_path = vscode_dir / "settings.json"
    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2)

    print_colored(f"✅ VS Code settings created: {settings_path}", Colors.OKGREEN)

    # Launch configuration
    launch_config = {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python: Current File",
                "type": "python",
                "request": "launch",
                "program": "${file}",
                "console": "integratedTerminal",
                "justMyCode": True,
            },
            {
                "name": "Python: Flask App",
                "type": "python",
                "request": "launch",
                "program": "${workspaceFolder}/src/hwautomation/web/app.py",
                "env": {"FLASK_ENV": "development", "FLASK_DEBUG": "1"},
                "console": "integratedTerminal",
                "justMyCode": True,
            },
            {
                "name": "Python: Run Tests",
                "type": "python",
                "request": "launch",
                "module": "pytest",
                "args": ["tests"],
                "console": "integratedTerminal",
                "justMyCode": False,
            },
        ],
    }

    launch_path = vscode_dir / "launch.json"
    with open(launch_path, "w") as f:
        json.dump(launch_config, f, indent=2)

    print_colored(f"✅ VS Code launch config created: {launch_path}", Colors.OKGREEN)

    return True


def print_next_steps():
    """Print next steps for the user."""
    print_colored("\n🎉 Development environment setup complete!", Colors.HEADER)
    print_colored("\n📋 Next steps:", Colors.OKBLUE)
    print_colored("1. Activate the virtual environment:", Colors.ENDC)
    if os.name == "nt":
        print_colored("   hwautomation-env\\Scripts\\activate.bat", Colors.WARNING)
    else:
        print_colored("   source hwautomation-env/bin/activate", Colors.WARNING)

    print_colored("\n2. Run tests to verify setup:", Colors.ENDC)
    print_colored("   python -m pytest", Colors.WARNING)

    print_colored("\n3. Run code quality checks:", Colors.ENDC)
    print_colored("   python tools/quality/code_quality.py --all", Colors.WARNING)

    print_colored("\n4. Use development helper script:", Colors.ENDC)
    print_colored("   python scripts/dev.py test", Colors.WARNING)
    print_colored("   python scripts/dev.py lint", Colors.WARNING)
    print_colored("   python scripts/dev.py format", Colors.WARNING)

    print_colored("\n5. Make a test commit to verify pre-commit hooks:", Colors.ENDC)
    print_colored("   git add .", Colors.WARNING)
    print_colored(
        "   git commit -m 'feat: setup development environment'", Colors.WARNING
    )

    print_colored("\n📚 Additional resources:", Colors.OKBLUE)
    print_colored("• Code quality script: tools/quality/code_quality.py", Colors.ENDC)
    print_colored("• Pre-commit config: .pre-commit-config.yaml", Colors.ENDC)
    print_colored("• VS Code settings: .vscode/settings.json", Colors.ENDC)
    print_colored("• Project config: pyproject.toml", Colors.ENDC)


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(
        description="Setup HWAutomation development environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--no-venv", action="store_true", help="Skip virtual environment setup"
    )
    parser.add_argument(
        "--no-hooks", action="store_true", help="Skip pre-commit hooks setup"
    )
    parser.add_argument(
        "--no-vscode", action="store_true", help="Skip VS Code configuration"
    )

    args = parser.parse_args()

    print_colored("🚀 HWAutomation Development Environment Setup", Colors.HEADER)
    print_colored("=" * 50, Colors.HEADER)

    # Check prerequisites
    if not check_python_version():
        return 1

    if not check_git_repo():
        return 1

    success = True

    # Set up virtual environment
    if not args.no_venv:
        if not setup_virtual_environment():
            success = False

    # Install dependencies
    if success:
        if not install_dev_dependencies(use_venv=not args.no_venv):
            success = False

    # Set up pre-commit hooks
    if success and not args.no_hooks:
        if not setup_pre_commit_hooks():
            success = False

    # Create development scripts
    if success:
        if not create_dev_scripts():
            success = False

    # Set up VS Code configuration
    if success and not args.no_vscode:
        if not setup_vscode_settings():
            success = False

    if success:
        print_next_steps()
        return 0
    else:
        print_colored(
            "\n❌ Setup completed with errors. Check the output above.", Colors.FAIL
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
