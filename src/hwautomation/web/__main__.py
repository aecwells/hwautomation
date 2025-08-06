#!/usr/bin/env python3
"""
Web Application Module Entry Point

This allows running the web application as a Python module:
    python -m hwautomation.web

This is cleaner than having a separate webapp.py launcher in the root directory.
"""

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main entry point for web application module."""
    
    # Import the Flask app factory
    try:
        from . import create_app
        app, socketio = create_app()
    except ImportError as e:
        logger.error(f"Failed to import web application: {e}")
        logger.error("Make sure the hwautomation.web module is properly configured")
        sys.exit(1)
    
    # Get configuration from environment
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"🌐 Starting HWAutomation Web Interface")
    logger.info(f"   Host: {host}")
    logger.info(f"   Port: {port}")
    logger.info(f"   Debug: {debug}")
    logger.info(f"   Mode: Container-optimized web module")
    
    # Start the application
    try:
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=True  # For development
        )
    except Exception as e:
        logger.error(f"Failed to start web application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
