#!/usr/bin/env bash
# Help text extractor
# Usage: print_help_from_header "$0" start_line line_count

print_help_from_header() {
  local file="$1"
  local start="${2:-1}"
  local count="${3:-0}"

  if [ "$count" -eq 0 ]; then
    # default: consume initial comment block
    sed -n '/^#/!q; /^#/p' "$file" | sed 's/^# \\{0,1\\}//'
  else
    head -n "$((start + count - 1))" "$file" | tail -n "$count" | sed 's/^# \\{0,1\\}//'
  fi
}
