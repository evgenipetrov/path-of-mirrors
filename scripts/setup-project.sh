#!/usr/bin/env bash

# Script: setup-project.sh
# Description: Initial project setup for new developers
# Usage: ./scripts/setup-project.sh [OPTIONS]
#
# Options:
#   --help        Show this help message
#   --skip-seed   Skip seeding sample data

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

source "$SCRIPT_DIR/lib/log.sh"
source "$SCRIPT_DIR/lib/compose.sh"
source "$SCRIPT_DIR/lib/wait.sh"
source "$SCRIPT_DIR/lib/backend.sh"
source "$SCRIPT_DIR/lib/frontend.sh"

MODE="${MODE:-dev}"
COMPOSE_FILES="$(select_compose_files "$MODE")"

# Configuration
SKIP_SEED=false

show_help() {
    head -n 10 "$0" | tail -n 8 | sed 's/^# //'
    exit 0
}

check_command() {
    if command -v "$1" &> /dev/null; then
        local version
        version=$($2 2>&1 || echo "unknown")
        log_success "$3 installed ($version)"
        return 0
    else
        log_error "$3 not found"
        return 1
    fi
}

# Main setup function
main() {
    log_step "🚀 Path of Mirrors - Initial Setup"

    # Check prerequisites
    log_step "📋 Checking prerequisites..."
    local prereqs_ok=true

    check_command "docker" "docker --version" "Docker" || prereqs_ok=false
    check_command "docker" "docker compose $COMPOSE_FILES version" "Docker Compose" || prereqs_ok=false
    check_command "node" "node --version" "Node.js" || prereqs_ok=false
    check_command "npm" "npm --version" "npm" || prereqs_ok=false

    if [ "$prereqs_ok" = false ]; then
        log_error "Missing required dependencies. Please install them and try again."
        echo ""
        log_info "Installation instructions:"
        echo "  - Docker: https://docs.docker.com/get-docker/"
        echo "  - Node.js: https://nodejs.org/"
        exit 1
    fi

    # Install frontend dependencies
    log_step "📦 Installing frontend dependencies..."
    if ensure_frontend_deps; then
        log_success "Frontend dependencies installed"
    else
        log_info "Frontend dependencies already installed (skipping)"
    fi

    # Build and start Docker services
    log_step "🐳 Building and starting Docker services..."
    docker compose $COMPOSE_FILES up -d --build

    # Wait for PostgreSQL
    log_info "Waiting for PostgreSQL to be ready..."
    if wait_for_pg "$COMPOSE_FILES" 30; then
        log_success "PostgreSQL ready (port 5432)"
    else
        log_error "PostgreSQL failed to start after 30 seconds"
        log_info "Check logs with: docker compose $COMPOSE_FILES logs postgres"
        exit 1
    fi

    # Wait for Redis
    log_info "Waiting for Redis to be ready..."
    if wait_for_redis "$COMPOSE_FILES" 30; then
        log_success "Redis ready (port 6379)"
    else
        log_error "Redis failed to start after 30 seconds"
        log_info "Check logs with: docker compose $COMPOSE_FILES logs redis"
        exit 1
    fi

    # Wait for backend health check
    log_info "Waiting for Backend API to be ready..."
    if wait_for_url "http://localhost:8000/health" 30; then
        log_success "Backend API ready (port 8000)"
    else
        log_error "Backend API failed to start"
        log_info "Check logs with: docker compose $COMPOSE_FILES logs backend"
        exit 1
    fi

    # Run database migrations
    log_step "🗄️  Running database migrations..."
    docker compose $COMPOSE_FILES exec -T backend bash -c "cd /app && uv run alembic upgrade head"
    log_success "Migrations complete"

    # Seed sample data (optional)
    if [ "$SKIP_SEED" = false ]; then
        log_info "Checking for seed script..."
        if docker compose $COMPOSE_FILES exec -T backend test -f scripts/seed.py; then
            log_info "Seeding sample data..."
            docker compose $COMPOSE_FILES exec -T backend uv run python scripts/seed.py
            log_success "Sample data seeded"
        else
            log_info "No seed script found (skipping)"
        fi
    fi

    # Stop Docker services
    log_step "🛑 Stopping Docker services..."
    docker compose $COMPOSE_FILES down
    log_success "Services stopped"

    # Success message
    log_step "✅ Setup complete!"
    echo ""
    log_success "Your Path of Mirrors development environment is ready!"
    echo ""
    echo "Next steps:"
    echo -e "  1. Start development: ${BLUE}./scripts/start-services.sh${NC}"
    echo -e "  2. Run tests:         ${BLUE}./scripts/run-tests.sh${NC}"
    echo -e "  3. Build production:  ${BLUE}./scripts/build-images.sh --prod${NC}"
    echo ""
    log_info "The setup script has stopped all containers."
    log_info "Use ./scripts/start-services.sh to start the development environment."
    echo ""
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            ;;
        --skip-seed)
            SKIP_SEED=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            ;;
    esac
done

# Change to project root

# Docker Compose files for development

main
