#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


SERIAL_PORT = ["asyncio_tcp", "asyncio_tcp_ssl", "asyncio_websockets", "tornado_http"]
MULTICORE = ["dask", "concurrent_imap"]

ALL_BENCHMARKS = """2to3 argparse argparse_subparsers async_generators async_tree
async_tree_cpu_io_mixed async_tree_cpu_io_mixed_tg async_tree_eager
async_tree_eager_cpu_io_mixed async_tree_eager_cpu_io_mixed_tg async_tree_eager_io
async_tree_eager_io_tg async_tree_eager_memoization async_tree_eager_memoization_tg
async_tree_eager_tg async_tree_io async_tree_io_tg async_tree_memoization
async_tree_memoization_tg async_tree_tg asyncio_tcp asyncio_tcp_ssl asyncio_websockets
bpe_tokeniser chameleon chaos comprehensions concurrent_imap coroutines coverage
crypto_pyaes dask deepcopy deltablue django_template docutils dulwich_log fannkuch
float gc_collect gc_traversal generators genshi go hexiom html5lib json_dumps
json_loads logging mako mdp meteor_contest nbody networkx networkx_connected_components
networkx_k_core nqueens pathlib pickle pickle_dict pickle_list pickle_pure_python
pidigits pprint pyflate python_startup python_startup_no_site raytrace regex_compile
regex_dna regex_effbot regex_v8 richards richards_super scimark spectral_norm sphinx
sqlalchemy_declarative sqlalchemy_imperative sqlglot_v2 sqlglot_v2_optimize
sqlglot_v2_parse sqlglot_v2_transpile sqlite_synth sympy telco tomli_loads tornado_http
typing_runtime_protocols unpack_sequence unpickle unpickle_list unpickle_pure_python
xdsl xml_etree""".split()

FALLBACK_DURATIONS = {
    "coverage": 1,
    "sphinx": 180,
    "docutils": 137,
    "mdp": 66,
    "sympy": 50,
    "scimark": 18,
    "xdsl": 2,
    "networkx": 23,
    "sqlalchemy_declarative": 80,
    "django_template": 2,
    "pyflate": 20,
    "html5lib": 3,
    "genshi": 4,
    "chameleon": 1,
    "2to3": 226,
    "bpe_tokeniser": 213,
    "telco": 1,
}

JIT_ENV = {
    "CINDERX_PLUGIN_ENABLE": "1",
    "PYTHONJITAUTO": "2",
    "AUTO_JIT": "2",
    "PYTHONJITLIGHTWEIGHTFRAME": "1",
}

THREAD_LOCK_ENV = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}

DEFAULT_INHERIT = ",".join(
    [
        "http_proxy",
        "https_proxy",
        "LD_LIBRARY_PATH",
        "PYTHONPATH",
        "CINDERX_PLUGIN_ENABLE",
        "PYTHONJITAUTO",
        "AUTO_JIT",
        "PYTHONJITLIGHTWEIGHTFRAME",
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ]
)


@dataclass(frozen=True)
class Lane:
    label: str
    bind: str
    node: int


@dataclass(frozen=True)
class TailTrack:
    name: str
    benches: tuple[str, ...]
    bind: str
    node: int
    multicore: bool


def expand_cpulist(spec: str) -> set[int]:
    cpus: set[int] = set()
    for part in str(spec).split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-", 1)
            cpus.update(range(int(lo), int(hi) + 1))
        else:
            cpus.add(int(part))
    return cpus


def compact_cpulist(cpus: set[int]) -> str:
    ordered = sorted(cpus)
    if not ordered:
        return ""
    ranges: list[str] = []
    start = prev = ordered[0]
    for cpu in ordered[1:]:
        if cpu == prev + 1:
            prev = cpu
            continue
        ranges.append(f"{start}-{prev}" if start != prev else str(start))
        start = prev = cpu
    ranges.append(f"{start}-{prev}" if start != prev else str(start))
    return ",".join(ranges)


