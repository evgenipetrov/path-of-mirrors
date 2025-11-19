#!/bin/bash

# Path of Mirrors - Restart Services
# Usage: ./scripts/restart.sh [--dev|--prod] [--build]

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

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
            echo "Usage: ./scripts/restart.sh [--dev|--prod] [--build]"
            exit 1
            ;;
    esac
done

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${BLUE}→ Restarting Path of Mirrors (${MODE} mode)...${NC}"

# Stop services
./scripts/stop.sh --${MODE}

# Start services
if [ -n "$BUILD_FLAG" ]; then
    ./scripts/start.sh --${MODE} --build
else
    ./scripts/start.sh --${MODE}
fi
