# 调试线：cinderx-test

这条线用于 CinderX 调试和回归：

- 单 benchmark 快速验证
- HIR dump / JIT log
- native crash / gdb 复现

特点：
- 适合 correctness、稳定性和 JIT 路径确认
- 不直接把开启大量 dump 的结果当性能数据