def read_text(path: Path) -> str | None:
    try:
        return path.read_text().strip()
    except OSError:
        return None


def available_cpus() -> set[int]:
    if hasattr(os, "sched_getaffinity"):
        return set(os.sched_getaffinity(0))
    return set(range(os.cpu_count() or 1))


def numa_mem_total_mb(node: int) -> int | None:
    text = read_text(Path(f"/sys/devices/system/node/node{node}/meminfo"))
    if text is None:
        return None
    for line in text.splitlines():
        if "MemTotal" in line:
            parts = line.split()
            return int(parts[-2]) // 1024
    return None


def memory_backed_nodes() -> set[int]:
    nodes: set[int] = set()
    for path in Path("/sys/devices/system/node").glob("node[0-9]*"):
        try:
            node = int(path.name.removeprefix("node"))
        except ValueError:
            continue
        total = numa_mem_total_mb(node)
        if total is None or total > 0:
            nodes.add(node)
    return nodes or {0}


def cpu_to_node_map() -> dict[int, int]:
    mapping: dict[int, int] = {}
    for path in Path("/sys/devices/system/node").glob("node[0-9]*"):
        try:
            node = int(path.name.removeprefix("node"))
        except ValueError:
            continue
        cpulist = read_text(path / "cpulist")
        if not cpulist:
            continue
        for cpu in expand_cpulist(cpulist):
            mapping[cpu] = node
    if not mapping:
        for cpu in available_cpus():
            mapping[cpu] = 0
    return mapping


def cpu_thread_siblings(cpu: int) -> set[int]:
    text = read_text(Path(f"/sys/devices/system/cpu/cpu{cpu}/topology/thread_siblings_list"))
    if text:
        return expand_cpulist(text)
    sibling = cpu + 1 if cpu % 2 == 0 else cpu - 1
    return {cpu, sibling}


def cpu_l3_key(cpu: int) -> str:
    base = Path(f"/sys/devices/system/cpu/cpu{cpu}/cache")
    if base.is_dir():
        for path in sorted(base.glob("index*")):
            level = read_text(path / "level")
            cache_type = read_text(path / "type")
            shared = read_text(path / "shared_cpu_list")
            if level == "3" and cache_type == "Unified" and shared:
                return shared
    return f"cpu:{cpu}"


def blue53_topology(mode: int) -> tuple[list[Lane], list[TailTrack], str]:
    if mode != 8:
        raise SystemExit(
            "blue-server-53 tested profile supports mode 8 only. "
            "Use --profile generic on a host with 16 memory-backed L3-distinct lanes."
        )
    lanes = [
        Lane("main0", "0", 0),
        Lane("main1", "16", 0),
        Lane("main2", "32", 0),
        Lane("main3", "48", 0),
        Lane("main4", "192", 2),
        Lane("main5", "208", 2),
        Lane("main6", "224", 2),
        Lane("main7", "240", 2),
    ]
    tails = [
        TailTrack("ports", tuple(SERIAL_PORT), "80", 0, False),
        TailTrack("dask", ("dask",), "72,74,76,78", 0, True),
        TailTrack("cimap", ("concurrent_imap",), "264,266,268,270", 2, True),
    ]
    return lanes, tails, "blue-server-53 stable 8-lane profile"


def local384_topology(mode: int) -> tuple[list[Lane], list[TailTrack], str]:
    all_lanes = [
        Lane("main0", "16", 0),
        Lane("main1", "32", 0),
        Lane("main2", "48", 0),
        Lane("main3", "64", 0),
        Lane("main4", "96", 1),
        Lane("main5", "112", 1),
        Lane("main6", "128", 1),
        Lane("main7", "144", 1),
        Lane("main8", "192", 2),
        Lane("main9", "208", 2),
        Lane("main10", "224", 2),
        Lane("main11", "240", 2),
        Lane("main12", "288", 3),
        Lane("main13", "304", 3),
        Lane("main14", "320", 3),
        Lane("main15", "336", 3),
    ]
    if mode not in {8, 16}:
        raise SystemExit(f"local384 supports mode 8 or 16, got {mode}")
    tails = [
        TailTrack("ports", tuple(SERIAL_PORT), "80", 0, False),
        TailTrack("dask", ("dask",), "160,162,164,166", 1, True),
        TailTrack("cimap", ("concurrent_imap",), "256,258,260,262", 2, True),
    ]
    return all_lanes[:mode], tails, f"local384 {mode}-lane profile"


