#!/usr/bin/env python3

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"
AGENTS_DIR = ROOT / "agents"

REQUIRED_SKILLS = {
    "using-cpython-optimize",
    "cinderx-env-validate",
    "cinderx-env-clean",
    "cinderx-env-bootstrap",
    "cinderx-remote-lab-ops",
    "cinderx-ab-run-slot",
    "cpython-runtime-test-run",
    "cinderx-smoke-check",
    "pyperformance-worker-run",
    "pyperformance-suite-run",
    "pyperformance-result-compare",
    "cinderx-gdb-core-triage",
    "cinderx-hir-dump",
    "cinderx-jit-entry-check",
    "cinderx-hir-lir-analyze",
    "cinderx-interpreter-case-analyze",
    "cinderx-isa-microarch-compare",
    "cinderx-optimization-report",
    "cinderx-jit-review",
    "cinderx-parallel-pyperformance",
    "validation-strategy",
    "design-documentation",
    "workflow-remote-cinderx-lab-setup",
    "workflow-cinderx-crash-triage",
    "workflow-pyperformance-regression",
    "workflow-jit-optimization-analysis",
    "workflow-cross-platform-delta-triage",
    "workflow-feature-driven-optimization",
    "workflow-platform-differential-discovery",
    "workflow-platform-differential-discovery-deepdive",
    "cinderx-evidence-table",
}

REMOVED_SKILLS = {
    "remote-environment",
    "remote-workspace",
    "command-observability",
    "docker-runtime",
    "docker-lab-runtime",
    "cpython-build",
    "cpython-build-install",
    "test-execution",
    "pyperformance-test",
    "pyperformance-benchmark",
    "benchmark-result-analysis",
    "native-crash-debugging",
    "cinderx-analysis",
    "cinderx-jit-analysis",
    "platform-differential-analysis",
    "experiment-documentation",
}

REQUIRED_AGENTS = {
    "cinderx-orchestrator.md",
    "cinderx-environment-verifier.md",
    "pyperformance-baseline-runner.md",
    "pyperformance-candidate-runner.md",
    "pyperformance-benchmark-analyst.md",
    "cinderx-crash-triager.md",
    "cinderx-jit-analyst.md",
    "cinderx-platform-analyst.md",
    "cinderx-evidence-analyst.md",
}

# 期望的顶层结构：目录/文件名 -> 类型（dir/file）
TOP_LEVEL_LAYOUT = {
    ".claude-plugin": "dir",
    ".codex-plugin": "dir",
    "hooks": "dir",
    "agents": "dir",
    "skills": "dir",
    "tests": "dir",
    "package.json": "file",
    "CHANGELOG.md": "file",
}

# hooks/ 内结构
HOOKS_LAYOUT = {
    "hooks.json": "file",
    "runtime-skill-router": "file",
    "validation-skill-router": "file",
}

# plugin.json 内必须包含的 key
PLUGIN_REQUIRED_KEYS = {"name", "version", "skills"}

# SKILL.md frontmatter 必须包含的 key
FRONTMATTER_REQUIRED_KEYS = {"name", "description"}


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


def validate_directory_layout(base: Path, layout: dict[str, str], context: str) -> None:
    for name, expected_type in layout.items():
        path = base / name
        rel = path.relative_to(ROOT)
        if expected_type == "dir" and not path.is_dir():
            raise AssertionError(f"{context}缺少目录: {rel}")
        if expected_type == "file" and not path.is_file():
            raise AssertionError(f"{context}缺少文件: {rel}")


def validate_plugin_json(path: Path) -> None:
    import json
    data = json.loads(read_text(path))
    missing = PLUGIN_REQUIRED_KEYS - set(data.keys())
    if missing:
        raise AssertionError(f"{path.relative_to(ROOT)} 缺少字段: {missing}")


def validate_skill_dir(path: Path) -> None:
    skill_md = path / "SKILL.md"
    if not skill_md.is_file():
        raise AssertionError(f"缺少技能入口: {skill_md.relative_to(ROOT)}")

    fields = parse_frontmatter(read_text(skill_md))
    missing = FRONTMATTER_REQUIRED_KEYS - set(fields.keys())
    if missing:
        raise AssertionError(f"{skill_md.relative_to(ROOT)} 缺少 frontmatter 字段: {missing}")

    # 子目录只能是 references、scripts、templates 中的若干个（或无）
    allowed_subdirs = {"references", "scripts", "templates"}
    for child in path.iterdir():
        if child.is_dir() and child.name not in allowed_subdirs:
            raise AssertionError(f"技能目录含非标准子目录: {child.relative_to(ROOT)}")


def validate_agent_docs() -> None:
    agent_docs = sorted(AGENTS_DIR.glob("*.md"))
    if not agent_docs:
        raise AssertionError("agents/ 下没有 Agent 文档")

    agent_names = {path.name for path in agent_docs}
    missing = REQUIRED_AGENTS - agent_names
    if missing:
        raise AssertionError(f"agents/ 缺少 CPython/CinderX 专业 Agent: {sorted(missing)}")

    forbidden = ["## Focus", "## Use When", "## Output", "Return:", "Do not "]
    required = ["## 职责", "## 适用场景", "## 可调用技能", "## 反问 Gate", "## 输出要求"]
    for path in agent_docs:
        text = read_text(path)
        for needle in required:
            if needle not in text:
                raise AssertionError(f"{path.relative_to(ROOT)} 缺少中文章节: {needle}")
        for needle in forbidden:
            if needle in text:
                raise AssertionError(f"{path.relative_to(ROOT)} 仍包含英文模板: {needle}")


