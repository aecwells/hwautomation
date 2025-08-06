@echo off
echo BIOS Configuration System Test
echo ============================

REM Change to project root directory
cd /d "%~dp0.."

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org or Microsoft Store
    echo Then run this script again
    pause
    exit /b 1
)

echo Python is available

REM Check if required packages are installed
echo Checking dependencies...
python -c "import yaml" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyYAML...
    pip install pyyaml
)

python -c "import requests" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing requests...
    pip install requests
)

echo.
echo Running BIOS Configuration System Tests...
echo.
python tests/test_bios_system.py

pause
