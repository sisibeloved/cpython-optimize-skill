# Evidence-Driven Deepdive 设计

## 背景与问题

`workflow-platform-differential-discovery`（matrix-first）在系统找平台优化点时效果不佳。
用户归纳出一套按用例深钻的流程：先深钻单个用例 → 贴性能数据 → 描述用例与 autojit
函数形状 → HIR 分布 → LIR + wall clock → 差异点 → 根因下钻到 ISA/指令集/微架构/硬件 →
优化方向 → 穿刺验证 → 判定优化价值。这套流程与现有 matrix-first Gate 存在张力。

本设计把这套流程沉淀为可复用资产，**不破坏**现有 matrix-first workflow。

## 关键决定（brainstorming 共识）

1. **两层并行**：保留 matrix-first 粗筛 workflow，新增按用例深钻 workflow，router 按目标选择。
2. **新建 `cinderx-evidence-table` skill**：定义证据表结构、每步必填字段、证据闭环判据。被深钻
   workflow 与用例性能调优 workflow 共同复用。
3. **新建 `cinderx-evidence-analyst` agent**：跨层追因负责人，现有 jit/platform analyst 作为其
   上游证据提供者。
4. **粗筛 workflow 加输出契约**：候选用例清单，作为深钻 workflow 的推荐输入。
5. **skill 列出每层根因必带的工具输出**：机器码/ISA/微架构/硬件，含采样可用性探测。

## 拓扑

```
router (using-cpython-optimize)
├── 目标=系统找平台优化点（广覆盖）
│   └── workflow-platform-differential-discovery  [改：加输出契约]
│         产物：候选用例清单 candidate-cases.jsonl
│                    │（推荐输入，非强制）
│                    ▼
├── 目标=深钻单用例拿可信优化点
│   └── workflow-platform-differential-discovery-deepdive  [新建]
│         输入：单用例（来自清单 或 用户直指）
│         产物：单用例证据表 + 备选优化项
│         调用：cinderx-evidence-analyst (新) + cinderx-evidence-table (新)
│
└── 目标=用例性能调优（非平台差异）
    └── workflow-jit-optimization-analysis  [复用 evidence-table skill]
```

粗筛回答"先钻哪个"，深钻回答"这个用例值不值得优化、怎么优化"。两者是流水线关系，
但用户也可跳过粗筛直接指一个用例深钻。

## 新 skill `cinderx-evidence-table`

### 证据表结构

一张表，9 行（E1–E9），每行三段式：What（必贴客观证据）/ Verdict（一句结论）/
Gate（证据足够硬条件）。任一段不满足 Gate，证据表标记 `evidence_gap`/`verdict_missing`，
**流程停下来补证据**，不跳过。

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

第 1 步"先钻哪个用例"不在表内，是 workflow 层选例动作，证据表从 E1 起假设用例已选定。

### E6 根因层级的必带工具证据

通用必带（所有平台）：`perf stat` 的 cycles/instructions/cache-references/cache-misses/
branch-misses，双平台同口径采集。

| 根因层 | 必带工具输出（缺则 evidence_gap） |
|--------|------------------------------------|
| 机器码 | `objdump -d` 反汇编，双平台对齐 |
| ISA/指令集 | 指令选择差异、SIMD/原子/barrier 形态（对照 `cinderx-isa-microarch-compare` 矩阵） |
| 微架构 | `perf stat` 关键计数器（cycles/instructions/cache-miss/branch-miss）、`perf top` |
| 硬件 | PMU 计数器、必要时的 uops.info / llvm-mca 吞吐估算、cache/TLB 行为 |

### 指令级采样机制（SPE/IBS）处理原则

指令级精确采样在两平台是**不同机制、都有硬性开启条件**，且具体可用性随平台/内核/权限而变。
skill 只规定**处理原则**，不绑定任何特定平台的可用性结论：

1. **采样可用性是证据链前置判据，非默认前提**。E6 开头先做探测：
   - ARM 侧：`perf list | grep arm_spe` + 检查 `/sys/bus/event_source/devices/arm_spe_*/`。
     为空则 SPE 证据不可得，退化为 PMU 计数器 + `perf top`。
   - x86 侧：检查 `/sys/bus/event_source/devices/ibs_op/` 与权限（IBS 无用户/内核过滤，需
     `CAP_SYS_ADMIN` 或 `CAP_PERFMON`）。无特权则 IBS 证据不可得，退化为 top-down metric group。
   - 探测结果本身作为 E6 第一条证据记录，明确"本平台能拿到什么层级证据、缺什么"。

2. **估算必标置信度**。uops.info / llvm-mca 是吞吐估算而非实测；Zen4/Zen5 无每端口 uops PMU
   （Saarland port-mapping 论文），ARM 侧 uops.info 不覆盖。证据表必须标"估算来源 + 置信度"。

3. **不对称证据显式化**。当一侧能拿到指令级采样、另一侧拿不到时，证据表不得直接对比不对称
   采样数据。根因下钻以能拿到证据的一侧为锚，对侧只提供 PMU 级证据，并在 Verdict 标注根因
   置信度折扣。

## 新 agent `cinderx-evidence-analyst`

**职责**：证据表唯一负责人，跨层追因（HIR/LIR→机器码→ISA→微架构→硬件），把分散在
platform/jit analyst 的证据收口成一张可信证据表。对"证据够不够、根因对不对"负责。

**与现有 agent 边界**：

