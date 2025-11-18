#!/usr/bin/env bash

# Script: setup.sh
# Description: Initial project setup for new developers
# Usage: ./scripts/setup.sh [OPTIONS]
#
# Options:
#   --help        Show this help message
#   --skip-seed   Skip seeding sample data

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
SKIP_SEED=false

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

check_command() {
    if command -v "$1" &> /dev/null; then
        local version=$($2 2>&1 || echo "unknown")
        log_success "$3 installed ($version)"
        return 0
    else
        log_error "$3 not found"
        return 1
    fi
}

wait_for_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    return 1
}

# Main setup function
main() {
    log_step "🚀 Path of Mirrors - Initial Setup"

    # Check prerequisites
    log_step "📋 Checking prerequisites..."
    local prereqs_ok=true

    check_command "docker" "docker --version" "Docker" || prereqs_ok=false
    check_command "docker" "docker compose version" "Docker Compose" || prereqs_ok=false
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
    if [ ! -d "frontend/node_modules" ]; then
        cd frontend
        npm install
        cd ..
        log_success "Frontend dependencies installed"
    else
        log_info "Frontend dependencies already installed (skipping)"
    fi

    # Build and start Docker services
    log_step "🐳 Building and starting Docker services..."
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
        log_success "PostgreSQL ready (port 5432)"
    else
        log_error "PostgreSQL failed to start after ${max_attempts} seconds"
        log_info "Check logs with: docker compose logs postgres"
        exit 1
    fi

    # Wait for Redis
    log_info "Waiting for Redis to be ready..."
    local redis_ready=false
    attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
            redis_ready=true
            break
        fi
        attempt=$((attempt + 1))
        sleep 1
    done

    if [ "$redis_ready" = true ]; then
        log_success "Redis ready (port 6379)"
    else
        log_error "Redis failed to start after ${max_attempts} seconds"
        log_info "Check logs with: docker compose logs redis"
        exit 1
    fi

    # Wait for backend health check
    log_info "Waiting for Backend API to be ready..."
    if wait_for_service "backend" "http://localhost:8000/health"; then
        log_success "Backend API ready (port 8000)"
    else
        log_error "Backend API failed to start"
        log_info "Check logs with: docker compose logs backend"
        exit 1
    fi

    # Run database migrations
    log_step "🗄️  Running database migrations..."
    docker compose exec -T backend bash -c "cd /app && uv run alembic upgrade head"
    log_success "Migrations complete"

    # Seed sample data (optional)
    if [ "$SKIP_SEED" = false ]; then
        log_info "Checking for seed script..."
        if docker compose exec -T backend test -f scripts/seed.py; then
            log_info "Seeding sample data..."
            docker compose exec -T backend uv run python scripts/seed.py
            log_success "Sample data seeded"
        else
            log_info "No seed script found (skipping)"
        fi
    fi

    # Stop Docker services
    log_step "🛑 Stopping Docker services..."
    docker compose down
    log_success "Services stopped"

    # Success message
    log_step "✅ Setup complete!"
    echo ""
    log_success "Your Path of Mirrors development environment is ready!"
    echo ""
    echo "Next steps:"
    echo -e "  1. Start development: ${BLUE}./scripts/start-dev.sh${NC}"
    echo -e "  2. Run tests:         ${BLUE}./scripts/run-tests.sh${NC}"
    echo -e "  3. Build production:  ${BLUE}./scripts/build-prod.sh${NC}"
    echo ""
    log_info "The setup script has stopped all containers."
    log_info "Use ./scripts/start-dev.sh to start the development environment."
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
cd "$(dirname "$0")/.."

main
