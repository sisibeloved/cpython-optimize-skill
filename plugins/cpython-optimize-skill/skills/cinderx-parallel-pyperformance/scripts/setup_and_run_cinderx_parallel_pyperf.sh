#!/usr/bin/env bash
set -Eeuo pipefail

export LC_ALL="${LC_ALL:-C.UTF-8}"
export LANG="${LANG:-C.UTF-8}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DRIVER="$SCRIPT_DIR/parallel_pyperformance.py"

CPY="${CPY:-}"
RUNROOT="${RUNROOT:-/tmp/cinderx-parallel-pyperf-$(date +%Y%m%d-%H%M%S)}"
MODE="${MODE:-auto}"
PROFILE="${PROFILE:-auto}"
REPEAT="${REPEAT:-1}"
WARMUP="${WARMUP:-3}"
REMOTE_PROXY="${REMOTE_PROXY:-http://127.0.0.1:17890}"

log() {
  printf '[%(%F %T)T] %s\n' -1 "$*"
}

fail() {
  log "ERROR: $*"
  exit 1
}

[[ -n "$CPY" ]] || fail "Set CPY=/path/to/python3.14"
[[ -x "$CPY" ]] || fail "Python is not executable: $CPY"
[[ -f "$DRIVER" ]] || fail "parallel_pyperformance.py not found: $DRIVER"

if [[ -z "${CINDERX_WHEEL:-}" ]]; then
  [[ -n "${WHEEL_ROOT:-}" ]] || fail "Set CINDERX_WHEEL=/path/to/cinderx.whl or WHEEL_ROOT=/path/to/search"
  CINDERX_WHEEL="$(
    find "$WHEEL_ROOT" -type f -path '*/wheelhouse/cinderx-*.whl' -printf '%T@ %p\n' |
      sort -nr |
      head -n 1 |
      cut -d' ' -f2-
  )"
fi
[[ -n "$CINDERX_WHEEL" && -f "$CINDERX_WHEEL" ]] || fail "CinderX wheel not found: ${CINDERX_WHEEL:-<empty>}"

mkdir -p "$RUNROOT"

PIP_CONF="/root/.config/pip/pip.conf"
PIP_CONF_BACKUP="$RUNROOT/pip.conf.backup"
PIP_CONF_TOUCHED=0

restore_pip_proxy() {
  if [[ "$PIP_CONF_TOUCHED" == "1" ]]; then
    if [[ -f "$PIP_CONF_BACKUP" ]]; then
      cp "$PIP_CONF_BACKUP" "$PIP_CONF"
    else
      rm -f "$PIP_CONF"
    fi
    PIP_CONF_TOUCHED=0
  fi
}

clear_proxy_env() {
  unset HTTP_PROXY HTTPS_PROXY ALL_PROXY PIP_PROXY http_proxy https_proxy all_proxy
}

if [[ "${USE_PROXY:-auto}" != "none" ]] && timeout 8 curl -fsS -x "$REMOTE_PROXY" https://pypi.org/simple/pip/ >/dev/null 2>&1; then
  export HTTP_PROXY="$REMOTE_PROXY"
  export HTTPS_PROXY="$REMOTE_PROXY"
  export ALL_PROXY="$REMOTE_PROXY"
  export PIP_PROXY="$REMOTE_PROXY"
  export http_proxy="$REMOTE_PROXY"
  export https_proxy="$REMOTE_PROXY"
  export all_proxy="$REMOTE_PROXY"
  mkdir -p "$(dirname "$PIP_CONF")"
  if [[ -f "$PIP_CONF" ]]; then
    cp "$PIP_CONF" "$PIP_CONF_BACKUP"
  fi
  {
    printf '[global]\n'
    printf 'proxy = %s\n' "$REMOTE_PROXY"
  } > "$PIP_CONF"
  PIP_CONF_TOUCHED=1
  trap restore_pip_proxy EXIT
  log "using scoped pip proxy: $REMOTE_PROXY"
else
  log "proxy not reachable or disabled; continuing without scoped pip proxy"
fi

OPT_VENV="$RUNROOT/opt-venv"
OPT_PY="$OPT_VENV/bin/python"
PYPERF_WORK="$RUNROOT/pyperf-work"
RESULTS="$RUNROOT/results"
STARTUP_DIR="$RUNROOT/cinderx-startup"

log "RUNROOT=$RUNROOT"
log "CPY=$CPY"
log "CINDERX_WHEEL=$CINDERX_WHEEL"
log "MODE=$MODE PROFILE=$PROFILE REPEAT=$REPEAT"

if [[ ! -x "$OPT_PY" ]]; then
  log "creating opt venv"
  "$CPY" -m venv "$OPT_VENV"
  "$OPT_PY" -m ensurepip --upgrade >/dev/null 2>&1 || true
  "$OPT_PY" -m pip install --upgrade pip wheel
  "$OPT_PY" -m pip install 'pyperformance==1.13.0'
fi
"$OPT_PY" -m pip install --force-reinstall "$CINDERX_WHEEL"

