---
title: "refactor: Transform monolithic skill into compound skill repository"
type: refactor
status: active
date: 2026-05-13
---

# Refactor: Transform into Compound Skill Repository

## Overview

将 cpython-optimize-skill 从单体技能仓库重构为复合技能仓库，参照 superpowers 和 compound-engineering 的架构模式。每个子技能自包含（SKILL.md + 脚本 + 模板），通过 Skill 工具互相调用。

---

## Problem Frame

当前仓库存在以下问题：

1. **发现困难** — agent 需要主动读 SKILL.md 才知道有这个技能，无法通过 Skill 工具自动发现
2. **粒度过粗** — 所有工作流塞在一个大文档中，agent 无法按需加载
3. **无自动注入** — 没有 SessionStart hook，技能内容不会在新会话开始时自动进入上下文
4. **资源分散** — scripts/ 和 references/ 在仓库根目录，与技能描述分离，不原子
5. **docs/ 定位不清** — 既承载仓库文档又承载技能内容，职责混杂

---

## Requirements Trace

- R1. 仓库被 Claude Code 识别为合法插件（`.claude-plugin/plugin.json`）
- R2. 每个子技能自包含：SKILL.md + 专属脚本 + 专属模板，一个目录就是一个完整技能
- R3. 提供 `using-cpython-optimize` 引导技能，在新会话开始时自动注入
- R4. 通过 SessionStart hook 实现自动发现和上下文注入
- R5. 保持现有内容不丢失，只做结构迁移
- R6. 支持 Codex 插件注册（`.codex-plugin/plugin.json`）
- R7. `docs/` 只承载仓库级文档（开发、计划、设计），不再承载技能内容
- R8. 子技能间通过 Skill 工具互相调用，不依赖共享文件

---

## Scope Boundaries

- 不重写技能内容，只做结构迁移和 frontmatter 标准化
- 不实现 marketplace 发布（后续独立任务）
- 不实现 Cursor/OpenCode/Gemini 平台适配（后续按需扩展）
- 旧的 `docs/workflows/`、`references/`、`scripts/` 在迁移完成后移除（内容已分散到子技能目录中）

---

## Context & Research

### Relevant Code and Patterns

**superpowers 架构：**
- 每个子技能目录自包含（`skills/<name>/SKILL.md` + 可选 `scripts/`、`references/`）
- SessionStart hook 注入引导技能
- `.claude-plugin/plugin.json` 的 `skills` 字段指向 `./skills/`

**compound-engineering 架构：**
- 同样自包含模式：每个技能有自己的 `references/` 和 `scripts/`
- 30+ 独立子技能，互相通过 Skill 工具调用

**当前仓库内容分布：**

| 当前路径 | 归属子技能 |
|---------|-----------|
| `docs/workflows/build-and-install.md` | `cpython-build` |
| `docs/workflows/pyperformance-test.md` | `pyperformance-test` |
| `docs/workflows/case-analysis.md` | `cinderx-analysis` |
| `docs/workflows/docker-runtime.md` | `docker-runtime` |
| `docs/workflows/ssh-connection.md` | `remote-environment` |
| `docs/workflows/documentation.md` | `experiment-documentation` |
| `references/commands/pyperformance-run-realenv.sh` | `pyperformance-test` |
| `references/commands/run-benchmark-worker-realenv.sh` | `pyperformance-test` |
| `references/configs/report_schema.example.json` | `experiment-documentation` |
| `references/templates/docker/cpython-baseline/` | `docker-runtime` |
| `references/templates/docker/cinderx-test/` | `docker-runtime` |
| `scripts/docker/cinderx-test/setup.sh` | `docker-runtime` |
| `scripts/docker/cinderx-test/smoke.sh` | `docker-runtime` |
| `scripts/docker/cinderx-test/test-benchmark.sh` | `pyperformance-test` |
| `scripts/docker/cinderx-test/benchmark_harness.py` | `pyperformance-test` |
| `docs/playbooks/entry-decision-table.md` | → 吸收到 `using-cpython-optimize` |
| `docs/playbooks/faq.md` | → 吸收到 `using-cpython-optimize` |
| `docs/playbooks/performance-modes.md` | → 吸收到 `cinderx-analysis` |
| `docs/playbooks/pyperformance-crash-triage.md` | → 吸收到 `pyperformance-test` |

---

## Key Technical Decisions

