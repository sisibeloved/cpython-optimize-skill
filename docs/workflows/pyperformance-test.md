# pyperformance 测试

## 目标

统一 `pyperformance` 的测试入口、环境变量和结果解读方式，避免命令口径漂移。

## 三种入口

1. `python -m pyperformance run`
   - 官方入口
   - 适合回归和全量 smoke
2. 直接执行单个 `run_benchmark.py`
   - 适合单用例定位、gdb、JIT 日志采集
3. 批量直跑脚本
   - 适合快速扫描 crash 与性能异常

默认建议：
- 功能验证和 crash 复现：优先单个 `run_benchmark.py`
- 全量 smoke 和官方口径：优先 `python -m pyperformance run`
- 需要快速扫大量用例时，再用批量直跑脚本

## 真实命令参考

保留两类经过真实环境验证的命令模板：
- `references/commands/pyperformance-run-realenv.sh`
- `references/commands/run-benchmark-worker-realenv.sh`

使用方式：
- 不直接把工作流文档里的说明当命令运行
- 从 `references/commands/` 复制，再按机器路径、benchmark 名和日志路径修改

## 关键环境变量

- `PYTHONJITAUTO`
- `PYTHONJITSPECIALIZEDOPCODES`
- `PYTHONJITTYPEANNOTATIONGUARDS`
- `PYTHONJITENABLEHIRINLINER`
- `PYTHONJITHUGEPAGES`
- `PYTHONJITLOGFILE`
- `PYTHONJITDUMPFINALHIR`
- `PYTHONJITDUMPSTATS`
- `LD_LIBRARY_PATH`
- `PYTHONPATH`

额外经验：
- 真实环境跑 `pyperformance run` 时，`LD_LIBRARY_PATH` 必须显式继承到 worker
- JIT benchmark 功能验证时必须先打开 HIR dump，确认真的进了 CinderX JIT
- 跑性能数据时再关闭大部分 dump，避免日志和 dump 干扰
- 在 ARM / Kunpeng 上，`PYTHONJITHUGEPAGES=0` 常常是必需护栏

## 进程模型

`pyperformance run` 需要区分：
- driver
- benchmark manager
- pyperf worker
- 外部子命令子进程

要点：
- `--debug-single-value` 会改变 loops / warmups / values，不能把它的结果直接当真实性能
- `bench_command()` 类用例会拉起外部 Python 子进程，JIT 环境变量会继续继承过去
- 对 `sitecustomize` / hook 而言，要优先确认“真正执行 benchmark 的 worker”有没有命中逻辑

调试时必须先明确：
- 哪个进程真正执行 benchmark
- 哪个进程真正开启了 JIT
- 环境变量是否传到 worker
- worker 是否看得到 `_cinderx` / `cinderjit`

## 原则

- 功能验证时先开 HIR dump，确认真的进了 CinderX JIT
- 性能测试时再关掉大部分 dump，避免污染结果
- `bench_command` 类 benchmark 需要特别关注子进程环境继承
- 如果 `python -m pyperformance run` 行为异常，而单个 `run_benchmark.py` 正常，优先怀疑 worker/外部子进程模型差异
