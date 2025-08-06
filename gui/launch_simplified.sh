#!/bin/bash
"""
Simplified HWAutomation GUI Launcher

Launches the streamlined batch device management interface.
"""

cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "../hwautomation-env" ]; then
    source ../hwautomation-env/bin/activate
    echo "✅ Virtual environment activated"
fi

# Set environment variables
export PYTHONPATH="../src:$PYTHONPATH"

# Launch the simplified GUI
echo "🚀 Starting HWAutomation Simplified GUI..."
echo "📖 Access at: http://localhost:5001"
echo "🛑 Press Ctrl+C to stop"
echo ""

python3 app_simplified.py --host 0.0.0.0 --port 5001 --debug
