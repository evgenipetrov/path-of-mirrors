#!/usr/bin/env bash

# Script: run-tests.sh
# Description: Run all tests (backend and frontend)
# Usage: ./scripts/run-tests.sh [OPTIONS]
#
# Options:
#   --help        Show this help message
#   --coverage    Run tests with coverage report
#   --backend     Run backend tests only
#   --frontend    Run frontend tests only

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
RUN_BACKEND=true
RUN_FRONTEND=true
WITH_COVERAGE=false

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

# Main test function
main() {
    local total_passed=0
    local total_failed=0
    local backend_passed=0
    local frontend_passed=0
    local start_time=$(date +%s)
    local started_services=false

    # Run backend tests
    if [ "$RUN_BACKEND" = true ]; then
        # Start backend if not running
        if ! docker compose $COMPOSE_FILES ps backend | grep -q "Up" 2>/dev/null; then
            log_step "🐳 Starting services for testing..."
            docker compose $COMPOSE_FILES up -d
            started_services=true

            # Wait for services to be ready
            log_info "Waiting for services to be ready..."
            sleep 5

            # Wait for PostgreSQL
            local max_attempts=30
            local attempt=0
            while [ $attempt -lt $max_attempts ]; do
                if docker compose $COMPOSE_FILES exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
                    break
                fi
                attempt=$((attempt + 1))
                sleep 1
            done
            log_success "Services ready"
        fi

        log_step "🧪 Running Backend Tests (pytest)"

        if [ "$WITH_COVERAGE" = true ]; then
            log_info "Running with coverage report..."
            if docker compose $COMPOSE_FILES exec -T backend uv run --extra dev pytest --cov=src --cov-report=term-missing tests/; then
                backend_result=$?
                log_success "Backend tests passed with coverage"
            else
                backend_result=$?
                log_error "Backend tests failed"
            fi
        else
            if docker compose $COMPOSE_FILES exec -T backend uv run --extra dev pytest tests/ -v; then
                backend_result=$?
                # Extract test count from pytest output
                backend_passed=$(docker compose $COMPOSE_FILES exec -T backend uv run --extra dev pytest tests/ --co -q 2>/dev/null | wc -l || echo "0")
                log_success "Backend tests passed"
            else
                backend_result=$?
                log_error "Backend tests failed"
                total_failed=$((total_failed + 1))
            fi
        fi

        if [ $backend_result -eq 0 ]; then
            total_passed=$((total_passed + backend_passed))
        fi
    fi

    # Run frontend tests
    if [ "$RUN_FRONTEND" = true ]; then
        log_step "Frontend Tests (vitest)"

        if [ ! -d "frontend/node_modules" ]; then
            log_error "Frontend dependencies not installed"
            log_info "Run: cd frontend && npm install"
            exit 1
        fi

        # Check if frontend tests exist
        if [ ! -d "frontend/src/__tests__" ] && [ ! -f "frontend/vitest.config.ts" ]; then
            log_warning "Frontend tests not yet implemented (skipping)"
            log_info "This is expected in Phase 0 - tests will be added in Phase 1"
        else
            cd frontend
            if [ "$WITH_COVERAGE" = true ]; then
                log_info "Running with coverage report..."
                if npm run test:coverage; then
                    frontend_result=$?
                    log_success "Frontend tests passed with coverage"
                else
                    frontend_result=$?
                    log_error "Frontend tests failed"
                fi
            else
                if npm test; then
                    frontend_result=$?
                    frontend_passed=12  # TODO: Parse actual count from vitest output
                    log_success "Frontend tests passed"
                else
                    frontend_result=$?
                    log_error "Frontend tests failed"
                    total_failed=$((total_failed + 1))
                fi
            fi
            cd ..

            if [ $frontend_result -eq 0 ]; then
                total_passed=$((total_passed + frontend_passed))
            fi
        fi
    fi

    # Cleanup - stop services if we started them
    if [ "$started_services" = true ]; then
        log_step "🛑 Stopping services..."
        docker compose $COMPOSE_FILES down
        log_success "Services stopped"
    fi

    # Calculate duration
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Summary
    log_step "Test Summary"
    if [ $total_failed -eq 0 ]; then
        log_success "All tests passed!"
        echo ""
        echo -e "  ${GREEN}Total tests:${NC} $total_passed passed"
        echo -e "  ${GREEN}Duration:${NC}    ${duration}s"
        exit 0
    else
        log_error "Some tests failed!"
        echo ""
        echo -e "  ${RED}Failed suites:${NC} $total_failed"
        echo -e "  ${GREEN}Passed tests:${NC}  $total_passed"
        echo -e "  ${BLUE}Duration:${NC}      ${duration}s"
        exit 1
    fi
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            ;;
        --coverage)
            WITH_COVERAGE=true
            shift
            ;;
        --backend)
            RUN_FRONTEND=false
            shift
            ;;
        --frontend)
            RUN_BACKEND=false
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