probe_jit() {
  local label="$1"
  local py="$2"
  CINDERX_PLUGIN_ENABLE=1 \
  PYTHONJITAUTO=2 \
  AUTO_JIT=2 \
  PYTHONJITLIGHTWEIGHTFRAME=1 \
  "$py" - "$label" <<'PY'
import sys
label = sys.argv[1]
import cinderx
cinderx.init()
import cinderjit

def toy(n):
    total = 0
    for i in range(n):
        total += i
    return total

for _ in range(20):
    toy(64)

print(f"{label}_python={sys.executable}")
print(f"{label}_cinderx={getattr(cinderx, '__file__', '<builtin>')}")
print(f"{label}_frame_evaluator={cinderx.is_frame_evaluator_installed()}")
print(f"{label}_compile_after={cinderjit.get_compile_after_n_calls()}")
print(f"{label}_toy_compiled={cinderjit.is_jit_compiled(toy)}")
PY
}

log "probing manager JIT"
probe_jit manager "$OPT_PY" | tee "$RUNROOT/manager-jit-probe.log"

COMMON_ENV="CINDERX_PLUGIN_ENABLE,PYTHONJITAUTO,AUTO_JIT,PYTHONJITLIGHTWEIGHTFRAME,PYTHONPATH,LD_LIBRARY_PATH"
mkdir -p "$PYPERF_WORK"

if [[ ! -d "$PYPERF_WORK/venv" ]]; then
  log "creating pyperformance worker venv"
  (
    cd "$PYPERF_WORK"
    CINDERX_PLUGIN_ENABLE=1 \
    PYTHONJITAUTO=2 \
    AUTO_JIT=2 \
    PYTHONJITLIGHTWEIGHTFRAME=1 \
    "$OPT_PY" -m pyperformance venv create \
      --inherit-environ "$COMMON_ENV" \
      -p "$OPT_PY" \
      -b richards
  ) 2>&1 | tee "$RUNROOT/pyperformance-venv-create.log"
fi

mapfile -t WORKER_PYS < <(find "$PYPERF_WORK" -path '*/bin/python' \( -type f -o -type l \) | sort)
[[ "${#WORKER_PYS[@]}" -gt 0 ]] || fail "pyperformance worker python not found under $PYPERF_WORK"

log "installing CinderX into ${#WORKER_PYS[@]} worker python(s)"
for worker_py in "${WORKER_PYS[@]}"; do
  "$worker_py" -m pip install --force-reinstall "$CINDERX_WHEEL"
  probe_jit worker "$worker_py" | tee -a "$RUNROOT/worker-jit-probe.log"
done

restore_pip_proxy
clear_proxy_env

OPT_SITE="$("$OPT_PY" - <<'PY'
import site
print(site.getsitepackages()[0])
PY
)"
mkdir -p "$STARTUP_DIR" "$RESULTS"
cat > "$STARTUP_DIR/sitecustomize.py" <<'PY'
try:
    import _cinderx_auto
except Exception:
    raise
PY

run_once() {
  local idx="$1"
  local tag="run${idx}"
  local log_file="$RUNROOT/${tag}.log"
  local -a bench_args=()
  if [[ -n "${BENCHMARKS:-}" ]]; then
    bench_args+=(--benchmarks "$BENCHMARKS")
  fi
  log "starting parallel pyperformance $tag"
  (
    cd "$PYPERF_WORK"
    PYTHON="$OPT_PY" \
    PYTHONPATH="$STARTUP_DIR:$OPT_SITE${PYTHONPATH:+:$PYTHONPATH}" \
    WORK_DIR="$RESULTS" \
    MODE="$MODE" \
    PROFILE="$PROFILE" \
    WARMUP="$WARMUP" \
    "$OPT_PY" "$DRIVER" \
      --mode "$MODE" \
      --profile "$PROFILE" \
      --python "$OPT_PY" \
      --output-dir "$RESULTS" \
      --tag "$tag" \
      --warmup "$WARMUP" \
      "${bench_args[@]}"
  ) >"$log_file" 2>&1
  log "finished $tag; log=$log_file"
  grep -a 'Done! merged result:' "$log_file" | tail -n 1 | sed 's/^/[merged] /' || true
}

for idx in $(seq 1 "$REPEAT"); do
  run_once "$idx"
done

if [[ "$REPEAT" -ge 2 ]]; then
  JSON1="$(grep -a 'Done! merged result:' "$RUNROOT/run1.log" | tail -n 1 | sed 's/.*Done! merged result: //')"
  JSON2="$(grep -a 'Done! merged result:' "$RUNROOT/run2.log" | tail -n 1 | sed 's/.*Done! merged result: //')"
  log "run1_json=$JSON1"
  log "run2_json=$JSON2"
  if [[ -f "$JSON1" && -f "$JSON2" ]]; then
    "$OPT_PY" -m pyperf compare_to "$JSON1" "$JSON2" --table > "$RUNROOT/compare-run1-run2.log" 2>&1 || true
    log "compare log=$RUNROOT/compare-run1-run2.log"
    sed -n '1,180p' "$RUNROOT/compare-run1-run2.log"
  else
    log "compare skipped because one merged JSON is missing"
  fi
fi

log "DONE"
