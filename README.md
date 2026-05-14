# 🔧 CPython/CinderX 性能优化技能仓库

面向个人工作流的 CPython/CinderX 性能优化与设计文档技能集合，以 [Claude Code 技能插件](https://agentskills.io/) 形式交付。

---

## 📦 技能一览

| 技能 | 用途 | 自带资源 |
|------|------|---------|
| 🎯 `using-cpython-optimize` | 引导入口，自动注入 | — |
| 🔌 `remote-environment` | SSH、tmux、rsync | — |
| 🔨 `cpython-build` | CPython/CinderX 编译与安装 | — |
| 🐳 `docker-runtime` | Docker 双线隔离 | templates/、scripts/ |
| 📊 `pyperformance-test` | 基准测试、性能口径、crash triage | references/、scripts/ |
| 🔬 `cinderx-analysis` | JIT/非 JIT 分析、HIR/LIR 定位 | references/ |
| 📝 `experiment-documentation` | 实验记录、报告模板 | references/ |
| 📐 `design-documentation` | 架构/系统/功能/详细设计文档 | references/ |

---

## 🚀 安装

### Claude Code（插件市场）

```
/plugin marketplace add https://github.com/sisibeloved/cpython-optimize-skill
/plugin install cpython-optimize-skill
```

安装后，新会话启动时 `using-cpython-optimize` 引导技能会通过 SessionStart hook 自动注入上下文。

### Codex

将仓库放入 `~/.codex/skills/` 或通过 Codex 插件机制安装。

---

## 💬 使用示例

```
> 帮我在 Kunpeng 上编译 CinderX 并跑一次 pyperformance
> regex_compile 在容器里 SIGSEGV 了，帮我复现和定位
> 对比 stock CPython JIT 和 CinderX JIT 的 pyperformance 数据
> 帮我写一份 CinderX JIT 优化点的架构设计说明书
```

Agent 会根据任务自动选择对应技能，无需手动加载。

---

## 📁 仓库结构

```
.
├── .claude-plugin/              # Claude Code 插件注册
│   ├── marketplace.json         # 插件市场元数据
│   └── plugin.json              # 插件描述
├── .codex-plugin/               # Codex 插件注册
├── hooks/                       # SessionStart 自动注入
│   ├── hooks.json
│   └── session-start
├── skills/                      # 8 个自包含子技能
│   ├── using-cpython-optimize/
│   ├── remote-environment/
│   ├── cpython-build/
│   ├── docker-runtime/
│   ├── pyperformance-test/
│   ├── cinderx-analysis/
│   ├── experiment-documentation/
│   └── design-documentation/
├── tests/                       # 结构验证 + 压力测试场景
├── docs/                        # 仓库级文档（plans、design）
├── package.json
└── CHANGELOG.md
```

每个技能自包含 `SKILL.md` + 专属 `references/`、`scripts/`、`templates/`，技能间通过 Skill 工具互相调用。

---

## ✅ 验证

```bash
python3 tests/validate_skill_layout.py
```

## 📜 版本历史

见 [CHANGELOG.md](CHANGELOG.md)。

## 📄 许可

MIT
