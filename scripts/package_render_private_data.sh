#!/usr/bin/env bash
set -euo pipefail

out="${1:-/private/tmp/replocx-render-private-data.tar.gz}"

require_dir() {
  local name="$1"
  local value="${!name:-}"
  if [[ -z "$value" ]]; then
    echo "error: set $name to an existing source directory" >&2
    exit 2
  fi
  if [[ ! -d "$value" ]]; then
    echo "error: $name is not a directory: $value" >&2
    exit 2
  fi
}

require_dir RLE_ANALYSIS_SOURCE
require_dir RLE_ATLAS_SOURCE
require_dir RLE_ATLAS_FIGURE_SOURCE

workdir="$(mktemp -d)"
trap 'rm -rf "$workdir"' EXIT
export COPYFILE_DISABLE=1

mkdir -p \
  "$workdir/analysis" \
  "$workdir/atlas/replocx_tmy3_wallfix_4scen" \
  "$workdir/atlas-figures/f2v3_final"

cp -R "$RLE_ANALYSIS_SOURCE"/. "$workdir/analysis/"
cp -R "$RLE_ATLAS_SOURCE"/. "$workdir/atlas/replocx_tmy3_wallfix_4scen/"
cp -R "$RLE_ATLAS_FIGURE_SOURCE"/. "$workdir/atlas-figures/f2v3_final/"
find "$workdir" -name '._*' -type f -delete

mkdir -p "$(dirname "$out")"
tar -czf "$out" -C "$workdir" analysis atlas atlas-figures

echo "created: $out"
shasum -a 256 "$out"
