#!/bin/bash
# Test runner script for Path of Mirrors backend

set -e

# Change to backend directory
cd "$(dirname "$0")/.."

# Set PYTHONPATH to src directory
export PYTHONPATH="$(pwd)/src:$PYTHONPATH"

# Run pytest with arguments
uv run pytest "$@"
