#!/usr/bin/env bash

# Script: check-code.sh
# Description: Run all linters and formatters
# Usage: ./scripts/check-code.sh [OPTIONS]
#
# Options:
#   --help        Show this help message
#   --fix         Auto-fix issues where possible
#   --backend     Run backend linting only
#   --frontend    Run frontend linting only

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
AUTO_FIX=false
RUN_BACKEND=true
RUN_FRONTEND=true

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

# Main lint function
main() {
    local total_issues=0
    local total_errors=0
    local exit_code=0
    local started_services=false

    # Backend linting
    if [ "$RUN_BACKEND" = true ]; then
        # Start backend if not running
        if ! docker compose ps backend | grep -q "Up" 2>/dev/null; then
            log_step "🐳 Starting backend container for linting..."
            docker compose up -d backend
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
            if docker compose exec -T backend uv run ruff check --fix src/; then
                log_success "No issues found (auto-fixed where possible)"
            else
                log_warning "Some issues could not be auto-fixed"
                total_issues=$((total_issues + 1))
            fi
        else
            if docker compose exec -T backend uv run ruff check src/; then
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
            docker compose exec -T backend uv run ruff format src/
            log_success "Code formatted"
        else
            if docker compose exec -T backend uv run ruff format --check src/; then
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
        if docker compose exec -T backend bash -c "cd src && uv run mypy . --ignore-missing-imports"; then
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
        docker compose down
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
        exit 0
    else
        log_error "Linting failed with $total_errors error(s)"
        echo ""
        if [ "$AUTO_FIX" = false ]; then
            log_info "Run with --fix to automatically fix some issues"
        fi
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
