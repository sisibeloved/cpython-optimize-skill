#!/usr/bin/env python3
"""Regression tests for pre-execution routing, using disposable local fixtures."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "hooks" / "validation-skill-router"


def run_router(command: str, cwd: Path) -> dict:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command, "cwd": str(cwd)},
    }
    env = os.environ.copy()
    env.pop("CPYTHON_OPTIMIZE_HOOK_ACK", None)
    result = subprocess.run(
        [str(ROUTER)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )
    return json.loads(result.stdout)["hookSpecificOutput"] if result.stdout else {}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def make_cpython_repo(base: Path) -> Path:
    repo = base / "cpython"
    for rel in ["Include", "Python", "Objects", "Lib/test", "cinderx/Jit"]:
        (repo / rel).mkdir(parents=True, exist_ok=True)
    (repo / "Include" / "patchlevel.h").write_text('#define PY_VERSION "3.14.3"\n')
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    return repo


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        repo = make_cpython_repo(base)
        outside = base / "plain-project"
        outside.mkdir()

        for command in [
            "python -m pyperformance run",
            "python -m pip install -e .",
            "./python -m test test_dict",
        ]:
            require(not run_router(command, outside), f"outside repo triggered: {command}")

        for command in [
            "git show --stat HEAD",
            "cat .venv/pyvenv.cfg",
            "rg -n 'pyperformance run' docs",
            "CPYTHON_OPTIMIZE_HOOK_ACK=1 python -m pip install -e .",
            "CPYTHON_OPTIMIZE_HOOK_ACK=1 python -m pyperformance run",
        ]:
            require(not run_router(command, repo), f"unexpected routing: {command}")

        context_cases = [
            ("./python -m test test_dict", "cpython-runtime-test-run"),
            (
                "CINDERX_LOCAL_RUN_LIBTEST=1 ./python ci_pipeline/run_gate.py --suite cinderx_local",
                "cpython-runtime-test-run",
            ),
            ("python -m pyperformance run -b example", "pyperformance-suite-run"),
            ("pyperformance run --benchmarks=example", "pyperformance-suite-run"),
            ("env FLAG=1 python -m pyperformance run -b example", "pyperformance-suite-run"),
            (
                "./python /tmp/pyperformance/data-files/benchmarks/bm_x/run_benchmark.py --worker",
                "pyperformance-worker-run",
            ),
            ("python -m pyperf compare_to baseline.json candidate.json", "pyperformance-result-compare"),
        ]
        for command, skill in context_cases:
            output = run_router(command, repo)
            require(output.get("hookEventName") == "PreToolUse", f"wrong event: {command}")
            require("permissionDecision" not in output, f"routine command blocked: {command}")
            context = output.get("additionalContext", "")
            require(skill in context, f"missing focused route: {command}")
            route_context = context.replace(
                "skills/using-cpython-optimize/references/pyperformance-env-contract.md", ""
            )
            require("using-cpython-optimize" not in route_context and "agents/" not in context,
                    f"forced orchestration: {command}")

        for command in [
            "python -m pyperformance run -b example",
            "./python /tmp/run_benchmark.py --worker",
        ]:
            context = run_router(command, repo)["additionalContext"]
            for evidence in [
                "pyperformance-env-contract.md", "pyvenv.cfg",
                "include-system-site-packages", ".pth", "--inherit-environ",
                "cinderx.is_initialized()", "cinderx.get_import_error()",
            ]:
                require(evidence in context, f"missing {evidence}: {command}")

        comparison = run_router(
            "python -m pyperf compare_to baseline.json candidate.json", repo
        )["additionalContext"]
        require("pyperformance-env-contract.md" not in comparison,
                "result comparison should read its own skill, not execution preflight")
        require("pyperformance-suite-run" not in comparison,
                "result comparison must not route to benchmark execution")

        deny_cases = [
            ("python -m pyperformance run", "pyperformance-suite-run"),
            ("./python -m test", "cpython-runtime-test-run"),
            ("./python ci_pipeline/run_gate.py --suite runtime", "cpython-runtime-test-run"),
            ("BENCHMARK=example ./scripts/test-benchmark.sh", "pyperformance-worker-run"),
            ("python -m pip install --no-build-isolation --no-deps -e .", "cinderx-env-validate"),
            ("pip install --verbose .", "cinderx-env-validate"),
            ("uv pip install --no-deps .", "cinderx-env-validate"),
            (
                "sed -i 's/include-system-site-packages = false/include-system-site-packages = true/' .venv/pyvenv.cfg",
                "cinderx-env-validate",
            ),
            # A low-cost first command must not hide a later full run or mutation.
            ("./python -m test test_dict && python -m pip install -e .", "cinderx-env-validate"),
            ("python -m pyperformance run -b example && python -m pyperformance run", "pyperformance-suite-run"),
            ("python -m pyperf compare_to a.json b.json ; python -m pip install -e .", "cinderx-env-validate"),
        ]
        for command, skill in deny_cases:
            output = run_router(command, repo)
            require(output.get("permissionDecision") == "deny", f"missing preflight: {command}")
            reason = output.get("permissionDecisionReason", "")
            require(skill in reason and "CPYTHON_OPTIMIZE_HOOK_ACK=1" in reason,
                    f"missing route or acknowledgement: {command}")
            require("agents/" not in reason, f"forced delegation: {command}")

    print("validation hook router validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
