---
name: cpython-cinderx-optimize-codex
description: Use when在 Codex 中执行本技能，需要将核心工作流映射到 Codex 的工具、权限模型和 skill 目录约定。
---

# Codex 薄包装

## 定位

Codex 只负责：
- 选择合适的核心工作流
- 使用 Codex 工具完成落地
- 遵守 Codex 的权限、目录和提交约定

## 约定

- 技能目录：`~/.codex/skills`
- 需要远端验证时，优先复用已有 SSH 别名与 `tmux`
- 编辑技能或仓库文件时，先跑最小验证，再重构

## 工具映射

- 代码修改：优先 `apply_patch`
- 远端执行：优先 `ssh <host>`
- 多命令读取：优先并行读取，再集中判断

## 下一步

回到核心层并按工作流执行：`../../core/SKILL.md`
