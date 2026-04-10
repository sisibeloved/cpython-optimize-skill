# Pressure Scenarios

这些场景用于压测 skill 在真实对话中的引导能力。

## 场景 1：用户要在 Kunpeng 上做 CinderX 功能验证

用户话术示例：

> 我想在 Kunpeng 上验证 `regex_compile` 是否真的进了 CinderX JIT，先别看性能。

期望行为：
- 引导到 `docs/workflows/pyperformance-test.md`
- 优先推荐单个 `run_benchmark.py`
- 明确先开 HIR dump
- 提醒检查 worker 是否真的进入 JIT

## 场景 2：用户要做正式性能对照

用户话术示例：

> 我要比较 stock CPython JIT 和 CinderX 在 Docker 里的 pyperformance 数据。

期望行为：
- 引导到 `docs/workflows/docker-runtime.md`
- 明确这是 Docker 双线里的 `cpython-baseline`
- 不直接把 `cinderx-test` 调试线当正式对照

## 场景 3：用户说 pyperformance run 异常，但单 benchmark 正常

用户话术示例：

> `python -m pyperformance run` 不对，但我直接跑 `run_benchmark.py` 是正常的。

期望行为：
- 联想到 driver / manager / worker / bench_command 子进程模型
- 引导到 `docs/workflows/pyperformance-test.md`
- 必要时引导到 `docs/playbooks/pyperformance-crash-triage.md`

## 场景 4：用户要复现 native crash

用户话术示例：

> `bm_logging` 在真实环境 `SIGSEGV`，我想先最小复现，再抓 HIR 和 gdb。

期望行为：
- 优先建议调试线 `cinderx-test`
- 强调单 benchmark worker 入口
- 同时给出 JIT log / HIR / gdb 的取证顺序

## 场景 5：用户要整理实验文档

用户话术示例：

> 这次修复要沉淀成文档，后面给别的 Agent 复用。

期望行为：
- 引导到 `docs/workflows/documentation.md`
- 强调背景、复现命令、证据链、根因、修复、回归结果

## 场景 6：用户要分析性能退化

用户话术示例：

> `scimark` 退化了，帮我对比 HIR 和性能，找根因。

期望行为：
- 引导到 `docs/workflows/case-analysis.md`
- 区分 JIT 与非 JIT 路线
- 强调先对齐命令口径、解释器和依赖，再比较 HIR / LIR / 机器码

## 场景 7：用户在 Docker 里连续调试

用户话术示例：

> 帮我进容器里调试一下这个 benchmark，先别一条条 `docker exec`。

期望行为：
- 联想到 Docker 调试应优先保留一个长连接交互终端
- 不把反复 `docker exec` 当成主路径
- 引导到 `docs/workflows/docker-runtime.md` 或 `docs/playbooks/faq.md`

## 场景 8：用户要做 Docker 正式对照，但先提到了 crash

用户话术示例：

> 这个用例之前在容器里崩过，现在我想正式对比 stock CPython JIT 和 CinderX。

期望行为：
- 先识别“当前目标是正式对照”
- 把路线切到 `cpython-baseline`
- 必要时提醒先在 `cinderx-test` 完成功能确认，再回到基线线
