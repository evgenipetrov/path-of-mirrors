#!/usr/bin/env bash

# Script: build-prod.sh
# Description: Build production artifacts
# Usage: ./scripts/build-prod.sh [OPTIONS]
#
# Options:
#   --help         Show this help message
#   --skip-tests   Skip running tests
#   --skip-lint    Skip running linters
#   --skip-all     Skip both tests and linting

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
SKIP_TESTS=false
SKIP_LINT=false

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
    head -n 11 "$0" | tail -n 9 | sed 's/^# //'
    exit 0
}

get_size() {
    if [ -d "$1" ]; then
        du -sh "$1" 2>/dev/null | cut -f1 || echo "unknown"
    else
        echo "not found"
    fi
}

get_image_size() {
    docker images "$1" --format "{{.Size}}" 2>/dev/null | head -n1 || echo "unknown"
}

# Main build function
main() {
    log_step "🏗️  Building Production Artifacts"

    local start_time=$(date +%s)

    # Run linting
    if [ "$SKIP_LINT" = false ]; then
        log_step "🔍 Running linters..."
        if ./scripts/check-code.sh; then
            log_success "Linting passed"
        else
            log_error "Linting failed - build aborted"
            exit 1
        fi
    else
        log_warning "Skipping linting (--skip-lint)"
    fi

    # Run tests
    if [ "$SKIP_TESTS" = false ]; then
        log_step "🧪 Running tests..."
        if ./scripts/run-tests.sh; then
            log_success "Tests passed"
        else
            log_error "Tests failed - build aborted"
            exit 1
        fi
    else
        log_warning "Skipping tests (--skip-tests)"
    fi

    # Build Docker images using docker-compose
    log_step "🐳 Building Docker images..."

    docker compose -f docker-compose.prod.yml build

    # Tag images with timestamp
    docker tag path-of-mirrors-backend:latest path-of-mirrors-backend:$(date +%Y%m%d-%H%M%S)
    docker tag path-of-mirrors-frontend:latest path-of-mirrors-frontend:$(date +%Y%m%d-%H%M%S)

    local backend_size=$(get_image_size "path-of-mirrors-backend:latest")
    local frontend_size=$(get_image_size "path-of-mirrors-frontend:latest")
    log_success "Backend image built: path-of-mirrors-backend:latest ($backend_size)"
    log_success "Frontend image built: path-of-mirrors-frontend:latest ($frontend_size)"

    # Calculate build time
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))

    # Success summary
    log_step "✅ Build Complete!"
    echo ""
    echo "Docker Images:"
    echo -e "  ${GREEN}Frontend:${NC}     path-of-mirrors-frontend:latest ($frontend_size)"
    echo -e "  ${GREEN}Backend:${NC}      path-of-mirrors-backend:latest ($backend_size)"
    echo ""
    echo "Build time: ${minutes}m ${seconds}s"
    echo ""
    echo "Next steps:"
    echo -e "  ${BLUE}Start production:${NC}  ./scripts/start-prod.sh"
    echo -e "  ${BLUE}View images:${NC}       docker images | grep path-of-mirrors"
    echo ""
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --skip-lint)
            SKIP_LINT=true
            shift
            ;;
        --skip-all)
            SKIP_TESTS=true
            SKIP_LINT=true
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
