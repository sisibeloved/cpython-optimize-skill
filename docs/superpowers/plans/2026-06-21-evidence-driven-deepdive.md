# Evidence-Driven Deepdive Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把按用例深钻的证据驱动流程沉淀为可复用资产：新建 `cinderx-evidence-table` skill、`cinderx-evidence-analyst` agent、`workflow-platform-differential-discovery-deepdive` workflow，并给粗筛 workflow 加输出契约、给 router 加深钻路由。

**Architecture:** 两层并行——保留 matrix-first 粗筛 workflow 不变（仅加输出契约），新增按用例深钻 workflow 承载 10 步流程。证据表 skill 定义 E1–E9 三段式结构 + E6 工具证据表 + SPE/IBS 采样探测原则，被深钻 workflow 和现有 jit-optimization-analysis workflow 共同复用。evidence-analyst 是证据表唯一负责人，E6 接手收口判读，现有 jit/platform analyst 是其上游证据提供者。

**Tech Stack:** 纯 Markdown skill/agent/workflow 文档（无代码），Python 测试校验布局与 frontmatter。注册方式：skills/ 和 agents/ 目录自动发现，无需改 plugin.json；但 `tests/validate_skill_layout.py` 有硬编码 `REQUIRED_SKILLS` / `REQUIRED_AGENTS` 白名单，新增项必须同步登记，否则布局校验失败。

**设计依据:** `docs/superpowers/specs/2026-06-21-evidence-driven-deepdive-design.md`

---

## 约定与约束（所有任务共享）

- **skill frontmatter 格式**（见 `validate_skill_layout.py:107` parse_frontmatter）：
  ```
  ---
  name: <skill-name>
  description: Use when <触发条件>。
  ---

  # <标题>
  ```
  `name` 必须等于目录名；`description` 必须以 "Use when" 开头。
- **skill 子目录**只能是 `references` / `scripts` / `templates` 之一，或无子目录（`validate_skill_layout.py:151`）。
- **agent 文档必须中文**，章节固定为 `## 职责`、`## 适用场景`、`## 可调用技能`、`## 反问 Gate`、`## 输出要求`（`validate_skill_layout.py:168`），且**不得**含英文模板串 `## Focus` / `## Use When` / `## Output` / `Return:` / `Do not `（`validate_skill_layout.py:167`）。无 frontmatter（以 `# <名字> Agent` 开头，见 `cinderx-platform-analyst.md`）。
- **目录基准**：`plugins/cpython-optimize-skill/`。
- **测试入口**：`python plugins/cpython-optimize-skill/tests/validate_skill_layout.py`。
- **提交粒度**：每个 Task 末尾提交一次。

---

## 文件结构

| 动作 | 路径 | 职责 |
|------|------|------|
| 新建 | `skills/cinderx-evidence-table/SKILL.md` | 证据表 E1–E9 三段式结构 + E6 工具证据表 + SPE/IBS 采样探测原则 |
| 新建 | `agents/cinderx-evidence-analyst.md` | 跨层追因、证据闭环判定、穿刺判读的负责人 |
| 新建 | `skills/workflow-platform-differential-discovery-deepdive/SKILL.md` | 深钻 workflow，12 阶段 agent 分派表 |
| 修改 | `skills/workflow-platform-differential-discovery/SKILL.md` | 粗筛 workflow 加候选用例清单输出契约 |
| 修改 | `skills/using-cpython-optimize/SKILL.md` | router 加深钻路由 + agent 路由表登记 evidence-analyst |
| 修改 | `tests/validate_skill_layout.py` | `REQUIRED_SKILLS` 加深钻 workflow + 证据表 skill；`REQUIRED_AGENTS` 加 evidence-analyst |

---

### Task 1: 新建 `cinderx-evidence-table` skill

**Files:**
- Create: `plugins/cpython-optimize-skill/skills/cinderx-evidence-table/SKILL.md`

- [ ] **Step 1: 写 SKILL.md**

完整内容如下（frontmatter 的 `name` 与目录名一致，`description` 以 "Use when" 开头）：

