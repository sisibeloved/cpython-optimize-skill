# Docker / cinderx-test 脚本

这些脚本来自当前已验证的 `cinderx/docker/cinderx-test` 工作流。

## 脚本

- `benchmark_harness.py`
  - 统一 benchmark 配置、路径和结果文件约定
- `setup.sh`
  - 在容器中构建并安装 CinderX，安装 pyperformance，并做最小校验
- `test-benchmark.sh`
  - 在容器中执行单 benchmark 的 `pyperformance` 验证
- `smoke.sh`
  - 做最小 JIT smoke test

## 使用方式

它们是“已验证原型”，不是对任意仓库直接零改动可运行的通用工具。
复用时应优先保留：
- 代理处理逻辑
- 强制重装逻辑
- `LD_LIBRARY_PATH` / hook / worker 环境继承逻辑
