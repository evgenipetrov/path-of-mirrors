#!/usr/bin/env bash

# Script: view-logs.sh
# Description: View Docker service logs
# Usage: ./scripts/view-logs.sh [SERVICE] [OPTIONS]
#
# Services:
#   (no args)    Show all services
#   backend      Backend API logs
#   db           PostgreSQL logs
#   redis        Redis logs
#
# Options:
#   --dev             Use dev compose files (default)
#   --prod            Use prod compose files
#   -f, --follow      Follow log output (tail -f)
#   -n, --lines NUM   Show last NUM lines (default: all)
#   --help            Show this help message

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
MODE="dev"
SERVICE=""
FOLLOW=false
LINES=""

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_step() {
    echo -e "\n${BOLD}$1${NC}"
    echo "====================================="
}

show_help() {
    head -n 16 "$0" | tail -n 14 | sed 's/^# //'
    exit 0
}

# Main function
main() {
    # Set compose files based on mode
    if [ "$MODE" = "prod" ]; then
        COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
    else
        COMPOSE_FILES="-f docker-compose.yml -f docker-compose.dev.yml"
    fi

    # Check if Docker Compose is running
    if ! docker compose $COMPOSE_FILES ps | grep -q "Up"; then
        log_error "No services are running"
        log_info "Start services with: ./scripts/start.sh"
        exit 1
    fi

    # Build docker compose logs command
    local cmd="docker compose $COMPOSE_FILES logs"

    # Add follow flag
    if [ "$FOLLOW" = true ]; then
        cmd="$cmd -f"
    fi

    # Add lines flag
    if [ -n "$LINES" ]; then
        cmd="$cmd --tail=$LINES"
    fi

    # Add service if specified
    if [ -n "$SERVICE" ]; then
        # Validate service name
        case "$SERVICE" in
            backend|postgres|redis)
                cmd="$cmd $SERVICE"
                log_step "📋 Viewing logs: $SERVICE"
                ;;
            *)
                log_error "Unknown service: $SERVICE"
                echo ""
                echo "Available services:"
                echo "  - backend    Backend API"
                echo "  - postgres   PostgreSQL"
                echo "  - redis      Redis"
                exit 1
                ;;
        esac
    else
        log_step "📋 Viewing logs: all services"
    fi

    if [ "$FOLLOW" = true ]; then
        echo ""
        log_info "Following logs (press Ctrl+C to stop)..."
    fi

    echo ""

    # Execute command
    eval "$cmd"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            ;;
        --dev)
            MODE="dev"
            shift
            ;;
        --prod)
            MODE="prod"
            shift
            ;;
        -f|--follow)
            FOLLOW=true
            shift
            ;;
        -n|--lines)
            LINES="$2"
            shift 2
            ;;
        backend|db|redis)
            SERVICE="$1"
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
