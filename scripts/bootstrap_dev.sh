#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
TOOLS_DIR="$ROOT_DIR/.tools"
NODE_DIR="$TOOLS_DIR/node"
NODE_VERSION="24.16.0"
NODE_ARCHIVE="node-v${NODE_VERSION}-darwin-arm64.tar.gz"
NODE_SHA256="39189dab4eeb15706c424af0ac08a3044c9e48f7db12a7d77f6b7aafc7dd5df6"
NODE_URL="https://nodejs.org/dist/v${NODE_VERSION}/${NODE_ARCHIVE}"

log() {
  printf '\n==> %s\n' "$1"
}

fail() {
  printf 'error: %s\n' "$1" >&2
  exit 1
}

python_is_312() {
  [[ -x "$1" ]] && [[ "$("$1" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" == "3.12" ]]
}

find_python_312() {
  local candidate
  local candidates=()

  [[ -n "${CODEX_PYTHON:-}" ]] && candidates+=("$CODEX_PYTHON")
  [[ -n "${PYTHON312:-}" ]] && candidates+=("$PYTHON312")

  for candidate in "$HOME"/.cache/codex-runtimes/*/dependencies/python/bin/python3; do
    candidates+=("$candidate")
  done

  if command -v python3.12 >/dev/null 2>&1; then
    candidates+=("$(command -v python3.12)")
  fi
  if command -v python3 >/dev/null 2>&1; then
    candidates+=("$(command -v python3)")
  fi

  for candidate in "${candidates[@]}"; do
    if python_is_312 "$candidate"; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

node_is_lts() {
  [[ -x "$1" ]] && [[ "$("$1" -p 'process.release.lts ? "yes" : "no"')" == "yes" ]]
}

install_local_node() {
  local archive_path="$TOOLS_DIR/$NODE_ARCHIVE"
  local actual_sha
  local install_dir

  [[ "$(uname -s)" == "Darwin" && "$(uname -m)" == "arm64" ]] || fail \
    "npm was not found. Automatic Node installation supports macOS arm64; install an active Node.js LTS release and rerun."
  command -v curl >/dev/null 2>&1 || fail "curl is required to download the official Node.js LTS archive."
  command -v tar >/dev/null 2>&1 || fail "tar is required to unpack the official Node.js LTS archive."
  command -v shasum >/dev/null 2>&1 || fail "shasum is required to verify the Node.js archive."
  [[ ! -e "$NODE_DIR" ]] || fail "$NODE_DIR exists but does not contain a usable Node/npm toolchain. Remove it and rerun."

  mkdir -p "$TOOLS_DIR"
  log "Downloading Node.js ${NODE_VERSION} LTS for macOS arm64"
  if [[ ! -f "$archive_path" ]]; then
    curl -fL "$NODE_URL" -o "${archive_path}.tmp"
    mv "${archive_path}.tmp" "$archive_path"
  fi

  actual_sha="$(shasum -a 256 "$archive_path" | awk '{print $1}')"
  if [[ "$actual_sha" != "$NODE_SHA256" ]]; then
    fail "Node.js archive checksum mismatch. Delete $archive_path and rerun."
  fi

  install_dir="$(mktemp -d "$TOOLS_DIR/node-install.XXXXXX")"
  tar -xzf "$archive_path" -C "$install_dir" --strip-components=1
  mv "$install_dir" "$NODE_DIR"
}

cd "$ROOT_DIR"
mkdir -p "$TOOLS_DIR"
export PIP_CACHE_DIR="$TOOLS_DIR/pip-cache"
export npm_config_cache="$TOOLS_DIR/npm-cache"
export PLAYWRIGHT_BROWSERS_PATH="$TOOLS_DIR/playwright"

log "Preparing Python 3.12 virtual environment"
if [[ -x "$VENV_DIR/bin/python" ]]; then
  python_is_312 "$VENV_DIR/bin/python" || fail \
    "$VENV_DIR uses the wrong Python version. Remove it and rerun this script with Python 3.12 available."
else
  PYTHON_BIN="$(find_python_312)" || fail \
    "Python 3.12 was not found. Set CODEX_PYTHON or PYTHON312 to a Python 3.12 executable and rerun."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install -r backend/requirements.txt -r requirements-dev.txt

if [[ "$(uname -s)" == "Darwin" ]]; then
  SITE_PACKAGES="$("$VENV_DIR/bin/python" -c 'import site; print(site.getsitepackages()[0])')"
  cat >"$SITE_PACKAGES/sitecustomize.py" <<'PY'
"""Keep copied subprocess interpreters linked to the bundled Codex Python runtime."""

import os
import sys
from pathlib import Path

if sys.platform == "darwin":
    library_dir = Path(sys.base_prefix) / "lib"
    library = library_dir / f"libpython{sys.version_info.major}.{sys.version_info.minor}.dylib"
    if library.exists():
        current = os.environ.get("DYLD_LIBRARY_PATH", "")
        entries = [entry for entry in current.split(":") if entry]
        if str(library_dir) not in entries:
            os.environ["DYLD_LIBRARY_PATH"] = ":".join([str(library_dir), *entries])
PY
fi

log "Preparing Node.js LTS with npm"
if [[ -x "$NODE_DIR/bin/node" && -x "$NODE_DIR/bin/npm" ]]; then
  :
elif command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1 && node_is_lts "$(command -v node)"; then
  NODE_DIR="$(cd -- "$(dirname -- "$(command -v node)")/.." && pwd)"
else
  install_local_node
fi

export PATH="$NODE_DIR/bin:$VENV_DIR/bin:$PATH"
node_is_lts "$(command -v node)" || fail "The discovered Node.js executable is not an LTS release."
command -v npm >/dev/null 2>&1 || fail "npm is unavailable after Node.js setup."
command -v npx >/dev/null 2>&1 || fail "npx is unavailable after Node.js setup."

log "Installing Node dependencies (root: Playwright/e2e)"
if [[ -f package-lock.json ]]; then
  npm ci
else
  npm install
fi

log "Installing frontend dependencies (React/Vite app)"
if [[ -f frontend/package-lock.json ]]; then
  npm --prefix frontend ci
else
  npm --prefix frontend install
fi

log "Building the frontend once (frontend/dist)"
npm --prefix frontend run build

log "Installing Playwright Chromium"
npx playwright install chromium

log "Development toolchain ready"
printf 'Python: %s\n' "$("$VENV_DIR/bin/python" --version 2>&1)"
printf 'Node:   %s\n' "$(node --version)"
printf 'npm:    %s\n' "$(npm --version)"
printf 'Run all checks with: scripts/verify_all.sh\n'
