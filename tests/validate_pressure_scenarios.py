#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(text: str, needle: str, context: str) -> None:
    if needle not in text:
        raise AssertionError(f"{context} 缺少关键信号: {needle}")


def main() -> int:
    pyperf = read(ROOT / "docs" / "workflows" / "pyperformance-test.md")
    docker = read(ROOT / "docs" / "workflows" / "docker-runtime.md")
    docs = read(ROOT / "docs" / "workflows" / "documentation.md")
    case = read(ROOT / "docs" / "workflows" / "case-analysis.md")
    triage = read(ROOT / "docs" / "playbooks" / "pyperformance-crash-triage.md")
    decision = read(ROOT / "docs" / "playbooks" / "entry-decision-table.md")
    faq = read(ROOT / "docs" / "playbooks" / "faq.md")
    scenarios = read(ROOT / "tests" / "pressure-scenarios.md")

    require(scenarios, "场景 1", "pressure scenarios")
    require(scenarios, "场景 6", "pressure scenarios")
    require(scenarios, "场景 7", "pressure scenarios")
    require(scenarios, "场景 8", "pressure scenarios")

    for needle in [
        "run_benchmark.py",
        "HIR dump",
        "worker",
        "bench_command",
        "sitecustomize",
    ]:
        require(pyperf, needle, "pyperformance workflow")

    for needle in [
        "双线结构",
        "cpython-baseline",
        "cinderx-test",
        "长连接交互终端",
        "docker exec",
    ]:
        require(docker, needle, "docker workflow")

    for needle in [
        "run_benchmark.py",
        "python -m pyperformance run",
        "cpython-baseline",
        "cinderx-test",
        "HIR dump",
        "长连接交互 shell",
        "docker exec",
    ]:
        require(decision, needle, "entry decision table")

    for needle in [
        "功能，不看性能",
        "run_benchmark.py --worker",
        "driver / manager / worker",
        "Kunpeng 宿主机",
        "docker exec",
    ]:
        require(faq, needle, "faq")

    review = read(ROOT / "tests" / "dynamic-pressure-review.md")
    for needle in [
        "双线区分",
        "长连接交互终端",
        "正式对照",
    ]:
        require(review, needle, "dynamic pressure review")

    for needle in [
        "背景",
        "复现命令",
        "证据链",
        "根因",
        "修复方法",
        "回归结果",
    ]:
        require(docs, needle, "documentation workflow")

    for needle in [
        "HIR",
        "LIR",
        "uop",
        "机器码",
    ]:
        require(case, needle, "case analysis workflow")

    for needle in [
        "LD_LIBRARY_PATH",
        "compile storm",
        "SIGSEGV",
    ]:
        require(triage, needle, "crash triage playbook")

    print("pressure scenario validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
