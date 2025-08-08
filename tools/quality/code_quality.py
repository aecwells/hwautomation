#!/usr/bin/env python3
"""
Code quality automation script for HWAutomation.

This script provides automated code formatting, linting, and quality checks
to maintain consistent code standards across the project.
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path
from typing import List, Tuple, Optional
import time

# ANSI color codes for output formatting
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message: str, color: str = Colors.ENDC):
    """Print colored message to terminal."""
    print(f"{color}{message}{Colors.ENDC}")

def run_command(cmd: List[str], description: str, check: bool = True, 
                capture_output: bool = False) -> Tuple[int, str, str]:
    """Run a command and return result."""
    print_colored(f"\n🔧 {description}...", Colors.OKBLUE)
    print_colored(f"Command: {' '.join(cmd)}", Colors.OKBLUE)
    
    start_time = time.time()
    
    try:
        if capture_output:
            result = subprocess.run(cmd, capture_output=True, text=True, check=check)
            stdout, stderr = result.stdout, result.stderr
        else:
            result = subprocess.run(cmd, check=check)
            stdout, stderr = "", ""
        
        execution_time = time.time() - start_time
        
        if result.returncode == 0:
            print_colored(f"✅ {description} completed successfully ({execution_time:.2f}s)", Colors.OKGREEN)
        else:
            print_colored(f"❌ {description} failed with return code {result.returncode}", Colors.FAIL)
            
        return result.returncode, stdout, stderr
        
    except subprocess.CalledProcessError as e:
        execution_time = time.time() - start_time
        print_colored(f"❌ {description} failed ({execution_time:.2f}s)", Colors.FAIL)
        return e.returncode, "", str(e)
    except FileNotFoundError:
        print_colored(f"❌ Command not found: {cmd[0]}", Colors.FAIL)
        print_colored(f"💡 Try installing it with: pip install {cmd[0]}", Colors.WARNING)
        return 1, "", f"Command not found: {cmd[0]}"

def check_tool_availability() -> List[str]:
    """Check which code quality tools are available."""
    tools = {
        'black': 'Code formatting',
        'isort': 'Import sorting', 
        'flake8': 'Code linting',
        'mypy': 'Type checking',
        'bandit': 'Security scanning',
        'pytest': 'Testing framework'
    }
    
    available_tools = []
    missing_tools = []
    
    print_colored("\n🔍 Checking tool availability...", Colors.HEADER)
    
    for tool, description in tools.items():
        try:
            subprocess.run([tool, '--version'], capture_output=True, check=True)
            print_colored(f"✅ {tool:10} - {description}", Colors.OKGREEN)
            available_tools.append(tool)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_colored(f"❌ {tool:10} - {description} (not installed)", Colors.FAIL)
            missing_tools.append(tool)
    
    if missing_tools:
        print_colored(f"\n💡 To install missing tools:", Colors.WARNING)
        print_colored(f"pip install {' '.join(missing_tools)}", Colors.WARNING)
    
    return available_tools

def format_code(paths: List[str], fix: bool = False) -> int:
    """Format code using black and isort."""
    total_errors = 0
    
    # Black formatting
    black_cmd = ['black']
    if not fix:
        black_cmd.append('--check')
    black_cmd.extend(paths)
    
    returncode, stdout, stderr = run_command(
        black_cmd, 
        "Running Black code formatter" + (" (check only)" if not fix else ""),
        check=False,
        capture_output=True
    )
    total_errors += returncode
    
    if returncode != 0 and not fix:
        print_colored("💡 Run with --fix to automatically format code", Colors.WARNING)
    
    # Import sorting with isort
    isort_cmd = ['isort']
    if not fix:
        isort_cmd.append('--check-only')
    isort_cmd.extend(paths)
    
    returncode, stdout, stderr = run_command(
        isort_cmd,
        "Running isort import sorting" + (" (check only)" if not fix else ""),
        check=False,
        capture_output=True
    )
    total_errors += returncode
    
    if returncode != 0 and not fix:
        print_colored("💡 Run with --fix to automatically sort imports", Colors.WARNING)
    
    return total_errors

def lint_code(paths: List[str]) -> int:
    """Lint code using flake8."""
    cmd = ['flake8'] + paths
    returncode, stdout, stderr = run_command(
        cmd, 
        "Running Flake8 linting",
        check=False,
        capture_output=True
    )
    
    if stdout:
        print_colored("📋 Linting issues found:", Colors.WARNING)
        print(stdout)
    
    return returncode

def type_check(paths: List[str]) -> int:
    """Type check code using mypy."""
    cmd = ['mypy'] + paths
    returncode, stdout, stderr = run_command(
        cmd,
        "Running MyPy type checking", 
        check=False,
        capture_output=True
    )
    
    if stdout:
        print_colored("🔍 Type checking results:", Colors.WARNING)
        print(stdout)
    
    return returncode

def security_scan(paths: List[str]) -> int:
    """Security scan using bandit."""
    cmd = ['bandit', '-r'] + paths
    returncode, stdout, stderr = run_command(
        cmd,
        "Running Bandit security scan",
        check=False,
        capture_output=True
    )
    
    if stdout:
        print_colored("🔒 Security scan results:", Colors.WARNING)
        print(stdout)
    
    return returncode

def run_tests(test_type: str = "unit") -> int:
    """Run tests using pytest."""
    cmd = ['pytest']
    
    if test_type == "unit":
        cmd.extend(['-m', 'unit', '--tb=short'])
    elif test_type == "integration":
        cmd.extend(['-m', 'integration', '--tb=short'])
    elif test_type == "performance":
        cmd.extend(['-m', 'performance', '--tb=short'])
    elif test_type == "all":
        cmd.extend(['--tb=short'])
    else:
        cmd.extend(['-k', test_type, '--tb=short'])
    
    returncode, stdout, stderr = run_command(
        cmd,
        f"Running {test_type} tests",
        check=False
    )
    
    return returncode

def generate_coverage_report() -> int:
    """Generate test coverage report."""
    # Run tests with coverage
    cmd = ['pytest', '--cov=src/hwautomation', '--cov-report=html', '--cov-report=term']
    returncode, stdout, stderr = run_command(
        cmd,
        "Generating coverage report",
        check=False
    )
    
    if returncode == 0:
        print_colored("📊 Coverage report generated in htmlcov/index.html", Colors.OKGREEN)
    
    return returncode

def main():
    """Main function for code quality automation."""
    parser = argparse.ArgumentParser(
        description="HWAutomation Code Quality Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/quality/code_quality.py --format --check
  python tools/quality/code_quality.py --lint --type-check
  python tools/quality/code_quality.py --all --fix
  python tools/quality/code_quality.py --test unit
  python tools/quality/code_quality.py --coverage
        """
    )
    
    # Operation flags
    parser.add_argument('--format', action='store_true', 
                       help='Run code formatting (black, isort)')
    parser.add_argument('--lint', action='store_true',
                       help='Run code linting (flake8)')
    parser.add_argument('--type-check', action='store_true',
                       help='Run type checking (mypy)')
    parser.add_argument('--security', action='store_true',
                       help='Run security scanning (bandit)')
    parser.add_argument('--test', choices=['unit', 'integration', 'performance', 'all'],
                       help='Run tests')
    parser.add_argument('--coverage', action='store_true',
                       help='Generate test coverage report')
    parser.add_argument('--all', action='store_true',
                       help='Run all quality checks')
    
    # Modifier flags
    parser.add_argument('--fix', action='store_true',
                       help='Automatically fix issues where possible')
    parser.add_argument('--check', action='store_true',
                       help='Check only, do not modify files')
    
    # Path specification
    parser.add_argument('paths', nargs='*', default=['src/', 'tests/'],
                       help='Paths to check (default: src/ tests/)')
    
    args = parser.parse_args()
    
    # Validate paths exist
    valid_paths = []
    for path in args.paths:
        if os.path.exists(path):
            valid_paths.append(path)
        else:
            print_colored(f"⚠️  Path does not exist: {path}", Colors.WARNING)
    
    if not valid_paths:
        print_colored("❌ No valid paths specified", Colors.FAIL)
        return 1
    
    print_colored("🚀 HWAutomation Code Quality Automation", Colors.HEADER)
    print_colored(f"📁 Checking paths: {', '.join(valid_paths)}", Colors.OKBLUE)
    
    # Check tool availability
    available_tools = check_tool_availability()
    
    total_errors = 0
    operations_run = 0
    
    # Determine what operations to run
    if args.all:
        run_format = run_lint = run_type_check = run_security = True
        run_test_type = 'unit'
        run_coverage = True
    else:
        run_format = args.format
        run_lint = args.lint
        run_type_check = args.type_check
        run_security = args.security
        run_test_type = args.test
        run_coverage = args.coverage
    
    # If no operations specified, show help
    if not any([run_format, run_lint, run_type_check, run_security, run_test_type, run_coverage]):
        parser.print_help()
        return 0
    
    start_time = time.time()
    
    # Run code formatting
    if run_format and 'black' in available_tools and 'isort' in available_tools:
        total_errors += format_code(valid_paths, fix=args.fix and not args.check)
        operations_run += 1
    
    # Run linting
    if run_lint and 'flake8' in available_tools:
        total_errors += lint_code(valid_paths)
        operations_run += 1
    
    # Run type checking
    if run_type_check and 'mypy' in available_tools:
        total_errors += type_check(valid_paths)
        operations_run += 1
    
    # Run security scanning
    if run_security and 'bandit' in available_tools:
        total_errors += security_scan(valid_paths)
        operations_run += 1
    
    # Run tests
    if run_test_type and 'pytest' in available_tools:
        total_errors += run_tests(run_test_type)
        operations_run += 1
    
    # Generate coverage report
    if run_coverage and 'pytest' in available_tools:
        total_errors += generate_coverage_report()
        operations_run += 1
    
    # Summary
    total_time = time.time() - start_time
    print_colored(f"\n{'='*50}", Colors.HEADER)
    print_colored(f"🏁 Quality check completed in {total_time:.2f}s", Colors.HEADER)
    print_colored(f"📊 Operations run: {operations_run}", Colors.OKBLUE)
    
    if total_errors == 0:
        print_colored("✅ All quality checks passed!", Colors.OKGREEN)
        return 0
    else:
        print_colored(f"❌ {total_errors} issues found", Colors.FAIL)
        if args.check:
            print_colored("💡 Run without --check to fix automatically", Colors.WARNING)
        return 1

if __name__ == '__main__':
    sys.exit(main())
