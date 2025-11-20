#!/usr/bin/env bash

# Regenerate frontend API client/hooks from the backend OpenAPI spec
# Usage: ./scripts/generate-api.sh [--config path/to/orval.config.ts]

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT/frontend"

CONFIG="orval.config.ts"

if [[ $# -ge 2 && $1 == "--config" ]]; then
  CONFIG="$2"
  shift 2
fi

if [[ ! -f "$CONFIG" ]]; then
  echo "Config file not found: $CONFIG" >&2
  echo "Create frontend/orval.config.ts (or pass --config) before regenerating." >&2
  exit 1
fi

echo "Using config: $CONFIG"

npx orval --config "$CONFIG" "$@"

echo "API client generation complete."

echo ""
echo "Next steps:"
echo "  - Run lint:     ./scripts/check-code.sh --frontend"
echo "  - Run tests:    ./scripts/run-tests.sh --frontend"
echo "  - Start dev:    ./scripts/start-services.sh --dev"
