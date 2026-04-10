---
name: cpython-optimization-shared
description: 面向 Windows、macOS 和 Linux 的多 Agent 协作 CPython/CinderX 性能优化共享工作流、脚本与规范。
tags: [cpython, cinderx, performance, benchmarking, multi-agent, cross-platform]
compatible_agents: [codex, claude-code, opencode, openclaw]
compatible_environments: [linux, macos, windows-wsl]
---

# CPython 优化共享技能

## 目标
该技能用于标准化 CPython/CinderX 优化中的重复性任务：
- 为本地开发快速完成可运行基准测试的环境初始化。
- 可复现实验的基准测试执行，并产出可机读的结果文件。
- 安全地执行分支间对比，不污染上游分支。
- 统一指标解析与报告格式，使不同 Agent 的输出可比较。

该仓库旨在通过 GitHub 在多个协作 Agent 之间复用。

## 核心原则
1. 不要把临时的基准测试改动提交到上游分支。
2. 保持本地分支与 worktree 干净且可丢弃。
3. 保证测试的隔离性，包括分支隔离、环境隔离、产物隔离、结果隔离。
4. 使用结构化 JSON 输出，确保各 Agent 可相互消费结果。

## 背景

分析CPython/CinderX在Arm（Kunpeng）服务器上的性能瓶颈、与AMD（9654、9755）的性能差异，修改CPython/CinderX达到优化效果。

## 前置条件

前置条件中部分信息需要用户提供，需要询问用户以确保流程可用。

### 环境

- 不要在本地编译（Linux除外）
- 确认是Arm（Kunpeng）的服务器还是x86（AMD）的服务器
- 不管在远程服务器还是本地，必须启动Docker容器进行环境隔离

### CPython

- 源码地址
- Git Tag为3.14.3
- `gcc == 14.2.0`

### CinderX

- 源码地址正常应为会话所在仓库
- `gcc == 14.2.0`
- `Python == 3.14.3`
- `pyperformance == 1.14.0`

### 环境

## 目录结构
- `SKILL.md`：该技能的入口与执行约定。
- `docs/`：快速开始、工作流指南、互操作与故障排查。
- `references/`：可复用模板、配置与 patch 示例。
- `scripts/`：可复用脚本。
