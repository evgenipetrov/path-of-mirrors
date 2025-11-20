#!/bin/bash

# Path of Mirrors - Build Docker Images
# Usage: ./scripts/build-images.sh [--dev|--prod]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

source "$SCRIPT_DIR/lib/log.sh"
source "$SCRIPT_DIR/lib/compose.sh"

# Parse arguments
MODE="dev"
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
        *)
            echo "Unknown option: $1"
            echo "Usage: ./scripts/build-images.sh [--dev|--prod]"
            exit 1
            ;;
    esac
done

COMPOSE_FILES="$(select_compose_files "$MODE")"

log_info "Building Docker images for ${MODE} mode..."
docker compose $COMPOSE_FILES build
log_success "Build complete"

log_info "Next steps:"
echo "  - Start services: ./scripts/start-services.sh --${MODE}"
echo "  - View logs:      ./scripts/view-logs.sh backend -n 50"
