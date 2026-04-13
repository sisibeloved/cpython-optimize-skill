---
name: cpython-cinderx-optimize
description: Use when开展 CPython/CinderX 性能优化、远程基准测试、JIT/非JIT 用例分析，且需要复用个人工作流、平台包装和结构化产物约定。
---

# CPython/CinderX 优化技能

这是一个面向个人工作流的 `v0.3.0` 技能仓库，当前版本以 **CinderX 优先** 的视角组织。

本仓库采用两层结构：
- 核心层：见 `core/SKILL.md`
- 平台薄包装：见 `platforms/`

## 使用方式

1. 先进入核心层：`core/SKILL.md`
2. 再根据当前 Agent 选择平台包装：
   - Codex：`platforms/codex/SKILL.md`
   - Claude Code：`platforms/claude-code/SKILL.md`
   - OpenCode：`platforms/opencode/SKILL.md`
   - OpenClaw：`platforms/openclaw/SKILL.md`
3. 版本变更见：`CHANGELOG.md`

## 当前版本范围

本版聚焦以下工作流：
- 环境获取：SSH 配置、`tmux` 会话复用、远端会话管理
- CPython/CinderX 编译：环境隔离、强制覆盖安装、远端构建
- `pyperformance` 测试：命令、环境变量、进程模型、单用例/全量入口
- 运行时环境隔离：Docker 创建、挂载、镜像与容器复用
- 文档：目录、命名和实验记录格式
- 用例分析：
  - JIT：`HIR -> LIR -> 机器码`
  - 非 JIT：`字节码 -> uop -> 机器码`

## v0.3.0 增量

- 重构为“核心层 + 四平台薄包装”
- 补齐 `pyperformance`、Docker、文档、用例分析工作流
- 收录真实环境命令模板
- 固化 Docker 双线：
  - `cpython-baseline`
  - `cinderx-test`
- 迁入已验证的 `cinderx-test` 脚本
- 增加 FAQ、入口决策表、静态/动态 pressure test
- 补强远程 `rsync` 同步、容器内 `pip` 镜像源、性能口径定义和 HIR 分析顺序

## 原则

- 不在本地盲目编译，优先在目标服务器验证
- 不污染上游分支，测试性改动默认可丢弃
- 先拿可复现证据，再下根因结论
- 用结构化产物沉淀实验结果，避免只留口头结论
