# FAQ

## 我现在只想看功能，不看性能

优先：
- `cinderx-test`
- 单个 `run_benchmark.py`
- 先开 HIR dump

不要直接拿开启大量 dump 的结果当性能数据。

## 我只想复现一个 crash

优先：
- 单个 `run_benchmark.py --worker ...`
- 调试线 `cinderx-test`
- 先拿 `jit.log` / HIR，再决定是否进 `gdb`

## 为什么 `python -m pyperformance run` 和单 benchmark 结果不一样

优先怀疑：
- `driver / manager / worker` 进程模型
- `bench_command()` 外部子进程
- worker 环境变量继承
- `sitecustomize` / hook 是否真的命中

## 什么时候该回到 Kunpeng 宿主机

满足任意一条：
- Docker 和真实环境行为不一致
- 需要最终兼容性复核
- 容器内问题已经缩小到 native 层或系统差异

## 什么时候该写文档，而不是继续试

满足任意一条：
- 已经修掉真实环境 crash
- 已经定位到性能退化根因
- 改了 benchmark 入口、环境变量或护栏约定

## Docker 调试时为什么不建议反复 `docker exec`

因为这会让：
- 调试命令不一致
- 上下文丢失
- 容器内临时状态和日志更难追踪

更推荐：
- 先进入一个固定的长连接交互 shell
- 后续在这个 shell 里持续执行调试命令
- 只有自动化脚本或一次性检查才用 `docker exec`
