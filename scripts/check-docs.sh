#!/usr/bin/env bash

# Script: check-docs.sh
# Description: Enforce route-to-documentation consistency
# Usage: ./scripts/check-docs.sh [OPTIONS]
#
# Options:
#   --help        Show this help message
#
# This script ensures all active API routes are documented in docs/API_ROUTES.md
# and that no documented routes are missing from the actual backend code.

set -e
set -u
set -o pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/log.sh"
source "$SCRIPT_DIR/lib/compose.sh"

MODE="${MODE:-dev}"
COMPOSE_FILES="$(select_compose_files "$MODE")"

# Configuration
DOCS_FILE="docs/API_ROUTES.md"

# Helper functions
show_help() {
    head -n 11 "$0" | tail -n 9 | sed 's/^# //'
    exit 0
}

# Extract routes from OpenAPI spec
extract_routes_from_openapi() {
    local openapi_file="$1"
    # Extract all paths and their methods from OpenAPI spec
    # Output format: "METHOD /path"
    python3 -c "
import json
import sys

with open('$openapi_file') as f:
    spec = json.load(f)

routes = []
for path, methods in spec.get('paths', {}).items():
    for method in methods.keys():
        if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
            routes.append(f'{method.upper()} {path}')

for route in sorted(routes):
    print(route)
"
}

# Extract routes from docs/API_ROUTES.md
extract_routes_from_docs() {
    local docs_file="$1"
    # Extract markdown code blocks that look like route definitions
    # Looking for patterns like: GET /api/v1/...
    grep -E '^(GET|POST|PUT|DELETE|PATCH) /' "$docs_file" | sort | uniq || true
}

# Main check function
main() {
    local exit_code=0
    local started_services=false

    log_step "🔍 Checking Route-to-Documentation Consistency"

    # Change to project root
    cd "$(dirname "$0")/.."

    # Verify docs file exists
    if [ ! -f "$DOCS_FILE" ]; then
        log_error "Documentation file not found: $DOCS_FILE"
        exit 1
    fi

    # Verify OpenAPI schema exists
    if [ ! -f "backend/openapi.json" ]; then
        log_error "OpenAPI schema not found: backend/openapi.json"
        log_info "Run: ./scripts/check-schema.sh --update to generate it"
        exit 1
    fi

    # Start backend if not running (to ensure we have the latest OpenAPI spec)
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

    # Fetch current OpenAPI spec
    log_info "Fetching current OpenAPI spec..."
    TEMP_SCHEMA=$(mktemp)
    if ! curl -sf http://localhost:8000/openapi.json -o "$TEMP_SCHEMA"; then
        log_error "Failed to fetch OpenAPI spec from backend"
        rm -f "$TEMP_SCHEMA"
        if [ "$started_services" = true ]; then
            docker compose $COMPOSE_FILES down
        fi
        exit 1
    fi

    # Extract routes
    log_info "Extracting routes from OpenAPI spec..."
    TEMP_OPENAPI_ROUTES=$(mktemp)
    extract_routes_from_openapi "$TEMP_SCHEMA" > "$TEMP_OPENAPI_ROUTES"

    log_info "Extracting routes from documentation..."
    TEMP_DOCS_ROUTES=$(mktemp)
    extract_routes_from_docs "$DOCS_FILE" > "$TEMP_DOCS_ROUTES"

    # Compare routes
    log_step "Comparing routes..."

    # Find routes in code but not in docs
    TEMP_MISSING_DOCS=$(mktemp)
    comm -23 "$TEMP_OPENAPI_ROUTES" "$TEMP_DOCS_ROUTES" > "$TEMP_MISSING_DOCS"

    # Find routes in docs but not in code
    TEMP_MISSING_CODE=$(mktemp)
    comm -13 "$TEMP_OPENAPI_ROUTES" "$TEMP_DOCS_ROUTES" > "$TEMP_MISSING_CODE"

    # Report findings
    if [ ! -s "$TEMP_MISSING_DOCS" ] && [ ! -s "$TEMP_MISSING_CODE" ]; then
        log_success "All routes are properly documented"
        exit_code=0
    else
        log_error "Route-to-documentation inconsistencies found!"
        echo ""

        if [ -s "$TEMP_MISSING_DOCS" ]; then
            log_warning "Routes in code but NOT documented in $DOCS_FILE:"
            while IFS= read -r route; do
                echo "  ❌ $route"
            done < "$TEMP_MISSING_DOCS"
            echo ""
            exit_code=1
        fi

        if [ -s "$TEMP_MISSING_CODE" ]; then
            log_warning "Routes documented but NOT in code:"
            while IFS= read -r route; do
                echo "  ❌ $route"
            done < "$TEMP_MISSING_CODE"
            echo ""
            exit_code=1
        fi

        log_info "To fix these issues:"
        echo "  1. Add missing routes to $DOCS_FILE"
        echo "  2. Remove documented routes that no longer exist"
        echo "  3. Verify route definitions match OpenAPI spec"
        echo ""
        log_info "Tip: Check the OpenAPI spec at http://localhost:8000/docs"
    fi

    # Cleanup
    rm -f "$TEMP_SCHEMA" "$TEMP_OPENAPI_ROUTES" "$TEMP_DOCS_ROUTES" "$TEMP_MISSING_DOCS" "$TEMP_MISSING_CODE"

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
        *)
            log_error "Unknown option: $1"
            show_help
            ;;
    esac
done

main
