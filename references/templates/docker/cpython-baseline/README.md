# 基线线：cpython-baseline

这条线用于更正式的对照：

- stock CPython JIT
- CPython + CinderX

特点：
- `python -m pyperformance run` 作为正式入口
- 先做功能诊断，再跑性能
- 更强调“对比公平性”
