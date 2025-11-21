#!/usr/bin/env bash

# Install Path of Building Community (PoE1 + PoE2 portable) and LuaJIT into ./bin
# for local development and CI. Designed to be idempotent and self-contained.
#
# Usage:
#   ./scripts/install-pob-cli.sh                      # latest PoB1/PoB2
#   ./scripts/install-pob-cli.sh --force              # re-download PoB + rebuild LuaJIT
#   POB_POE1_VERSION=v2.54.0 ./scripts/install-pob-cli.sh   # pin PoB1 version tag
#
# After install, set env (add to your shell rc):
#   export POB_CLI_POE1="$PWD/bin/pob-poe1/Path of Building.exe"
#   export POB_CLI_POE2="$PWD/bin/pob-poe2/Path of Building-PoE2.exe"
#   export POB_LUAJIT="$PWD/bin/luajit/bin/luajit"
#   export POB_BRIDGE="$PWD/bin/pob_bridge.lua"
#
# Notes:
# - Upstream only ships Windows builds; we download the official portable zips from GitHub.
#   Running them on Linux requires Wine/Proton; containers can stage them under /opt/pob.
# - LuaJIT is built locally from the official git repo; requires build-essential/make/git.
# - All artifacts live under ./bin to avoid system pollution.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BIN_DIR="$ROOT/bin"
mkdir -p "$BIN_DIR"
FORCE=0

usage() {
  cat <<'USAGE'
Usage: ./scripts/install-pob-cli.sh [--force] [--help]
  --force   Re-download PoB zips and rebuild LuaJIT even if present
  -h,--help Show this help
Environment overrides:
  POB_POE1_VERSION (default: latest), POB_POE2_VERSION (default: latest)
  POB_POE1_URL, POB_POE2_URL, LUAJIT_URL
USAGE
}

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      -f|--force) FORCE=1 ;;
      -h|--help) usage; exit 0 ;;
      *) echo "Unknown option: $1" >&2; usage >&2; exit 1 ;;
    esac
    shift
  done
}

parse_args "$@"

# Versions / URLs (can be overridden via env)
POB_POE1_VERSION="${POB_POE1_VERSION:-latest}"
POB_POE2_VERSION="${POB_POE2_VERSION:-latest}"

LUAJIT_VERSION="${LUAJIT_VERSION:-2.1.0-beta3}"
LUAJIT_URL="${LUAJIT_URL:-https://github.com/LuaJIT/LuaJIT.git}"

command -v curl >/dev/null || { echo "curl required"; exit 1; }
command -v unzip >/dev/null || { echo "unzip required"; exit 1; }
command -v python3 >/dev/null || { echo "python3 required"; exit 1; }
command -v git >/dev/null || { echo "git required"; exit 1; }
command -v make >/dev/null || { echo "make required"; exit 1; }

resolve_latest_asset_url() {
  local repo="$1"
  local pattern="$2"
  python3 - <<'PY' "$repo" "$pattern"
import json, re, sys, urllib.request
repo = sys.argv[1]
pat = re.compile(sys.argv[2])
url = f"https://api.github.com/repos/{repo}/releases/latest"
req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "path-of-mirrors-install"})
with urllib.request.urlopen(req, timeout=30) as resp:
    data = json.load(resp)
for asset in data.get("assets", []):
    name = asset.get("name") or ""
    if pat.fullmatch(name):
        print(asset.get("browser_download_url", ""))
        sys.exit(0)
sys.exit(1)
PY
}

resolve_pob_url() {
  local repo="$1"         # e.g., PathOfBuildingCommunity/PathOfBuilding
  local version="$2"      # e.g., latest or v2.54.0
  local asset_name="$3"   # e.g., PathOfBuildingCommunity-Portable.zip
  local pattern="$4"      # regex string

  if [[ "${version}" == "latest" ]]; then
    resolve_latest_asset_url "${repo}" "${pattern}"
  else
    echo "https://github.com/${repo}/releases/${version}/download/${asset_name}"
  fi
}

