#!/usr/bin/env bash

# Script: migrate-db.sh
# Description: Database migration management (Alembic wrapper)
# Usage: ./scripts/migrate-db.sh [COMMAND] [OPTIONS]
#
# Commands:
#   (no args)         Run migrations (upgrade to latest)
#   create <message>  Create new migration
#   current           Show current migration version
#   rollback          Rollback one migration
#   history           Show migration history

set -e
set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/log.sh"
source "$SCRIPT_DIR/lib/compose.sh"
source "$SCRIPT_DIR/lib/wait.sh"
source "$SCRIPT_DIR/lib/backend.sh"

MODE="${MODE:-dev}"
COMPOSE_FILES="$(select_compose_files "$MODE")"

# Helper functions
show_help() {
    head -n 13 "$0" | tail -n 11 | sed 's/^# //'
    exit 0
}

ensure_backend_running() {
    local started_services=false

    if ! docker compose $COMPOSE_FILES ps backend | grep -q "Up" 2>/dev/null; then
        log_step "🐳 Starting services for migration..."
        dc up -d
        started_services=true

        # Wait for services to be ready
        log_info "Waiting for PostgreSQL..."
        if wait_for_pg "$COMPOSE_FILES" 30; then
            log_success "PostgreSQL ready"
        else
            log_error "PostgreSQL failed to start"
            exit 1
        fi
    fi

    echo "$started_services"
}

# Command handlers
cmd_upgrade() {
    log_step "🗄️  Running database migrations..."
    backend_exec "$COMPOSE_FILES" "uv run alembic upgrade head"
    log_success "Migrations complete!"
    echo ""
    log_info "Current revision:"
    backend_exec "$COMPOSE_FILES" "uv run alembic current"
}

cmd_create() {
    if [ -z "${1:-}" ]; then
        log_error "Migration message required"
        echo "Usage: ./scripts/db-migrate.sh create \"migration message\""
        exit 1
    fi

    local message="$1"
    log_step "📝 Creating new migration: $message"
    backend_exec "$COMPOSE_FILES" "uv run alembic revision --autogenerate -m \"$message\""
    log_success "Migration created!"
    echo ""
    log_info "Next steps:"
    echo "  1. Review migration file in backend/alembic/versions/"
    echo -e "  2. Run migration: ${BLUE}./scripts/migrate-db.sh${NC}"
}

cmd_current() {
    log_step "📍 Current migration version"
    backend_exec "$COMPOSE_FILES" "uv run alembic current"
}

cmd_rollback() {
    log_step "⏪ Rolling back one migration..."
    log_info "Current version:"
    backend_exec "$COMPOSE_FILES" "uv run alembic current"
    echo ""
    echo -n "Are you sure you want to rollback? (yes/no): "
    read -r confirmation

    if [ "$confirmation" != "yes" ]; then
        log_info "Rollback cancelled"
        exit 0
    fi

    backend_exec "$COMPOSE_FILES" "uv run alembic downgrade -1"
    log_success "Rollback complete!"
    echo ""
    log_info "New version:"
    backend_exec "$COMPOSE_FILES" "uv run alembic current"
}

cmd_history() {
    log_step "📜 Migration history"
    backend_exec "$COMPOSE_FILES" "uv run alembic history"
}

# Main function
main() {
    # Ensure backend is running
    local started_services
    started_services=$(ensure_backend_running)

    # Parse command
    local command="${1:-upgrade}"

    case "$command" in
        --help|-h|help)
            show_help
            ;;
        create)
            shift
            cmd_create "$@"
            ;;
        current)
            cmd_current
            ;;
        rollback)
            cmd_rollback
            ;;
        history)
            cmd_history
            ;;
        upgrade|"")
            cmd_upgrade
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            ;;
    esac

    # Cleanup - stop services if we started them
    if [ "$started_services" = "true" ]; then
        log_step "🛑 Stopping services..."
        dc down
        log_success "Services stopped"
    fi
}

# Change to project root
cd "$(dirname "$0")/.."

main "$@"