```markdown
---
name: cinderx-evidence-table
description: Use when 需要为单个用例建立从性能数据到根因的完整证据表，定义 E1–E9 三段式结构、每步必贴证据与闭环判据，并规定 ISA/指令集/微架构/硬件层的工具证据和 SPE/IBS 采样可用性探测原则。
---

# CinderX Evidence Table

证据表是单用例深钻的唯一产物。一张表 9 行（E1–E9），每行三段式：What（必贴客观证据）/ Verdict（一句结论）/ Gate（证据足够硬条件）。任一段不满足 Gate，证据表标记 `evidence_gap` 或 `verdict_missing`，**流程停下来补证据**，不跳过。

证据表本身不负责"先钻哪个用例"——那是 workflow 层的选例动作。证据表从 E1 起假设用例已选定。

## E1–E9 结构

| # | 证据段 | What（必贴） | Verdict | Gate（证据闭环判据） |
|---|--------|--------------|---------|----------------------|
| E1 | 性能基线 | 双平台 wall clock、speedup、置信区间、样本数、运行环境句柄 | 该用例是否存在显著且稳定的平台差距 | 差距 > 噪声带（默认 3%）且置信区间不含 0 |
| E2 | 用例画像 | 用例内容描述、autojit 函数形状（签名、热点循环结构） | 该用例的优化价值定位（compute-bound? memory-bound? branchy?） | 函数形状与 perf 热点吻合 |
| E3 | HIR 分布 | HIR 节点分布表（按 pass 或 node kind 统计）、双平台 HIR 是否同构 | 差异是否源于编译期（HIR 层） | 双平台 HIR 形态已比对，差异点已定位到节点级 |
| E4 | LIR + wall clock | LIR/机器码段、调用计数、wall clock 拆解（该段占总时间比） | 差异是否源于 codegen（LIR 层） | wall clock 拆解能与 LIR 段对齐，热点段已锁定 |
| E5 | 差异点 | bb 维度整体差异 或 单条机器码级差异，双平台逐指令对齐 | 具体差异指令/序列是什么 | 双平台指令已逐条对齐，差异序列 ≤ N 条可枚举 |
| E6 | 根因下钻 | 跨层证据链：LIR→机器码→ISA/指令集→微架构→硬件 | 表面原因之下的真实根因 | 根因已落到 ISA/微架构/硬件某一层，且非表面原因 |
| E7 | 优化方向 | 由根因推出的优化策略（不是猜测） | 该方向能否直接解决 E6 根因 | 策略 ↔ 根因一一对应，无悬空假设 |
| E8 | 穿刺数据 | A/B 验证（baseline=原形态，candidate=优化形态），wall clock + 必要 PMU | 优化是否真的消除差异、是否带来收益 | 穿刺隔离满足 `cinderx-ab-run-slot`，结果可重复 |
| E9 | 优化价值判定 | 净收益（穿刺收益 − 实现成本 − 风险）、通用性、是否进备选 | 该优化项是否进入备选优化项清单 | 收益与成本均有数据支撑，无纯定性结论 |

## E6 根因层级必带工具证据

通用必带（所有平台）：`perf stat` 的 cycles / instructions / cache-references / cache-misses / branch-misses，双平台同口径采集。

| 根因层 | 必带工具输出（缺则 `evidence_gap`） |
|--------|------------------------------------|
| 机器码 | `objdump -d` 反汇编，双平台对齐 |
| ISA/指令集 | 指令选择差异、SIMD/原子/barrier 形态（对照 `cinderx-isa-microarch-compare` 矩阵） |
| 微架构 | `perf stat` 关键计数器（cycles/instructions/cache-miss/branch-miss）、`perf top` |
| 硬件 | PMU 计数器、必要时的 uops.info / llvm-mca 吞吐估算、cache/TLB 行为 |

## 指令级采样机制（SPE/IBS）处理原则

指令级精确采样在两平台是**不同机制、都有硬性开启条件**，且具体可用性随平台/内核/权限而变。本节只规定**处理原则**，不绑定任何特定平台的可用性结论——具体某平台能否拿到 SPE/IBS，由运行时探测决定，不预设。

1. **采样可用性是证据链前置判据，非默认前提**。E6 开头先做探测，探测结果本身作为 E6 第一条证据记录：

   - ARM 侧：`perf list | grep arm_spe`，并检查 `/sys/bus/event_source/devices/arm_spe_*/` 是否存在。为空则 SPE 证据不可得，退化为 PMU 计数器 + `perf top`。
   - x86 侧：检查 `/sys/bus/event_source/devices/ibs_op/` 是否存在，并确认权限——IBS 无用户/内核过滤能力，需 `CAP_SYS_ADMIN` 或 `CAP_PERFMON`。无特权则 IBS 证据不可得，退化为 top-down metric group。
   - 探测结果明确"本平台能拿到什么层级的证据、缺什么"。

2. **估算必标置信度**。uops.info / llvm-mca 是吞吐估算而非实测；Zen4/Zen5 无每端口 uops PMU（Saarland port-mapping 论文），ARM 侧 uops.info 不覆盖。证据表必须标注"估算来源 + 置信度"，不能把估算当实测。

3. **不对称证据显式化**。当一侧能拿到指令级采样、另一侧拿不到时，证据表不得直接对比不对称的采样数据。根因下钻以能拿到证据的一侧为锚，对侧只提供 PMU 级证据，并在 Verdict 标注证据不对称带来的根因置信度折扣。

## 失败处理

任一证据段不满足 Gate：

- 标记 `evidence_gap`（What 缺失）或 `verdict_missing`（Verdict 缺失）。
- **停下来补证据**，不进入下一段。
- evidence-analyst 在 E6 有权回退要求 E3–E5 补证据（如指令没对齐回到 E5）。
```

