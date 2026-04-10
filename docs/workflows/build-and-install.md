# CPython/CinderX 编译与强制覆盖安装

## 目标

在目标环境中完成隔离构建，并确保安装结果真正覆盖到当前解释器。

## 原则

- 不在本地盲目编译，优先远端验证
- 明确 Python、编译器、`pyperformance` 版本
- 每次切分支或切验证目标后，优先 `--force-reinstall`

## CPython

- 版本基线：`3.14.3`
- 编译器基线：`gcc == 14.2.0`

## CinderX

- 版本基线：当前会话仓库
- Python：`3.14.3`
- `pyperformance == 1.14.0`
- 安装建议：

```bash
python -m pip install -e . --no-build-isolation --no-deps --force-reinstall
```

## 验证

- 检查 `cinderx.__file__`
- 检查 `cinderx.is_initialized()`
- 检查 `cinderx.get_import_error()`
- 明确当前解释器路径
