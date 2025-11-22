#!/usr/bin/env bash
# Backend-related helpers
# Usage: source "$(dirname "$0")/lib/backend.sh"

ensure_services_up() {
  local compose_files="$1"
  if ! docker compose $compose_files ps backend | grep -q "Up" 2>/dev/null; then
    docker compose $compose_files up -d
    return 0
  fi
  return 1
}

backend_exec() {
  local compose_files="$1"
  shift
  docker compose $compose_files exec -T backend bash -c "cd /app && $*"
}