- [ ] **Step 2: 运行布局校验，预期 PASS**

Run: `python plugins/cpython-optimize-skill/tests/validate_skill_layout.py`
Expected: PASS，输出 `layout validation passed`。

说明：白名单检查是 `REQUIRED_SKILLS - 已存在目录`（只管"要求的缺失"），新建但未登记的 skill 不会触发失败；本步仅确认新 skill 目录结构本身合法（SKILL.md 存在、frontmatter 有 name+description、子目录合规）。白名单登记在 Task 6，作用是让这些新项成为"必须存在"的删改护栏。

- [ ] **Step 3: 提交**

```bash
git add plugins/cpython-optimize-skill/skills/cinderx-evidence-table/SKILL.md
git commit -m "Add cinderx-evidence-table skill"
```

---

### Task 2: 新建 `cinderx-evidence-analyst` agent

**Files:**
- Create: `plugins/cpython-optimize-skill/agents/cinderx-evidence-analyst.md`

- [ ] **Step 1: 写 agent 文档**

章节严格用中文 `## 职责` / `## 适用场景` / `## 可调用技能` / `## 反问 Gate` / `## 输出要求`，不得含英文模板串。无 frontmatter，以 `# CinderX Evidence Analyst Agent` 开头。

```markdown
# CinderX Evidence Analyst Agent

## 职责

证据表的唯一负责人。对单个用例建立从性能数据到根因的完整证据链，做跨层（HIR/LIR/机器码/ISA/微架构/硬件）归因，判定每段证据是否闭环（满足 E1–E9 的 Gate），推导优化方向，并判读穿刺数据是否可信。

不亲自执行 perf 采集、不亲自 dump HIR/LIR、不亲自跑 pyperformance——而是编排 `cinderx-jit-analyst`、`cinderx-platform-analyst`、`pyperformance-benchmark-analyst` 收集证据，并对证据闭环和根因置信度负责。E6（根因下钻）是采集与收口的分界线：E1–E5 由上游 analyst 贴事实，E6–E9 由本 agent 下判断。

亲自做、不外包的核心判断：采样可用性探测设计、PMU 采集命令设计、根因置信度判定、穿刺数据可信度判定（隔离是否满足、是否可重复、收益是否落噪声带外）。穿刺数据不合格时，有权把备选优化项打回。

## 适用场景

- 单个用例需要从性能数据一路追到 ISA/微架构/硬件根因。
- E1–E5 证据已由 jit/platform analyst 产出，需要收口判读、跨层归因。
- 需要判定证据是否闭环、根因置信度、优化方向是否成立。
- 需要判读 A/B 穿刺数据是否可信、是否值得进入备选优化项。

## 可调用技能

- `cinderx-evidence-table`
- `cinderx-isa-microarch-compare`
- `cinderx-optimization-report`
- `cinderx-ab-run-slot`（用于校验穿刺隔离是否满足，不亲自跑 slot）

## 反问 Gate

- 上游 analyst 的 E1–E5 证据存在 `evidence_gap` 或指令未逐条对齐时，先回退要求补证据，不强行进入 E6。
- SPE/IBS 采样可用性探测结果导致两侧证据颗粒度不对称时，先询问以哪一侧为锚，并标注根因置信度折扣。
- 优化方向无法与 E6 根因建立一一对应（存在悬空假设）时，不进入 E7，先补根因或修正方向。
- 穿刺数据不满足 `cinderx-ab-run-slot` 隔离要求或不可重复时，不进入 E9，先重跑或调整实验轴。

## 输出要求

返回填好的证据表（E1–E9，每段 What/Verdict/Gate），其中：

- E6 含采样可用性探测结论、跨层根因证据链、根因置信度与（若适用）证据不对称折扣。
- E7 的优化方向与 E6 根因一一对应。
- E8 的穿刺可信度判定（隔离、可重复、收益是否落噪声带外）。
- E9 的备选优化项结论（是否进备选、净收益、通用性、风险）。

任一段不满足 Gate，显式标记 `evidence_gap` / `verdict_missing` 并指出要补什么证据，不停留在模糊结论。
```

