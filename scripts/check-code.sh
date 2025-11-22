#!/usr/bin/env bash

# Script: check-code.sh
# Description: Run all code quality checks (schema, docs, locks, linting, type checking)
# Usage: ./scripts/check-code.sh [OPTIONS]
#
# Options:
#   --help        Show this help message
#   --fix         Auto-fix issues where possible
#   --backend     Run backend checks only
#   --frontend    Run frontend checks only
#
# This script runs comprehensive code quality checks including:
#   - OpenAPI schema freshness
#   - Route documentation consistency
#   - Dependency lock file consistency
#   - Code linting (ruff, eslint)
#   - Code formatting (ruff format, prettier)
#   - Type checking (mypy, tsc)

set -e
set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/log.sh"
source "$SCRIPT_DIR/lib/compose.sh"
source "$SCRIPT_DIR/lib/backend.sh"

MODE="${MODE:-dev}"
COMPOSE_FILES="$(select_compose_files "$MODE")"

# Configuration
AUTO_FIX=false
RUN_BACKEND=true
RUN_FRONTEND=true

# Helper functions
show_help() {
    head -n 19 "$0" | tail -n 17 | sed 's/^# //'
    exit 0
}

# Main lint function
main() {
    local total_issues=0
    local total_errors=0
    local exit_code=0
    local started_services=false

    # Pre-flight checks (schema, docs, locks)
    log_step "🔍 Running Pre-flight Checks"

    # Check OpenAPI schema freshness
    log_step "Checking OpenAPI schema freshness..."
    if "$SCRIPT_DIR/check-schema.sh"; then
        log_success "OpenAPI schema is up to date"
    else
        log_error "OpenAPI schema check failed"
        total_errors=$((total_errors + 1))
        exit_code=1
    fi

    # Check route documentation consistency
    log_step "Checking route documentation..."
    if "$SCRIPT_DIR/check-docs.sh"; then
        log_success "Route documentation is consistent"
    else
        log_error "Route documentation check failed"
        total_errors=$((total_errors + 1))
        exit_code=1
    fi

    # Check dependency lock files
    log_step "Checking dependency locks..."
    if "$SCRIPT_DIR/check-locks.sh"; then
        log_success "Dependency locks are consistent"
    else
        log_error "Dependency lock check failed"
        total_errors=$((total_errors + 1))
        exit_code=1
    fi

    # Backend linting
    if [ "$RUN_BACKEND" = true ]; then
        # Start backend if not running
        if ! docker compose $COMPOSE_FILES ps backend | grep -q "Up" 2>/dev/null; then
            log_step "🐳 Starting backend container for linting..."
            docker compose $COMPOSE_FILES up -d backend
            started_services=true

            # Wait for backend to be ready
            log_info "Waiting for backend to be ready..."
            sleep 5
            log_success "Backend ready"
        fi

        log_step "🔍 Running Backend Linters"

        # Ruff check
        log_step "Backend: ruff check"
        if [ "$AUTO_FIX" = true ]; then
            if dc exec -T backend uv run ruff check --fix src/; then
                log_success "No issues found (auto-fixed where possible)"
            else
                log_warning "Some issues could not be auto-fixed"
                total_issues=$((total_issues + 1))
            fi
        else
            if dc exec -T backend uv run ruff check src/; then
                log_success "No issues found"
            else
                log_error "Linting issues found"
                total_errors=$((total_errors + 1))
                exit_code=1
            fi
        fi

        # Ruff format
        log_step "Backend: ruff format"
        if [ "$AUTO_FIX" = true ]; then
            dc exec -T backend uv run ruff format src/
            log_success "Code formatted"
        else
            if dc exec -T backend uv run ruff format --check src/; then
                log_success "Code is properly formatted"
            else
                log_error "Code formatting issues found"
                log_info "Run with --fix to auto-format"
                total_errors=$((total_errors + 1))
                exit_code=1
            fi
        fi

        # MyPy type checking
        log_step "Backend: mypy type checking"
        if dc exec -T backend bash -c "cd src && uv run mypy . --ignore-missing-imports"; then
            log_success "Type checking passed"
        else
            log_error "Type errors found"
            total_errors=$((total_errors + 1))
            exit_code=1
        fi
    fi

    # Frontend linting
    if [ "$RUN_FRONTEND" = true ]; then
        if [ ! -d "frontend/node_modules" ]; then
            log_error "Frontend dependencies not installed"
            log_info "Run: cd frontend && npm install"
            exit 1
        fi

        # ESLint
        log_step "Frontend: eslint"
        cd frontend
        if [ "$AUTO_FIX" = true ]; then
            if npm run lint -- --fix; then
                log_success "No issues found (auto-fixed where possible)"
            else
                log_warning "Some issues could not be auto-fixed"
                total_issues=$((total_issues + 1))
            fi
        else
            if npm run lint; then
                log_success "No issues found"
            else
                log_error "Linting issues found"
                log_info "Run with --fix to auto-fix"
                total_errors=$((total_errors + 1))
                exit_code=1
            fi
        fi

        # Prettier formatting
        log_step "Frontend: prettier formatting"
        if [ "$AUTO_FIX" = true ]; then
            npx prettier --write "src/**/*.{ts,tsx,js,jsx,json,css,md}"
            log_success "Code formatted"
        else
            if npx prettier --check "src/**/*.{ts,tsx,js,jsx,json,css,md}"; then
                log_success "Code is properly formatted"
            else
                log_error "Code formatting issues found"
                log_info "Run with --fix to auto-format"
                total_errors=$((total_errors + 1))
                exit_code=1
            fi
        fi

        # TypeScript type checking
        log_step "Frontend: tsc type checking"
        if npx tsc --noEmit; then
            log_success "Type checking passed"
        else
            log_error "Type errors found"
            total_errors=$((total_errors + 1))
            exit_code=1
        fi
        cd ..
    fi

    # Cleanup - stop services if we started them
    if [ "$started_services" = true ]; then
        log_step "🛑 Stopping services..."
        docker compose $COMPOSE_FILES down
        log_success "Services stopped"
    fi

    # Summary
    log_step "Linting Summary"
    if [ $exit_code -eq 0 ]; then
        log_success "All linting checks passed!"
        if [ $total_issues -gt 0 ]; then
            echo ""
            log_info "Auto-fixed $total_issues issue(s)"
        fi
        echo ""
        log_info "Next steps:"
        echo "  - Run tests:          ./scripts/run-tests.sh"
        echo "  - Backend only lint:  ./scripts/check-code.sh --backend"
        echo "  - Frontend only lint: ./scripts/check-code.sh --frontend"
        exit 0
    else
        log_error "Linting failed with $total_errors error(s)"
        echo ""
        if [ "$AUTO_FIX" = false ]; then
            log_info "Run with --fix to automatically fix some issues"
        fi
        echo ""
        log_info "Next steps:"
        echo "  - Auto-fix:           ./scripts/check-code.sh --fix"
        echo "  - Narrow scope:       ./scripts/check-code.sh --backend|--frontend"
        exit 1
    fi
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            ;;
        --fix)
            AUTO_FIX=true
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
