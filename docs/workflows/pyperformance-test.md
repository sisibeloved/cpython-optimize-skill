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
- dump HIR 时优先使用“真实命令 + debug 环境变量”的形式，不要先跑一条简化命令再单独分析另一份 HIR

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
- 分析阶段和测试阶段应尽量共用同一条真实命令，只通过 debug 环境变量增减观测项

## 性能口径

正式讨论性能前，必须先明确当前是哪一种口径：

1. `CPython 解释执行`
2. `CPython JIT`
3. `CinderX 解释执行`
4. `CinderX JIT`

默认对照原则：
- JIT 和 JIT 比
- 解释执行和解释执行比
- 这条性能线主要回答：`CinderX` 相对原生 `CPython` 是否有收益

常见组合：
- `CPython 解释执行` vs `CinderX 解释执行`
- `CPython JIT` vs `CinderX JIT`

最小区分原则：
- `CPython 解释执行`：不启 CPython JIT，不启 CinderX JIT
- `CPython JIT`：只启 CPython JIT
- `CinderX 解释执行`：导入/安装 CinderX，但不显式启用 CinderX JIT
- `CinderX JIT`：显式开启 CinderX JIT，并用 HIR / jit.log 证明 benchmark 本体已编译

与 CinderX JIT 口径强相关的环境变量：
- `PYTHONJITAUTO`
- `PYTHONJITSPECIALIZEDOPCODES`
- `PYTHONJITTYPEANNOTATIONGUARDS`
- `PYTHONJITENABLEHIRINLINER`
- `PYTHONJITHUGEPAGES`
- `PYTHONJITLOGFILE`
- `PYTHONJITDUMPFINALHIR`
- `PYTHONJITDUMPSTATS`
- `PYTHONPATH`
- `LD_LIBRARY_PATH`

注意：
- `PYTHONJITLOGFILE` / `PYTHONJITDUMPFINALHIR` 这类变量属于调试观测变量，不应默认带入正式性能口径
- `CinderX 解释执行` 与 `CinderX JIT` 的分界，必须靠是否显式启用 JIT 来确认，而不是只看是否安装了 `cinderx`

## baseline 的定义

`baseline` 这个词至少有两种常见含义，必须在文档和报告里写清楚：

1. 口径基线
   - 例如 `CPython JIT` 是 `CinderX JIT` 的对照基线
   - 这条线回答的是：CinderX 相对原生 CPython 是否有收益

2. 提交基线
   - 例如“改动前那个 commit”
   - 这条线回答的是：当前改动相对改动前是否提升或退化

禁止混用：
- 如果是在做“自提升”分析，`baseline` 默认指改动前提交
- 如果是在做“CinderX vs CPython”分析，`baseline` 默认指对照解释器口径
- 报告里必须写清：当前 baseline 是“口径基线”还是“提交基线”

## 跨平台口径

Arm vs x86 对比属于第三条线：
- 隐含前提是参数必须一致
- 也隐含要求口径一致，例如 `JIT vs JIT`、`解释执行 vs 解释执行`

跨平台对比前至少要对齐：
- benchmark 命令
- 关键环境变量
- JIT 开关状态
- dump/debug 变量是否开启
- warmup / loops / affinity 等运行参数

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
- dump HIR 时优先用真实测试命令，只叠加 debug 环境变量；不要分裂成“测试命令”和“分析命令”两套口径
- 做对比前先写清当前属于：口径基线、提交基线，还是跨平台对比
