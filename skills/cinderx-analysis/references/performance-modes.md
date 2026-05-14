# 性能口径定义

这页只回答一个问题：**当前测到的到底是哪一种性能口径。**

## 四种口径

1. `CPython 解释执行`
   - stock CPython
   - 不启 CPython JIT
   - 不引入 CinderX

2. `CPython JIT`
   - stock CPython
   - 启用 CPython JIT
   - 不引入 CinderX

3. `CinderX 解释执行`
   - 使用带 `cinderx` 的解释器/运行时
   - 不显式启用 CinderX JIT

4. `CinderX JIT`
   - 使用带 `cinderx` 的解释器/运行时
   - 显式启用 CinderX JIT
   - 并用 HIR / jit.log 证明 benchmark 本体真的编译了

## 默认比较规则

- JIT 和 JIT 比
- 解释执行和解释执行比
- 不同口径不能直接横向比较

常见正式比较：
- `CPython 解释执行` vs `CinderX 解释执行`
- `CPython JIT` vs `CinderX JIT`

## 口径边界

- 安装了 `cinderx` 不等于已经进入 `CinderX JIT`
- 开了 `PYTHONJITLOGFILE` 不等于 benchmark 本体真的进了 JIT
- `CPython JIT` 和 `CinderX JIT` 不能共用同一套结论

## baseline 的两种含义

1. 口径基线
   - 对照解释器/运行模式
   - 例如 `CPython JIT` 是 `CinderX JIT` 的 baseline

2. 提交基线
   - 改动前的 commit / branch
   - 用于回答“这次改动相对之前是提升还是退化”

报告中必须显式写清：
- 当前 baseline 是哪一种
- 不要把“CPython baseline”和“改动前 baseline”混成一个词

## 跨平台对比

Arm vs x86 属于第三条比较线。

前提：
- 参数一致
- 口径一致
- JIT 状态一致

最小要求：
- `JIT vs JIT`
- `解释执行 vs 解释执行`
- 相同 benchmark 命令
- 相同 warmup / loops / affinity / 关键环境变量

## CinderX JIT 常用变量

基础启用变量：
- `PYTHONJITAUTO`
- `PYTHONJITSPECIALIZEDOPCODES`
- `PYTHONJITTYPEANNOTATIONGUARDS`
- `PYTHONJITENABLEHIRINLINER`
- `PYTHONJITHUGEPAGES`
- `PYTHONPATH`
- `LD_LIBRARY_PATH`

调试观测变量：
- `PYTHONJITLOGFILE`
- `PYTHONJITDUMPFINALHIR`
- `PYTHONJITDUMPSTATS`

## 原则

- 先明确口径，再跑 benchmark
- 正式性能数据默认不带大量 dump 变量
- 功能验证、HIR 分析和 crash 定位可以叠加调试变量
- 如果要对比 HIR，优先固定真实测试命令，只增减调试环境变量
