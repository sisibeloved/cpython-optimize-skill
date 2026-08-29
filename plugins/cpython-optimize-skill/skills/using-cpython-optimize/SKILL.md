---
name: using-cpython-optimize
description: Use when 开始 CPython/CinderX 优化、环境审计、A/B 跑分、pyperformance 性能测试、RuntimeTests 功能测试、crash、JIT 或 Kunpeng/x86 平台差异任务。
---

# CPython/CinderX Optimize Router

薄 router：Orchestrator 选 Workflow，Workflow 分派 Agent，Agent 调专业 Skill。

## 层级

| 层 | 职责 |
|----|------|
| Orchestrator | 运行时主 Agent，理解目标、选 Workflow、分派 Agent、合并结果 |
| Workflow | 端到端剧本和 gate |
| Agent | 阶段负责人，接管环境、跑分、crash、JIT 或平台分析 |
| Skill | CPython/CinderX 专业动作 |

## Agent 路由

Agent 文档不是原生 Skill 自动触发单元。主 Agent 或 hook 一旦决定分派某个 Agent，必须按 `agents/<agent>.md` 路径显式读取对应角色文档，再执行其职责、反问 Gate 和输出要求。

| Agent | 触发 |
|-------|------|
| `cinderx-orchestrator` | 任意入口和任务分发 |
| `cinderx-environment-verifier` / environment-verifier | 环境审计、三态判断 |
| `pyperformance-baseline-runner` / baseline-runner | baseline slot 跑分 |
| `pyperformance-candidate-runner` / candidate-runner | candidate slot 跑分 |
| `pyperformance-benchmark-analyst` | `run.json` / `speedup.json` 结果解读 |
| `cinderx-crash-triager` / crash-triager | `SIGSEGV`、`exit 139`、core dump |
| `cinderx-jit-analyst` | CinderX JIT、HIR/LIR、解释执行用例、机器码优化点 |
| `cinderx-platform-analyst` | Kunpeng/x86、ISA、微架构差异 |
| `cinderx-evidence-analyst` | 单用例证据表、跨层根因下钻、穿刺判读 |

## 反问 Gate

能从仓库、环境、日志或历史产物查证的信息先查证，不问用户。以下信息无法唯一确定时必须暂停反问：

| 缺口 | 典型问题 |
|------|----------|
| 目标路线 | 三个主 Workflow、supporting workflow 或验证等级无法唯一选择 |
| 实验轴 | benchmark、平台、baseline/candidate、JIT 口径或环境句柄缺失 |
| 高成本动作 | 清理环境、bootstrap、在线安装、编译 CinderX、全量 Runtime、全量 pyperformance |
| 运行中异常 | 远端无输出、timeout、网络卡顿时需要继续等待、换镜像、复用缓存或中止 |
| 证据链断裂 | crash 缺真实命令/core，结果比较缺配对 `run.json`，平台分析缺平台对 |

平台映射：Codex 优先用 `request_user_input`，Claude Code 优先用 `AskUserQuestion`；工具不可用时，退化为普通文本选择题并等待用户回答。

需要结构化选项时读取 `references/clarifying-question-templates.md`，复用其中的 `question_id`、选项和文本降级格式。

## Environment Verifier 三态

| 状态 | 下一步 |
|------|--------|
| 可复用 / `reusable` | 返回环境句柄 |
| 新环境 / `needs_bootstrap` | 调 `cinderx-env-bootstrap` |
| 被破坏 / `needs_clean_bootstrap` | 调 `cinderx-env-clean` 再 bootstrap |

## 专业 Skill

`cinderx-env-validate`、`cinderx-env-clean`、`cinderx-env-bootstrap`、`cinderx-remote-lab-ops`、`cinderx-ab-run-slot`、`cpython-runtime-test-run`、`cinderx-smoke-check`、`pyperformance-worker-run`、`pyperformance-suite-run`、`pyperformance-result-compare`、`pyperformance-stat-report`、`cinderx-gdb-core-triage`、`cinderx-hir-dump`、`cinderx-jit-entry-check`、`cinderx-hir-lir-analyze`、`cinderx-interpreter-case-analyze`、`cinderx-isa-microarch-compare`、`cinderx-evidence-table`、`cinderx-optimization-report`、`validation-strategy`、`isa-instruction-lookup`、`compiler-optimization-theory`。

## Workflow 路由

- 双平台性能差距：`workflow-cross-platform-delta-triage`
- 已知特性优化：`workflow-feature-driven-optimization`
- 系统找平台优化点：`workflow-platform-differential-discovery`
- 深钻单用例拿可信优化点：`workflow-platform-differential-discovery-deepdive`
- 环境准备：`workflow-remote-cinderx-lab-setup`
- crash：`workflow-cinderx-crash-triage`
- 正式回归：`workflow-pyperformance-regression`
- 单 benchmark JIT / 非 JIT 用例分析：`workflow-jit-optimization-analysis`

## 不变原则

- 先让 `cinderx-environment-verifier` 审计环境，再跑昂贵任务。
- A/B 并行前用 `cinderx-ab-run-slot` 确认 CPU 绑核和结果目录不冲突。
- `SIGSEGV` / core dump 走 `cinderx-gdb-core-triage`，日志不能替代 `gdb bt full`。
- 远程命令输出契约用 `cinderx-remote-lab-ops`，异常耗时要诊断并询问用户。
- 验证阶梯和成本预算用 `validation-strategy`。
- 指令集规格（编码、汇编语法、伪代码、`FEAT_xxx` 依赖、跨平台等价候选）一律查 `isa-instruction-lookup`，禁止凭记忆回答；引用必须带 `source_doc` 和页码。
