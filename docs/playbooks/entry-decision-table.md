# 入口决策表

这页只回答一个问题：**现在应该走哪条线、用哪个入口。**

## Docker 线怎么选

| 当前目标 | 选择 |
|---|---|
| 验证 benchmark 是否真的进入 CinderX JIT | `cinderx-test` |
| 抓 HIR / JIT log / native crash / gdb | `cinderx-test` |
| 做 stock CPython JIT vs CinderX 的正式对照 | `cpython-baseline` |
| 怀疑 Docker 本身与真实环境有差异，需要最终复核 | 回到 Kunpeng 宿主机 |

## 宿主机目录怎么选

| 当前目标 | 选择 |
|---|---|
| 新 Agent 进入远程环境 | 先创建独立宿主机目录 |
| 已存在目录不确定是否被他人使用 | 不复用，重新建目录 |
| 准备 bind mount 到容器 | 只挂当前 Agent 自己的目录 |
| 需要同步代码仓 | 优先 `rsync` 到当前 Agent 目录 |

## Docker 调试终端怎么选

| 当前目标 | 入口 |
|---|---|
| 连续调试、反复看日志、手动跑命令 | 先进入一个固定的长连接交互 shell |
| 一次性自动化命令 | `docker exec` |
| 批量脚本执行 | `docker exec` 或 compose 包装命令 |

规则：
- HIR dump 优先复用真实测试命令，只叠加 debug 环境变量
- 调试主流程不要反复新开 `docker exec`
- 先保持一个容器内 shell，再在里面持续推进
- 在进入容器前，先确认宿主机目录已经隔离

## 性能口径怎么选

| 当前目标 | 口径 |
|---|---|
| 看 stock baseline | `CPython 解释执行` |
| 看 stock JIT 收益 | `CPython JIT` |
| 看 CinderX 运行时但不启 JIT | `CinderX 解释执行` |
| 看 CinderX 最终加速 | `CinderX JIT` |

规则：
- 正式对比前先明确当前口径
- 默认是 JIT 和 JIT 比、解释执行和解释执行比
- 不要把 `CinderX 解释执行` 和 `CinderX JIT` 混成一类
- 不要把 debug dump 环境变量混进正式性能口径

## baseline 是哪一种

| 当前目标 | baseline 含义 |
|---|---|
| 比较 CinderX 和原生 CPython | 口径基线 |
| 比较改动前后提交 | 提交基线 |
| 比较 Arm 和 x86 | 平台对齐后的口径基线 |

规则：
- 写报告时必须把 `baseline` 解释清楚
- 不要把“改动前提交”和“对照解释器”都叫 baseline 却不说明

## Benchmark 入口怎么选

| 当前目标 | 入口 |
|---|---|
| 单用例功能验证 | 直接跑 `run_benchmark.py` |
| 单用例 crash 复现 | 直接跑 `run_benchmark.py --worker ...` |
| 官方口径全量 / 子集 smoke | `python -m pyperformance run` |
| 快速扫大量样本 | 批量直跑脚本 |
| `bench_command()` 类问题 | 优先看外部子进程链 |

## HIR dump 什么时候开

| 当前目标 | 是否开 HIR dump |
|---|---|
| 功能验证 / JIT correctness | 必开 |
| 判断 worker 是否真的进入 CinderX JIT | 必开 |
| 正式性能测试 | 先关 |
| crash 定位 | 先开，再视情况减小噪声 |

## 什么时候优先怀疑进程模型

满足任意一条，就先看 `driver / manager / worker / bench_command`：

- `python -m pyperformance run` 异常，但单个 `run_benchmark.py` 正常
- JIT log 只有 pyperf 自己，没有 benchmark 本体
- 外部子命令 benchmark 报错
- worker 行为和手工直跑完全不一致

## 什么时候必须沉淀文档

满足任意一条，就写文档：

- 修掉了真实环境 crash
- 找到了性能退化根因
- 调整了 benchmark 入口或环境约定
- 修复依赖于非显然护栏或平台差异
