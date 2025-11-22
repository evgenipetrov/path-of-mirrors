#!/usr/bin/env bash

# Script: check-locks.sh
# Description: Enforce dependency lock file consistency
# Usage: ./scripts/check-locks.sh [OPTIONS]
#
# Options:
#   --help        Show this help message
#   --backend     Check backend (uv.lock) only
#   --frontend    Check frontend (package-lock.json) only
#
# This script ensures dependency lock files are consistent with their
# package manifests and haven't drifted.

set -e
set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/log.sh"
source "$SCRIPT_DIR/lib/compose.sh"

MODE="${MODE:-dev}"
COMPOSE_FILES="$(select_compose_files "$MODE")"

# Configuration
CHECK_BACKEND=true
CHECK_FRONTEND=true

# Helper functions
show_help() {
    head -n 13 "$0" | tail -n 11 | sed 's/^# //'
    exit 0
}

# Main check function
main() {
    local exit_code=0
    local started_services=false

    log_step "🔍 Checking Dependency Lock File Consistency"

    # Change to project root
    cd "$(dirname "$0")/.."

    # Backend lock check
    if [ "$CHECK_BACKEND" = true ]; then
        log_step "Backend: Checking uv.lock consistency"

        # Verify lock file exists
        if [ ! -f "backend/uv.lock" ]; then
            log_error "Backend lock file not found: backend/uv.lock"
            log_info "Run: cd backend && uv sync"
            exit_code=1
        else
            # Start backend if not running
            if ! docker compose $COMPOSE_FILES ps backend | grep -q "Up" 2>/dev/null; then
                log_info "Starting backend container..."
                docker compose $COMPOSE_FILES up -d backend
                started_services=true
                sleep 3
            fi

            # Check if lock file is in sync with pyproject.toml
            log_info "Verifying uv.lock is in sync with pyproject.toml..."
            # uv sync --locked exits non-zero if lock is stale
            # We temporarily disable exit-on-error to capture the exit code
            set +e
            dc exec -T backend uv sync --locked > /dev/null 2>&1
            uv_exit_code=$?
            set -e

            if [ $uv_exit_code -ne 0 ]; then
                log_error "Backend lock file is out of sync with pyproject.toml"
                echo ""
                log_info "To fix this issue:"
                echo "  1. Update lock: cd backend && uv sync"
                echo "  2. Commit lock:  git add backend/uv.lock"
                echo ""
                exit_code=1
            else
                log_success "Backend lock file is consistent"
            fi
        fi
    fi

    # Frontend lock check
    if [ "$CHECK_FRONTEND" = true ]; then
        log_step "Frontend: Checking package-lock.json consistency"

        # Verify lock file exists
        if [ ! -f "frontend/package-lock.json" ]; then
            log_error "Frontend lock file not found: frontend/package-lock.json"
            log_info "Run: cd frontend && npm install"
            exit_code=1
        else
            # Check if lock file is in sync with package.json
            log_info "Verifying package-lock.json is in sync with package.json..."
            cd frontend

            # npm ci --dry-run will fail if lock is out of sync
            if ! npm ci --dry-run > /dev/null 2>&1; then
                log_error "Frontend lock file is out of sync with package.json"
                echo ""
                log_info "To fix this issue:"
                echo "  1. Update lock: cd frontend && npm install"
                echo "  2. Commit lock:  git add frontend/package-lock.json"
                echo ""
                exit_code=1
            else
                log_success "Frontend lock file is consistent"
            fi

            cd ..
        fi
    fi

    # Cleanup - stop services if we started them
    if [ "$started_services" = true ]; then
        log_step "🛑 Stopping services..."
        docker compose $COMPOSE_FILES down
        log_success "Services stopped"
    fi

    # Summary
    if [ $exit_code -eq 0 ]; then
        log_step "Summary"
        log_success "All dependency lock files are consistent"
        exit 0
    else
        log_step "Summary"
        log_error "Dependency lock file inconsistencies detected"
        echo ""
        log_info "Lock files must stay in sync with package manifests."
        log_info "After fixing, run: ./scripts/check-locks.sh to verify"
        exit 1
    fi
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            ;;
        --backend)
            CHECK_FRONTEND=false
            shift
            ;;
        --frontend)
            CHECK_BACKEND=false
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            ;;
    esac
done

main
