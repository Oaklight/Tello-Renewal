#!/bin/bash
set -e

# Run script for Tello Renewal Docker container

# Default values
CONFIG_DIR="$HOME/.config/tello-renewal"
LOGS_DIR="./logs"

# Parse script-specific arguments
SCRIPT_ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --config-dir)
            CONFIG_DIR="$2"
            shift 2
            ;;
        --logs-dir)
            LOGS_DIR="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [SCRIPT_OPTIONS] [TELLO_RENEWAL_ARGS...]"
            echo ""
            echo "Script Options:"
            echo "  --config-dir DIR    Configuration directory (default: ~/.config/tello-renewal)"
            echo "  --logs-dir DIR      Logs directory (default: ./logs)"
            echo "  --help             Show this help"
            echo ""
            echo "All other arguments are passed directly to tello-renewal CLI."
            echo ""
            echo "Examples:"
            echo "  $0 renew --dry-run                   # Run dry-run renewal"
            echo "  $0 renew                             # Run actual renewal"
            echo "  $0 status                            # Check status"
            echo "  $0 config-validate                   # Validate config"
            echo "  $0 config-init                       # Create example config"
            echo "  $0 email-test                        # Send test email"
            echo "  $0 --help                            # Show tello-renewal help"
            echo ""
            echo "For tello-renewal specific help, run:"
            echo "  $0 --help"
            exit 0
            ;;
        *)
            # All other arguments go to tello-renewal
            SCRIPT_ARGS+=("$1")
            shift
            ;;
    esac
done

# Check if config directory exists
if [ ! -d "$CONFIG_DIR" ]; then
    echo "❌ Config directory not found: $CONFIG_DIR"
    echo "Please create it and add your config.toml file"
    echo "You can create an example config with: $0 config-init --output $CONFIG_DIR/config.toml"
    exit 1
fi

# Check if config file exists
if [ ! -f "$CONFIG_DIR/config.toml" ]; then
    echo "❌ Config file not found: $CONFIG_DIR/config.toml"
    echo "Please create your configuration file"
    echo "You can create an example config with: $0 config-init --output $CONFIG_DIR/config.toml"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

echo "🚀 Running Tello Renewal..."
echo "📁 Config: $CONFIG_DIR"
echo "📝 Logs: $LOGS_DIR"
echo "🔧 Args: ${SCRIPT_ARGS[*]}"
echo ""

# Run the container, passing all remaining arguments to tello-renewal
docker run --rm \
    -v "$(realpath "$CONFIG_DIR"):/app/config:ro" \
    -v "$(realpath "$LOGS_DIR"):/app/logs" \
    -e TZ=America/Chicago \
    oaklight/tello-renewal:latest \
    tello-renewal --config /app/config/config.toml "${SCRIPT_ARGS[@]}"

echo ""
echo "✅ Execution completed!"