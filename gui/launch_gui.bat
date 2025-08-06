@echo off
REM HWAutomation GUI Launcher for Windows
REM This script sets up and launches the web GUI

echo HWAutomation GUI Launcher
echo ===========================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Change to the GUI directory
cd /d "%~dp0"

REM Check if we're in the right directory
if not exist "app.py" (
    echo ERROR: app.py not found
    echo Make sure you're running this from the gui directory
    pause
    exit /b 1
)

REM Run GUI setup based on command line arguments
if "%1"=="install-only" (
    echo Installing GUI dependencies only...
    python setup_gui.py --install-only
) else if "%1"=="no-install" (
    echo Launching GUI without installing dependencies...
    python setup_gui.py --no-install --host %2 --port %3
) else if "%1"=="debug" (
    echo Launching GUI in debug mode...
    python setup_gui.py --debug
) else if "%1"=="help" (
    echo Usage: %0 [install-only^|no-install^|debug^|help]
    echo.
    echo   install-only  - Only install dependencies
    echo   no-install    - Launch without installing dependencies
    echo   debug         - Launch in debug mode
    echo   help          - Show this help
    echo.
    echo Default: Install dependencies and launch GUI
) else (
    echo Installing dependencies and launching GUI...
    python setup_gui.py
)

echo.
if not "%1"=="install-only" (
    echo GUI launcher completed.
    echo.
    echo To access the GUI, open your web browser and go to:
    echo http://127.0.0.1:5000
    echo.
)
if not "%1"=="no-install" pause