def generic_topology(requested_mode: str) -> tuple[list[Lane], list[TailTrack], str]:
    avail = available_cpus()
    cpu_node = cpu_to_node_map()
    mem_nodes = memory_backed_nodes()
    groups: dict[str, list[int]] = {}
    for cpu in sorted(avail):
        node = cpu_node.get(cpu, 0)
        if node not in mem_nodes:
            continue
        siblings = cpu_thread_siblings(cpu)
        usable_siblings = siblings & avail
        if usable_siblings and cpu != min(usable_siblings):
            continue
        groups.setdefault(cpu_l3_key(cpu), []).append(cpu)

    by_node: dict[int, list[tuple[str, int]]] = {}
    for key, cpus in groups.items():
        cpu = min(cpus)
        by_node.setdefault(cpu_node.get(cpu, 0), []).append((key, cpu))
    for entries in by_node.values():
        entries.sort(key=lambda item: item[1])

    target = 16 if requested_mode in {"auto", "16"} else 8
    selected: list[tuple[str, int]] = []
    used_keys: set[str] = set()
    nodes = sorted(by_node)
    while len(selected) < target:
        progressed = False
        for node in nodes:
            entries = by_node[node]
            while entries and entries[0][0] in used_keys:
                entries.pop(0)
            if not entries:
                continue
            key, cpu = entries.pop(0)
            selected.append((key, cpu))
            used_keys.add(key)
            progressed = True
            if len(selected) == target:
                break
        if not progressed:
            break

    if requested_mode == "auto" and len(selected) < 16:
        return generic_topology("8")
    if len(selected) < target:
        raise SystemExit(
            f"Need {target} memory-backed L3-distinct lanes, found {len(selected)}. "
            "Use --mode 8 or run on a larger host."
        )

    lanes = [
        Lane(f"main{i}", str(cpu), cpu_node.get(cpu, 0))
        for i, (_, cpu) in enumerate(selected[:target])
    ]
    return lanes, [], f"generic {target}-lane memory-backed L3-distinct profile"


def choose_topology(profile: str, mode_arg: str) -> tuple[int, list[Lane], list[TailTrack], str]:
    profile = profile.lower()
    mode = mode_arg.lower()
    if profile == "auto":
        avail = available_cpus()
        if {0, 16, 32, 48, 192, 208, 224, 240}.issubset(avail):
            selected_mode = 8 if mode == "auto" else int(mode)
            lanes, tails, note = blue53_topology(selected_mode)
            return selected_mode, lanes, tails, note
        lanes, tails, note = generic_topology(mode)
        return len(lanes), lanes, tails, note
    if profile in {"blue53", "blue-server-53", "53"}:
        selected_mode = 8 if mode == "auto" else int(mode)
        lanes, tails, note = blue53_topology(selected_mode)
        return selected_mode, lanes, tails, note
    if profile in {"local384", "local"}:
        selected_mode = 16 if mode == "auto" else int(mode)
        lanes, tails, note = local384_topology(selected_mode)
        return selected_mode, lanes, tails, note
    if profile == "generic":
        lanes, tails, note = generic_topology(mode)
        return len(lanes), lanes, tails, note
    raise SystemExit(f"Unknown profile: {profile}")


