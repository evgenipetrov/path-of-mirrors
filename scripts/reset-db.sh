#!/usr/bin/env bash

# Script: db-reset.sh
# Description: Reset the database (WARNING: deletes all data)
# Usage: ./scripts/db-reset.sh [OPTIONS]
#
# Options:
#   --help        Show this help message
#   --force       Skip confirmation prompt
#   --seed        Seed sample data after reset
#   --greenfield  Clean and regenerate migrations (for development)

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
FORCE=false
SEED=false
GREENFIELD=false

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
    head -n 12 "$0" | tail -n 10 | sed 's/^# //'
    exit 0
}

# Main reset function
main() {
    log_step "⚠️  Database Reset"

    # Warning and confirmation
    if [ "$FORCE" = false ]; then
        echo ""
        log_warning "WARNING: This will delete ALL data in the database!"
        echo ""
        echo -n "Are you sure you want to continue? (yes/no): "
        read -r confirmation

        if [ "$confirmation" != "yes" ]; then
            log_info "Database reset cancelled"
            exit 0
        fi
    fi

    # Stop services
    log_step "🛑 Stopping services..."
    docker compose down
    log_success "Services stopped"

    # Remove database volume
    log_step "🗑️  Removing database volume..."
    docker volume rm path-of-mirrors_postgres_data 2>/dev/null || true
    log_success "Database volume removed"

    # Start services with fresh build
    log_step "🚀 Building and starting services..."
    docker compose up -d --build

    # Wait for PostgreSQL
    log_info "Waiting for PostgreSQL to be ready..."
    local pg_ready=false
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if docker compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
            pg_ready=true
            break
        fi
        attempt=$((attempt + 1))
        sleep 1
    done

    if [ "$pg_ready" = true ]; then
        log_success "PostgreSQL ready"
    else
        log_error "PostgreSQL failed to start after ${max_attempts} seconds"
        log_info "Check logs with: docker compose logs postgres"
        exit 1
    fi

    # Wait for backend
    log_info "Waiting for backend to be ready..."
    sleep 2
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
            log_success "Backend ready"
            break
        fi
        attempt=$((attempt + 1))
        sleep 1
    done

    # Clean old migrations if greenfield mode
    if [ "$GREENFIELD" = true ]; then
        log_step "🧹 Cleaning old migrations (greenfield mode)..."
        find backend/alembic/versions -name "*.py" -type f ! -name "__init__.py" -delete 2>/dev/null || true
        log_success "Old migrations removed"

        log_step "📝 Generating fresh migration..."
        docker compose exec -T backend bash -c "cd /app && uv run alembic revision --autogenerate -m 'initial schema'"
        log_success "Fresh migration generated"
    fi

    # Run migrations
    log_step "🗄️  Running database migrations..."
    docker compose exec -T backend bash -c "cd /app && uv run alembic upgrade head"
    log_success "Migrations complete"

    # Seed data if requested
    if [ "$SEED" = true ]; then
        log_step "🌱 Seeding sample data..."
        if docker compose exec -T backend test -f scripts/seed.py; then
            docker compose exec -T backend uv run python scripts/seed.py
            log_success "Sample data seeded"
        else
            log_warning "No seed script found at scripts/seed.py (skipping)"
        fi
    fi

    # Success
    log_step "✅ Database reset complete!"
    echo ""
    log_info "Your database has been reset with a fresh schema"
    if [ "$GREENFIELD" = true ]; then
        log_info "Fresh migrations generated (greenfield mode)"
    fi
    if [ "$SEED" = true ]; then
        log_info "Sample data has been loaded"
    fi
    echo ""
    echo "Next steps:"
    echo -e "  - Access frontend: ${BLUE}http://localhost:5173${NC}"
    echo -e "  - Access backend:  ${BLUE}http://localhost:8000${NC}"
    echo -e "  - View API docs:   ${BLUE}http://localhost:8000/docs${NC}"
    echo ""
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --seed)
            SEED=true
            shift
            ;;
        --greenfield)
            GREENFIELD=true
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
