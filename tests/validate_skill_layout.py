#!/usr/bin/env python3

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if match is None:
        raise AssertionError("SKILL.md 缺少 frontmatter")
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip():
            continue
        key, _, value = line.partition(":")
        if not _:
            raise AssertionError(f"frontmatter 格式非法: {line!r}")
        fields[key.strip()] = value.strip()
    return fields


def assert_non_empty_markdown(path: Path) -> None:
    text = read_text(path).strip()
    if len(text) < 20:
        raise AssertionError(f"{path.relative_to(ROOT)} 内容过少")


def main() -> int:
    skill_path = ROOT / "SKILL.md"
    fields = parse_frontmatter(read_text(skill_path))
    assert set(fields) == {"name", "description"}, (
        "根 SKILL.md frontmatter 只能包含 name 和 description"
    )

    expected_dirs = [
        ROOT / "core",
        ROOT / "platforms" / "codex",
        ROOT / "platforms" / "claude-code",
        ROOT / "platforms" / "opencode",
        ROOT / "platforms" / "openclaw",
        ROOT / "docs" / "workflows",
        ROOT / "docs" / "playbooks",
        ROOT / "references",
    ]
    for path in expected_dirs:
        if not path.exists():
            raise AssertionError(f"缺少目录: {path.relative_to(ROOT)}")

    expected_files = [
        ROOT / "core" / "SKILL.md",
        ROOT / "platforms" / "codex" / "SKILL.md",
        ROOT / "platforms" / "claude-code" / "SKILL.md",
        ROOT / "platforms" / "opencode" / "SKILL.md",
        ROOT / "platforms" / "openclaw" / "SKILL.md",
        ROOT / "docs" / "workflows" / "ssh-connection.md",
        ROOT / "docs" / "workflows" / "build-and-install.md",
        ROOT / "docs" / "workflows" / "pyperformance-test.md",
        ROOT / "docs" / "workflows" / "docker-runtime.md",
        ROOT / "docs" / "workflows" / "documentation.md",
        ROOT / "docs" / "workflows" / "case-analysis.md",
        ROOT / "docs" / "playbooks" / "entry-decision-table.md",
        ROOT / "docs" / "playbooks" / "faq.md",
        ROOT / "references" / "commands" / "README.md",
        ROOT / "references" / "commands" / "pyperformance-run-realenv.sh",
        ROOT / "references" / "commands" / "run-benchmark-worker-realenv.sh",
        ROOT / "references" / "templates" / "docker" / "README.md",
        ROOT / "references" / "templates" / "docker" / "cpython-baseline" / "README.md",
        ROOT / "references" / "templates" / "docker" / "cpython-baseline" / "docker-compose.yml",
        ROOT / "references" / "templates" / "docker" / "cpython-baseline" / "Dockerfile",
        ROOT / "references" / "templates" / "docker" / "cpython-baseline" / "project-readme.md",
        ROOT / "references" / "templates" / "docker" / "cinderx-test" / "README.md",
        ROOT / "references" / "templates" / "docker" / "cinderx-test" / "docker-compose.yml",
        ROOT / "references" / "templates" / "docker" / "cinderx-test" / "project-readme.md",
        ROOT / "scripts" / "README.md",
        ROOT / "scripts" / "docker" / "cinderx-test" / "README.md",
        ROOT / "scripts" / "docker" / "cinderx-test" / "benchmark_harness.py",
        ROOT / "scripts" / "docker" / "cinderx-test" / "setup.sh",
        ROOT / "scripts" / "docker" / "cinderx-test" / "test-benchmark.sh",
        ROOT / "scripts" / "docker" / "cinderx-test" / "smoke.sh",
        ROOT / "tests" / "pressure-scenarios.md",
        ROOT / "tests" / "dynamic-pressure-review.md",
        ROOT / "tests" / "validate_pressure_scenarios.py",
    ]
    for path in expected_files:
        if not path.exists():
            raise AssertionError(f"缺少文件: {path.relative_to(ROOT)}")
        assert_non_empty_markdown(path)

    root_skill = read_text(skill_path)
    if "core/SKILL.md" not in root_skill:
        raise AssertionError("根 SKILL.md 应该明确指向核心层入口")

    pyperf_workflow = read_text(ROOT / "docs" / "workflows" / "pyperformance-test.md")
    if "references/commands/pyperformance-run-realenv.sh" not in pyperf_workflow:
        raise AssertionError("pyperformance 工作流应链接真实 run 命令模板")
    if "references/commands/run-benchmark-worker-realenv.sh" not in pyperf_workflow:
        raise AssertionError("pyperformance 工作流应链接真实 worker 命令模板")

    docker_workflow = read_text(ROOT / "docs" / "workflows" / "docker-runtime.md")
    for relpath in [
        "scripts/docker/cinderx-test/setup.sh",
        "scripts/docker/cinderx-test/test-benchmark.sh",
        "scripts/docker/cinderx-test/smoke.sh",
        "scripts/docker/cinderx-test/benchmark_harness.py",
        "references/templates/docker/cpython-baseline/",
        "references/templates/docker/cinderx-test/",
    ]:
        if relpath not in docker_workflow:
            raise AssertionError(f"docker 工作流应链接 {relpath}")

    core_skill = read_text(ROOT / "core" / "SKILL.md")
    if "docs/playbooks/entry-decision-table.md" not in core_skill:
        raise AssertionError("core skill 应链接入口决策表")

    print("layout validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
