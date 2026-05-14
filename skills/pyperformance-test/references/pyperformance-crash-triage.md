# pyperformance Crash Triage

## 目标

快速判断问题属于：
- 依赖缺失
- 环境变量没传到 worker
- `_cinderx` / `cinderjit` 导入失败
- JIT 启动期 compile storm
- 真正的 native crash

## 最小检查顺序

1. 看退出码
   - `139` 通常是 `SIGSEGV`
2. 看是否进入 JIT
3. 看 worker 进程环境
4. 看 `jit.log` 最后一个函数
5. 必要时直接 `gdb` / core dump

## 常见误判

- `JIT log` 里没有 `__main__:*`，不代表没有进入 JIT
- `venv python` 手工导入成功，不代表 `pyperformance` worker 里也成功
- `python -m pyperformance run` 正常，不代表 `bench_command()` 子进程链也正常

## 高频根因

- `LD_LIBRARY_PATH` 没有传到 worker，导致 `_cinderx` 因 `libstdc++` 版本不匹配而导入失败
- `PYTHONPATH` 只让 hook 可见，但没有让 editable 安装对应的源码路径真正生效
- 坏代理导致容器或 worker 里的 `pip` / 初始化链路失败
- 低阈值 AutoJIT 把启动期、第三方包或 synthetic code 也卷进 compile storm
