#!/usr/bin/env python3
"""
Makefile-style task runner for HWAutomation development.

This script provides common development tasks that can be run from any environment.
It serves as a cross-platform alternative to Makefiles.
"""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


# ANSI color codes
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


def run_command(
    cmd: List[str],
    description: str,
    check: bool = True,
    capture_output: bool = False,
    cwd: Optional[Path] = None,
) -> subprocess.CompletedProcess:
    """Run a command and return result."""
    print_colored(f"🔧 {description}...", Colors.OKBLUE)
    print_colored(f"Command: {' '.join(cmd)}", Colors.OKBLUE)

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd, check=check, capture_output=capture_output, text=True, cwd=cwd
        )

        execution_time = time.time() - start_time

        if result.returncode == 0:
            print_colored(
                f"✅ {description} completed successfully ({execution_time:.2f}s)",
                Colors.OKGREEN,
            )
        else:
            print_colored(
                f"❌ {description} failed with return code {result.returncode}",
                Colors.FAIL,
            )

        return result

    except subprocess.CalledProcessError as e:
        execution_time = time.time() - start_time
        print_colored(f"❌ {description} failed ({execution_time:.2f}s)", Colors.FAIL)
        raise
    except FileNotFoundError:
        print_colored(f"❌ Command not found: {cmd[0]}", Colors.FAIL)
        print_colored(f"💡 Make sure it's installed and in your PATH", Colors.WARNING)
        raise


