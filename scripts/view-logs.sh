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

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/log.sh"
source "$SCRIPT_DIR/lib/compose.sh"

# Configuration
MODE="dev"
SERVICE=""
FOLLOW=false
LINES=""

show_help() {
    head -n 16 "$0" | tail -n 14 | sed 's/^# //'
    exit 0
}

# Main function
main() {
    # Set compose files based on mode
    COMPOSE_FILES="$(select_compose_files "$MODE")"

    # Check if Docker Compose is running
    if ! docker compose $COMPOSE_FILES ps | grep -q "Up"; then
        log_error "No services are running"
        log_info "Start services with: ./scripts/start-services.sh"
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

    if [ "$FOLLOW" = false ]; then
        echo ""
        log_info "Next steps:"
        echo "  - Follow logs: ${YELLOW}$cmd -f${NC}"
        echo "  - Restart:     ./scripts/restart-services.sh --${MODE}"
    fi
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
