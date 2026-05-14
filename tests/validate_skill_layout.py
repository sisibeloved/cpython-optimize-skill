#!/usr/bin/env python3

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"

# 期望的顶层结构：目录/文件名 -> 类型（dir/file）
TOP_LEVEL_LAYOUT = {
    ".claude-plugin": "dir",
    ".codex-plugin": "dir",
    "hooks": "dir",
    "skills": "dir",
    "tests": "dir",
    "package.json": "file",
    "CHANGELOG.md": "file",
    ".gitignore": "file",
}

# hooks/ 内结构
HOOKS_LAYOUT = {
    "hooks.json": "file",
    "session-start": "file",
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


def main() -> int:
    # 1. 顶层目录结构
    validate_directory_layout(ROOT, TOP_LEVEL_LAYOUT, "")

    # 2. hooks 结构
    validate_directory_layout(ROOT / "hooks", HOOKS_LAYOUT, "hooks/ ")

    # 3. plugin.json 字段
    validate_plugin_json(ROOT / ".claude-plugin" / "plugin.json")
    validate_plugin_json(ROOT / ".codex-plugin" / "plugin.json")

    # 4. skills/ 下每个子目录都是合法技能
    if not SKILLS_DIR.is_dir():
        raise AssertionError("缺少 skills/ 目录")

    skill_dirs = [p for p in SKILLS_DIR.iterdir() if p.is_dir()]
    if not skill_dirs:
        raise AssertionError("skills/ 下没有子技能")

    for skill_dir in skill_dirs:
        validate_skill_dir(skill_dir)

    print("layout validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
