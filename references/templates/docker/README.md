# Docker 模板

这里保存已经在 `cinderx/docker/` 下验证过的模板文件。

当前采用双线结构：

- `cpython-baseline/`
  - 用于基线与正式对照
  - 关注 stock CPython JIT 与 CinderX 的可比性
- `cinderx-test/`
  - 用于 CinderX 调试、HIR 验证、native crash 复现
  - 关注快速定位问题，而不是正式对照

使用建议：
- 要做正式性能对照，优先从 `cpython-baseline/` 开始
- 要做功能验证、HIR dump、gdb/native crash 复现，优先从 `cinderx-test/` 开始
