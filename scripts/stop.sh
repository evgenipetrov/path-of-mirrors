#!/bin/bash

# Path of Mirrors - Stop Services
# Usage: ./scripts/stop.sh [--dev|--prod]

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# Parse arguments
MODE="dev"
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
        *)
            echo "Unknown option: $1"
            echo "Usage: ./scripts/stop.sh [--dev|--prod]"
            exit 1
            ;;
    esac
done

# Set compose files based on mode
if [ "$MODE" = "prod" ]; then
    COMPOSE_FILES="-f docker-compose.yml -f docker-compose.prod.yml"
else
    COMPOSE_FILES="-f docker-compose.yml -f docker-compose.dev.yml"
fi

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}→ Stopping Path of Mirrors services (${MODE} mode)...${NC}"

# Stop Docker services
docker compose $COMPOSE_FILES down

# Kill any remaining frontend processes (dev mode)
if [ "$MODE" = "dev" ]; then
    pkill -f "vite" 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true
fi

echo -e "${GREEN}✓ All services stopped${NC}"
