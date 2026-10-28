#!/usr/bin/env bash

set -uo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$ROOT_DIR/.venv"
TOOLS_DIR="$ROOT_DIR/.tools"
PYTHON_BIN="$VENV_DIR/bin/python"
failures=()

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  printf 'Usage: %s\n' "${0##*/}"
  printf 'Run the complete local verification matrix after scripts/bootstrap_dev.sh.\n'
  exit 0
fi
[[ $# -eq 0 ]] || {
  printf 'error: unexpected argument: %s\n' "$1" >&2
  exit 2
}

fail_setup() {
  printf 'toolchain error: %s\n' "$1" >&2
  printf 'Run scripts/bootstrap_dev.sh, then retry.\n' >&2
  exit 2
}

run_check() {
  local label="$1"
  local status
  shift

  printf '\n==> %s\n' "$label"
  "$@"
  status=$?
  if [[ $status -eq 0 ]]; then
    printf 'PASS: %s\n' "$label"
  else
    printf 'FAIL: %s (exit %d)\n' "$label" "$status" >&2
    failures+=("$label (exit $status)")
  fi
}

cd "$ROOT_DIR"

[[ -x "$PYTHON_BIN" ]] || fail_setup "Python virtual environment not found at $VENV_DIR."
[[ "$("$PYTHON_BIN" -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" == "3.12" ]] || \
  fail_setup "$VENV_DIR is not using Python 3.12."

if [[ -x "$TOOLS_DIR/node/bin/node" && -x "$TOOLS_DIR/node/bin/npm" ]]; then
  export PATH="$TOOLS_DIR/node/bin:$VENV_DIR/bin:$PATH"
else
  export PATH="$VENV_DIR/bin:$PATH"
fi

command -v node >/dev/null 2>&1 || fail_setup "Node.js was not found."
[[ "$(node -p 'process.release.lts ? "yes" : "no"')" == "yes" ]] || fail_setup "The active Node.js release is not LTS."
[[ -f package-lock.json ]] || fail_setup "package-lock.json is missing."
[[ -f frontend/package-lock.json ]] || fail_setup "frontend/package-lock.json is missing."
[[ -d frontend/node_modules ]] || fail_setup "frontend/node_modules is missing; run scripts/bootstrap_dev.sh."
[[ -x node_modules/.bin/playwright ]] || fail_setup "Playwright is not installed in node_modules."
[[ -d "$TOOLS_DIR/playwright" ]] || fail_setup "The repository-local Playwright browser directory is missing."

for module in ruff black mypy coverage pip_audit; do
  "$PYTHON_BIN" -c "import $module" >/dev/null 2>&1 || fail_setup "Python module '$module' is not installed."
done

export PIP_CACHE_DIR="$TOOLS_DIR/pip-cache"
export npm_config_cache="$TOOLS_DIR/npm-cache"
export PLAYWRIGHT_BROWSERS_PATH="$TOOLS_DIR/playwright"
FIXTURE_OUT="$(mktemp -d "${TMPDIR:-/tmp}/rle-fixture-out.XXXXXX")"
trap 'rm -rf "$FIXTURE_OUT"' EXIT
if [[ "$(uname -s)" == "Darwin" ]]; then
  PYTHON_LIBRARY_DIR="$("$PYTHON_BIN" -c 'import sys; from pathlib import Path; print(Path(sys.base_prefix) / "lib")')"
  if [[ -f "$PYTHON_LIBRARY_DIR/libpython3.12.dylib" ]]; then
    export DYLD_LIBRARY_PATH="$PYTHON_LIBRARY_DIR${DYLD_LIBRARY_PATH:+:$DYLD_LIBRARY_PATH}"
  fi
fi

run_check "Fixture pipeline" \
  "$PYTHON_BIN" -m pipeline.run --source fixture --out "$FIXTURE_OUT"
run_check "Validate regenerated fixture outputs" \
  "$PYTHON_BIN" -m pipeline.validate --dir "$FIXTURE_OUT"
run_check "Unit tests with bundled demo data" \
  "$PYTHON_BIN" -m unittest discover -s tests -v
run_check "Unit tests with pipeline outputs" \
  env RLE_ANALYSIS_DATA_DIR="$FIXTURE_OUT" "$PYTHON_BIN" -m unittest discover -s tests -v
run_check "Ruff lint" \
  "$PYTHON_BIN" -m ruff check backend pipeline scripts tests clients/python/rle_client
run_check "Black formatting check" \
  "$PYTHON_BIN" -m black --check backend pipeline scripts tests clients/python/rle_client
run_check "Mypy type check" \
  "$PYTHON_BIN" -m mypy backend/api.py backend/auth.py backend/observability.py backend/scenario_store.py \
  clients/python/rle_client
run_check "Coverage test run" \
  "$PYTHON_BIN" -m coverage run -m unittest discover -s tests -v
run_check "Coverage report" \
  "$PYTHON_BIN" -m coverage report
run_check "Runtime dependency audit" \
  "$PYTHON_BIN" -m pip_audit -r backend/requirements.txt
run_check "API + security + degraded-mode contract" \
  "$PYTHON_BIN" scripts/check_release_contract.py
run_check "Frontend type check" \
  npm --prefix frontend run typecheck
run_check "Frontend lint" \
  npm --prefix frontend run lint
run_check "Frontend unit tests" \
  npm --prefix frontend run test
run_check "Frontend production build" \
  npm --prefix frontend run build
run_check "Frontend dependency audit" \
  npm --prefix frontend audit --omit=dev --audit-level=high
run_check "Playwright end-to-end tests" \
  node_modules/.bin/playwright test

printf '\n==> Verification summary\n'
if [[ ${#failures[@]} -eq 0 ]]; then
  printf 'All checks passed.\n'
  exit 0
fi

printf '%d check(s) failed:\n' "${#failures[@]}" >&2
printf '  - %s\n' "${failures[@]}" >&2
exit 1
