#!/bin/bash

# Path of Mirrors - Restart Development Environment
# Convenience script to stop and restart all dev services

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "Restarting Path of Mirrors development environment..."

# Stop everything
./scripts/stop-dev.sh

# Wait a moment
sleep 2

# Start everything
./scripts/start-dev.sh
