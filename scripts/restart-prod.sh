#!/usr/bin/env bash

# Script: restart-prod.sh
# Description: Restart production environment
# Usage: ./scripts/restart-prod.sh [OPTIONS]
#
# Options:
#   --help     Show this help message
#   --rebuild  Rebuild artifacts before restarting

set -e
set -u
set -o pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
REBUILD=false

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "\n${BOLD}$1${NC}"
    echo "====================================="
}

show_help() {
    head -n 10 "$0" | tail -n 8 | sed 's/^# //'
    exit 0
}

# Main function
main() {
    log_step "🔄 Restarting Production Environment"

    # Rebuild if requested
    if [ "$REBUILD" = true ]; then
        if ./scripts/build-prod.sh; then
            log_success "Rebuild completed"
        else
            log_error "Rebuild failed"
            exit 1
        fi
    fi

    # Stop
    log_info "Stopping services..."
    docker compose -f docker-compose.prod.yml down 2>/dev/null || true

    # Start
    log_info "Starting services..."
    ./scripts/start-prod.sh --detach

    log_success "Restart complete"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            ;;
        --rebuild)
            REBUILD=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            ;;
    esac
done

# Change to project root
cd "$(dirname "$0")/.."

main