def validate_topology(lanes: list[Lane], tails: list[TailTrack]) -> None:
    track_cpus: list[tuple[str, set[int]]] = [(lane.label, expand_cpulist(lane.bind)) for lane in lanes]
    track_cpus.extend((track.name, expand_cpulist(track.bind)) for track in tails)

    owners: dict[int, str] = {}
    for label, cpus in track_cpus:
        for cpu in cpus:
            if cpu in owners:
                raise SystemExit(f"CPU {cpu} assigned to both {owners[cpu]} and {label}")
            owners[cpu] = label

    all_cpus = set(owners)
    missing = all_cpus - available_cpus()
    if missing:
        raise SystemExit(f"assigned CPU(s) are not available to this process: {sorted(missing)}")

    for cpu in sorted(all_cpus):
        conflict = (cpu_thread_siblings(cpu) - {cpu}) & all_cpus
        if conflict:
            raise SystemExit(f"CPU {cpu} shares SMT sibling with assigned CPU(s): {sorted(conflict)}")

    for lane in lanes:
        total = numa_mem_total_mb(lane.node)
        if total == 0:
            raise SystemExit(f"lane {lane.label} uses memoryless NUMA node{lane.node}")
    for track in tails:
        total = numa_mem_total_mb(track.node)
        if total == 0:
            raise SystemExit(f"tail {track.name} uses memoryless NUMA node{track.node}")

    l3_owner: dict[str, str] = {}
    for label, cpus in track_cpus:
        for cpu in cpus:
            key = cpu_l3_key(cpu)
            owner = l3_owner.setdefault(key, label)
            if owner != label:
                raise SystemExit(f"L3 cluster {key} assigned to both {owner} and {label}")


def load_durations(path: str) -> dict[str, float]:
    durations: dict[str, float] = {}
    if not path or not os.path.exists(path):
        return durations
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                durations[parts[0]] = float(parts[1])
            except ValueError:
                pass
    return durations


def duration_lookup(durations: dict[str, float], bench: str) -> float:
    return durations.get(bench, FALLBACK_DURATIONS.get(bench, 20.0))


def lpt_assign(benches: list[str], lanes: list[Lane], durations: dict[str, float]) -> tuple[dict[str, list[str]], dict[str, float]]:
    queue = {lane.label: [] for lane in lanes}
    load = {lane.label: 0.0 for lane in lanes}
    for bench in sorted(benches, key=lambda name: (-duration_lookup(durations, name), name)):
        lane = min(lanes, key=lambda item: (load[item.label], item.bind))
        queue[lane.label].append(bench)
        load[lane.label] += duration_lookup(durations, bench)
    return queue, load


def fmt_seconds(seconds: float) -> str:
    return f"{int(seconds) // 60:02d}:{int(seconds) % 60:02d}"


def print_plan(
    mode: int,
    profile_note: str,
    lanes: list[Lane],
    tails: list[TailTrack],
    queue: dict[str, list[str]],
    load: dict[str, float],
    durations: dict[str, float],
) -> None:
    print("=" * 72)
    print(f"Parallel pyperformance plan: mode={mode} ({profile_note})")
    print("=" * 72)
    for lane in lanes:
        benches = queue[lane.label]
        print(f"[{lane.label:>6} | bind={lane.bind:<12} node{lane.node}] load={load[lane.label]:6.0f}s count={len(benches)}")
        for bench in benches:
            print(f"        {duration_lookup(durations, bench):6.0f}s {bench}")
    active_loads = [load[lane.label] for lane in lanes if queue[lane.label]]
    main_max = max(active_loads) if active_loads else 0.0
    main_min = min(active_loads) if active_loads else 0.0
    print("-" * 72)
    print(f"main benches={sum(len(v) for v in queue.values())} min={main_min:.0f}s max={main_max:.0f}s ({fmt_seconds(main_max)})")
    print("tail tracks:")
    tail_max = 0.0
    for track in tails:
        total = sum(duration_lookup(durations, bench) for bench in track.benches)
        tail_max = max(tail_max, total)
        kind = "multicore" if track.multicore else "serial"
        print(f"  [{track.name:<5}] bind={track.bind:<18} node{track.node} {kind:<9} ~{total:.0f}s {list(track.benches)}")
    if not tails:
        print("  (none; generic profile schedules every requested benchmark on main lanes)")
    active_cpus: set[int] = set()
    for lane in lanes:
        active_cpus.update(expand_cpulist(lane.bind))
    for track in tails:
        active_cpus.update(expand_cpulist(track.bind))
    print("-" * 72)
    print(f"estimated wall ~= max(main {fmt_seconds(main_max)}, tail {fmt_seconds(tail_max)})")
    print(f"peak active physical CPUs={len(active_cpus)} ({compact_cpulist(active_cpus)})")
    print("=" * 72)


