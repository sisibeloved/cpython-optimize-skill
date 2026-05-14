#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import os
import sys
import tomllib
from pathlib import Path


def benchmark_config_root() -> Path:
    env_root = os.environ.get("BENCHMARK_CONFIG_ROOT")
    if env_root:
        return Path(env_root)
    return Path(__file__).resolve().parent.parent / "configs"


def load_benchmark_config(config_root: Path | str, benchmark_name: str) -> dict:
    config_path = Path(config_root) / benchmark_name / "benchmark.toml"
    with config_path.open("rb") as fp:
        return tomllib.load(fp)


def benchmark_downloads(
    benchmark_name: str,
    config_root: Path | str = benchmark_config_root(),
) -> tuple[tuple[str, str], ...]:
    config = load_benchmark_config(config_root, benchmark_name)
    return tuple(
        (entry["target"], entry["url"])
        for entry in config.get("downloads", [])
    )


def pyperformance_benchmark_name(
    benchmark_name: str,
    config_root: Path | str = benchmark_config_root(),
) -> str:
    config = load_benchmark_config(config_root, benchmark_name)
    return config["pyperformance_benchmark"]


def benchmark_prepare_mode(
    benchmark_name: str,
    config_root: Path | str = benchmark_config_root(),
) -> str:
    config = load_benchmark_config(config_root, benchmark_name)
    return config["prepare"]["mode"]


def default_run_excludes(
    benchmark_name: str,
    config_root: Path | str = benchmark_config_root(),
) -> tuple[str, ...]:
    config = load_benchmark_config(config_root, benchmark_name)
    return tuple(config.get("run", {}).get("default_excludes", []))


def benchmark_extra_env(
    benchmark_name: str,
    config_root: Path | str = benchmark_config_root(),
) -> dict[str, str]:
    config = load_benchmark_config(config_root, benchmark_name)
    return dict(config.get("run", {}).get("extra_env", {}))


def resolve_bench_args(module, config: dict) -> tuple[object, ...]:
    args_config = config.get("args", {})
    mode = args_config.get("mode")

    if mode == "fixed_tuple":
        return tuple(args_config.get("values", []))

    if mode == "regex_compile_capture":
        capture_func_name = args_config["capture_func"]
        capture_func = getattr(module, capture_func_name)
        regexes = capture_func()
        return (args_config["fixed_int"], regexes)

    raise ValueError(f"unsupported args.mode: {mode!r}")


def resolve_benchmark_metadata(
    name: str,
    config_root: Path | str = benchmark_config_root(),
) -> dict:
    return load_benchmark_config(config_root, name)


def benchmark_root() -> Path:
    return Path(os.environ.get("BENCHMARK_ROOT", "/root/benchmarks"))


def pyperformance_source_root() -> Path:
    return Path(os.environ.get("PYPERFORMANCE_ROOT", "/pyperformance"))


def pyperformance_hook_root() -> Path:
    env_root = os.environ.get("PYPERFORMANCE_HOOK_ROOT")
    if env_root:
        return Path(env_root)

    container_path = Path("/pyperf_env_hook")
    if container_path.exists():
        return container_path

    host_repo_path = cinderx_source_root() / "scripts" / "arm" / "pyperf_env_hook"
    if host_repo_path.exists():
        return host_repo_path

    return container_path


def pyperformance_benchmark_filter(
    selection: str,
    config_root: Path | str = benchmark_config_root(),
) -> str:
    tokens = [token.strip() for token in selection.split(",") if token.strip()]
    mapped: list[str] = []

    for token in tokens:
        negative = token.startswith("-")
        name = token[1:] if negative else token
        if name in {"all", "<default>"}:
            mapped_name = name
        else:
            try:
                mapped_name = pyperformance_benchmark_name(name, config_root=config_root)
            except FileNotFoundError:
                mapped_name = name
        mapped.append(f"-{mapped_name}" if negative else mapped_name)

    return ",".join(mapped) if mapped else selection


def config_backed_selection_name(
    selection: str,
    config_root: Path | str = benchmark_config_root(),
) -> str | None:
    tokens = [token.strip() for token in selection.split(",") if token.strip()]
    if len(tokens) != 1:
        return None

    token = tokens[0]
    if token.startswith("-") or token in {"all", "<default>"}:
        return None

    try:
        resolve_benchmark_metadata(token, config_root)
    except FileNotFoundError:
        return None
    return token


def benchmark_module_path(
    root: Path | str,
    name: str,
    config_root: Path | str = benchmark_config_root(),
) -> Path:
    config = resolve_benchmark_metadata(name, config_root)
    return Path(root) / config["module_dir"] / config["entry_file"]


def benchmark_module_dir(
    root: Path | str,
    name: str,
    config_root: Path | str = benchmark_config_root(),
) -> Path:
    return benchmark_module_path(root, name, config_root=config_root).parent


def load_benchmark(
    root: Path | str,
    name: str,
    config_root: Path | str = benchmark_config_root(),
):
    config = resolve_benchmark_metadata(name, config_root)
    module_path = benchmark_module_path(root, name, config_root=config_root)
    import_spec = importlib.util.spec_from_file_location(config["module_dir"], module_path)
    if import_spec is None or import_spec.loader is None:
        raise RuntimeError(f"failed to load benchmark module from {module_path}")
    module = importlib.util.module_from_spec(import_spec)
    sys.path.insert(0, str(module_path.parent))
    try:
        import_spec.loader.exec_module(module)
    finally:
        try:
            sys.path.remove(str(module_path.parent))
        except ValueError:
            pass
    bench = getattr(module, config["bench_func"])
    return module, bench


def pyperf_shim_code() -> str:
    return (
        "import time\n"
        "perf_counter = time.perf_counter\n"
        "class Runner:\n"
        "    def __init__(self, *a, **k): pass\n"
        "    def bench_time_func(self, *a, **k): pass\n"
    )


def cinderx_wheel_glob() -> Path:
    return Path(os.environ.get("CINDERX_WHEEL_GLOB", "/dist/cinderx-*-linux_aarch64.whl"))


def cinderx_source_root() -> Path:
    return Path(os.environ.get("CINDERX_SOURCE_ROOT", "/cinderx"))


def default_opt_env_file(name: str) -> Path | None:
    config_name = config_backed_selection_name(name)
    if config_name is None:
        return None
    return benchmark_config_root() / config_name / "stable.env"


def results_root() -> Path:
    return Path(os.environ.get("RESULTS_ROOT", "/results"))


def load_opt_env_file(path: Path | str | None) -> dict[str, str]:
    if path is None:
        return {}
    env_path = Path(path)
    if not env_path.exists():
        return {}
    env: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, sep, value = line.partition("=")
        if not sep or not key:
            raise ValueError(f"invalid env line in {env_path}: {raw_line!r}")
        env[key] = value
    return env


def opt_config_name(path: Path | str | None, enable_optimization: bool) -> str:
    if not enable_optimization:
        return "baseline"
    if path is None:
        return "stable"
    return Path(path).stem


def comparison_results_path(results_root: Path | str, benchmark: str, config_name: str) -> Path:
    return Path(results_root) / benchmark / config_name / "comparison.json"
