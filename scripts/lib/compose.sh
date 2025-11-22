#!/usr/bin/env bash
# Docker Compose helpers
# Usage: source "$(dirname "$0")/lib/compose.sh"

select_compose_files() {
  local mode="${1:-dev}"
  if [ "$mode" = "prod" ]; then
    echo "-f docker-compose.yml -f docker-compose.prod.yml"
  else
    echo "-f docker-compose.yml -f docker-compose.dev.yml"
  fi
}

# docker compose wrapper that respects MODE env (default dev)
dc() {
  local mode="${MODE:-dev}"
  local files
  files=$(select_compose_files "$mode")
  docker compose $files "$@"
}