_print_lock = threading.Lock()


def log(message: str) -> None:
    with _print_lock:
        print(message, flush=True)


def run_one(args: argparse.Namespace, bind: str, node: int, bench: str, outdir: Path, multicore: bool = False) -> None:
    env = dict(os.environ)
    env.update(JIT_ENV)
    if multicore:
        env.update(THREAD_LOCK_ENV)

    outjson = outdir / f"{bench}.json"
    outlog = outdir / f"{bench}.log"
    cmd = [
        "numactl",
        f"--physcpubind={bind}",
        f"--membind={node}",
        args.python,
        "-m",
        "pyperformance",
        "run",
        "-p",
        args.python,
        f"--affinity={bind}",
        "--warmup",
        str(args.warmup),
    ]
    if args.fast:
        cmd.append("--fast")
    cmd.extend(
        [
            f"--benchmarks={bench}",
            "--inherit-environ",
            args.inherit_environ,
            "-o",
            str(outjson),
        ]
    )
    if args.dry_run:
        log(f"[DRY-RUN] bind={bind} node{node} bench={bench}: {' '.join(cmd)}")
        return

    log(f">>> START bind={bind} node{node} bench={bench}")
    started = time.time()
    with outlog.open("w", encoding="utf-8") as handle:
        rc = subprocess.run(cmd, env=env, stdout=handle, stderr=subprocess.STDOUT).returncode
    elapsed = time.time() - started
    if rc == 0:
        log(f"OK bind={bind} node{node} bench={bench} elapsed={fmt_seconds(elapsed)}")
    else:
        log(f"FAIL bind={bind} node{node} bench={bench} rc={rc} log={outlog}")


def run_lane(args: argparse.Namespace, lane: Lane, benches: list[str], outdir: Path) -> None:
    for bench in benches:
        run_one(args, lane.bind, lane.node, bench, outdir)


def run_tail(args: argparse.Namespace, track: TailTrack, outdir: Path) -> None:
    for bench in track.benches:
        run_one(args, track.bind, track.node, bench, outdir, multicore=track.multicore)
    log(f"tail track complete: {track.name}")


