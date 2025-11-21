#!/usr/bin/env bash

# Install headless Path of Building (PoE1 + PoE2) and LuaJIT into ./bin
# for local development and CI. Designed to be idempotent and self-contained.
#
# Usage:
#   ./scripts/install-pob-cli.sh
#   POB_POE1_VERSION=2.38.1 ./scripts/install-pob-cli.sh
#
# After install, set env (add to your shell rc):
#   export POB_CLI_POE1="$PWD/bin/pob-poe1/PathOfBuilding"
#   export POB_CLI_POE2="$PWD/bin/pob-poe2/PathOfBuilding"
#   export POB_LUAJIT="$PWD/bin/luajit/bin/luajit"
#   export POB_BRIDGE="$PWD/bin/pob_bridge.lua"
#
# Notes:
# - This script keeps dependencies inside ./bin to avoid system pollution.
# - PoE1/PoE2 URLs are Linux headless release zips from Community Fork.
# - LuaJIT is built locally; requires build-essential/make.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="$ROOT/bin"
mkdir -p "$BIN_DIR"

# Versions / URLs (can be overridden via env)
POB_POE1_VERSION="${POB_POE1_VERSION:-2.38.1}"
POB_POE2_VERSION="${POB_POE2_VERSION:-2.38.1}"
POB_BASE_URL="${POB_BASE_URL:-https://github.com/PathOfBuildingCommunity/PathOfBuilding/releases/download}"

POB_POE1_URL="${POB_POE1_URL:-$POB_BASE_URL/v$POB_POE1_VERSION/PathOfBuildingLinux.tar.gz}"
POB_POE2_URL="${POB_POE2_URL:-$POB_BASE_URL/v$POB_POE2_VERSION/PathOfBuildingPoE2Linux.tar.gz}"

LUAJIT_VERSION="${LUAJIT_VERSION:-2.1.0-beta3}"
LUAJIT_URL="${LUAJIT_URL:-https://luajit.org/download/LuaJIT-$LUAJIT_VERSION.tar.gz}"

command -v curl >/dev/null || { echo "curl required"; exit 1; }
command -v tar >/dev/null || { echo "tar required"; exit 1; }

fetch_and_unpack() {
  local url="$1"
  local dest_dir="$2"
  local label="$3"
  if [ -d "$dest_dir" ]; then
    echo "✓ $label already present: $dest_dir"
    return
  fi
  mkdir -p "$dest_dir"
  tmp=$(mktemp)
  echo "⬇️  Downloading $label ..."
  curl -fL "$url" -o "$tmp"
  echo "📦 Unpacking $label ..."
  tar -xzf "$tmp" -C "$dest_dir" --strip-components=1
  rm "$tmp"
  echo "✓ $label ready"
}

build_luajit() {
  local build_dir="$BIN_DIR/luajit-src"
  local prefix="$BIN_DIR/luajit"

  if [ -x "$prefix/bin/luajit" ]; then
    echo "✓ LuaJIT already built at $prefix/bin/luajit"
    return
  fi

  rm -rf "$build_dir"
  mkdir -p "$build_dir"
  tmp=$(mktemp)
  echo "⬇️  Downloading LuaJIT ..."
  curl -fL "$LUAJIT_URL" -o "$tmp"
  tar -xzf "$tmp" -C "$build_dir" --strip-components=1
  rm "$tmp"

  echo "🔧 Building LuaJIT ..."
  (cd "$build_dir" && make PREFIX="$prefix" && make install PREFIX="$prefix")
  echo "✓ LuaJIT built at $prefix/bin/luajit"
}

# Fetch PoB binaries
fetch_and_unpack "$POB_POE1_URL" "$BIN_DIR/pob-poe1" "PoB PoE1"
fetch_and_unpack "$POB_POE2_URL" "$BIN_DIR/pob-poe2" "PoB PoE2"

# Build LuaJIT
build_luajit

# Drop a minimal bridge stub (replace later with full bridge logic)
cat > "$BIN_DIR/pob_bridge.lua" <<'EOF'
-- Minimal PoB bridge stub: echoes fixed JSON.
local json = '{ "ok": true, "message": "stub bridge", "stats": {} }'
io.write(json)
EOF
chmod +x "$BIN_DIR/pob_bridge.lua"

echo ""
echo "✅ Install complete."
echo "Set env vars (example):"
echo "  export POB_CLI_POE1=\"$BIN_DIR/pob-poe1/PathOfBuilding\""
echo "  export POB_CLI_POE2=\"$BIN_DIR/pob-poe2/PathOfBuilding\""
echo "  export POB_LUAJIT=\"$BIN_DIR/luajit/bin/luajit\""
echo "  export POB_BRIDGE=\"$BIN_DIR/pob_bridge.lua\""
echo ""
echo "Smoke test (bridge stub):"
echo "  POB_LUAJIT=\"$BIN_DIR/luajit/bin/luajit\" POB_BRIDGE=\"$BIN_DIR/pob_bridge.lua\" \\"
echo "    LUA_PATH=\"$BIN_DIR/?.lua;;\" \\"
echo "    $BIN_DIR/luajit/bin/luajit $BIN_DIR/pob_bridge.lua <<< '<PathOfBuilding></PathOfBuilding>'"
