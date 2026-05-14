---
name: experiment-documentation
description: 在需要记录实验结果、写性能分析报告、规范产物格式时使用
---

# 文档规范

## 目标

让实验、回归和 crash 定位结果可以被后续 Agent 或未来的自己直接消费。

## 推荐目录

- `docs/guides/` — 过程性修复记录

## 推荐命名

- `YYYY-MM-DD-topic.md`
- 标题直接写问题域，不写模糊词

## 每篇文档最少包含

- 背景
- 复现命令
- 证据链
- 根因
- 修复方法
- 回归结果

## 推荐模板

### 背景

说明问题场景、平台、分支和目标。

### 复现命令

给出真实可执行命令，避免只写伪代码。

### 证据链

记录：
- 日志
- JIT/HIR/LIR
- `gdb bt`
- 关键环境变量

### 根因

明确指出根因，不只描述现象。

### 修复方法

写清改动点、护栏或验证手段。

### 回归结果

列出：
- 是否复现消失
- 哪些 benchmark 通过
- 是否存在已知残余风险

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

产物格式参考：`references/report_schema.example.json`
