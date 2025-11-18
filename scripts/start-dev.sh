#!/bin/bash

# Path of Mirrors - Start Development Environment
# Starts all services: PostgreSQL, Redis, Backend, and Frontend
# Usage: ./scripts/start-dev.sh [--build]
#
# Options:
#   --build    Rebuild Docker images before starting

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Parse arguments
BUILD_FLAG=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            BUILD_FLAG="--build"
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./scripts/start-dev.sh [--build]"
            exit 1
            ;;
    esac
done

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Path of Mirrors - Development Stack      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}⚠️  Shutting down services...${NC}"
    
    # Kill frontend if running
    if [ ! -z "$FRONTEND_PID" ]; then
        echo -e "${BLUE}→ Stopping frontend (PID: $FRONTEND_PID)${NC}"
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    
    # Stop Docker services
    echo -e "${BLUE}→ Stopping Docker services${NC}"
    docker compose down
    
    echo -e "${GREEN}✓ All services stopped${NC}"
    exit 0
}

# Register cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Step 1: Start Docker services
if [ -n "$BUILD_FLAG" ]; then
    echo -e "${BLUE}→ Building and starting Docker services (PostgreSQL, Redis, Backend)...${NC}"
else
    echo -e "${BLUE}→ Starting Docker services (PostgreSQL, Redis, Backend)...${NC}"
fi
docker compose up -d $BUILD_FLAG

# Wait for services to be healthy
echo -e "${BLUE}→ Waiting for services to be healthy...${NC}"
timeout=60
elapsed=0
while [ $elapsed -lt $timeout ]; do
    # Count healthy services (should be 2: postgres and redis)
    healthy_count=$(docker compose ps --format json 2>/dev/null | grep -c '"Health":"healthy"' || echo "0")
    backend_running=$(docker compose ps backend --format json 2>/dev/null | grep -c '"State":"running"' || echo "0")

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
    docker compose logs
    exit 1
fi

# Step 2: Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Frontend dependencies not found${NC}"
    echo -e "${BLUE}→ Installing frontend dependencies...${NC}"
    cd frontend
    npm install
    cd ..
    echo -e "${GREEN}✓ Dependencies installed${NC}"
fi

# Step 3: Start frontend dev server in background
echo -e "${BLUE}→ Starting frontend dev server...${NC}"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait a moment for Vite to start
sleep 3

# Step 4: Display status
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          🚀 ALL SYSTEMS OPERATIONAL        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Services running:${NC}"
echo -e "  ${GREEN}✓${NC} PostgreSQL:    http://localhost:5432"
echo -e "  ${GREEN}✓${NC} Redis:         http://localhost:6379"
echo -e "  ${GREEN}✓${NC} Backend API:   http://localhost:8000"
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

# Keep script running and show logs
docker compose logs -f &
wait $FRONTEND_PID