- [ ] **Step 2: 运行布局校验，预期 PASS**

Run: `python plugins/cpython-optimize-skill/tests/validate_skill_layout.py`
Expected: PASS，输出 `layout validation passed`。

说明：`REQUIRED_AGENTS` 检查是 `已要求 - 已存在`（只管"要求的缺失"），新建但未登记的 agent 不会触发失败；本步确认 agent 文档本身章节合法（含全部中文必备章节、无英文模板串）。白名单登记在 Task 6。

- [ ] **Step 3: 提交**

```bash
git add plugins/cpython-optimize-skill/agents/cinderx-evidence-analyst.md
git commit -m "Add cinderx-evidence-analyst agent"
```

---

### Task 3: 新建深钻 workflow `workflow-platform-differential-discovery-deepdive`

**Files:**
- Create: `plugins/cpython-optimize-skill/skills/workflow-platform-differential-discovery-deepdive/SKILL.md`

- [ ] **Step 1: 写 workflow SKILL.md**

```markdown
---
name: workflow-platform-differential-discovery-deepdive
description: Use when 需要深钻单个用例，从性能数据一路追到 ISA/微架构/硬件根因，建立完整证据表并产出可信备选优化项。与 matrix-first 粗筛 workflow 并行，按用例深钻而非按矩阵广覆盖。
---

# Platform Differential Discovery Deepdive Workflow

## 定位

按用例深钻的端到端剧本。输入是单个用例（来自粗筛 `workflow-platform-differential-discovery` 的候选用例清单，或用户直指），产物是单用例证据表 + 备选优化项。与粗筛 workflow 是流水线关系但相互独立——用户也可跳过粗筛直接指一个用例深钻。

## Agent 分派

| 阶段 | 对应用户流程步骤 | Agent | 技能 | Gate |
|------|-----------------|-------|------|------|
| 0 选例 | ① 先钻哪个用例 | `cinderx-orchestrator` | 读粗筛清单或用户直指 | 用例已锁定，实验轴齐全 |
| 1 环境确认 | — | `cinderx-environment-verifier` | `cinderx-env-validate` | 双平台环境可复用 |
| E1 性能基线 | ② 总性能数据 | `pyperformance-benchmark-analyst` | `pyperformance-result-compare` | 差距 > 噪声带，置信区间不含 0 |
| E2 用例画像 | ③ 用例内容 + autojit 函数形状 | `cinderx-jit-analyst` | `cinderx-hir-lir-analyze` | 函数形状与 perf 热点吻合 |
| E3 HIR 分布 | ④ HIR 分布 | `cinderx-jit-analyst` | `cinderx-hir-dump`、`cinderx-hir-lir-analyze` | 差异点定位到节点级 |
| E4 LIR + wall clock | ⑤ LIR 分析，含调用数与 wall clock | `cinderx-jit-analyst` | `cinderx-hir-lir-analyze` | wall clock 拆解与 LIR 段对齐 |
| E5 差异点 | ⑥ 差异点（bb 级或单条机器码级） | `cinderx-jit-analyst` | `cinderx-hir-lir-analyze` | 双平台指令逐条对齐，差异序列可枚举 |
| E6 根因下钻 | ⑦ 拆解根因到 ISA/指令集/微架构/硬件 | `cinderx-evidence-analyst` | `cinderx-evidence-table`、`cinderx-isa-microarch-compare` | 根因落到 ISA/微架构/硬件，证据闭环（含采样可用性探测） |
| E7 优化方向 | ⑧ 优化方向 | `cinderx-evidence-analyst` | `cinderx-evidence-table` | 策略 ↔ 根因一一对应 |
| E8 穿刺（跑） | ⑨ 穿刺 | `cinderx-orchestrator` → `pyperformance-candidate-runner` | `cinderx-ab-run-slot`、`pyperformance-worker-run` | 隔离满足、可重复 |
| E8 穿刺（判读） | ⑨ 穿刺数据可信度 | `cinderx-evidence-analyst` | `cinderx-evidence-table` | 收益落噪声带外，证据表签发可信度 |
| E9 优化价值 | ⑩ 备选优化项 | `cinderx-evidence-analyst` | `cinderx-evidence-table`、`cinderx-optimization-report` | 收益/成本均有数据支撑 |

## Gate

E1–E5 是证据采集（贴事实），E6–E9 是收口判读（下判断），分界线在 E6。任一阶段 Gate 不满足，**停在该阶段补证据**，不往后走：

- evidence-analyst 在 E6 接手时拿到 E1–E5 证据，填入证据表前 5 段（或标记 `evidence_gap` 要求补），再推进 E6–E9。
- evidence-analyst 在 E6 有权回退要求 E3–E5 补证据（如指令没对齐回到 E5）。
- E8 拆两半：穿刺跑分（orchestrator + candidate-runner）与穿刺判读（evidence-analyst）分离，判读权归 evidence-analyst。

有了足够深层的根因（E6），才不被表面原因迷惑；有了优化方向（E7），才进入穿刺（E8）；穿刺数据可信，才判定优化价值（E9），产出最终备选优化项。
```

