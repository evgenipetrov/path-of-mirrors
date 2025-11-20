#!/bin/bash

# Path of Mirrors - Stop Services
# Usage: ./scripts/stop-services.sh [--dev|--prod]

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
            echo "Usage: ./scripts/stop-services.sh [--dev|--prod]"
            exit 1
            ;;
    esac
done

COMPOSE_FILES="$(select_compose_files "$MODE")"

log_info "Stopping Path of Mirrors services (${MODE} mode)..."

# Stop Docker services
docker compose $COMPOSE_FILES down

# Kill any remaining frontend processes (dev mode)
if [ "$MODE" = "dev" ]; then
    pkill -f "vite" 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true
fi

log_success "All services stopped"

log_info "Next steps:"
echo "  - Start dev:   ./scripts/start-services.sh --dev"
echo "  - Start prod:  ./scripts/start-services.sh --prod"