def validate_hooks() -> None:
    hooks_dir = ROOT / "hooks"
    hooks_json = read_text(hooks_dir / "hooks.json")
    router = hooks_dir / "runtime-skill-router"
    validation_router = hooks_dir / "validation-skill-router"
    router_text = read_text(router)
    validation_router_text = read_text(validation_router)

    if (hooks_dir / "session-start").exists():
        raise AssertionError("hooks/session-start 已废弃，不能继续全量注入入口技能")

    for needle in [
        "PreToolUse",
        "PostToolUse",
        "Bash",
        "runtime-skill-router",
        "validation-skill-router",
    ]:
        if needle not in hooks_json:
            raise AssertionError(f"hooks.json 缺少运行中路由信号: {needle}")

    if "SessionStart" in hooks_json:
        raise AssertionError("hooks.json 不应再使用 SessionStart 全量注入")

    for needle in [
        "SIGSEGV",
        "Segmentation fault",
        "exit 139",
        "EXIT_STATUS",
        "core dump",
        "additionalContext",
        "workflow-cinderx-crash-triage",
        "cinderx-gdb-core-triage",
        "gdb bt full",
        "validation-strategy",
        "cinderx-remote-lab-ops",
        "extract_command",
        "extract_signal_text",
        "is_observation_command",
        "is_observation_output",
    ]:
        if needle not in router_text:
            raise AssertionError(f"runtime-skill-router 缺少关键信号: {needle}")

    if not os.access(router, os.X_OK):
        raise AssertionError("runtime-skill-router 需要可执行权限")

    for needle in [
        "PreToolUse",
        "permissionDecision",
        "additionalContext",
        "CPYTHON_OPTIMIZE_HOOK_ACK",
        "using-cpython-optimize",
        "validation-strategy",
        "cinderx-env-validate",
        "pyperformance",
        "pyperf",
        "ci_pipeline/run_gate.py",
        "cpython-runtime-test-run",
        "pyperformance-worker-run",
        "pyperformance-result-compare",
        "pip install",
        "Include",
        "patchlevel.h",
    ]:
        if needle not in validation_router_text:
            raise AssertionError(f"validation-skill-router 缺少关键信号: {needle}")

    if not os.access(validation_router, os.X_OK):
        raise AssertionError("validation-skill-router 需要可执行权限")


def validate_template_contents() -> None:
    cpython_baseline_dockerfile = (
        SKILLS_DIR
        / "cinderx-env-bootstrap"
        / "templates"
        / "cpython-baseline"
        / "Dockerfile"
    )
    dockerfile_text = read_text(cpython_baseline_dockerfile)

    if "gcc-toolset-14-gcc-c++" not in dockerfile_text:
        raise AssertionError("cpython-baseline Dockerfile 缺少 openEuler GCC 14 C++ 正确包名: gcc-toolset-14-gcc-c++")
    if "gcc-toolset-14-c++*" in dockerfile_text:
        raise AssertionError("cpython-baseline Dockerfile 仍包含错误包名模板: gcc-toolset-14-c++*")
    if "--enable-shared" in dockerfile_text:
        raise AssertionError("cpython-baseline Dockerfile 不应构建共享 libpython，否则 AArch64 RuntimeTests TLS offset 探测会落到 PLT/TLSDESC 形态")

    env_validate_text = read_text(SKILLS_DIR / "cinderx-env-validate" / "SKILL.md")
    for needle in [
        "Py_ENABLE_SHARED",
        "_Python_LIBRARY_RELEASE",
        "TLSDESC",
        "DetectsThreadStateOffset",
    ]:
        if needle not in env_validate_text:
            raise AssertionError(f"cinderx-env-validate 缺少 AArch64 TLS 环境漂移信号: {needle}")

    setup_sh = SKILLS_DIR / "cinderx-env-bootstrap" / "scripts" / "setup.sh"
    setup_text = read_text(setup_sh)
    if "repo.huaweicloud.com/repository/pypi/simple" not in setup_text:
        raise AssertionError("cinderx-env-bootstrap setup.sh 默认 pip 镜像源应为华为云")
    if "mirrors.aliyun.com" in setup_text or "aliyun" in setup_text.lower():
        raise AssertionError("cinderx-env-bootstrap setup.sh 不应再默认使用阿里云 pip 镜像源")


def main() -> int:
    # 1. 顶层目录结构
    validate_directory_layout(ROOT, TOP_LEVEL_LAYOUT, "")

    # 2. hooks 结构
    validate_directory_layout(ROOT / "hooks", HOOKS_LAYOUT, "hooks/ ")
    validate_hooks()

    # 3. plugin.json 字段
    validate_plugin_json(ROOT / ".claude-plugin" / "plugin.json")
    validate_plugin_json(ROOT / ".codex-plugin" / "plugin.json")

    # 4. skills/ 下每个子目录都是合法技能
    if not SKILLS_DIR.is_dir():
        raise AssertionError("缺少 skills/ 目录")

    skill_dirs = [p for p in SKILLS_DIR.iterdir() if p.is_dir()]
    if not skill_dirs:
        raise AssertionError("skills/ 下没有子技能")

    skill_names = {p.name for p in skill_dirs}
    missing = REQUIRED_SKILLS - skill_names
    if missing:
        raise AssertionError(f"skills/ 缺少新原子层或 workflow: {sorted(missing)}")

    removed = REMOVED_SKILLS & skill_names
    if removed:
        raise AssertionError(f"skills/ 仍保留旧原子 skill 边界: {sorted(removed)}")

    for skill_dir in skill_dirs:
        validate_skill_dir(skill_dir)

    # 5. agents/ 角色文档应保持中文模板
    validate_agent_docs()

    # 6. 模板内容不能包含已知坏包名或坏命令
    validate_template_contents()

    print("layout validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
