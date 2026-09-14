# 维护本技能仓库

可安装内容位于 `plugins/cpython-optimize-skill/`；修改这里的源文件，不修改宿主的插件缓存。技能名、脚本参数和实验输出契约是兼容接口。

## 按任务读取

- 修改技能描述或工作流：读对应 `SKILL.md` 及会受影响的调用方。参考资料按当前分支加载。
- 修改 hook：读对应 `hooks/*-skill-router` 和 `tests/test_*_skill_router.py`。
- 修改实验脚本：读所属技能和对应环境契约，保留 Python/ABI、baseline source、worker JIT、CPU 隔离及 crash 证据约束。
- `docs/superpowers/` 和插件 `docs/plans/` 是历史设计记录，不是每次维护的执行步骤。

## 本地验证

以下检查使用本地文件与临时夹具，不运行真实 CPython/CinderX 实验，也不连接远程 lab：

```bash
python3 plugins/cpython-optimize-skill/tests/validate_skill_layout.py
python3 plugins/cpython-optimize-skill/tests/validate_pressure_scenarios.py
python3 plugins/cpython-optimize-skill/tests/test_runtime_skill_router.py
python3 plugins/cpython-optimize-skill/tests/test_validation_skill_router.py
python3 plugins/cpython-optimize-skill/tests/test_pyperformance_stat_report.py
python3 plugins/cpython-optimize-skill/tests/test_isa_instruction_lookup.py
python3 plugins/cpython-optimize-skill/tests/test_data_quality.py
```

按改动选择相关检查，修复本次引起的失败并重跑受影响检查；已通过且没有新风险时交付。描述、文档和 hook 提示修改不需要编译 CinderX 或跑远程性能全量。

收紧技能描述的触发范围，保留专业约束；把默认流程与实际阻塞条件分开。用户明确要求和已有授权优先于技能默认建议。需要外部实验时沿用当前任务指定的环境、预算和权限。