- **D1. 子技能自包含** — 每个子技能目录包含完整的 SKILL.md + 专属 references/ + 专属 scripts/。参照 superpowers 和 ce 的模式。
- **D2. 技能间通过 Skill 工具交互** — 不共享文件。如 `pyperformance-test` 需要 Docker 环境，它通过 Skill 工具调用 `docker-runtime`，不直接引用后者的脚本。
- **D3. `docs/` 只承载仓库文档** — 开发指南、计划文档（`docs/plans/`）、设计文档等。工作流内容和 playbook 内容迁移到子技能目录中。
- **D4. 引导技能命名 `using-cpython-optimize`** — 遵循 superpowers 的 `using-*` 约定。
- **D5. 子技能命名无前缀短名** — 如 `cpython-build`、`pyperformance-test`。
- **D6. 描述语言中文** — frontmatter description 保持中文。
- **D7. SessionStart hook 复用 superpowers 模式** — bash 脚本读取引导技能注入上下文。
- **D8. 旧目录迁移后移除** — `docs/workflows/`、`references/`、`scripts/` 在内容迁移到子技能目录后删除。
- **D9. 平台适配分两期** — 首期 Claude Code + Codex。

---

## Open Questions

### Resolved During Planning

- 技能内容策略：自包含（全文迁移），不链接回源文档
- `docs/playbooks/` 归属：按主题吸收到对应子技能
- 旧目录处理：迁移后删除

### Deferred to Implementation

- 是否需要 `agents/` 目录定义专用 subagent（等技能拆分稳定后再评估）
- `platforms/` 目录是否保留（平台适配二期时再决定）

---

## Output Structure

```
cpython-optimize-skill/
  .claude-plugin/
    plugin.json                         # NEW
  .codex-plugin/
    plugin.json                         # NEW
  hooks/
    hooks.json                          # NEW
    session-start                       # NEW
  skills/
    using-cpython-optimize/
      SKILL.md                          # NEW: 引导技能 + entry-decision-table + FAQ
    cpython-build/
      SKILL.md                          # NEW: 含完整编译流程
    pyperformance-test/
      SKILL.md                          # NEW: 含完整测试流程
      references/
        pyperformance-run-realenv.sh    # MOVED from references/commands/
        run-benchmark-worker-realenv.sh # MOVED from references/commands/
        pyperformance-crash-triage.md   # MOVED from docs/playbooks/
      scripts/
        test-benchmark.sh               # MOVED from scripts/docker/cinderx-test/
        benchmark_harness.py            # MOVED from scripts/docker/cinderx-test/
    cinderx-analysis/
      SKILL.md                          # NEW: 含完整分析流程
      references/
        performance-modes.md            # MOVED from docs/playbooks/
    docker-runtime/
      SKILL.md                          # NEW: 含完整 Docker 流程
      templates/
        cpython-baseline/               # MOVED from references/templates/docker/cpython-baseline/
        cinderx-test/                   # MOVED from references/templates/docker/cinderx-test/
      scripts/
        setup.sh                        # MOVED from scripts/docker/cinderx-test/
        smoke.sh                        # MOVED from scripts/docker/cinderx-test/
    remote-environment/
      SKILL.md                          # NEW: 含完整 SSH/环境流程
    experiment-documentation/
      SKILL.md                          # NEW: 含完整文档规范
      references/
        report_schema.example.json      # MOVED from references/configs/
  docs/
    plans/                              # PRESERVED: 仓库级计划文档
    agent-interoperability.md           # PRESERVED: 仓库级开发文档
    README.md                           # PRESERVED: 仓库级 README
  package.json                          # NEW
  CHANGELOG.md                          # MODIFIED
  .gitignore                            # PRESERVED
  tests/                                # PRESERVED
```

**移除的目录（内容已迁移）：**
- `docs/workflows/` — 内容迁入 `skills/*/SKILL.md`
- `docs/playbooks/` — 内容迁入对应子技能目录
- `references/` — 内容迁入对应子技能目录
- `scripts/` — 内容迁入对应子技能目录
- `SKILL.md`（根目录）— 保留为迁移指引
- `core/SKILL.md` — 保留为迁移指引
- `platforms/` — 暂保留

---

## Implementation Units

- [ ] U1. **Create plugin registration files**

**Goal:** 让仓库被 Claude Code 和 Codex 识别为合法插件

