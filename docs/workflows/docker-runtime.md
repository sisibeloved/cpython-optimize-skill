# 运行时环境隔离：Docker

## 目标

在远程服务器上复用可控、可重建的运行时环境，同时保留源码挂载能力。

前提：
- 宿主机目录必须先隔离好
- 容器隔离建立在宿主机目录隔离之上

## 推荐做法

- 宿主机提供：
  - Docker
  - `docker compose`
  - `rsync`
- 每个 Agent 先准备独立宿主机目录
- 源码通过 `rsync` 同步到远端
- 容器通过 bind mount 直接使用源码目录
- 容器内构建和验证，宿主机主要负责同步和编排

调试约束：
- Docker 调试时优先保留一个长连接交互终端
- 不要把反复 `docker exec ...` 当成主要调试方式
- 更推荐先进入固定 shell，再在容器内持续执行命令

目录隔离约束：
- 不复用已有宿主机工作目录
- bind mount 前先确认挂载源目录是当前 Agent 自己的目录
- 结果目录、源码目录、pyperformance 目录都应避免与他人共享写入

可直接参考的已验证脚本：
- `scripts/docker/cinderx-test/setup.sh`
- `scripts/docker/cinderx-test/test-benchmark.sh`
- `scripts/docker/cinderx-test/smoke.sh`
- `scripts/docker/cinderx-test/benchmark_harness.py`

## 双线结构

Docker 工作流明确分成两条线：

1. 基线线：`cpython-baseline`
   - 用于 stock CPython JIT 和 CinderX 的正式对照
   - 侧重性能对比、公平性和统一入口
2. 调试线：`cinderx-test`
   - 用于 CinderX 功能验证、HIR dump、native crash 复现
   - 侧重 correctness 和定位效率

模板入口：
- `references/templates/docker/cpython-baseline/`
- `references/templates/docker/cinderx-test/`

## 优先级

1. Kunpeng Docker：兼容性主验证环境
2. Kunpeng 宿主机：最终少量关键复核
3. 本地 Docker：开发期快速回归

在 Kunpeng Docker 内再分：
- 先走 `cinderx-test` 完成功能/调试验证
- 再走 `cpython-baseline` 做正式对照

## 实战注意事项

- 代理不可默认写死，容器内要能自动摘除坏代理
- `pip` 优先走国内源
- openEuler / Python 源码下载最好走国内镜像
- 初始化脚本要避免吞错误
- 首次构建要警惕过宽的包通配符把 `debuginfo` / `debugsource` 一起拉进来
- 容器和宿主机路径要尽量统一，便于挂载源码和复用命令
- `pyperformance` 源码目录必须挂到真正可安装的仓库根，而不是空目录或错误层级
- 只有自动化脚本、一次性检查或批量命令才优先 `docker exec`
- 如果宿主机目录隔离做不好，Docker 本身也会失去实验隔离意义
