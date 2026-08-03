# 🔧 CPython/CinderX 性能优化技能仓库

[![Version](https://img.shields.io/badge/version-1.0.4-blue.svg)](plugins/cpython-optimize-skill/CHANGELOG.md)
[![Codex](https://img.shields.io/badge/Codex-plugin-0A7EA4.svg)](#codex-cli)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-plugin-D97757.svg)](#claude-code插件市场)
[![Skills](https://img.shields.io/badge/skills-32-success.svg)](#-技能一览)
[![Agents](https://img.shields.io/badge/agents-9-informational.svg)](#-agent-一览)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

面向个人工作流的 CPython/CinderX 性能优化与设计文档技能集合，以 Claude Code / Codex 插件形式交付。

---

## 🔁 Workflow 一览

主 Workflow 是用户目标入口；Supporting Workflow 是主流程内部按需调用的阶段或异常分支。

### 主 Workflow

| Workflow | 用途 |
|----------|------|
| `workflow-cross-platform-delta-triage` | 双平台性能差距根因定位和收益验证 |
| `workflow-feature-driven-optimization` | 已知特性驱动的代码优化、功能用例和性能验证 |
| `workflow-platform-differential-discovery` | 系统分析 ISA / 微架构差异并发现优化点（matrix-first 粗筛，产出候选用例清单） |
| `workflow-platform-differential-discovery-deepdive` | 按单个用例深钻，从性能数据追到 ISA / 微架构 / 硬件根因，产出可信备选优化项 |

### Supporting Workflow

| Workflow | 用途 |
|----------|------|
| `workflow-remote-cinderx-lab-setup` | 从零准备远程 CPython/CinderX 优化实验环境 |
| `workflow-cinderx-crash-triage` | 复现、定位并记录 CinderX/pyperformance crash |
| `workflow-pyperformance-regression` | L3/L4 正式 pyperformance 对比、性能回归和报告沉淀 |
| `workflow-jit-optimization-analysis` | 单 benchmark JIT 热点、HIR/LIR 和优化点分析 |

Workflow 是多个技能和专门 Agent 的编排入口；原子技能继续负责具体领域知识、命令约束和产物格式。

## 👥 Agent 一览

| Agent | 职责 |
|-------|------|
| `cinderx-orchestrator` | 运行时主 Agent，选择 workflow 并分派阶段 Agent |
| `cinderx-environment-verifier` | 环境三态：可复用、新环境、被破坏环境 |
| `pyperformance-baseline-runner` | 接管 baseline slot |
| `pyperformance-candidate-runner` | 接管 candidate slot |
| `pyperformance-benchmark-analyst` | 解读 run.json / speedup.json |
| `cinderx-crash-triager` | 接管 native crash 取证 |
| `cinderx-jit-analyst` | 接管 JIT/HIR/LIR 优化分析 |
| `cinderx-platform-analyst` | 接管 ISA / 微架构差异分析 |
| `cinderx-evidence-analyst` | 接管单用例证据表，跨层根因下钻（HIR/LIR→机器码→ISA→微架构→硬件）与穿刺判读 |

## 📦 技能一览

| 技能 | 用途 | 自带资源 |
|------|------|---------|
| 🎯 `using-cpython-optimize` | Orchestrator 路由入口 | — |
| 🧪 `cinderx-env-validate` | Python/SOABI/CinderX/pyperformance 环境三态校验 | — |
| 🧹 `cinderx-env-clean` | 清理被污染的 CinderX lab | — |
| 🐳 `cinderx-env-bootstrap` | 初始化 Docker 双线、CinderX editable、pyperformance | templates/、scripts/ |
| 🔌 `cinderx-remote-lab-ops` | 远端 SSH/tmux/rsync/docker compose 和输出契约 | — |
| 🧷 `cinderx-ab-run-slot` | baseline/candidate slot、CPU affinity、结果目录隔离 | — |
| 🧪 `cpython-runtime-test-run` | RuntimeTests 功能测试 / test_cinderx 和 lib test 集成测试 | — |
| 🔎 `cinderx-smoke-check` | import cinderx、_cinderx、最小 JIT、HIR smoke | — |
| ⚡ `cinderx-fast-validation` | 用 ccache wrapper 加速 CinderX setup_release、release wheel 和 gate 重复验证 | scripts/ |
| 📊 `pyperformance-worker-run` | 单 benchmark worker、bench_command、sitecustomize | references/、scripts/ |
| 📈 `pyperformance-suite-run` | 正式 `python -m pyperformance run` | — |
| ⚡ `cinderx-parallel-pyperformance` | NUMA/L3-aware 8/16 lane 并行 pyperformance、worker venv 注入和稳定性复跑 | references/、scripts/ |
| 📉 `pyperformance-result-compare` | run.json、speedup.json、收益/回归/噪声判断 | — |
| 🧾 `pyperformance-stat-report` | 多个 pyperformance JSON 生成控制台、Excel 和趋势图报告 | scripts/ |
| 🧯 `cinderx-gdb-core-triage` | SIGSEGV、exit 139、core、gdb 证据链 | references/ |
| 🧾 `cinderx-hir-dump` | 真实 worker 命令叠加 HIR / jit.log | — |
| 🔬 `cinderx-jit-entry-check` | 确认 benchmark 本体进入 CinderX JIT | — |
| 🧑‍⚖️ `cinderx-jit-review` | CinderX JIT PR correctness-first review、RuntimeTests/test_cinderx/test_kunpeng 覆盖和 exact comment placement | references/ |
| 🔬 `cinderx-hir-lir-analyze` | HIR/LIR/uop/机器码和修改方案 | references/ |
| 🧩 `cinderx-interpreter-case-analyze` | 非 JIT / 解释执行用例的阶段表、函数形状和 gate 策略 | — |
| 🧭 `cinderx-isa-microarch-compare` | Kunpeng/x86 ISA、微架构、perf 差异矩阵 | — |
| 🧾 `cinderx-evidence-table` | 单用例深钻证据表 E1–E9 三段式结构（What/Verdict/Gate）、根因层级工具证据和 SPE/IBS 采样探测原则 | — |
| 📝 `cinderx-optimization-report` | CinderX 优化报告和证据链沉淀 | references/ |
| ✅ `validation-strategy` | 验证阶梯、成本预算、缓存复用 | — |
| 📐 `design-documentation` | 架构/系统/功能/详细设计文档 | references/ |

## 🌟 推荐插件 / 技能 / 工具

这些仓库适合用来学习 agent 技能设计、插件封装、上下文压缩、代码图检索和多 Agent 编排。它们不一定都适合直接套进本仓，但都值得作为设计参考。

| 项目 | 类型 | 推荐理由 | 适合借鉴 |
|------|------|----------|----------|
| [`obra/superpowers`](https://github.com/obra/superpowers) | 跨工具技能框架 | 用 skill 把 brainstorming、TDD、debug、verification、git worktree 等工程流程制度化。 | 技能触发、TDD 写 skill、验证前置、流程纪律 |
| [`EveryInc/compound-engineering-plugin`](https://github.com/everyinc/compound-engineering-plugin) | 复合工程插件 | 把 plan、work、review、commit、PR、frontend polish 等工程动作做成插件化 workflow。 | 插件结构、工程任务编排、代码审查与提交流程 |
| [`forrestchang/andrej-karpathy-skills`](https://github.com/forrestchang/andrej-karpathy-skills) | Karpathy 风格技能集 | 将 first-principles、简洁推理、研究/写作习惯沉淀成可调用技能。 | 思维风格技能、研究型任务提示、低噪声表达 |
| [`openai/codex-plugin-cc`](https://github.com/openai/codex-plugin-cc) | Claude Code ↔ Codex 插件 | 在 Claude Code 中调用 Codex 做 review 或任务委派，适合作为跨 Agent 桥接参考。 | 插件互操作、任务委派、Codex/Claude Code 协作 |
| [`colbymchenry/codegraph`](https://github.com/colbymchenry/codegraph) | 本地代码知识图 / MCP 工具 | 预索引代码库的符号、调用、依赖和路由关系，让 Agent 少 grep、少读文件。 | 按需上下文、代码图检索、MCP 工具设计 |
| [`code-yeongyu/oh-my-openagent`](https://github.com/code-yeongyu/oh-my-openagent) | 多 Agent harness | 面向 Claude Code、Codex、OpenCode 等工具的多 Agent 配置与任务路由框架。 | Agent 编排、模型/角色匹配、harness 配置 |
| [`mattpocock/skills`](https://github.com/mattpocock/skills) | 工程实践技能集 | 面向真实工程项目的可组合小技能，强调 TDD、诊断、架构改进和 issue/PR 工作流。 | 小而专的技能粒度、工程诊断、PRD/issue 拆解 |

---

## 🚀 安装

### Claude Code（插件市场）

```
/plugin marketplace add https://github.com/sisibeloved/cpython-optimize-skill
/plugin install cpython-optimize-skill
```

安装后，Agent 通过 skill 描述按需加载 `using-cpython-optimize`。插件还带有轻量运行中 hook：当真实执行命令的 stdout/stderr 出现 `SIGSEGV`、`exit 139`、core dump、timeout 或远程无输出等信号时，只注入短提醒，提示 Agent 加载 `cinderx-gdb-core-triage` 或 `cinderx-remote-lab-ops`；`git show/log/diff`、`rg`、`sed`、`cat` 等只读查看命令不会因为历史文本里的触发词误报。

首次启用或更新 hook 后，按宿主 Agent 的要求在 `/hooks` 中 review / trust 新的 hook 定义。

### Codex CLI

```bash
codex plugin marketplace add https://github.com/sisibeloved/cpython-optimize-skill
codex plugin add cpython-optimize-skill@cpython-optimize-skill
```

---

## 💬 使用示例

```
> 帮我在 Kunpeng 上编译 CinderX 并跑一次 pyperformance
> regex_compile 在容器里 SIGSEGV 了，帮我复现和定位
> 对比 stock CPython JIT 和 CinderX JIT 的 pyperformance 数据
> 在 53 上用 8 核自适应并行跑 pyperformance dry-run，再做两次稳定性复跑
> 帮我 review 这个 CinderX JIT PR 的 correctness 风险，并给出 exact comment placement
> Kunpeng 和 x86 上哪些 benchmark 差距最大，帮我系统筛一遍候选用例
> 深钻 regex_compile 这一个用例，从性能数据追到 ISA/微架构根因，给我一份能落地的优化点证据表
> 帮我写一份 CinderX JIT 优化点的架构设计说明书
```

Agent 会根据任务自动选择对应技能，无需手动加载。

---

## 📁 仓库结构

```
.
├── .agents/plugins/                         # Codex 插件市场元数据
│   └── marketplace.json
├── .claude-plugin/                          # Claude Code 插件市场元数据
│   └── marketplace.json
├── plugins/cpython-optimize-skill/          # 实际插件包
│   ├── .claude-plugin/
│   │   └── plugin.json
│   ├── .codex-plugin/
│   │   └── plugin.json
│   ├── hooks/
│   │   ├── hooks.json
│   │   └── runtime-skill-router
│   ├── skills/                              # 原子技能 + workflow 技能
│   │   ├── using-cpython-optimize/
│   │   ├── cinderx-env-validate/
│   │   ├── cinderx-evidence-table/
│   │   ├── cinderx-env-clean/
│   │   ├── cinderx-env-bootstrap/
│   │   ├── cinderx-remote-lab-ops/
│   │   ├── cinderx-ab-run-slot/
│   │   ├── cpython-runtime-test-run/
│   │   ├── cinderx-smoke-check/
│   │   ├── cinderx-fast-validation/
│   │   ├── pyperformance-worker-run/
│   │   ├── pyperformance-suite-run/
│   │   ├── cinderx-parallel-pyperformance/
│   │   ├── pyperformance-result-compare/
│   │   ├── pyperformance-stat-report/
│   │   ├── cinderx-gdb-core-triage/
│   │   ├── cinderx-hir-dump/
│   │   ├── cinderx-jit-entry-check/
│   │   ├── cinderx-jit-review/
│   │   ├── cinderx-hir-lir-analyze/
│   │   ├── cinderx-interpreter-case-analyze/
│   │   ├── cinderx-isa-microarch-compare/
│   │   ├── cinderx-optimization-report/
│   │   ├── validation-strategy/
│   │   ├── design-documentation/
│   │   ├── workflow-remote-cinderx-lab-setup/
│   │   ├── workflow-cinderx-crash-triage/
│   │   ├── workflow-pyperformance-regression/
│   │   ├── workflow-jit-optimization-analysis/
│   │   ├── workflow-cross-platform-delta-triage/
│   │   ├── workflow-feature-driven-optimization/
│   │   ├── workflow-platform-differential-discovery/
│   │   └── workflow-platform-differential-discovery-deepdive/
│   ├── agents/                              # workflow 可引用的专门 Agent 角色文档
│   ├── tests/
│   ├── docs/
│   ├── package.json
│   └── CHANGELOG.md
├── README.md
└── .gitignore
```

每个技能自包含 `SKILL.md` + 专属 `references/`、`scripts/`、`templates/`，技能间通过 Skill 工具互相调用。

---

## ✅ 验证

```bash
cd plugins/cpython-optimize-skill
python3 tests/validate_skill_layout.py
python3 tests/validate_pressure_scenarios.py
python3 tests/test_pyperformance_stat_report.py
```

## 📜 版本历史

见 `plugins/cpython-optimize-skill/CHANGELOG.md`。

## 📄 许可

MIT
