#!/usr/bin/env python3
"""
GUI Setup Script for HWAutomation

This script sets up and launches the web-based GUI for hardware automation.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def check_python_version():
    """Check if Python version is adequate."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    return True

def install_requirements():
    """Install required packages."""
    # First install core requirements
    core_requirements = Path(__file__).parent.parent / "requirements.txt"
    gui_requirements = Path(__file__).parent / "requirements.txt"
    
    if not core_requirements.exists():
        print("Error: Core requirements.txt not found")
        return False
    
    if not gui_requirements.exists():
        print("Error: GUI requirements.txt not found")
        return False
    
    print("Installing core requirements...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(core_requirements)
        ])
        print("✓ Core requirements installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error installing core requirements: {e}")
        return False
    
    print("Installing GUI requirements...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", str(gui_requirements)
        ])
        print("✓ GUI requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing GUI requirements: {e}")
        return False

def check_core_dependencies():
    """Check if core HWAutomation package dependencies are available."""
    try:
        import yaml
        import requests
        print("✓ Core dependencies available")
        return True
    except ImportError as e:
        print(f"Error: Core dependency missing: {e}")
        print("Please install core requirements first:")
        print("  pip install pyyaml requests requests-oauthlib")
        return False

def launch_gui(host="127.0.0.1", port=5000, debug=False):
    """Launch the GUI application."""
    app_file = Path(__file__).parent / "app.py"
    
    if not app_file.exists():
        print("Error: app.py not found")
        return False
    
    print(f"Starting HWAutomation Web GUI...")
    print(f"URL: http://{host}:{port}")
    print("Press Ctrl+C to stop")
    
    try:
        # Set environment variables
        os.environ['FLASK_APP'] = str(app_file)
        if debug:
            os.environ['FLASK_ENV'] = 'development'
        
        # Launch the application
        subprocess.check_call([
            sys.executable, str(app_file),
            "--host", host,
            "--port", str(port)
        ] + (["--debug"] if debug else []))
        
    except KeyboardInterrupt:
        print("\nGUI stopped by user")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error launching GUI: {e}")
        return False

def main():
    """Main setup and launch function."""
    parser = argparse.ArgumentParser(
        description="HWAutomation GUI Setup and Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Install and launch GUI
  %(prog)s --no-install             # Launch without installing deps
  %(prog)s --host 0.0.0.0 --port 8080  # Launch on all interfaces, port 8080
  %(prog)s --debug                  # Launch in debug mode
        """
    )
    
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host to bind to (default: 127.0.0.1)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to bind to (default: 5000)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )
    parser.add_argument(
        '--no-install',
        action='store_true',
        help='Skip dependency installation'
    )
    parser.add_argument(
        '--install-only',
        action='store_true',
        help='Only install dependencies, don\'t launch'
    )
    
    args = parser.parse_args()
    
    print("HWAutomation GUI Setup")
    print("=" * 25)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Check core dependencies
    if not check_core_dependencies():
        return 1
    
    # Install GUI requirements if requested
    if not args.no_install:
        if not install_requirements():
            return 1
    
    # Exit if only installing
    if args.install_only:
        print("Dependencies installed successfully!")
        return 0
    
    # Launch GUI
    if not launch_gui(args.host, args.port, args.debug):
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
