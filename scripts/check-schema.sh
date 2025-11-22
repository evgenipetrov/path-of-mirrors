#!/usr/bin/env bash

# Script: check-schema.sh
# Description: Enforce OpenAPI schema freshness - fails if generated spec differs from committed spec
# Usage: ./scripts/check-schema.sh [OPTIONS]
#
# Options:
#   --help        Show this help message
#   --update      Update the committed schema file (use with caution)
#
# This script ensures the backend/openapi.json file is always in sync with the FastAPI code.
# It generates the OpenAPI spec in-memory and compares it with the committed version.

set -e
set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/log.sh"
source "$SCRIPT_DIR/lib/compose.sh"

MODE="${MODE:-dev}"
COMPOSE_FILES="$(select_compose_files "$MODE")"

# Configuration
UPDATE_SCHEMA=false
SCHEMA_FILE="backend/openapi.json"

# Helper functions
show_help() {
    head -n 13 "$0" | tail -n 11 | sed 's/^# //'
    exit 0
}

# Main check function
main() {
    local exit_code=0
    local started_services=false

    log_step "🔍 Checking OpenAPI Schema Freshness"

    # Change to project root
    cd "$(dirname "$0")/.."

    # Verify schema file exists
    if [ ! -f "$SCHEMA_FILE" ]; then
        log_error "OpenAPI schema file not found: $SCHEMA_FILE"
        log_info "Run: ./scripts/generate-api.sh to create it"
        exit 1
    fi

    # Start backend if not running
    if ! docker compose $COMPOSE_FILES ps backend | grep -q "Up" 2>/dev/null; then
        log_step "🐳 Starting backend container..."
        docker compose $COMPOSE_FILES up -d backend
        started_services=true

        # Wait for backend to be ready
        log_info "Waiting for backend to be ready..."
        max_attempts=30
        attempt=0
        while [ $attempt -lt $max_attempts ]; do
            if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
                log_success "Backend ready"
                break
            fi
            attempt=$((attempt + 1))
            sleep 1
        done

        if [ $attempt -eq $max_attempts ]; then
            log_error "Backend failed to become ready within ${max_attempts}s"
            docker compose $COMPOSE_FILES down
            exit 1
        fi
    fi

    # Generate current OpenAPI spec from running backend
    log_info "Fetching current OpenAPI spec from backend..."
    TEMP_SCHEMA=$(mktemp)
    if ! curl -sf http://localhost:8000/openapi.json -o "$TEMP_SCHEMA"; then
        log_error "Failed to fetch OpenAPI spec from backend"
        rm -f "$TEMP_SCHEMA"
        if [ "$started_services" = true ]; then
            docker compose $COMPOSE_FILES down
        fi
        exit 1
    fi

    # Pretty-print both schemas for comparison (normalize formatting)
    TEMP_CURRENT=$(mktemp)
    TEMP_COMMITTED=$(mktemp)

    python3 -m json.tool "$TEMP_SCHEMA" > "$TEMP_CURRENT" 2>/dev/null || {
        log_error "Failed to parse generated OpenAPI schema"
        rm -f "$TEMP_SCHEMA" "$TEMP_CURRENT" "$TEMP_COMMITTED"
        if [ "$started_services" = true ]; then
            docker compose $COMPOSE_FILES down
        fi
        exit 1
    }

    python3 -m json.tool "$SCHEMA_FILE" > "$TEMP_COMMITTED" 2>/dev/null || {
        log_error "Failed to parse committed OpenAPI schema"
        rm -f "$TEMP_SCHEMA" "$TEMP_CURRENT" "$TEMP_COMMITTED"
        if [ "$started_services" = true ]; then
            docker compose $COMPOSE_FILES down
        fi
        exit 1
    }

    # Compare schemas
    if diff -q "$TEMP_CURRENT" "$TEMP_COMMITTED" > /dev/null 2>&1; then
        log_success "OpenAPI schema is up to date"
        exit_code=0
    else
        log_error "OpenAPI schema is out of sync!"
        echo ""
        log_info "The committed schema (backend/openapi.json) differs from the current backend code."
        echo ""

        if [ "$UPDATE_SCHEMA" = true ]; then
            log_warning "Updating committed schema file..."
            cp "$TEMP_SCHEMA" "$SCHEMA_FILE"
            log_success "Schema file updated: $SCHEMA_FILE"
            log_info "Don't forget to commit this change!"
            exit_code=0
        else
            log_info "Differences:"
            diff -u "$TEMP_COMMITTED" "$TEMP_CURRENT" || true
            echo ""
            log_info "To fix this issue:"
            echo "  1. Update schema:   ./scripts/check-schema.sh --update"
            echo "  2. Regenerate API:  ./scripts/generate-api.sh"
            echo "  3. Commit changes:  git add backend/openapi.json frontend/src/hooks/api/"
            echo ""
            log_info "Or to update in one command:"
            echo "  ./scripts/check-schema.sh --update && ./scripts/generate-api.sh"
            exit_code=1
        fi
    fi

    # Cleanup
    rm -f "$TEMP_SCHEMA" "$TEMP_CURRENT" "$TEMP_COMMITTED"

    if [ "$started_services" = true ]; then
        log_step "🛑 Stopping services..."
        docker compose $COMPOSE_FILES down
        log_success "Services stopped"
    fi

    exit $exit_code
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --help)
            show_help
            ;;
        --update)
            UPDATE_SCHEMA=true
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            ;;
    esac
done

main
