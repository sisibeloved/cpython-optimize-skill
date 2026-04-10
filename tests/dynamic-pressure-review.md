# 动态对话级 Pressure Test 记录

## 目标

验证 skill 在真实用户问法下，是否能把人快速引导到正确路线，而不是只在文档静态结构上“看起来覆盖了”。

## 本轮场景

1. Kunpeng 上验证 benchmark 是否真的进 CinderX JIT
2. Docker 内做 stock CPython JIT vs CinderX 正式对照
3. `pyperformance run` 异常但单 benchmark 正常
4. 真实环境 native crash 复现
5. 文档沉淀
6. 性能退化分析
7. Docker 内连续调试，不想反复 `docker exec`
8. Docker 里既提 crash 又要正式对照

## 当前结论

### 已覆盖较好

- `cinderx-test` 与 `cpython-baseline` 的双线区分
- `run_benchmark.py` vs `python -m pyperformance run` 的入口区分
- HIR dump 应先开后关
- `driver / manager / worker / bench_command` 进程模型
- 文档沉淀的最小结构

### 本轮新增补强

- Docker 调试优先保留一个长连接交互终端
- 不把反复 `docker exec` 当作主调试路径
- 当用户同时提到 crash 和正式对照时，要先判断“当前目标”，避免只盯着历史 crash 线走偏

## 结论

当前 skill 已经能支持第一轮真实对话级路由，但后续如果继续迭代，最值得补的是：

- 更细的“正式对照 vs correctness 验证”切换提示
- 对 `bench_command()` 类 benchmark 的专门 FAQ
- 对“容器里有代理 / 没代理”这种环境前置条件的显式提醒