| Agent | 角色 | 深钻流程位置 |
|-------|------|--------------|
| `cinderx-jit-analyst` | 提供 E2–E5 证据（HIR、LIR、机器码、指令对齐） | 上游证据提供者 |
| `cinderx-platform-analyst` | 提供 E6 硬件层平台矩阵 | 上游证据提供者 |
| `cinderx-evidence-analyst`（新） | 收口 E1–E9、跨层根因下钻、证据闭环判定、优化方向推导、穿刺数据判读 | 证据表唯一负责人 |

**能力边界（明确不做）**：
- 不跑 pyperformance、不做环境 bootstrap（verifier/runner 的事）。
- 不亲自 dump HIR/LIR（调 jit-analyst 的 `cinderx-hir-lir-analyze`）。
- 不写代码改 CinderX（穿刺实现由 orchestrator 另行分派）。

**亲自做（不外包，核心判断职责）**：
- 采样可用性探测、PMU 采集命令设计、根因置信度判定。
- 穿刺数据判读：E8 的 A/B 由 ab-run-slot + runner 跑，evidence-analyst 对穿刺数据可信度
  负责（隔离、可重复、收益落噪声带外）。不合格有权打回备选优化项。

**触发条件**：
> Use when 需要对单个用例建立从性能数据到根因的完整证据链，做跨层（HIR/LIR/机器码/ISA/
> 微架构/硬件）归因、判定证据是否闭环、推导优化方向并判读穿刺数据。不亲自执行 perf/HIR
> dump，而是编排 jit/platform analyst 收集证据并对闭环负责。

## 新 workflow `workflow-platform-differential-discovery-deepdive`

| 阶段 | 对应用户步骤 | Agent | 技能 | Gate |
|------|-------------|-------|------|------|
| 0 选例 | 10步① | `cinderx-orchestrator` | 读粗筛清单或用户直指 | 用例已锁定，实验轴齐全 |
| 1 环境确认 | — | `cinderx-environment-verifier` | `cinderx-env-validate` | 双平台环境可复用 |
| E1 性能基线 | 10步② | `pyperformance-benchmark-analyst` | `pyperformance-result-compare` | 差距 > 噪声带，置信区间不含 0 |
| E2 用例画像 | 10步③ | `cinderx-jit-analyst` | `cinderx-hir-lir-analyze` | 函数形状与 perf 热点吻合 |
| E3 HIR 分布 | 10步④ | `cinderx-jit-analyst` | `cinderx-hir-dump`、`cinderx-hir-lir-analyze` | 差异点定位到节点级 |
| E4 LIR + wall clock | 10步⑤ | `cinderx-jit-analyst` | `cinderx-hir-lir-analyze` | wall clock 拆解与 LIR 段对齐 |
| E5 差异点 | 10步⑥ | `cinderx-jit-analyst` | `cinderx-hir-lir-analyze` | 双平台指令逐条对齐，差异序列可枚举 |
| E6 根因下钻 | 10步⑦ | `cinderx-evidence-analyst`（新） | `cinderx-evidence-table`（新）、`cinderx-isa-microarch-compare` | 根因落到 ISA/微架构/硬件，证据闭环（含采样探测） |
| E7 优化方向 | 10步⑧ | `cinderx-evidence-analyst` | `cinderx-evidence-table` | 策略 ↔ 根因一一对应 |
| E8 穿刺（跑） | 10步⑨ | `cinderx-orchestrator`→`pyperformance-candidate-runner` | `cinderx-ab-run-slot`、`pyperformance-worker-run` | 隔离满足、可重复 |
| E8 穿刺（判读） | 10步⑨ | `cinderx-evidence-analyst` | `cinderx-evidence-table` | 收益落噪声带外，证据表签发可信度 |
| E9 优化价值 | 10步⑩ | `cinderx-evidence-analyst` | `cinderx-evidence-table`、`cinderx-optimization-report` | 收益/成本均有数据支撑 |

### 编排要点

1. **E1–E5 证据采集，E6–E9 收口判读**。分界线在 E6：之前是"贴事实"，之后是"下判断"。
2. **Gate 失败即停**。任一阶段 Gate 不满足，停在该阶段补证据，不往后走。evidence-analyst 在
   E6 有权回退要求 E3–E5 补证据（如指令没对齐回到 E5）。
3. **证据表是贯穿物**。evidence-analyst 在 E6 接手时拿到 E1–E5 证据，填入证据表前 5 段（或
   标记 `evidence_gap` 要求补），再推进 E6–E9。
4. **E8 拆两半**：穿刺跑分（orchestrator + runner）与穿刺判读（evidence-analyst）分离，判读
   权归 evidence-analyst。

## 粗筛 workflow 输出契约

`workflow-platform-differential-discovery` 加输出契约：候选用例清单。每个候选至少带：
- 用例名
- 双平台 wall clock 差距
- 热度信号
- 为何值得深钻（一句话）

此清单是深钻 workflow 阶段 0 的推荐输入，非强制。

## Router 更新

`using-cpython-optimize` 的 Workflow 路由表加一行：

| 目标 | 路由到 |
|------|--------|
| 深钻单用例拿可信优化点 | `workflow-platform-differential-discovery-deepdive` |

现有"系统找平台优化点"仍路由到粗筛 `workflow-platform-differential-discovery`。

## 范围边界

**本设计包含**：
- 新建 `cinderx-evidence-table` skill
- 新建 `cinderx-evidence-analyst` agent
- 新建 `workflow-platform-differential-discovery-deepdive` workflow
- 粗筛 workflow 加输出契约
- router 加深钻路由

**本设计不包含**：
- 不改 evidence-analyst/jit/platform analyst 的底层技能实现
- 不改环境 verifier、runner、ab-run-slot 逻辑
- 不改证据表判据的默认数值（噪声带、样本数、置信区间）——用 skill 默认值，用户可调
