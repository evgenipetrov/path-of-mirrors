#!/usr/bin/env bash

# Script: db-migrate.sh
# Description: Database migration management (Alembic wrapper)
# Usage: ./scripts/db-migrate.sh [COMMAND] [OPTIONS]
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

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

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
    head -n 13 "$0" | tail -n 11 | sed 's/^# //'
    exit 0
}

check_backend() {
    if ! docker compose ps backend | grep -q "Up"; then
        log_error "Backend container is not running"
        log_info "Start services with: ./scripts/dev.sh"
        exit 1
    fi
}

# Command handlers
cmd_upgrade() {
    log_step "🗄️  Running database migrations..."
    docker compose exec -T backend bash -c "cd src && uv run alembic upgrade head"
    log_success "Migrations complete!"
    echo ""
    log_info "Current revision:"
    docker compose exec -T backend bash -c "cd src && uv run alembic current"
}

cmd_create() {
    if [ -z "${1:-}" ]; then
        log_error "Migration message required"
        echo "Usage: ./scripts/db-migrate.sh create \"migration message\""
        exit 1
    fi

    local message="$1"
    log_step "📝 Creating new migration: $message"
    docker compose exec -T backend bash -c "cd src && uv run alembic revision --autogenerate -m \"$message\""
    log_success "Migration created!"
    echo ""
    log_info "Next steps:"
    echo "  1. Review migration file in backend/src/migrations/versions/"
    echo -e "  2. Run migration: ${BLUE}./scripts/db-migrate.sh${NC}"
}

cmd_current() {
    log_step "📍 Current migration version"
    docker compose exec -T backend bash -c "cd src && uv run alembic current"
}

cmd_rollback() {
    log_step "⏪ Rolling back one migration..."
    log_info "Current version:"
    docker compose exec -T backend bash -c "cd src && uv run alembic current"
    echo ""
    echo -n "Are you sure you want to rollback? (yes/no): "
    read -r confirmation

    if [ "$confirmation" != "yes" ]; then
        log_info "Rollback cancelled"
        exit 0
    fi

    docker compose exec -T backend bash -c "cd src && uv run alembic downgrade -1"
    log_success "Rollback complete!"
    echo ""
    log_info "New version:"
    docker compose exec -T backend bash -c "cd src && uv run alembic current"
}

cmd_history() {
    log_step "📜 Migration history"
    docker compose exec -T backend bash -c "cd src && uv run alembic history"
}

# Main function
main() {
    # Check backend is running
    check_backend

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
}

# Change to project root
cd "$(dirname "$0")/.."

main "$@"
