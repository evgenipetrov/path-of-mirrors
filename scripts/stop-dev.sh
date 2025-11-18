#!/bin/bash

# Path of Mirrors - Stop All Services Script

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}→ Stopping all Path of Mirrors services...${NC}"

# Stop Docker services
docker compose down

# Kill any remaining frontend processes
pkill -f "vite" 2>/dev/null || true
pkill -f "npm run dev" 2>/dev/null || true

echo -e "${GREEN}✓ All services stopped${NC}"
