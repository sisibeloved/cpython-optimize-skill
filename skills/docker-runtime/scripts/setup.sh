#!/bin/bash
# Setup cinderx and pyperformance in the container
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYPERFORMANCE_TMP="$(mktemp -d /tmp/pyperformance.XXXXXX)"
CINDERX_WHEEL_TMP="$(mktemp -d /tmp/cinderx-wheel.XXXXXX)"
CINDERX_WHEEL_CACHE_DIR=${CINDERX_WHEEL_CACHE_DIR:-/opt/cinderx-wheel-cache}
PIP_INDEX_URL=${PIP_INDEX_URL:-https://mirrors.aliyun.com/pypi/simple/}
DEFAULT_CPU_JOBS=$(getconf _NPROCESSORS_ONLN 2>/dev/null || nproc 2>/dev/null || echo 4)
DEFAULT_MEM_JOBS=$(awk '/MemAvailable:/ {jobs = int($2 / 2097152); if (jobs < 1) jobs = 1; print jobs; exit}' /proc/meminfo 2>/dev/null || echo 1)
if (( DEFAULT_MEM_JOBS < DEFAULT_CPU_JOBS )); then
  DEFAULT_BUILD_JOBS=$DEFAULT_MEM_JOBS
else
  DEFAULT_BUILD_JOBS=$DEFAULT_CPU_JOBS
fi
CINDERX_BUILD_JOBS=${CINDERX_BUILD_JOBS:-$DEFAULT_BUILD_JOBS}
CMAKE_BUILD_PARALLEL_LEVEL=${CMAKE_BUILD_PARALLEL_LEVEL:-$CINDERX_BUILD_JOBS}
trap 'rm -rf "$PYPERFORMANCE_TMP" "$CINDERX_WHEEL_TMP"' EXIT

export SCRIPT_DIR
export PIP_INDEX_URL
eval "$(python3 <<'PY'
import os
import sys

sys.path.insert(0, os.environ["SCRIPT_DIR"])
from benchmark_harness import cinderx_source_root

print(f'export CINDERX_SOURCE_ROOT_RESOLVED="{cinderx_source_root()}"')
PY
)"

echo "=== Installing cinderx ==="
mkdir -p "$CINDERX_WHEEL_CACHE_DIR"
PYTHONJITDISABLE=1 python3 -m pip install --quiet build 2>&1 | grep -v notice | tail -1 || true
(
  cd "$CINDERX_SOURCE_ROOT_RESOLVED"
  PYTHONJITDISABLE=1 \
    CMAKE_BUILD_PARALLEL_LEVEL="$CMAKE_BUILD_PARALLEL_LEVEL" \
    CINDERX_BUILD_JOBS="$CINDERX_BUILD_JOBS" \
    python3 -m build --wheel --outdir "$CINDERX_WHEEL_TMP" 2>&1 | tail -5
)
cp "$CINDERX_WHEEL_TMP"/cinderx-*-linux_aarch64.whl "$CINDERX_WHEEL_CACHE_DIR"/
PYTHONJITDISABLE=1 pip3 install --quiet --no-deps "$CINDERX_WHEEL_CACHE_DIR"/cinderx-*-linux_aarch64.whl 2>&1 | grep -v notice | tail -1

echo "=== Installing pyperformance ==="
cp -a /pyperformance/. "$PYPERFORMANCE_TMP"/
PYTHONJITDISABLE=1 python3 -m pip install --quiet "$PYPERFORMANCE_TMP" 2>&1 | grep -v notice | tail -1 || true

echo "=== Verifying installation ==="
python3 << 'PY'
import cinderx
import cinderx.jit as jit
import pyperformance

if cinderx.get_import_error() is not None:
    raise SystemExit(f"failed to import _cinderx: {cinderx.get_import_error()!r}")
print(f"✓ cinderx import ok, initialized={cinderx.is_initialized()}")
print(f"✓ pyperformance available: {pyperformance.__file__}")
PY

echo ""
echo "=== Setup complete ==="
echo "Run '/scripts/smoke.sh' to verify JIT functionality"
echo "Run 'BENCHMARK=mdp /scripts/test-benchmark.sh' to run a pyperformance benchmark"
