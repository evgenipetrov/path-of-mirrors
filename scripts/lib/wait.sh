#!/usr/bin/env bash
# Service waiting utilities
# Usage: source "$(dirname "$0")/lib/wait.sh"

wait_for_pg() {
  local compose_files="$1"
  local timeout="${2:-30}"
  local attempt=0

  while [ $attempt -lt $timeout ]; do
    if docker compose $compose_files exec -T postgres pg_isready -U postgres >/dev/null 2>&1; then
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 1
  done
  return 1
}

wait_for_redis() {
  local compose_files="$1"
  local timeout="${2:-30}"
  local attempt=0

  while [ $attempt -lt $timeout ]; do
    if docker compose $compose_files exec -T redis redis-cli ping >/dev/null 2>&1; then
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 1
  done
  return 1
}

wait_for_url() {
  local url="$1"
  local timeout="${2:-30}"
  local attempt=0

  while [ $attempt -lt $timeout ]; do
    if curl -sf "$url" >/dev/null 2>&1; then
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 1
  done
  return 1
}
