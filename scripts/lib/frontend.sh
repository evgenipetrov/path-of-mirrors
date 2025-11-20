#!/usr/bin/env bash
# Frontend helpers
# Usage: source "$(dirname "$0")/lib/frontend.sh"

ensure_frontend_deps() {
  if [ ! -d "frontend/node_modules" ]; then
    (cd frontend && npm install)
    return 0
  fi
  return 1
}