POB_POE1_URL="${POB_POE1_URL:-$(resolve_pob_url "PathOfBuildingCommunity/PathOfBuilding" "${POB_POE1_VERSION}" "PathOfBuildingCommunity-Portable.zip" "PathOfBuildingCommunity-Portable\\.zip")}"
POB_POE2_URL="${POB_POE2_URL:-$(resolve_pob_url "PathOfBuildingCommunity/PathOfBuilding-PoE2" "${POB_POE2_VERSION}" "PathOfBuildingCommunity-PoE2-Portable.zip" "PathOfBuildingCommunity-PoE2-Portable\\.zip")}"

fetch_and_unpack() {
  local url="$1"
  local dest_dir="$2"
  local label="$3"
  if [ -d "$dest_dir" ]; then
    if [ "$FORCE" -eq 0 ]; then
      echo "✓ $label already present: $dest_dir"
      return
    fi
    echo "↻ Re-downloading $label (--force)"
    rm -rf "$dest_dir"
  fi
  mkdir -p "$dest_dir"
  tmp=$(mktemp)
  echo "⬇️  Downloading $label ..."
  curl -fL "$url" -o "$tmp"
  echo "📦 Unpacking $label ..."
  unzip -q "$tmp" -d "$dest_dir"
  rm "$tmp"
  echo "✓ $label ready"
}

build_luajit() {
  local build_dir="$BIN_DIR/luajit-src"
  local prefix="$BIN_DIR/luajit"

  if [ "$FORCE" -eq 1 ]; then
    rm -rf "$prefix" "$build_dir"
  fi

  if [ -x "$prefix/bin/luajit" ]; then
    echo "✓ LuaJIT already built at $prefix/bin/luajit"
    return
  fi

  rm -rf "$build_dir"
  echo "⬇️  Cloning LuaJIT ..."
  if ! git clone --depth=1 "$LUAJIT_URL" "$build_dir" >/dev/null 2>&1; then
    echo "   shallow clone failed; falling back to full clone"
    git clone "$LUAJIT_URL" "$build_dir" >/dev/null
  fi

  echo "🔧 Building LuaJIT ..."
  (cd "$build_dir" && make PREFIX="$prefix" && make install PREFIX="$prefix" >/dev/null)
  echo "✓ LuaJIT built at $prefix/bin/luajit"
}

# Fetch PoB binaries
fetch_and_unpack "$POB_POE1_URL" "$BIN_DIR/pob-poe1" "PoB PoE1 (portable)"
fetch_and_unpack "$POB_POE2_URL" "$BIN_DIR/pob-poe2" "PoB PoE2 (portable)"

# Build LuaJIT
build_luajit

# Copy the bridge script from the repo into bin for runtime use
cp "$ROOT/backend/resources/pob_bridge.lua" "$BIN_DIR/pob_bridge.lua"
chmod +x "$BIN_DIR/pob_bridge.lua"

echo ""
echo "✅ Install complete."
echo "Set env vars (example):"
echo "  export POB_CLI_POE1=\"$BIN_DIR/pob-poe1/Path of Building.exe\""
echo "  export POB_CLI_POE2=\"$BIN_DIR/pob-poe2/Path of Building-PoE2.exe\""
echo "  export POB_LUAJIT=\"$BIN_DIR/luajit/bin/luajit\""
echo "  export POB_BRIDGE=\"$BIN_DIR/pob_bridge.lua\""
echo ""
echo "Smoke test (bridge):"
echo "  POB_LUAJIT=\"$BIN_DIR/luajit/bin/luajit\" POB_BRIDGE=\"$BIN_DIR/pob_bridge.lua\" \\"
echo "    LUA_PATH=\"$BIN_DIR/?.lua;;\" \\"
echo "    $BIN_DIR/luajit/bin/luajit $BIN_DIR/pob_bridge.lua <<< '<PathOfBuilding></PathOfBuilding>'"
