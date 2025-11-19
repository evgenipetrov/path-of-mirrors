#!/bin/bash

# Path of Mirrors - Build Docker Images
# Usage: ./scripts/build.sh [--dev|--prod]

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
            echo "Usage: ./scripts/build.sh [--dev|--prod]"
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

echo -e "${BLUE}→ Building Docker images for ${MODE} mode...${NC}"

docker compose $COMPOSE_FILES build

echo -e "${GREEN}✓ Build complete${NC}"