- [ ] **Step 2: 运行布局校验，预期 PASS**

Run: `python plugins/cpython-optimize-skill/tests/validate_skill_layout.py`
Expected: PASS，输出 `layout validation passed`（白名单检查只管"要求的缺失"，新建未登记不触发失败；本步确认 workflow 目录 frontmatter 合法）。

- [ ] **Step 3: 提交**

```bash
git add plugins/cpython-optimize-skill/skills/workflow-platform-differential-discovery-deepdive/SKILL.md
git commit -m "Add platform differential discovery deepdive workflow"
```

---

### Task 4: 粗筛 workflow 加候选用例清单输出契约

**Files:**
- Modify: `plugins/cpython-optimize-skill/skills/workflow-platform-differential-discovery/SKILL.md`

先读现有全文确认锚点（需在脑中保留当前内容；以下是现有 SKILL.md 的完整结构：frontmatter → `# Platform Differential Discovery Workflow` → `## Agent 分派` 表 → `## Gate`）。本 Task 在 Gate 之后追加 `## 输出契约` 段。

- [ ] **Step 1: 读现有 workflow 确认锚点**

Run（仅查看，不改）: 用 Read 工具读取 `plugins/cpython-optimize-skill/skills/workflow-platform-differential-discovery/SKILL.md`，确认末尾是 Gate 段的一句话：`先建立 ISA、微架构、perf、benchmark 覆盖矩阵，再进入具体 HIR/LIR。`

- [ ] **Step 2: 在 Gate 段后追加输出契约**

用 Edit 工具，`old_string` 为现有 Gate 段全文：

```
## Gate

先建立 ISA、微架构、perf、benchmark 覆盖矩阵，再进入具体 HIR/LIR。
```

`new_string` 为：

```
## Gate

先建立 ISA、微架构、perf、benchmark 覆盖矩阵，再进入具体 HIR/LIR。

## 输出契约

产物是候选用例清单，供深钻 `workflow-platform-differential-discovery-deepdive` 的阶段 0 选例使用（推荐输入，非强制）。每个候选至少带：

- 用例名
- 双平台 wall clock 差距
- 热度信号
- 为何值得深钻（一句话）

清单回答"先钻哪个用例"，不回答"这个用例怎么优化"——后者交给深钻 workflow 的证据表。
```

- [ ] **Step 3: 运行布局校验，预期 PASS**

Run: `python plugins/cpython-optimize-skill/tests/validate_skill_layout.py`
Expected: PASS，输出 `layout validation passed`（粗筛 workflow 已在白名单内，仅追加段落不改结构）。

- [ ] **Step 4: 提交**

```bash
git add plugins/cpython-optimize-skill/skills/workflow-platform-differential-discovery/SKILL.md
git commit -m "Add candidate-cases output contract to matrix-first workflow"
```

---

### Task 5: router 加深钻路由 + 登记 evidence-analyst

**Files:**
- Modify: `plugins/cpython-optimize-skill/skills/using-cpython-optimize/SKILL.md`

现有 router 的两处需更新：`## Agent 路由` 表（加 evidence-analyst 行）、`## Workflow 路由` 列表（加深钻行）、`## 专业 Skill` 列表（加 `cinderx-evidence-table`）。

- [ ] **Step 1: Agent 路由表加 evidence-analyst**

