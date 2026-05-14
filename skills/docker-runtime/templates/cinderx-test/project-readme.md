# CinderX Docker Benchmark 环境

这个目录用于在 Docker 中跑 **CinderX + pyperformance** 的真实验证入口。  
和旧版直接 `import benchmark`、再调用 `bench(*args)` 的脚本不同，这套流程已经统一收敛到：

```bash
python -m pyperformance run ...
```

## 目标

- 尽量贴近真实服务器环境
  - `openEuler 24.03 LTS SP1`
  - `gcc 14.2.0`
  - 容器内代理默认走 `host.docker.internal:7890`
- 使用真实 `pyperformance run` 路径暴露 JIT 正确性问题
- benchmark 元数据仍然由 `configs/<benchmark>/benchmark.toml` 驱动

## 基础约定

容器会挂载以下宿主机目录：

- `dist/`：CinderX wheel
- `docker/cinderx-test/scripts/`：执行脚本
- `docker/cinderx-test/configs/`：benchmark 配置
- `${HOME}/Repo/pyperformance`：挂载到容器 `/pyperformance`
- `scripts/arm/pyperf_env_hook`：挂载到容器 `/pyperf_env_hook`

说明：

- `pyperformance` 源码挂载是必须的，因为 `mdp` 等用例不属于标准发布包内置集合
- `/pyperf_env_hook` 用于给 pyperformance worker 注入 CinderX JIT 启动逻辑

## 快速开始

### 1. 构建 wheel

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"
./docker/cinderx-test/scripts/build-wheel.sh
```

### 2. 启动容器

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT/docker/cinderx-test"
docker compose -p cinderx-exp up -d
```

### 3. 安装 CinderX 与 pyperformance

```bash
docker compose -p cinderx-exp exec cinderx-arm64 /scripts/setup.sh
```

### 4. 先做功能诊断，再做性能测试

这是当前必须遵守的约束：

1. 先开启 HIR dump，确认 benchmark 在当前 Docker 环境下功能正常
2. 再关闭 HIR dump，重新跑性能测试

不要直接拿开启 dump 的结果当性能数据。

功能诊断示例：

```bash
docker compose -p cinderx-exp exec cinderx-arm64 sh -lc \
  'BENCHMARK=mdp WARMUP=3 PYTHONJITAUTO=2 DIAG=1 /scripts/test-benchmark.sh'
```

性能测试示例：

```bash
docker compose -p cinderx-exp exec cinderx-arm64 sh -lc \
  'BENCHMARK=mdp WARMUP=3 PYTHONJITAUTO=2 /scripts/test-benchmark.sh'
```

也可以跑别的配置，例如：

```bash
docker compose -p cinderx-exp exec cinderx-arm64 sh -lc \
  'BENCHMARK=regex_compile WARMUP=3 PYTHONJITAUTO=2 DIAG=1 /scripts/test-benchmark.sh'
```

## benchmark 选择方式

`BENCHMARK` 现在传给 `pyperformance -b/--benchmarks`，支持三类形式：

- 单 benchmark
  - `BENCHMARK=mdp`
- 指定子集
  - `BENCHMARK=all,-dask`
- 多项组合
  - `BENCHMARK=mdp,regex_compile`

其中简单名字会先经过 `benchmark.toml` 映射到对应的 `pyperformance_benchmark`。

## 支持的 benchmark

当前已配置：

- `generators`
- `mdp`
- `regex_compile`

配置目录：

- `docker/cinderx-test/configs/generators/`
- `docker/cinderx-test/configs/mdp/`
- `docker/cinderx-test/configs/regex_compile/`

## 优化开关

如果某个 benchmark 有稳定优化配置，可以通过：

- `OPT_ENV_FILE`
- `OPT_CONFIG_NAME`

来选择。

例如：

```bash
docker compose -p cinderx-exp exec cinderx-arm64 sh -lc \
  'BENCHMARK=mdp OPT_ENV_FILE=/scripts/configs/mdp/stable.env PYTHONJITAUTO=10 /scripts/test-benchmark.sh'
```

## 关键环境变量

- `BENCHMARK`
  - pyperformance benchmark selector
- `WARMUP`
  - 传给 `pyperformance run --warmups`
- `PYTHONJITAUTO`
  - 这里直接作为 CinderX AutoJIT 阈值使用，推荐先用 `2` 做功能诊断
- `DIAG`
  - 设为 `1` 时开启诊断模式
- `JIT_LOG_FILE`
  - 诊断模式下的 JIT 日志输出路径，默认 `/tmp/cinderx-jit.log`
- `OPT_ENV_FILE`
  - 优化开关配置文件
- `OPT_CONFIG_NAME`
  - 结果标签名
- `OUTPUT_FILE`
  - pyperformance JSON 输出路径
- `RESULTS_DIR`
  - 宿主机结果目录

## Native crash 调试

遇到 Docker 下的 native auto-JIT crash 时，统一使用容器内固定入口：

```bash
docker compose -p cinderx-exp exec cinderx-arm64 sh -lc \
  'BENCHMARK=mdp WARMUP=1 PYTHONJITAUTO=2 JIT_LOG_FILE=/results/mdp-native-jit.log /scripts/run-native-gdb.sh'
```

不要再临时手写长串 `gdb --args ...`，这样可以保证每次调试命令一致。

## 代理说明

容器内代理默认是：

- `http://host.docker.internal:7890`
- `https://host.docker.internal:7890`

不要再在容器里使用：

- `127.0.0.1:7890`

因为那会指向容器自身，不是宿主机代理。

## 新增 benchmark

目标仍然是“尽量只改配置”。

通常只需要新增：

1. `docker/cinderx-test/configs/<benchmark>/benchmark.toml`
2. `docker/cinderx-test/configs/<benchmark>/stable.env`

`benchmark.toml` 当前至少描述：

- `pyperformance_benchmark`
- `module_dir`
- `entry_file`
- `bench_func`
- `downloads`
- `args`
- `prepare.mode`
- `run.default_excludes`
- `run.extra_env`

## 注意事项

1. 这套容器现在已经比旧脚本更接近真实环境，但仍然不是服务器的完全复制品。
2. 后续使用 Docker 进行功能测试时，必须先开 `DIAG=1` 确认 HIR dump 正常，再关闭 `DIAG` 跑性能。
3. 如果 benchmark 在这里失败而在真实环境通过，优先检查：
   - 代理
   - pyperformance 源码挂载
   - 真实环境与 Docker 是否都使用原生 `PYTHONJITAUTO`
4. 如果要做正式对照，请优先使用 `docker/cpython-baseline/`。
