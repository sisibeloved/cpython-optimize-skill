# pyperformance 环境变量契约

pyperformance 是 driver -> manager -> worker 架构，部分 benchmark 还会经 `bench_command()` 再派生子进程。写在命令前面的 `<env-vars>` 只保证 driver 看到变量；worker 是否继承，CinderX JIT 是否启用，必须由 `--inherit-environ`、venv/site-packages、`.pth` 和真实 worker 命令共同证明。

## 运行前必查

每次正式 suite、worker 复现或 A/B 对比前，先输出环境契约表：

| 项 | 必查内容 |
|----|----------|
| driver env | 命令前显式设置了哪些变量，当前 shell 中还残留哪些相关变量 |
| inherit list | `--inherit-environ` 是否包含所有需要传给 worker 的变量 |
| worker env | worker 真实命令或日志能证明变量已到达 worker |
| worker JIT | worker 可见的 `.pth`、venv、import 和 JIT 初始化证据是否完整 |
| baseline/candidate | 两边除目标实验变量外，其余环境变量一致 |
| formal/debug | 正式性能数据不得混入 HIR/JIT dump、`DIAG=1`、`JIT_LOG_FILE`、`--debug-single-value` |

## 判断 CinderX JIT 是否在 worker 中启用

不要用 driver import、交互式 import 或 smoke 结果替代 pyperformance worker 证据。必须在真实 worker 口径下同时检查四层：

| 层级 | 必须证明 |
|------|----------|
| `.pth` 安装 | worker 可见的 `site-packages` 中存在 CinderX `.pth`，路径指向本次 candidate 的 CinderX 安装；记录 `.pth` 路径、内容摘要和 `site.getsitepackages()` / `sys.path` |
| venv 传递 | pyperformance worker venv 的 `pyvenv.cfg` 中 `include-system-site-packages = true`，或有等价 `PYTHONPATH` 把系统 site-packages / CinderX 路径传入 worker；记录 worker 使用的 Python 和 venv 路径 |
| 环境变量 | `--inherit-environ` 覆盖 `PYTHONPATH`、`LD_LIBRARY_PATH`、`PYTHONJIT*`、`CINDERX_*`、`PYPERFORMANCE_HOOK_ROOT` / `PYPERF_HOOK_ROOT` 等需要传给 worker 的变量 |
| JIT 初始化 | 在 worker 内证明 `import cinderx`、`import _cinderx`、`cinderx.__file__`、`cinderx.get_import_error()`、`cinderx.is_initialized()` 与 CinderX JIT 口径一致，并能在 jit.log/HIR/统计中关联到目标 benchmark 本体 |

人工创建 pyperformance venv 时，CinderX candidate 线在 `python3.14 -m pyperformance venv create --inherit-environ http_proxy,https_proxy` 之后必须把 worker `pyvenv.cfg` 改成 `include-system-site-packages = true`：

```bash
sed -i 's/^include-system-site-packages = false/include-system-site-packages = true/' venv/<venv_name>/pyvenv.cfg
```

测试 CPython baseline 数据时保持或改回 `include-system-site-packages = false`，并证明没有误继承 CinderX。

结论规则：
- 只看到 driver import 成功，不代表 worker 启用了 CinderX JIT。
- 只安装 CinderX 包，不代表 pyperformance 新建的 worker venv 能看到 `.pth`。
- 只设置 `PYTHONJITAUTO` 或 `PYTHONJIT*`，但没有进 `--inherit-environ`，不算 worker 口径。
- jit.log 有启动期或第三方包函数，不等于目标 benchmark 本体进入 CinderX JIT。

## 必须核对的变量

- 网络与下载：`http_proxy`、`https_proxy`、`no_proxy` 及大写同名变量。
- 动态链接：`LD_LIBRARY_PATH`、必要时 `LD_PRELOAD`。
- Python 搜索路径：`PYTHONPATH`、`PYTHONHOME`、`PYTHONNOUSERSITE`、`VIRTUAL_ENV`；除非口径明确，`PYTHONHOME` 通常应为空。
- pyperformance / hook：`PYPERFORMANCE_ROOT`、`PYPERFORMANCE_HOOK_ROOT`、`PYPERF_HOOK_ROOT`。
- CinderX / JIT：`PYTHONJIT`、`PYTHONJITAUTO`、`PYTHONJITHUGEPAGES`、`PYTHONJITLISTFILE`、`PYTHONJITLOGFILE`、`PYTHONJITDUMPFINALHIR`、`PYTHONJITDUMPHIR`、`PYTHONJITDUMPLIR`、`PYTHONJITDEBUG`、`CINDERX_*`。
- helper 变量：`BENCHMARK`、`WARMUP`、`OPT_ENV_FILE`、`OPT_CONFIG_NAME`、`RESULTS_DIR`、`DIAG`。

## 常见错误

- 只在 driver 命令前设置 `PYTHONPATH` / `PYTHONJITAUTO`，但 `--inherit-environ` 没列出，worker 实际没拿到。
- CinderX `.pth` 只装在系统解释器，pyperformance worker venv 没开 `include-system-site-packages`，worker 看不到 CinderX。
- worker 的 `pyvenv.cfg` 正确，但 candidate 的 `.pth` 指向旧 editable install 或旧 wheel。
- 只报告 driver import 的 `cinderx.__file__`，没有 worker 内的 `_cinderx`、`cinderx.get_import_error()` 和 `cinderx.is_initialized()`。
- baseline 误继承 CinderX 的 `PYTHONPATH`、hook 或 editable install。
- candidate 少继承 `LD_LIBRARY_PATH`，导致 worker import 或动态链接路径与 smoke 不一致。
- 正式结果里残留 `DIAG=1`、HIR/JIT dump 或 debug single value。
- A/B 两边 `PYTHONJITAUTO`、huge pages、代理、site-packages 继承不一致，却直接比较 `run.json`。

## 输出要求

报告中必须写明：真实命令、`--inherit-environ` 列表、driver/worker 环境差异、`.pth` 路径、`pyvenv.cfg` / site-packages 证据、worker 内 CinderX import/JIT 初始化证据、baseline/candidate 唯一差异轴，以及是否为正式非 debug 口径。
