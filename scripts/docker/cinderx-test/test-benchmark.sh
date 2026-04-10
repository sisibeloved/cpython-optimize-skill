#!/bin/bash
# Run a CinderX pyperformance benchmark inside the container.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BENCHMARK=${BENCHMARK:-mdp}
WARMUP=${WARMUP:-3}
AUTOJIT=${PYTHONJITAUTO:-10}
DIAG=${DIAG:-0}
JIT_LOG_FILE=${JIT_LOG_FILE:-/tmp/cinderx-jit.log}
OPT_ENV_FILE=${OPT_ENV_FILE:-}
OPT_CONFIG_NAME=${OPT_CONFIG_NAME:-}
OUTPUT_FILE=${OUTPUT_FILE:-/tmp/pyperformance-cinderx.json}
PYPERFORMANCE_TMP="$(mktemp -d /tmp/pyperformance.XXXXXX)"
CINDERX_WHEEL_CACHE_DIR=${CINDERX_WHEEL_CACHE_DIR:-/opt/cinderx-wheel-cache}
trap 'rm -rf "$PYPERFORMANCE_TMP"' EXIT

echo "=== CinderX pyperformance ==="
echo "Benchmark selector: $BENCHMARK"
echo "Warmup: $WARMUP"
echo "AutoJIT: $AUTOJIT"
echo "Diag: $DIAG"
echo "Output: $OUTPUT_FILE"

export SCRIPT_DIR BENCHMARK OPT_ENV_FILE OPT_CONFIG_NAME AUTOJIT OUTPUT_FILE
eval "$(PYTHONJITDISABLE=1 python3 <<'PY'
import os
import sys
import sysconfig

sys.path.insert(0, os.environ["SCRIPT_DIR"])
from benchmark_harness import (
    cinderx_source_root,
    default_opt_env_file,
    load_opt_env_file,
    opt_config_name,
    pyperformance_hook_root,
    pyperformance_benchmark_filter,
)

path = os.environ.get("OPT_ENV_FILE")
if not path:
    default_path = default_opt_env_file(os.environ["BENCHMARK"])
    path = str(default_path) if default_path is not None else ""
config_name = os.environ.get("OPT_CONFIG_NAME") or opt_config_name(path or None, True)
env = load_opt_env_file(path or None)
benchmark_filter = pyperformance_benchmark_filter(os.environ["BENCHMARK"])
jit_arm_keys = ",".join(
    key for key in sorted(os.environ) if key.startswith("PYTHONJIT_ARM_")
)

print(f'export BENCHMARK_FILTER="{benchmark_filter}"')
print(f'export CINDERX_SOURCE_ROOT_RESOLVED="{cinderx_source_root()}"')
print(f'export PYPERFORMANCE_HOOK_ROOT_RESOLVED="{pyperformance_hook_root()}"')
print(f'export PYTHON_BASE_SITE_PACKAGES="{sysconfig.get_paths()["purelib"]}"')
print(f'export OPT_ENV_FILE_RESOLVED="{path}"')
print(f'export OPT_CONFIG_NAME_RESOLVED="{config_name}"')
print(f'export JIT_ARM_INHERIT_KEYS="{jit_arm_keys}"')
for key, value in env.items():
    print(f'export {key}="{value}"')
PY
)"

CINDERX_WHEEL_PATH=$(ls -t "$CINDERX_WHEEL_CACHE_DIR"/cinderx-*-linux_aarch64.whl 2>/dev/null | head -n1 || true)
if [[ -z "$CINDERX_WHEEL_PATH" ]]; then
  echo "missing cached cinderx wheel under $CINDERX_WHEEL_CACHE_DIR" >&2
  echo "run /scripts/setup.sh first to build and cache the wheel" >&2
  exit 1
fi
PYTHONJITDISABLE=1 python3 -m pip install --quiet --no-deps "$CINDERX_WHEEL_PATH" 2>&1 | grep -v notice | tail -1 || true
cp -a /pyperformance/. "$PYPERFORMANCE_TMP"/
PYTHONJITDISABLE=1 python3 -m pip install --quiet "$PYPERFORMANCE_TMP" 2>&1 | grep -v notice | tail -1 || true

env \
  LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}" \
  PYTHONJITDISABLE=1 \
  PYTHONJITAUTO="$AUTOJIT" \
  PYTHONPATH="${PYPERFORMANCE_HOOK_ROOT_RESOLVED}:${PYTHON_BASE_SITE_PACKAGES}${PYTHONPATH:+:${PYTHONPATH}}" \
  CINDERX_WORKER_PYTHONJITAUTO="$AUTOJIT" \
  CINDERX_ENABLE_SPECIALIZED_OPCODES="${CINDERX_ENABLE_SPECIALIZED_OPCODES:-1}" \
  PYTHONJITHUGEPAGES=0 \
  $(if [[ "$DIAG" != "0" ]]; then
      printf '%s\n' \
        "PYTHONJITLOGFILE=$JIT_LOG_FILE" \
        "PYTHONJITDUMPFINALHIR=1" \
        "PYTHONJITDUMPSTATS=1"
    fi) \
  $(PYTHONJITDISABLE=1 python3 <<'PY'
import os

for key, value in sorted(os.environ.items()):
    if key.startswith("PYTHONJIT_ARM_"):
        print(f"{key}={value}")
PY
) \
  python3 -m pyperformance run \
    --debug-single-value \
    --warmups "$WARMUP" \
    -b "$BENCHMARK_FILTER" \
    --inherit-environ "$(PYTHONJITDISABLE=1 python3 <<'PY'
import os

base = [
    "LD_LIBRARY_PATH",
    "PYTHONJITAUTO",
    "PYTHONPATH",
    "CINDERX_WORKER_PYTHONJITAUTO",
    "CINDERX_ENABLE_SPECIALIZED_OPCODES",
    "PYTHONJITHUGEPAGES",
]
diag = ["PYTHONJITLOGFILE", "PYTHONJITDUMPFINALHIR", "PYTHONJITDUMPSTATS"]
extra = [key for key in os.environ.get("JIT_ARM_INHERIT_KEYS", "").split(",") if key]
if os.environ.get("DIAG", "0") != "0":
    base.extend(diag)
print(",".join(base + extra))
PY
)" \
    -o "$OUTPUT_FILE"

PYTHONJITDISABLE=1 python3 <<'PY'
import os
import pyperf

suite = pyperf.BenchmarkSuite.load(os.environ["OUTPUT_FILE"])
bench = suite.get_benchmarks()[0]
print(f"\nCinderX Result ({bench.get_name()}): {bench.mean():.6f}s")
print(f"Results saved to {os.environ['OUTPUT_FILE']}")
PY