**Requirements:** R1, R6

**Dependencies:** None

**Files:**
- Create: `.claude-plugin/plugin.json`
- Create: `.codex-plugin/plugin.json`
- Create: `package.json`

**Approach:**
- `.claude-plugin/plugin.json` 参照 superpowers 格式，包含 name、version、description、author、keywords、`skills: "./skills/"`、interface 字段
- `.codex-plugin/plugin.json` 同格式
- `package.json` 最小化，只含 name、version、type

**Test expectation:** none — 纯配置文件

**Verification:**
- JSON 语法合法，`skills` 字段指向 `./skills/`

---

- [ ] U2. **Create bootstrap skill (`using-cpython-optimize`)**

**Goal:** 引导技能，包含子技能清单、发现规则、决策流程图，用于 SessionStart 自动注入。吸收 `entry-decision-table.md` 和 `faq.md` 的内容。

**Requirements:** R2, R3

**Dependencies:** None

**Files:**
- Create: `skills/using-cpython-optimize/SKILL.md`

**Approach:**
- frontmatter：`name: using-cpython-optimize`，中文 description
- 内容包含：核心原则（从 `core/SKILL.md` 提取）、子技能列表 + 触发条件、执行顺序决策流程图（从 `docs/playbooks/entry-decision-table.md` 吸收）、常见问题（从 `docs/playbooks/faq.md` 吸收）
- 目标 <800 词（比之前多，因为要吸收 playbook 内容）

**Patterns to follow:**
- superpowers `skills/using-superpowers/SKILL.md`

**Test scenarios:**
- Happy path: 新会话启动，引导技能被注入，agent 能根据用户请求选择正确的子技能

**Verification:**
- frontmatter 格式正确，所有子技能在列表中提及

---

- [ ] U3. **Create SessionStart hook**

**Goal:** 在新会话开始时自动注入引导技能到上下文

**Requirements:** R4

**Dependencies:** U2

**Files:**
- Create: `hooks/hooks.json`
- Create: `hooks/session-start`

**Approach:**
- 完全参照 superpowers 的 `hooks/hooks.json` + `hooks/session-start` 实现
- 支持 Claude Code（`CLAUDE_PLUGIN_ROOT`）环境检测

**Patterns to follow:**
- superpowers `hooks/` 精确复制并适配

**Test expectation:** none — 通过集成测试验证

**Verification:**
- 脚本可执行，JSON 输出格式正确

---

- [ ] U4. **Create self-contained workflow skills**

**Goal:** 将 6 个工作流 + 关联的 references/scripts 迁移为自包含子技能

**Requirements:** R2, R5, R8

**Dependencies:** U1

**Files:**
- Create: `skills/cpython-build/SKILL.md`（内容源自 `docs/workflows/build-and-install.md`）
- Create: `skills/pyperformance-test/SKILL.md`（内容源自 `docs/workflows/pyperformance-test.md`）
- Create: `skills/pyperformance-test/references/pyperformance-run-realenv.sh`（源自 `references/commands/`）
- Create: `skills/pyperformance-test/references/run-benchmark-worker-realenv.sh`（源自 `references/commands/`）
- Create: `skills/pyperformance-test/references/pyperformance-crash-triage.md`（源自 `docs/playbooks/`）
- Create: `skills/pyperformance-test/scripts/test-benchmark.sh`（源自 `scripts/docker/cinderx-test/`）
- Create: `skills/pyperformance-test/scripts/benchmark_harness.py`（源自 `scripts/docker/cinderx-test/`）
- Create: `skills/cinderx-analysis/SKILL.md`（内容源自 `docs/workflows/case-analysis.md`）
- Create: `skills/cinderx-analysis/references/performance-modes.md`（源自 `docs/playbooks/`）
- Create: `skills/docker-runtime/SKILL.md`（内容源自 `docs/workflows/docker-runtime.md`）
- Create: `skills/docker-runtime/templates/cpython-baseline/*`（源自 `references/templates/docker/cpython-baseline/`）
- Create: `skills/docker-runtime/templates/cinderx-test/*`（源自 `references/templates/docker/cinderx-test/`）
- Create: `skills/docker-runtime/scripts/setup.sh`（源自 `scripts/docker/cinderx-test/`）
- Create: `skills/docker-runtime/scripts/smoke.sh`（源自 `scripts/docker/cinderx-test/`）
- Create: `skills/remote-environment/SKILL.md`（内容源自 `docs/workflows/ssh-connection.md`）
- Create: `skills/experiment-documentation/SKILL.md`（内容源自 `docs/workflows/documentation.md`）
- Create: `skills/experiment-documentation/references/report_schema.example.json`（源自 `references/configs/`）

