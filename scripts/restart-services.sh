#!/bin/bash

# Path of Mirrors - Restart Services
# Usage: ./scripts/restart-services.sh [--dev|--prod] [--build]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

source "$SCRIPT_DIR/lib/log.sh"

# Parse arguments
MODE="dev"
BUILD_FLAG=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            MODE="dev"
            shift
            ;;
        --prod)
            MODE="prod"
            shift
            ;;
        --build)
            BUILD_FLAG="--build"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./scripts/restart-services.sh [--dev|--prod] [--build]"
            exit 1
            ;;
    esac
done

log_info "Restarting Path of Mirrors (${MODE} mode)..."

# Stop services
./scripts/stop-services.sh --${MODE}

# Start services
if [ -n "$BUILD_FLAG" ]; then
    ./scripts/start-services.sh --${MODE} --build
else
    ./scripts/start-services.sh --${MODE}
fi

log_success "All services restarted"

log_info "Next steps:"
echo "  - View logs:   ./scripts/view-logs.sh backend -f"
echo "  - Stop:        ./scripts/stop-services.sh --${MODE}"