用 Edit 工具，`old_string`：

```
| `cinderx-platform-analyst` | Kunpeng/x86、ISA、微架构差异 |
```

`new_string`：

```
| `cinderx-platform-analyst` | Kunpeng/x86、ISA、微架构差异 |
| `cinderx-evidence-analyst` | 单用例证据表、跨层根因下钻、穿刺判读 |
```

- [ ] **Step 2: Workflow 路由加深钻**

用 Edit 工具，`old_string`：

```
- 系统找平台优化点：`workflow-platform-differential-discovery`
```

`new_string`：

```
- 系统找平台优化点：`workflow-platform-differential-discovery`
- 深钻单用例拿可信优化点：`workflow-platform-differential-discovery-deepdive`
```

- [ ] **Step 3: 专业 Skill 列表加证据表**

用 Edit 工具，`old_string`：

```
`cinderx-hir-lir-analyze`、`cinderx-isa-microarch-compare`、`cinderx-optimization-report`、`validation-strategy`。
```

`new_string`：

```
`cinderx-hir-lir-analyze`、`cinderx-isa-microarch-compare`、`cinderx-evidence-table`、`cinderx-optimization-report`、`validation-strategy`。
```

- [ ] **Step 4: 提交**

```bash
git add plugins/cpython-optimize-skill/skills/using-cpython-optimize/SKILL.md
git commit -m "Route deepdive workflow and register evidence-analyst"
```

---

### Task 6: 更新布局校验白名单

**Files:**
- Modify: `plugins/cpython-optimize-skill/tests/validate_skill_layout.py`

- [ ] **Step 1: `REQUIRED_SKILLS` 加两项**

用 Edit 工具，`old_string`：

```
    "workflow-feature-driven-optimization",
    "workflow-platform-differential-discovery",
}
```

`new_string`：

```
    "workflow-feature-driven-optimization",
    "workflow-platform-differential-discovery",
    "workflow-platform-differential-discovery-deepdive",
    "cinderx-evidence-table",
}
```

- [ ] **Step 2: `REQUIRED_AGENTS` 加 evidence-analyst**

用 Edit 工具，`old_string`：

```
    "cinderx-platform-analyst.md",
}
```

`new_string`：

```
    "cinderx-platform-analyst.md",
    "cinderx-evidence-analyst.md",
}
```

- [ ] **Step 3: 运行布局校验，预期 PASS**

Run: `python plugins/cpython-optimize-skill/tests/validate_skill_layout.py`
Expected: PASS，输出 `layout validation passed`

- [ ] **Step 4: 运行两个 router 回归测试，预期都 PASS**

Run: `python plugins/cpython-optimize-skill/tests/test_runtime_skill_router.py`
Expected: PASS，输出 `runtime hook router validation passed`

Run: `python plugins/cpython-optimize-skill/tests/test_validation_skill_router.py`
Expected: PASS，输出 `validation hook router validation passed`

- [ ] **Step 5: 提交**

```bash
git add plugins/cpython-optimize-skill/tests/validate_skill_layout.py
git commit -m "Register deepdive workflow, evidence-table skill and evidence-analyst agent in layout validator"
```

---

## 验收清单

全部完成后，整体验证一次：

- [ ] **验收 Step 1: 三项测试全绿**

Run:
```
python plugins/cpython-optimize-skill/tests/validate_skill_layout.py && python plugins/cpython-optimize-skill/tests/test_runtime_skill_router.py && python plugins/cpython-optimize-skill/tests/test_validation_skill_router.py
```
Expected: 三行 PASS 输出，退出码 0。

- [ ] **验收 Step 2: 核对 spec 覆盖**

逐条对照 `docs/superpowers/specs/2026-06-21-evidence-driven-deepdive-design.md`：

| Spec 要求 | 落地 Task |
|-----------|----------|
| 新建 `cinderx-evidence-table` skill（E1–E9 + E6 工具表 + SPE/IBS 原则不绑平台结论） | Task 1 |
| 新建 `cinderx-evidence-analyst` agent（跨层追因、E6 接手、穿刺判读权） | Task 2 |
| 新建 `workflow-platform-differential-discovery-deepdive`（12 阶段分派表、E6 分界） | Task 3 |
| 粗筛 workflow 加候选用例清单输出契约 | Task 4 |
| router 加深钻路由 + 登记 evidence-analyst + 登记 evidence-table skill | Task 5 |

Expected: 五条全部有对应 Task，无遗漏。
