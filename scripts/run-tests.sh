#!/usr/bin/env bash

# Script: run-tests.sh
# Description: Run all tests (backend and frontend)
# Usage: ./scripts/run-tests.sh [OPTIONS]
#
# Options:
#   --help        Show this help message
#   --coverage    Run tests with coverage report (default)
#   --no-coverage Skip coverage collection
#   --backend     Run backend tests only
#   --frontend    Run frontend tests only

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/log.sh"
source "$SCRIPT_DIR/lib/compose.sh"
source "$SCRIPT_DIR/lib/wait.sh"
source "$SCRIPT_DIR/lib/backend.sh"
source "$SCRIPT_DIR/lib/frontend.sh"

MODE="${MODE:-dev}"
COMPOSE_FILES="$(select_compose_files "$MODE")"

# Configuration
RUN_BACKEND=true
RUN_FRONTEND=true
WITH_COVERAGE=true

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
    local start_time
    start_time=$(date +%s)
    local started_services=false

    # Run backend tests
    if [ "$RUN_BACKEND" = true ]; then
        # Start backend if not running
        if ! docker compose $COMPOSE_FILES ps backend | grep -q "Up" 2>/dev/null; then
            log_step "🐳 Starting services for testing..."
            docker compose $COMPOSE_FILES up -d
            started_services=true
        fi

        log_info "Waiting for PostgreSQL..."
        if wait_for_pg "$COMPOSE_FILES" 30; then
            log_success "PostgreSQL ready"
        else
            log_error "PostgreSQL failed to start"
            exit 1
        fi

        log_info "Running database migrations..."
        docker compose $COMPOSE_FILES exec -T backend uv run alembic upgrade head >/dev/null

        log_step "🧪 Running Backend Tests (pytest)"

        if [ "$WITH_COVERAGE" = true ]; then
            log_info "Running with coverage report..."
            if docker compose $COMPOSE_FILES exec -T backend uv run --extra dev pytest --cov=src --cov-report=term-missing --cov-fail-under=70 tests/; then
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

        if ensure_frontend_deps; then
            log_success "Frontend dependencies installed"
        else
            log_info "Frontend dependencies already installed"
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
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - start_time))

    # Summary
    log_step "Test Summary"
    if [ $total_failed -eq 0 ]; then
        log_success "All tests passed!"
        echo ""
        echo -e "  ${GREEN}Total tests:${NC} $total_passed passed"
        echo -e "  ${GREEN}Duration:${NC}    ${duration}s"
        echo ""
        log_info "Next steps:"
        echo "  - Lint & types: ./scripts/check-code.sh"
        echo "  - Run backend only: ./scripts/run-tests.sh --backend"
        echo "  - Run frontend only: ./scripts/run-tests.sh --frontend"
        exit 0
    else
        log_error "Some tests failed!"
        echo ""
        echo -e "  ${RED}Failed suites:${NC} $total_failed"
        echo -e "  ${GREEN}Passed tests:${NC}  $total_passed"
        echo -e "  ${BLUE}Duration:${NC}      ${duration}s"
        echo ""
        log_info "Next steps:"
        echo "  - Inspect logs: ./scripts/view-logs.sh backend -n 100"
        echo "  - Rerun with coverage: ./scripts/run-tests.sh --coverage"
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
        --no-coverage)
            WITH_COVERAGE=false
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
