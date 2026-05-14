# CinderX / CPython 基线对照环境

这个目录用于做更正式的：

- `stock CPython JIT`
- `CPython + CinderX`

之间的 pyperformance 对照。

和旧版脚本相比，这套流程已经统一切到：

```bash
python -m pyperformance run ...
```

而不再把直接调用 `bench(*args)` 当成正式验证入口。

## 环境目标

当前镜像尽量向真实环境对齐：

- `openEuler 24.03 LTS SP1`
- `gcc 14.2.0`
- 容器内代理默认使用 `host.docker.internal:7890`
- Python 3.14 在镜像内构建并安装到 `/opt/python314`

## 挂载约定

容器会使用以下挂载：

- `${HOME}/Repo/cpython` -> `/cpython`
  - stock CPython 源码
- `${HOME}/Repo/pyperformance` -> `/pyperformance`
  - pyperformance 源码
- `dist/` -> `/dist`
  - CinderX wheel
- `docker/cpython-baseline/scripts/` -> `/scripts`
- `docker/cpython-baseline/configs/` -> `/scripts/configs`

另外还会挂载：

- `scripts/arm/pyperf_env_hook` -> `/pyperf_env_hook`

它用于在 CinderX 路径下给 pyperformance worker 注入 JIT 启动逻辑。

## 快速开始

### 1. 构建 wheel

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"
./docker/cinderx-test/scripts/build-wheel.sh
```

### 2. 构建并启动容器

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT/docker/cpython-baseline"
docker compose up -d --build
```

### 3. 跑 stock CPython baseline

```bash
docker compose exec cpython-baseline sh -lc \
  'BENCHMARK=mdp WARMUP=3 /scripts/test-baseline.sh'
```

### 4. 先做功能诊断，再跑 CinderX 性能

这是当前必须遵守的约束：

1. 先开启 HIR dump，确认 benchmark 在当前 Docker 环境下功能正常
2. 再关闭 HIR dump，重新跑性能测试

功能诊断示例：

```bash
docker compose exec cpython-baseline sh -lc \
  'BENCHMARK=mdp WARMUP=3 PYTHONJITAUTO=2 DIAG=1 /scripts/test-cinderx.sh'
```

性能测试示例：

```bash
docker compose exec cpython-baseline sh -lc \
  'BENCHMARK=mdp WARMUP=3 PYTHONJITAUTO=2 /scripts/test-cinderx.sh'
```

### 5. 跑正式对比

```bash
docker compose exec cpython-baseline sh -lc \
  'BENCHMARK=mdp WARMUP=3 OPT_ENV_FILE=/scripts/configs/mdp/stable.env /scripts/test-comparison.sh'
```

## benchmark 选择方式

`BENCHMARK` 直接映射到 `pyperformance --benchmarks`，支持：

- 单 benchmark
  - `mdp`
- 多 benchmark
  - `mdp,regex_compile`
- 子集 / 全量
  - `all,-dask`

简单 benchmark 名会先按 `benchmark.toml` 中的 `pyperformance_benchmark` 做转换。

## 当前已配置 benchmark

- `generators`
- `mdp`
- `regex_compile`

配置目录：

- `docker/cpython-baseline/configs/generators/`
- `docker/cpython-baseline/configs/mdp/`
- `docker/cpython-baseline/configs/regex_compile/`

## 结果文件

各脚本现在都会生成 pyperformance JSON 结果文件。

对比脚本会额外生成：

- `/results/<benchmark>/<config-name>/comparison.json`

这个文件记录：

- baseline 时间
- cinderx baseline 时间
- cinderx optimized 时间
- 对应 JSON 文件路径

## 关键环境变量

- `BENCHMARK`
  - pyperformance benchmark selector
- `WARMUP`
  - 对应 `pyperformance run --warmups`
- `PYTHONJITAUTO`
  - CinderX AutoJIT 阈值，当前推荐先用 `2` 做功能诊断
- `DIAG`
  - 设为 `1` 时开启诊断模式
- `JIT_LOG_FILE`
  - 诊断模式下的 JIT 日志输出路径，默认 `/tmp/cinderx-jit.log`
- `OPT_ENV_FILE`
  - 优化开关配置文件
- `OPT_CONFIG_NAME`
  - 结果标签
- `CPYTHON_ROOT`
  - stock CPython 源码目录
- `RESULTS_DIR`
  - 宿主机结果目录
- `BASE_IMAGE`
  - 共享基础镜像名，默认 `cinderx-pyperf-realenv:arm64`

## 代理说明

容器内默认代理：

- `http://host.docker.internal:7890`
- `https://host.docker.internal:7890`

不要在容器内使用：

- `127.0.0.1:7890`

## 新增 benchmark

目标仍然是“新增 benchmark 主要改配置，而不是改通用脚本”。

通常需要新增：

1. `docker/cpython-baseline/configs/<benchmark>/benchmark.toml`
2. `docker/cpython-baseline/configs/<benchmark>/stable.env`

当前配置字段已经覆盖：

- `pyperformance_benchmark`
- `downloads`
- `args`
- `prepare.mode`
- `run.default_excludes`
- `run.extra_env`

## 注意事项

1. 这套环境比旧版 direct-bench 脚本更贴近真实环境，但仍然可能和真实服务器存在系统差异。
2. `dask` 一类 benchmark 可能仍受网络/环境因素影响，不应和 JIT correctness 混为一谈。
3. 后续使用 Docker 做功能测试时，必须先开 `DIAG=1` 验证 HIR dump，再关闭 `DIAG` 跑性能。
4. 如果出现 CinderX JIT 行为异常，优先检查：
   - `PYTHONJITAUTO` 是否与真实环境一致
   - `PYTHONJITLOGFILE` / `PYTHONJITDUMPFINALHIR` 是否已在诊断模式打开
