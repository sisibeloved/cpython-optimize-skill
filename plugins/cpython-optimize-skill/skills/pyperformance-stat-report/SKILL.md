---
name: pyperformance-stat-report
description: Use when 已有两个或更多 pyperformance JSON 结果文件，需要用 bundled scripts/get_stat.py 生成多轮统计表、console-only 对比、Excel 表格或分页趋势 PNG 报告。
---

# pyperformance Stat Report

负责把已存在的 pyperformance JSON 结果整理成适合人工阅读和汇报的统计产物。此 skill 只读结果，不负责跑 benchmark，也不能替代 `pyperformance-result-compare` 对 baseline source、CPU affinity、worker env、噪声和可信度的判断。

CinderX/JIT 性能结论必须先确认结果满足 `../using-cpython-optimize/references/pyperformance-env-contract.md`；`get_stat.py` 只格式化已有数据。

## 输入

- 两个或更多 `run.json` / pyperformance JSON 文件，按对比顺序传入。
- 第一个 JSON 是 ratio 计算的 baseline。
- 可选 benchmark 名称，用于只输出指定用例。

## 脚本

使用 bundled helper：

```bash
python skills/pyperformance-stat-report/scripts/get_stat.py [-c] [-b <benchmark> ...] <baseline.json> <candidate.json> [more.json ...]
```

从希望写入报告产物的目录执行，或传入 JSON 的绝对路径。未传 JSON 时脚本会扫描当前目录 `*.json`；正式报告中优先写显式路径。

## 模式

- `-c` / `--console-only`：只打印对比表，不生成文件，不需要 `openpyxl` 或 `matplotlib`。
- 默认模式：打印表格后生成 `benchmark_comparison.xlsx` 和 `benchmark_trends_part<N>.png`。
- `-b` / `--benchmarks`：只保留指定的公共 benchmark，并保持用户给定顺序。

默认产物模式需要：

```bash
python -m pip install openpyxl matplotlib
```

## 语义

- 只比较所有有效 JSON 共有的 benchmark。
- 单项 ratio 和几何平均都使用 `baseline_time / current_time`。
- ratio 大于 `1.0` 表示快于第一个 JSON；小于 `1.0` 表示慢于第一个 JSON。
- 显示单位按 baseline 文件中该 benchmark 的耗时量级选择。

## 输出要求

使用此 skill 时必须输出：

- 真实命令和 working directory；
- JSON 顺序，以及哪个文件是 baseline；
- benchmark filter（如使用）；
- 公共 benchmark 数量；
- 生成的 `benchmark_comparison.xlsx` / `benchmark_trends_part<N>.png` 路径，或说明使用了 `--console-only`；
- 被跳过的 JSON 或未命中的指定 benchmark。