**Approach:**
- 每个子技能 SKILL.md 包含：frontmatter（中文 description）+ 完整工作流内容（从 `docs/workflows/` 迁移）
- 关联的 references、scripts、templates 移入子技能目录
- 子技能 SKILL.md 中的路径引用更新为子技能目录内的相对路径
- 需要其他技能时，通过 Skill 工具引用（如 pyperformance-test 需要 Docker 时调用 docker-runtime）

**Patterns to follow:**
- superpowers 各子技能的自包含结构

**Test scenarios:**
- Happy path: Skill 工具加载 `cpython-build`，获得完整编译流程
- Happy path: `pyperformance-test` 目录下包含所有需要的脚本和命令模板
- Edge case: 子技能脚本路径在 SKILL.md 中用子技能内相对路径引用

**Verification:**
- 每个子技能 SKILL.md frontmatter 合法
- 每个子技能目录内包含所需的 references/scripts/templates
- 引导技能的子技能列表与实际一一对应

---

- [ ] U5. **Clean up old directories and update legacy entry points**

**Goal:** 迁移完成后清理旧目录，更新旧入口文件为迁移指引

**Requirements:** R5, R7

**Dependencies:** U2, U4

**Files:**
- Modify: `SKILL.md`（改为迁移指引）
- Modify: `core/SKILL.md`（改为迁移指引）
- Remove: `docs/workflows/`（内容已迁入 skills/）
- Remove: `docs/playbooks/`（内容已迁入 skills/）
- Remove: `references/`（内容已迁入 skills/）
- Remove: `scripts/`（内容已迁入 skills/）

**Approach:**
- `SKILL.md` 保留 frontmatter，内容改为简短迁移指引："本仓库已重构为复合技能仓库。通过 Skill 工具加载 `using-cpython-optimize` 开始。"
- `core/SKILL.md` 同理
- 确认所有内容已迁移后删除旧目录

**Test expectation:** none — 纯结构清理

**Verification:**
- `docs/workflows/`、`references/`、`scripts/` 目录已不存在
- 旧 SKILL.md 包含有效的迁移指引

---

- [ ] U6. **Update CHANGELOG and validate plugin installation**

**Goal:** 记录版本变更并验证完整插件安装流程

**Requirements:** R5

**Dependencies:** U1, U2, U3, U4, U5

**Files:**
- Modify: `CHANGELOG.md`

**Approach:**
- CHANGELOG.md 顶部追加 v0.4.0 条目，列出结构变更
- 通过 `claude plugin add` 验证插件被正确识别
- 确认 Skill 工具能列出所有 7 个子技能

**Test scenarios:**
- Integration: `claude plugin add` 成功注册
- Integration: 新会话中引导技能被自动注入
- Integration: 每个子技能可通过 Skill 工具独立加载

**Verification:**
- 7 个子技能全部可发现，CHANGELOG 条目完整

---

## System-Wide Impact

- **Interaction graph:** SessionStart hook 影响每个新会话的初始化流程
- **State lifecycle risks:** 无持久化状态变更，纯结构重组
- **Unchanged invariants:** `tests/` 目录内容不变，`docs/plans/` 和 `docs/agent-interoperability.md` 不变

---

## Risks & Dependencies

| Risk | Mitigation |
|------|------------|
| 插件安装失败（plugin.json 格式错误） | 参照 superpowers 已验证格式 |
| 子技能内脚本路径引用错误 | 迁移后统一用子技能内相对路径 |
| SessionStart hook 在非 Claude Code 环境出错 | 环境变量检测，未知环境静默退出 |
| 引导技能过长影响上下文窗口 | 目标 <800 词，控制 playbook 吸收量 |
| 旧内容迁移遗漏 | U6 验证时逐项对比 Content Distribution 表 |

---

## Documentation / Operational Notes

- v0.4.0 标记为结构重构，无功能变更
- 安装方式：`claude plugin add /opt/Claude-Code/cpython-optimize-skill`（本地路径）
- 后续可考虑发布到 marketplace（需要 marketplace.json）
