# 阶段角色索引

仅在需要角色交接或实际委派时读取。Agent 文档不是原生 Skill 自动触发单元：相对于插件根目录读取 `agents/<agent>.md`。角色名称不保证宿主提供同名 agent type；宿主未开放委派或用户要求顺序执行时，由主 Agent 承担对应职责。

| Agent | 职责 |
|-------|------|
| `cinderx-orchestrator` | 选择 Workflow、衔接阶段并合并结果 |
| `cinderx-environment-verifier` / environment-verifier | 环境三态：可复用、新环境、被破坏；独立校验 baseline source |
| `pyperformance-baseline-runner` / baseline-runner | baseline slot 运行与产物 |
| `pyperformance-candidate-runner` / candidate-runner | candidate slot 运行与产物 |
| `pyperformance-benchmark-analyst` | run.json / speedup.json 的可信度与收益判读 |
| `cinderx-crash-triager` / crash-triager | native crash 复现、gdb/core 取证 |
| `cinderx-jit-analyst` | JIT 进入判定、HIR/LIR 或解释执行分析 |
| `cinderx-platform-analyst` | ISA、微架构与 perf 平台归因 |
| `cinderx-evidence-analyst` | E1–E9 证据表、跨层根因和穿刺可信度 |

委派时给出具体问题、已有证据、文件/运行资源边界和所需产物；只交接相关角色文档与 Skill。A/B 并行依赖 `cinderx-ab-run-slot` 的隔离证据。环境与源码可信性门禁不因角色由同一 Agent 执行而省略。