def merge_results(args: argparse.Namespace, outdir: Path, output: Path) -> None:
    source = r'''
import glob
import os
import sys
from pyperf import BenchmarkSuite

outdir, merged = sys.argv[1], sys.argv[2]
files = [
    path for path in sorted(glob.glob(os.path.join(outdir, "*.json")))
    if os.path.abspath(path) != os.path.abspath(merged)
]
benchmarks = []
for path in files:
    try:
        benchmarks.extend(BenchmarkSuite.load(path).get_benchmarks())
    except Exception as exc:
        print(f"skip {path}: {exc}")
if benchmarks:
    BenchmarkSuite(benchmarks).dump(merged, replace=True)
    print(f"merged {len(benchmarks)} benchmarks -> {merged}")
else:
    print("no benchmark JSON files to merge")
'''
    subprocess.run([args.python, "-c", source, str(outdir), str(output)], check=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["auto", "8", "16"], default=os.environ.get("MODE", "auto"))
    parser.add_argument(
        "--profile",
        default=os.environ.get("PROFILE", "auto"),
        choices=["auto", "blue53", "blue-server-53", "53", "local384", "local", "generic"],
    )
    parser.add_argument("--python", default=os.environ.get("PYTHON", sys.executable))
    parser.add_argument("--benchmarks", default=os.environ.get("BENCHMARKS", ""))
    parser.add_argument("--output-dir", default=os.environ.get("WORK_DIR", ""))
    parser.add_argument("--output-name", default="")
    parser.add_argument("--tag", default=os.environ.get("TAG", ""))
    parser.add_argument("--durfile", default=os.environ.get("DURFILE", "dur.txt"))
    parser.add_argument("--warmup", "--warmups", dest="warmup", type=int, default=int(os.environ.get("WARMUP", "3")))
    parser.add_argument("--inherit-environ", default=os.environ.get("INHERIT_ENVIRON", DEFAULT_INHERIT))
    parser.add_argument("--fast", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--no-tail-tracks", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    mode, lanes, tails, note = choose_topology(args.profile, args.mode)
    if args.no_tail_tracks:
        tails = []
    validate_topology(lanes, tails)

    assert len(set(ALL_BENCHMARKS)) == len(ALL_BENCHMARKS), "duplicate benchmark in ALL_BENCHMARKS"
    if args.benchmarks:
        requested = [bench.strip() for bench in args.benchmarks.split(",") if bench.strip()]
        requested = list(dict.fromkeys(requested))
    else:
        requested = list(ALL_BENCHMARKS)

    known_tail_benches = {bench for track in tails for bench in track.benches}
    requested_set = set(requested)
    active_tails: list[TailTrack] = []
    for track in tails:
        selected = tuple(bench for bench in track.benches if bench in requested_set)
        if selected:
            active_tails.append(TailTrack(track.name, selected, track.bind, track.node, track.multicore))
    main_benches = [bench for bench in requested if bench not in known_tail_benches]

    durations = load_durations(args.durfile)
    queue, load = lpt_assign(main_benches, lanes, durations)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    outdir = Path(args.output_dir or f"results_parallel_{timestamp}")
    tag = f"-{args.tag}" if args.tag else ""
    output_name = args.output_name or f"pyperformance-parallel-mode{mode}-{timestamp}{tag}.json"
    merged = outdir / output_name

    print(f"python={args.python}")
    print(f"output_dir={outdir}")
    print(f"durfile={args.durfile} loaded={len(durations)}")
    print(f"requested={len(requested)} main={len(main_benches)} tail={sum(len(t.benches) for t in active_tails)}")
    print(f"inherit_environ={args.inherit_environ}")
    print_plan(mode, note, lanes, active_tails, queue, load, durations)

    if args.plan:
        return 0

    if args.dry_run:
        for lane in lanes:
            run_lane(args, lane, queue[lane.label], outdir)
        for track in active_tails:
            run_tail(args, track, outdir)
        print(f"[DRY-RUN] merged output -> {merged}")
        return 0

    outdir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    threads: list[threading.Thread] = []
    for lane in lanes:
        if not queue[lane.label]:
            continue
        thread = threading.Thread(target=run_lane, args=(args, lane, queue[lane.label], outdir), name=lane.label)
        thread.start()
        threads.append(thread)
    for track in active_tails:
        thread = threading.Thread(target=run_tail, args=(args, track, outdir), name=track.name)
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()

    elapsed = time.time() - started
    expected = len(main_benches) + sum(len(track.benches) for track in active_tails)
    jsons = [path for path in glob.glob(str(outdir / "*.json")) if Path(path).name != output_name]
    print(f"completed elapsed={fmt_seconds(elapsed)} jsons={len(jsons)} expected={expected}")
    if len(jsons) != expected:
        print("WARNING: output count mismatch; inspect per-benchmark logs")

    merge_results(args, outdir, merged)
    print("=" * 72)
    print(f"Done! merged result: {merged}")
    print(f"Compare: {args.python} -m pyperf compare_to <baseline>.json {merged} --table")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("Interrupted. You may need: pkill -f pyperformance", flush=True)
        raise SystemExit(130)
