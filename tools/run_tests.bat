@echo off
REM HWAutomation Test Runner for Windows
REM This script runs the Python test suite

echo HWAutomation Test Runner
echo ========================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Change to the tests directory
cd /d "%~dp0"

REM Check if we're in the right directory
if not exist "run_tests.py" (
    echo ERROR: run_tests.py not found
    echo Make sure you're running this from the tests directory
    pause
    exit /b 1
)

REM Run tests based on command line arguments
if "%1"=="quick" (
    echo Running quick integration test...
    python run_tests.py --quick
) else if "%1"=="verbose" (
    echo Running all tests with verbose output...
    python run_tests.py --verbose
) else if "%1"=="quiet" (
    echo Running all tests quietly...
    python run_tests.py --quiet
) else if "%1"=="" (
    echo Running all tests...
    python run_tests.py
) else (
    echo Running specific module: %1
    python run_tests.py --module %1
)

echo.
echo Test run completed.
if not "%1"=="quiet" pause
