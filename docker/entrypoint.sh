#!/bin/bash
# Smart entrypoint for HWAutomation containers
# Automatically detects the appropriate mode (web or CLI) based on context

set -e

# Default values
MODE=${HWAUTOMATION_MODE:-"auto"}
COMMAND=${1:-""}

# Function to detect mode
detect_mode() {
    # If explicitly set, use that
    if [[ "$MODE" != "auto" ]]; then
        echo "$MODE"
        return
    fi
    
    # If running in a container with port 5000 exposed, assume web mode
    if [[ -n "$FLASK_PORT" ]] || [[ -n "$WEB_MODE" ]] || [[ "$COMMAND" == "web" ]]; then
        echo "web"
        return
    fi
    
    # If interactive terminal, default to CLI
    if [[ -t 0 ]]; then
        echo "cli"
        return
    fi
    
    # Default to web for container deployment
    echo "web"
}

# Detect the mode
DETECTED_MODE=$(detect_mode)

echo "🚀 HWAutomation Container Starting..."
echo "   Mode: $DETECTED_MODE"
echo "   Command: $COMMAND"

# Set up environment
export PYTHONPATH="/app/src:$PYTHONPATH"

case "$DETECTED_MODE" in
    "web")
        echo "🌐 Starting Web Interface..."
        
        # If no command specified, start web app
        if [[ -z "$COMMAND" ]] || [[ "$COMMAND" == "web" ]]; then
            cd /app
            exec python -m hwautomation.web
        else
            # Execute custom command in web context
            exec "$@"
        fi
        ;;
        
    "cli")
        echo "💻 Starting CLI Interface..."
        
        # If no command specified, show help
        if [[ -z "$COMMAND" ]] || [[ "$COMMAND" == "cli" ]]; then
            exec python -m hwautomation.cli --help
        else
            # Execute CLI command
            exec python -m hwautomation.cli "$@"
        fi
        ;;
        
    *)
        echo "❌ Unknown mode: $DETECTED_MODE"
        echo "Available modes: web, cli"
        exit 1
        ;;
esac
