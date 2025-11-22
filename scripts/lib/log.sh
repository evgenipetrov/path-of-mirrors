#!/usr/bin/env bash
# Shared logging helpers for scripts
# Usage: source "$(dirname "$0")/lib/log.sh"

# Preserve caller shell options; do not set -e/-u here.

# Colors
if [ "${LOG_NO_COLOR:-false}" = "true" ]; then
  RED=""; GREEN=""; YELLOW=""; BLUE=""; BOLD=""; NC="";
else
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  BLUE='\033[0;34m'
  BOLD='\033[1m'
  NC='\033[0m'
fi

log_info() {
  echo -e "${BLUE}ℹ️  $*${NC}"
}

log_success() {
  echo -e "${GREEN}✅ $*${NC}"
}

log_error() {
  echo -e "${RED}❌ $*${NC}"
}

log_warning() {
  echo -e "${YELLOW}⚠️  $*${NC}"
}

log_step() {
  echo -e "\n${BOLD}$*${NC}"
  echo "====================================="
}
