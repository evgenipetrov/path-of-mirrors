#!/bin/bash

# Path of Mirrors - Restart All Services Script

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Restarting Path of Mirrors..."

# Stop everything
./scripts/stop.sh

# Wait a moment
sleep 2

# Start everything
./scripts/dev.sh
