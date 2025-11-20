#!/usr/bin/env bash

# Setup PoB headless binaries (PoE1 + PoE2) and LuaJIT bridge
# Usage: ./scripts/setup-pob-cli.sh
#
# This is a scaffold: it documents the steps and downloads releases if URLs
# are provided via env vars. Adjust versions/URLs to match your environment.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="${ROOT}/bin"
mkdir -p "$BIN_DIR"

POB_POE1_URL="${POB_POE1_URL:-}"
POB_POE2_URL="${POB_POE2_URL:-}"
LUAJIT_URL="${LUAJIT_URL:-https://luajit.org/download/LuaJIT-2.1.0-beta3.tar.gz}"

echo "➡️  Target bin dir: $BIN_DIR"
echo "ℹ️  Set POB_POE1_URL / POB_POE2_URL to download binaries automatically."

download_if_set() {
  local url="$1"
  local dest="$2"
  if [ -n "$url" ]; then
    echo "⬇️  Downloading $url"
    curl -fL "$url" -o "$dest"
    echo "   Saved to $dest"
  else
    echo "⚠️  Skip download (URL not set) for $dest"
  fi
}

# Download PoB PoE1/PoE2 if URLs provided
download_if_set "$POB_POE1_URL" "$BIN_DIR/pob-poe1.zip"
download_if_set "$POB_POE2_URL" "$BIN_DIR/pob-poe2.zip"

echo "ℹ️  If archives were downloaded, unzip them into $BIN_DIR and set:"
echo "    export POB_CLI_POE1=\"$BIN_DIR/pathofbuilding-poe1\""
echo "    export POB_CLI_POE2=\"$BIN_DIR/pathofbuilding-poe2\""

# LuaJIT scaffold
echo "ℹ️  LuaJIT URL: $LUAJIT_URL"
echo "    To build manually:"
cat <<'EOF'
    cd /tmp
    curl -fL "$LUAJIT_URL" -o luajit.tar.gz
    tar xzf luajit.tar.gz
    cd LuaJIT-2.1.0-beta3
    make && make install PREFIX=$HOME/.local
EOF

echo "✅ Scaffold complete. Install steps are documented above."
