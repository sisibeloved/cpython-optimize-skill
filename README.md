# CPython/CinderX 性能优化技能仓库

面向个人工作流的 CPython/CinderX 性能优化技能集合，以 [Claude Code 技能插件](https://agentskills.io/) 形式交付。覆盖从远程环境搭建到实验文档沉淀的完整闭环。

## 技能概览

本仓库包含 7 个自包含技能，每个技能独立拥有 SKILL.md、参考文档、脚本和模板：

| 技能 | 用途 | 自带资源 |
|------|------|---------|
| `using-cpython-optimize` | 引导入口，决策流程图 | — |
| `remote-environment` | SSH 连接、tmux 会话、rsync 同步 | — |
| `cpython-build` | CPython/CinderX 编译与强制覆盖安装 | — |
| `docker-runtime` | Docker 双线隔离（基线线 + 调试线） | templates/、scripts/ |
| `pyperformance-test` | pyperformance 基准测试、性能口径、crash triage | references/、scripts/ |
| `cinderx-analysis` | JIT/非 JIT 用例分析、HIR/LIR 定位 | references/ |
| `experiment-documentation` | 实验记录、报告模板、产物约定 | references/ |

### 工作流顺序

```
开始 → remote-environment → docker-runtime → cpython-build → pyperformance-test → cinderx-analysis → experiment-documentation
```

按需进入，不是每步都必须。已有环境时跳过对应步骤。

## 核心原则

- **默认 Docker 隔离** — 远程环境不直接在裸机上工作，先项目隔离（宿主机独立目录），再环境隔离（Docker 容器）
- **证据先行** — 先拿可复现证据，再下根因结论
- **结构化产物** — 用 `run.json`、`speedup.json`、`report.md` 沉淀实验结果，避免只留口头结论
- **口径明确** — 正式性能对比前必须定义口径（CPython 解释执行 / CPython JIT / CinderX 解释执行 / CinderX JIT），baseline 必须写清是"口径基线"还是"提交基线"

## 安装

```bash
# 本地安装（开发中）
claude plugin add /path/to/cpython-optimize-skill

# Codex
# 将仓库放入 ~/.codex/skills/ 或通过 Codex 插件机制安装
```

安装后，新会话启动时 `using-cpython-optimize` 引导技能会通过 SessionStart hook 自动注入上下文，无需手动加载。

## 使用

安装完成后，在 Claude Code 中直接对话即可。示例：

```
> 帮我在 Kunpeng 上编译 CinderX 并跑一次 pyperformance
> regex_compile 在容器里 SIGSEGV 了，帮我复现和定位
> 对比 stock CPython JIT 和 CinderX JIT 的 pyperformance 数据
> 帮我抓一下这个函数的 HIR 看看有没有优化点
```

Agent 会根据任务自动选择对应技能。也可以通过 Skill 工具手动加载特定技能：

```
/skill pyperformance-test
```

## 仓库结构

```
.
├── .claude-plugin/plugin.json       # Claude Code 插件注册
├── .codex-plugin/plugin.json        # Codex 插件注册
├── hooks/
│   ├── hooks.json                   # SessionStart hook 定义
│   └── session-start                # 自动注入引导技能的脚本
├── skills/
│   ├── using-cpython-optimize/      # 引导技能
│   ├── remote-environment/          # SSH / tmux / rsync
│   ├── cpython-build/               # 编译与安装
│   ├── docker-runtime/
│   │   ├── templates/               # Docker Compose 模板（cpython-baseline、cinderx-test）
│   │   └── scripts/                 # setup.sh、smoke.sh
│   ├── pyperformance-test/
│   │   ├── references/              # 真实环境命令模板、crash triage 指南
│   │   └── scripts/                 # benchmark 脚本
│   ├── cinderx-analysis/
│   │   └── references/              # 性能口径定义
│   └── experiment-documentation/
│       └── references/              # 产物 schema
├── tests/                           # 仓库结构验证 + 压力测试场景
├── docs/plans/                      # 开发计划文档
├── package.json
└── CHANGELOG.md
```

每个技能目录自包含：`SKILL.md` 是入口，`references/`、`scripts/`、`templates/` 是专属资源。技能间通过 Skill 工具互相调用，不依赖共享文件。

## 性能口径速查

正式对比前必须明确口径，不同口径不能横向比较：

| 口径 | 说明 | JIT 状态 |
|------|------|---------|
| `CPython 解释执行` | stock CPython 基线 | 关 |
| `CPython JIT` | stock CPython + JIT | 开 |
| `CinderX 解释执行` | 安装 cinderx 但不启 JIT | 关 |
| `CinderX JIT` | 显式启用 CinderX JIT | 开 + HIR 验证 |

默认对照：JIT 和 JIT 比，解释执行和解释执行比。

## Docker 双线

| 线路 | 用途 | 侧重点 |
|------|------|--------|
| `cinderx-test` | 功能验证、HIR dump、crash 复现 | correctness |
| `cpython-baseline` | stock CPython vs CinderX 正式对照 | 公平性 |

先走 `cinderx-test` 完成功能确认，再走 `cpython-baseline` 做正式对照。

## 验证

```bash
python3 tests/validate_skill_layout.py   # 校验仓库目录层级和技能 frontmatter
```

## 版本历史

见 [CHANGELOG.md](CHANGELOG.md)。

## 许可

MIT
