# Agent 互操作

## 目标

让 Codex、Claude Code、OpenCode、OpenClaw 在同一套个人优化工作流下协作，同时不丢失结构化产物。

## 共享规则

- 统一从仓库根目录进入工作流
- 交换 JSON、日志、回归结论，不只交换口头描述
- 平台差异写在 `platforms/`，不写进核心流程

## 最小交接产物

- `baseline/run.json`
- `candidate/run.json`
- `speedup.json`
- `report.md`

如果是 crash / regression 调查，再补：
- `debug.log`
- `jit.log`
- `bt.txt`
