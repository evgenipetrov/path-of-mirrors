#!/usr/bin/env bash

# Script: start-prod.sh
# Description: Start production environment with built artifacts
# Usage: ./scripts/start-prod.sh [OPTIONS]
#
# Options:
#   --help           Show this help message
#   --build          Build artifacts before starting
#   --no-healthcheck Skip health checks
#   --detach         Run in detached mode (background)

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
BUILD_FIRST=false
SKIP_HEALTHCHECK=false
DETACHED=false

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

check_image() {
    if ! docker images "$1" --format "{{.Repository}}:{{.Tag}}" | grep -q "^$1$"; then
        log_error "Missing Docker image: $1"
        echo "Run './scripts/build-prod.sh' first to build production images"
        exit 1
    fi
}

wait_for_service() {
    local service=$1
    local url=$2
    local max_attempts=30
    local attempt=1

    log_info "Waiting for $service to be ready..."

    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$url" > /dev/null 2>&1; then
            log_success "$service is ready"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done

    log_error "$service failed to start within $max_attempts seconds"
    return 1
}

cleanup() {
    if [ "$DETACHED" = false ]; then
        log_step "🛑 Stopping production environment..."
        docker compose -f docker-compose.prod.yml down
        log_success "Stopped"
    fi
}

# Main function
main() {
    log_step "🚀 Starting Production Environment"

    # Build first if requested
    if [ "$BUILD_FIRST" = true ]; then
        log_step "🏗️  Building production artifacts..."
        if ./scripts/build-prod.sh; then
            log_success "Build completed"
        else
            log_error "Build failed"
            exit 1
        fi
    fi

    # Check prerequisites
    log_step "🔍 Checking prerequisites..."
    check_image "path-of-mirrors-backend:latest"
    check_image "path-of-mirrors-frontend:latest"
    log_success "All Docker images found"

    # Stop any running production containers
    log_step "🧹 Cleaning up existing containers..."
    docker compose -f docker-compose.prod.yml down 2>/dev/null || true
    log_success "Cleanup complete"

    # Start services
    log_step "🐳 Starting Docker containers..."

    if [ "$DETACHED" = true ]; then
        docker compose -f docker-compose.prod.yml up -d
    else
        # Set up cleanup on exit
        trap cleanup EXIT INT TERM

        # Start in foreground but run health checks first
        docker compose -f docker-compose.prod.yml up -d

        # Wait for services to be ready
        if [ "$SKIP_HEALTHCHECK" = false ]; then
            log_step "🏥 Running health checks..."

            # Wait for backend
            if wait_for_service "Backend API" "http://localhost:8000/health"; then
                # Check database connectivity
                if wait_for_service "Backend readiness" "http://localhost:8000/ready"; then
                    log_success "Backend is fully operational"
                else
                    log_warning "Backend started but database not ready"
                fi
            else
                log_error "Backend health check failed"
                exit 1
            fi

            # Wait for frontend
            if wait_for_service "Frontend" "http://localhost:3000"; then
                log_success "Frontend is operational"
            else
                log_error "Frontend health check failed"
                exit 1
            fi
        fi

        # Show summary
        log_step "✅ Production Environment Started!"
        echo ""
        echo "Services:"
        echo -e "  ${GREEN}Frontend:${NC}     http://localhost:3000"
        echo -e "  ${GREEN}Backend API:${NC}  http://localhost:8000"
        echo -e "  ${GREEN}API Docs:${NC}     http://localhost:8000/docs"
        echo -e "  ${GREEN}PostgreSQL:${NC}   localhost:5432"
        echo -e "  ${GREEN}Redis:${NC}        localhost:6379"
        echo ""
        echo "Container status:"
        docker compose -f docker-compose.prod.yml ps
        echo ""
        log_info "Press Ctrl+C to stop all services"
        echo ""

        # Attach to logs
        docker compose -f docker-compose.prod.yml logs -f
    fi

    if [ "$DETACHED" = true ]; then
        # Show health checks for detached mode
        if [ "$SKIP_HEALTHCHECK" = false ]; then
            log_step "🏥 Running health checks..."
            sleep 5  # Give services a moment to start

            if wait_for_service "Backend API" "http://localhost:8000/health" && \
               wait_for_service "Backend readiness" "http://localhost:8000/ready" && \
               wait_for_service "Frontend" "http://localhost:3000"; then
                log_success "All services healthy"
            else
                log_warning "Some services may not be ready yet"
            fi
        fi

        # Show summary for detached mode
        log_step "✅ Production Environment Started!"
        echo ""
        echo "Services:"
        echo -e "  ${GREEN}Frontend:${NC}     http://localhost:3000"
        echo -e "  ${GREEN}Backend API:${NC}  http://localhost:8000"
        echo -e "  ${GREEN}API Docs:${NC}     http://localhost:8000/docs"
        echo -e "  ${GREEN}PostgreSQL:${NC}   localhost:5432"
        echo -e "  ${GREEN}Redis:${NC}        localhost:6379"
        echo ""
        echo "Container status:"
        docker compose -f docker-compose.prod.yml ps
        echo ""
        echo "Useful commands:"
        echo -e "  ${BLUE}View logs:${NC}      docker compose -f docker-compose.prod.yml logs -f"
        echo -e "  ${BLUE}Stop services:${NC}  docker compose -f docker-compose.prod.yml down"
        echo -e "  ${BLUE}Restart:${NC}        ./scripts/restart-prod.sh"
        echo ""
    fi
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            ;;
        --build)
            BUILD_FIRST=true
            shift
            ;;
        --no-healthcheck)
            SKIP_HEALTHCHECK=true
            shift
            ;;
        --detach)
            DETACHED=true
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
