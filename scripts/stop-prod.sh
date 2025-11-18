#!/usr/bin/env bash

# Script: stop-prod.sh
# Description: Stop production environment
# Usage: ./scripts/stop-prod.sh [OPTIONS]
#
# Options:
#   --help       Show this help message
#   --volumes    Remove volumes (deletes database data)

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
REMOVE_VOLUMES=false

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

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
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
    log_step "🛑 Stopping Production Environment"

    # Check if any containers are running
    if ! docker compose -f docker-compose.prod.yml ps -q | grep -q .; then
        log_info "No production containers are running"
        exit 0
    fi

    # Show what will be stopped
    log_info "Containers to stop:"
    docker compose -f docker-compose.prod.yml ps

    echo ""

    # Stop containers
    if [ "$REMOVE_VOLUMES" = true ]; then
        log_warning "Removing volumes - database data will be deleted!"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker compose -f docker-compose.prod.yml down -v
            log_success "Stopped and removed volumes"
        else
            log_info "Cancelled"
            exit 0
        fi
    else
        docker compose -f docker-compose.prod.yml down
        log_success "Stopped (volumes preserved)"
    fi

    echo ""
    log_info "To start again: ./scripts/start-prod.sh"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            ;;
        --volumes)
            REMOVE_VOLUMES=true
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
