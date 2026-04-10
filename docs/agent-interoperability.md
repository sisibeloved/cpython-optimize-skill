# Agent 互操作性

## 支持的 Agent
- Codex
- Claude Code
- OpenCode
- OpenClaw

## 共享规则
- 从仓库根目录直接调用脚本。
- 通过 `--command` 字符串传递基准测试命令。
- 交换 JSON 产物，不交换临时口头解释。

## 产物交接

协作时的最小产物集合：
- `baseline/run.json`
- `candidate/run.json`
- `speedup.json`
- `report.md`
