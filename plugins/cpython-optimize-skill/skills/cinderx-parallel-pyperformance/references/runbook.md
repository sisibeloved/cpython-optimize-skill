# Parallel Pyperformance Runbook

## Mode Policy

This skill supports only 8-lane and 16-lane formal modes.

- `auto`: select 16 lanes only when 16 memory-backed, SMT-distinct, L3-distinct main lanes are available; otherwise select 8 lanes.
- `8`: force 8 main lanes.
- `16`: force 16 main lanes and fail if the topology cannot satisfy it safely.

Never fill a mode with CPUs from NUMA nodes that have no local memory. On hosts shaped like blue-server-53, node1/node3 CPUs exist but are not valid benchmark worker CPUs for this workflow because they do not have local memory.

Do not silently accept L3 overlap. If a user explicitly asks to explore oversubscription, mark the result as exploratory and not a formal performance conclusion.

## blue-server-53 Profile

The tested stable profile for blue-server-53 is 8 main lanes:

```text
main lanes:
  cpu 0   membind node0
  cpu 16  membind node0
  cpu 32  membind node0
  cpu 48  membind node0
  cpu 192 membind node2
  cpu 208 membind node2
  cpu 224 membind node2
  cpu 240 membind node2

tail tracks:
  ports: cpu 80, node0, serial asyncio/tornado network benchmarks
  dask: cpus 72,74,76,78, node0
  concurrent_imap: cpus 264,266,268,270, node2
```

This keeps benchmark workers on memory-backed NUMA nodes and avoids cross-track L3 overlap for the known 53 layout. `auto` should choose this 8-lane profile on 53 rather than forcing 16.

## Environment Contract

Use one fresh runroot per validation:

```text
<runroot>/
  opt-venv/
  pyperf-work/
  cinderx-startup/sitecustomize.py
  results/
  *.log
```

The same tested CinderX wheel must be visible in:

- the pyperformance manager, through `opt-venv`;
- the pyperformance base worker venv, through direct wheel install;
- any derived benchmark worker venv, through inherited `PYTHONPATH` pointing at `cinderx-startup` and `opt-venv` site-packages.

The startup file should do only this:

```python
try:
    import _cinderx_auto
except Exception:
    raise
```

Required runtime environment:

```bash
CINDERX_PLUGIN_ENABLE=1
PYTHONJITAUTO=2
AUTO_JIT=2
PYTHONJITLIGHTWEIGHTFRAME=1
PYTHONPATH=<runroot>/cinderx-startup:<runroot>/opt-venv/lib/.../site-packages
```

Always pass these through `--inherit-environ`:

```text
http_proxy,https_proxy,LD_LIBRARY_PATH,PYTHONPATH,
CINDERX_PLUGIN_ENABLE,PYTHONJITAUTO,AUTO_JIT,PYTHONJITLIGHTWEIGHTFRAME,
OMP_NUM_THREADS,OPENBLAS_NUM_THREADS,MKL_NUM_THREADS,NUMEXPR_NUM_THREADS
```

## Proxy Setup

If the remote host needs outbound Python package access, first establish the SSH reverse tunnel used by the environment, commonly:

```text
RemoteForward 17890 127.0.0.1:7897
```

Then pass:

```bash
REMOTE_PROXY=http://127.0.0.1:17890
```

The setup script tests the proxy with `curl -x`. If reachable, it temporarily writes `/root/.config/pip/pip.conf` with that proxy because pyperformance/pip setup may ignore ordinary proxy environment variables. The script restores the previous pip config before measurement.

## Commands

Dry-run the scheduler on the host:

```bash
PYTHON=/path/to/opt-venv/bin/python \
  python3 scripts/parallel_pyperformance.py \
    --profile auto --mode auto --dry-run --plan
```

Set up and run one full pass:

```bash
CPY=/path/to/python3.14 \
CINDERX_WHEEL=/path/to/cinderx.whl \
RUNROOT=/home/guo/codex-work/parallel-pyperf-$(date +%Y%m%d-%H%M%S) \
MODE=auto PROFILE=auto REPEAT=1 \
REMOTE_PROXY=http://127.0.0.1:17890 \
  bash scripts/setup_and_run_cinderx_parallel_pyperf.sh
```

Run a stability pair:

```bash
CPY=/path/to/python3.14 \
CINDERX_WHEEL=/path/to/cinderx.whl \
RUNROOT=/home/guo/codex-work/parallel-pyperf-$(date +%Y%m%d-%H%M%S) \
MODE=auto PROFILE=auto REPEAT=2 \
REMOTE_PROXY=http://127.0.0.1:17890 \
  bash scripts/setup_and_run_cinderx_parallel_pyperf.sh
```

Run a subset:

```bash
BENCHMARKS=richards,go,raytrace \
MODE=8 REPEAT=2 \
  bash scripts/setup_and_run_cinderx_parallel_pyperf.sh
```

## Result Reading

Report these facts:

- runroot and merged result JSON paths;
- selected mode, profile, main lanes, tail tracks, and peak active physical cores;
- manager and worker JIT probe output;
- whether proxy/pip config was used and restored;
- whether the host was shared or under background load;
- `pyperf compare_to` output for repeat pairs or baseline/candidate pairs.

On a busy machine, treat high variance as expected. Prefer "this validates the workflow and exposes no obvious instability under current load" over "this proves no regression".

Use `pyperf compare_to --table` and significance markers. Do not rely on mean-only wins.
