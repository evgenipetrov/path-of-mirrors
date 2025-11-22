#!/bin/bash

# Path of Mirrors - Start Services
# Starts all services: PostgreSQL, Redis, Backend, and optionally Frontend
# Usage: ./scripts/start-services.sh [OPTIONS]
#
# Options:
#   --dev      Start in development mode (default)
#   --prod     Start in production mode
#   --build    Rebuild Docker images before starting

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

source "$SCRIPT_DIR/lib/log.sh"
source "$SCRIPT_DIR/lib/compose.sh"
source "$SCRIPT_DIR/lib/frontend.sh"

# Parse arguments
MODE="dev"
BUILD_FLAG=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --dev)
            MODE="dev"
            shift
            ;;
        --prod)
            MODE="prod"
            shift
            ;;
        --build)
            BUILD_FLAG="--build"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./scripts/start-services.sh [--dev|--prod] [--build]"
            exit 1
            ;;
    esac
done

COMPOSE_FILES="$(select_compose_files "$MODE")"

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Path of Mirrors - ${MODE^^} Mode           ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Development mode - include frontend
if [ "$MODE" = "dev" ]; then
    # Cleanup function for dev mode
    cleanup() {
        echo -e "\n${YELLOW}⚠️  Shutting down services...${NC}"

        # Kill frontend if running
        if [ ! -z "$FRONTEND_PID" ]; then
            echo -e "${BLUE}→ Stopping frontend (PID: $FRONTEND_PID)${NC}"
            kill $FRONTEND_PID 2>/dev/null || true
        fi

        # Stop Docker services
        echo -e "${BLUE}→ Stopping Docker services${NC}"
        docker compose $COMPOSE_FILES down

        echo -e "${GREEN}✓ All services stopped${NC}"
        exit 0
    }
    trap cleanup SIGINT SIGTERM EXIT
fi

# Start Docker services
if [ -n "$BUILD_FLAG" ]; then
    echo -e "${BLUE}→ Building and starting Docker services...${NC}"
    docker compose $COMPOSE_FILES up -d $BUILD_FLAG
else
    echo -e "${BLUE}→ Starting Docker services...${NC}"
    docker compose $COMPOSE_FILES up -d
fi

# Wait for services to be healthy
echo -e "${BLUE}→ Waiting for services to be healthy...${NC}"
timeout=60
elapsed=0
while [ $elapsed -lt $timeout ]; do
    healthy_count=$(docker compose $COMPOSE_FILES ps --format json 2>/dev/null | grep -c '"Health":"healthy"' || echo "0")
    backend_running=$(docker compose $COMPOSE_FILES ps backend --format json 2>/dev/null | grep -c '"State":"running"' || echo "0")

    if [ "$healthy_count" -ge 2 ] && [ "$backend_running" -ge 1 ]; then
        echo -e "\n${GREEN}✓ Docker services are healthy${NC}"
        break
    fi
    sleep 2
    elapsed=$((elapsed + 2))
    echo -n "."
done

if [ $elapsed -ge $timeout ]; then
    echo -e "\n${RED}✗ Services failed to become healthy${NC}"
    docker compose $COMPOSE_FILES logs
    exit 1
fi

# Development mode - start frontend
if [ "$MODE" = "dev" ]; then
    # Check if frontend dependencies are installed
    if ensure_frontend_deps; then
        echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
    else
        echo -e "${BLUE}→ Frontend dependencies already present${NC}"
    fi

    # Start frontend dev server in background
    echo -e "${BLUE}→ Starting frontend dev server...${NC}"
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    sleep 3
fi

# Display status
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          🚀 ALL SYSTEMS OPERATIONAL        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Services running in ${MODE^^} mode:${NC}"
echo -e "  ${GREEN}✓${NC} PostgreSQL:    http://localhost:5432"
echo -e "  ${GREEN}✓${NC} Redis:         http://localhost:6379"
echo -e "  ${GREEN}✓${NC} Backend API:   http://localhost:8000"

if [ "$MODE" = "dev" ]; then
    echo -e "  ${GREEN}✓${NC} Frontend App:  http://localhost:5173"
    echo ""
    echo -e "${BLUE}Quick links:${NC}"
    echo -e "  ${YELLOW}→${NC} Frontend:      http://localhost:5173"
    echo -e "  ${YELLOW}→${NC} Notes Page:    http://localhost:5173/notes"
    echo -e "  ${YELLOW}→${NC} API Docs:      http://localhost:8000/docs"
    echo -e "  ${YELLOW}→${NC} Health Check:  http://localhost:8000/health"
    echo ""
    echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
    echo ""

    echo -e "${BLUE}Next steps:${NC}"
    echo -e "  - Run tests:     ${YELLOW}./scripts/run-tests.sh${NC}"
    echo -e "  - Lint & types:  ${YELLOW}./scripts/check-code.sh${NC}"
    echo -e "  - Stop services: ${YELLOW}./scripts/stop-services.sh --dev${NC}"
    echo ""

    # Keep script running and show logs
    docker compose $COMPOSE_FILES logs -f &
    wait $FRONTEND_PID
else
    echo ""
    echo -e "${BLUE}Quick links:${NC}"
    echo -e "  ${YELLOW}→${NC} API Docs:      http://localhost:8000/docs"
    echo -e "  ${YELLOW}→${NC} Health Check:  http://localhost:8000/health"
    echo ""
    echo -e "${GREEN}✓ Production services started${NC}"
    echo -e "${BLUE}Next steps:${NC}"
    echo -e "  - View logs:     ${YELLOW}docker compose $COMPOSE_FILES logs -f${NC}"
    echo -e "  - Restart:       ${YELLOW}./scripts/restart-services.sh --prod${NC}"
    echo -e "  - Stop:          ${YELLOW}./scripts/stop-services.sh --prod${NC}"
fi
