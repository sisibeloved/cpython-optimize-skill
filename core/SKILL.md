---
name: cpython-cinderx-optimize-core
description: Use when在个人工作流中系统化执行 CPython/CinderX 优化任务，需要统一环境、测试、分析、文档和产物约定。
---

# 核心层

这是整个技能仓库的统一入口。平台差异只负责补充工具映射和路径习惯，不重新定义主流程。

## 执行顺序

1. 先确认工作目标
   - 环境准备
   - 编译安装
   - 基准测试
   - 用例分析
   - 文档沉淀
2. 再选平台包装
3. 最后进入对应工作流文档

## 主工作流

- 环境获取：`docs/workflows/ssh-connection.md`
- CPython/CinderX 编译：`docs/workflows/build-and-install.md`
- `pyperformance` 测试：`docs/workflows/pyperformance-test.md`
- Docker 运行时隔离：`docs/workflows/docker-runtime.md`
- 文档规范：`docs/workflows/documentation.md`
- 用例分析：`docs/workflows/case-analysis.md`
- 快速路由：`docs/playbooks/entry-decision-table.md`

## 版本策略

- `v0.2`：以 CinderX 优先的个人作战手册为当前稳定基线
- 后续版本：在保持双线 Docker、真实命令模板和 pressure test 的前提下迭代
- 允许强绑定：
  - Kunpeng / ARM
  - Docker
  - `pyperformance`
  - 强制覆盖安装
  - 真实环境优先

## 产物约定

最小交付集合：
- `baseline/run.json`
- `candidate/run.json`
- `speedup.json`
- `report.md`

如果是 crash / regression 调查，还应补：
- `debug.log`
- `jit.log`
- `gdb bt`
- HIR / LIR / 反汇编片段