class TaskRunner:
    """Main task runner class."""

    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.src_dir = self.root_dir / "src"
        self.tests_dir = self.root_dir / "tests"
        self.tools_dir = self.root_dir / "tools"

    def task_help(self):
        """Show available tasks."""
        print_colored("🚀 HWAutomation Development Task Runner", Colors.HEADER)
        print_colored("=" * 50, Colors.HEADER)
        print()

        tasks = {
            "setup": "Set up development environment",
            "install": "Install project dependencies",
            "test": "Run all tests",
            "test-unit": "Run unit tests only",
            "test-integration": "Run integration tests only",
            "test-performance": "Run performance tests only",
            "coverage": "Generate test coverage report",
            "lint": "Run code quality checks",
            "format": "Format code with black and isort",
            "type-check": "Run type checking with mypy",
            "security": "Run security scans",
            "docs": "Build documentation",
            "clean": "Clean build artifacts",
            "build": "Build package",
            "dev-server": "Start development server",
            "pre-commit": "Install and run pre-commit hooks",
            "docker-build": "Build Docker image",
            "docker-run": "Run application in Docker",
            "profile": "Profile application performance",
            "benchmark": "Run performance benchmarks",
        }

        print_colored("Available tasks:", Colors.OKBLUE)
        for task, description in tasks.items():
            print(f"  {task:20} {description}")

        print()
        print_colored("Examples:", Colors.WARNING)
        print("  python dev.py setup")
        print("  python dev.py test")
        print("  python dev.py lint --fix")
        print("  python dev.py coverage --open")

    def task_setup(self):
        """Set up development environment."""
        print_colored("🔧 Setting up development environment", Colors.HEADER)

        setup_script = self.tools_dir / "setup" / "setup_dev.py"
        if not setup_script.exists():
            print_colored(f"❌ Setup script not found: {setup_script}", Colors.FAIL)
            return 1

        run_command([sys.executable, str(setup_script)], "Running development setup")
        return 0

    def task_install(self, dev: bool = True):
        """Install project dependencies."""
        print_colored("📦 Installing dependencies", Colors.HEADER)

        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "pip"]
        run_command(cmd, "Upgrading pip")

        if dev:
            cmd = [sys.executable, "-m", "pip", "install", "-e", ".[dev]"]
        else:
            cmd = [sys.executable, "-m", "pip", "install", "-e", "."]

        run_command(cmd, "Installing project dependencies")
        return 0

    def task_test(
        self, test_type: str = "all", verbose: bool = False, fail_fast: bool = False
    ):
        """Run tests."""
        print_colored(f"🧪 Running {test_type} tests", Colors.HEADER)

        cmd = [sys.executable, "-m", "pytest"]

        if test_type == "unit":
            cmd.extend(["-m", "unit"])
        elif test_type == "integration":
            cmd.extend(["-m", "integration"])
        elif test_type == "performance":
            cmd.extend(["-m", "performance"])
        elif test_type != "all":
            cmd.extend(["-k", test_type])

        if verbose:
            cmd.append("-v")

        if fail_fast:
            cmd.append("-x")

        cmd.append("tests/")

        result = run_command(cmd, f"Running {test_type} tests", check=False)
        return result.returncode

    def task_coverage(self, open_report: bool = False):
        """Generate test coverage report."""
        print_colored("📊 Generating coverage report", Colors.HEADER)

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "--cov=src/hwautomation",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=xml",
            "tests/",
        ]

        result = run_command(cmd, "Generating coverage report", check=False)

        if result.returncode == 0:
            coverage_file = self.root_dir / "htmlcov" / "index.html"
            if coverage_file.exists():
                print_colored(f"📋 Coverage report: {coverage_file}", Colors.OKGREEN)
                if open_report:
                    import webbrowser

                    webbrowser.open(f"file://{coverage_file.absolute()}")

        return result.returncode

    def task_lint(self, fix: bool = False):
        """Run code quality checks."""
        print_colored("🔍 Running code quality checks", Colors.HEADER)

        quality_script = self.tools_dir / "quality" / "code_quality.py"
        if not quality_script.exists():
            print_colored(f"❌ Quality script not found: {quality_script}", Colors.FAIL)
            return 1

        cmd = [sys.executable, str(quality_script), "--all"]
        if fix:
            cmd.append("--fix")

        result = run_command(cmd, "Running code quality checks", check=False)
        return result.returncode

    def task_format(self):
        """Format code with black and isort."""
        print_colored("🎨 Formatting code", Colors.HEADER)

        # Format with black
        cmd = [sys.executable, "-m", "black", "src/", "tests/"]
        run_command(cmd, "Formatting code with black")

        # Sort imports with isort
        cmd = [sys.executable, "-m", "isort", "src/", "tests/"]
        run_command(cmd, "Sorting imports with isort")

        return 0

    def task_type_check(self):
        """Run type checking with mypy."""
        print_colored("🔍 Running type checking", Colors.HEADER)

        cmd = [sys.executable, "-m", "mypy", "src/"]
        result = run_command(cmd, "Running MyPy type checking", check=False)
        return result.returncode

    def task_security(self):
        """Run security scans."""
        print_colored("🔒 Running security scans", Colors.HEADER)

        # Run bandit
        cmd = [sys.executable, "-m", "bandit", "-r", "src/"]
        result = run_command(cmd, "Running Bandit security scan", check=False)

        # Run safety check
        try:
            cmd = [sys.executable, "-m", "safety", "check"]
            safety_result = run_command(
                cmd, "Running Safety vulnerability check", check=False
            )
            result.returncode = max(result.returncode, safety_result.returncode)
        except FileNotFoundError:
            print_colored(
                "💡 Install safety for vulnerability checking: pip install safety",
                Colors.WARNING,
            )

        return result.returncode

    def task_docs(self):
        """Build documentation."""
        print_colored("📚 Building documentation", Colors.HEADER)

        # Check if Sphinx is configured
        docs_dir = self.root_dir / "docs"
        conf_file = docs_dir / "conf.py"

        if conf_file.exists():
            cmd = [
                sys.executable,
                "-m",
                "sphinx",
                "-b",
                "html",
                str(docs_dir),
                str(docs_dir / "_build" / "html"),
            ]
            run_command(cmd, "Building Sphinx documentation")
        else:
            print_colored(
                "📋 No Sphinx configuration found, generating API docs", Colors.WARNING
            )
            # Generate simple API documentation
            self._generate_api_docs()

        return 0

    def task_clean(self):
        """Clean build artifacts."""
        print_colored("🧹 Cleaning build artifacts", Colors.HEADER)

        patterns = [
            "build/",
            "dist/",
            "*.egg-info/",
            "__pycache__/",
            ".pytest_cache/",
            ".mypy_cache/",
            ".coverage",
            "htmlcov/",
            "*.pyc",
            "*.pyo",
            ".DS_Store",
        ]

        for pattern in patterns:
            self._clean_pattern(pattern)

        print_colored("✅ Cleanup completed", Colors.OKGREEN)
        return 0

    def task_build(self):
        """Build package."""
        print_colored("📦 Building package", Colors.HEADER)

        # Clean first
        self.task_clean()

        # Build package
        cmd = [sys.executable, "-m", "build"]
        run_command(cmd, "Building package")

        # Check package
        cmd = [sys.executable, "-m", "twine", "check", "dist/*"]
        result = run_command(cmd, "Checking package", check=False)

        return result.returncode

    def task_dev_server(self, host: str = "127.0.0.1", port: int = 5000):
        """Start development server."""
        print_colored("🚀 Starting development server", Colors.HEADER)

        app_file = self.src_dir / "hwautomation" / "web" / "app.py"
        if not app_file.exists():
            print_colored(f"❌ App file not found: {app_file}", Colors.FAIL)
            return 1

        env = os.environ.copy()
        env.update(
            {"FLASK_ENV": "development", "FLASK_DEBUG": "1", "FLASK_APP": str(app_file)}
        )

        cmd = [sys.executable, str(app_file)]
        print_colored(
            f"🌐 Server will be available at http://{host}:{port}", Colors.OKGREEN
        )

        try:
            subprocess.run(cmd, env=env, cwd=self.root_dir)
        except KeyboardInterrupt:
            print_colored("\n👋 Development server stopped", Colors.WARNING)

        return 0

    def task_pre_commit(self, install: bool = False):
        """Install and run pre-commit hooks."""
        print_colored("🪝 Managing pre-commit hooks", Colors.HEADER)

        if install:
            cmd = ["pre-commit", "install"]
            run_command(cmd, "Installing pre-commit hooks")

            cmd = ["pre-commit", "install", "--hook-type", "commit-msg"]
            run_command(cmd, "Installing commit-msg hooks")

        cmd = ["pre-commit", "run", "--all-files"]
        result = run_command(cmd, "Running pre-commit hooks", check=False)

        return result.returncode

    def task_docker_build(self, tag: str = "hwautomation:latest"):
        """Build Docker image."""
        print_colored("🐳 Building Docker image", Colors.HEADER)

        dockerfile = self.root_dir / "Dockerfile"
        if not dockerfile.exists():
            print_colored(f"❌ Dockerfile not found: {dockerfile}", Colors.FAIL)
            return 1

        cmd = ["docker", "build", "-t", tag, "."]
        run_command(cmd, f"Building Docker image '{tag}'", cwd=self.root_dir)

        return 0

    def task_docker_run(self, tag: str = "hwautomation:latest", port: int = 5000):
        """Run application in Docker."""
        print_colored("🐳 Running application in Docker", Colors.HEADER)

        cmd = ["docker", "run", "--rm", "-it", "-p", f"{port}:5000", tag]

        try:
            run_command(cmd, f"Running Docker container from '{tag}'")
        except KeyboardInterrupt:
            print_colored("\n👋 Docker container stopped", Colors.WARNING)

        return 0

    def task_profile(self, script: str = "main.py"):
        """Profile application performance."""
        print_colored("⚡ Profiling application performance", Colors.HEADER)

        script_path = self.root_dir / script
        if not script_path.exists():
            print_colored(f"❌ Script not found: {script_path}", Colors.FAIL)
            return 1

        output_file = self.root_dir / "profile.stats"

        cmd = [
            sys.executable,
            "-m",
            "cProfile",
            "-o",
            str(output_file),
            str(script_path),
        ]

        run_command(cmd, f"Profiling {script}")

        print_colored(f"📊 Profile saved to: {output_file}", Colors.OKGREEN)
        print_colored("💡 Analyze with: python -m pstats profile.stats", Colors.WARNING)

        return 0

    def task_benchmark(self):
        """Run performance benchmarks."""
        print_colored("📊 Running performance benchmarks", Colors.HEADER)

        cmd = [sys.executable, "-m", "pytest", "-m", "performance", "--benchmark-only"]
        result = run_command(cmd, "Running performance benchmarks", check=False)

        return result.returncode

    def _clean_pattern(self, pattern: str):
        """Clean files/directories matching pattern."""
        import glob

        for path in glob.glob(pattern, recursive=True):
            path_obj = Path(path)
            try:
                if path_obj.is_dir():
                    shutil.rmtree(path_obj)
                    print_colored(f"🗑️  Removed directory: {path}", Colors.WARNING)
                else:
                    path_obj.unlink()
                    print_colored(f"🗑️  Removed file: {path}", Colors.WARNING)
            except Exception as e:
                print_colored(f"❌ Failed to remove {path}: {e}", Colors.FAIL)

    def _generate_api_docs(self):
        """Generate simple API documentation."""
        docs_dir = self.root_dir / "docs"
        docs_dir.mkdir(exist_ok=True)

        api_doc = docs_dir / "API.md"
        with open(api_doc, "w") as f:
            f.write("# HWAutomation API Documentation\n\n")
            f.write("Auto-generated API documentation.\n\n")
            # Add more API documentation generation logic here

        print_colored(f"📋 API documentation generated: {api_doc}", Colors.OKGREEN)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="HWAutomation Development Task Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "task", nargs="?", default="help", help="Task to run (default: help)"
    )

    # Task-specific arguments
    parser.add_argument(
        "--fix", action="store_true", help="Automatically fix issues (for lint task)"
    )
    parser.add_argument(
        "--open", action="store_true", help="Open report in browser (for coverage task)"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--fail-fast", "-x", action="store_true", help="Stop on first failure"
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        default=True,
        help="Install development dependencies",
    )
    parser.add_argument(
        "--install", action="store_true", help="Install pre-commit hooks"
    )
    parser.add_argument("--tag", default="hwautomation:latest", help="Docker image tag")
    parser.add_argument("--port", type=int, default=5000, help="Port number for server")
    parser.add_argument("--host", default="127.0.0.1", help="Host address for server")
    parser.add_argument("--script", default="main.py", help="Script to profile")

    args = parser.parse_args()

    runner = TaskRunner()

    # Map tasks to methods
    task_methods = {
        "help": runner.task_help,
        "setup": runner.task_setup,
        "install": lambda: runner.task_install(dev=args.dev),
        "test": lambda: runner.task_test("all", args.verbose, args.fail_fast),
        "test-unit": lambda: runner.task_test("unit", args.verbose, args.fail_fast),
        "test-integration": lambda: runner.task_test(
            "integration", args.verbose, args.fail_fast
        ),
        "test-performance": lambda: runner.task_test(
            "performance", args.verbose, args.fail_fast
        ),
        "coverage": lambda: runner.task_coverage(args.open),
        "lint": lambda: runner.task_lint(args.fix),
        "format": runner.task_format,
        "type-check": runner.task_type_check,
        "security": runner.task_security,
        "docs": runner.task_docs,
        "clean": runner.task_clean,
        "build": runner.task_build,
        "dev-server": lambda: runner.task_dev_server(args.host, args.port),
        "pre-commit": lambda: runner.task_pre_commit(args.install),
        "docker-build": lambda: runner.task_docker_build(args.tag),
        "docker-run": lambda: runner.task_docker_run(args.tag, args.port),
        "profile": lambda: runner.task_profile(args.script),
        "benchmark": runner.task_benchmark,
    }

    if args.task not in task_methods:
        print_colored(f"❌ Unknown task: {args.task}", Colors.FAIL)
        runner.task_help()
        return 1

    try:
        return task_methods[args.task]()
    except KeyboardInterrupt:
        print_colored("\n👋 Task interrupted by user", Colors.WARNING)
        return 130
    except Exception as e:
        print_colored(f"❌ Task failed with error: {e}", Colors.FAIL)
        return 1


if __name__ == "__main__":
    sys.exit(main())
