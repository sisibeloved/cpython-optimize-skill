# JIT 正确性验证策略

来源页面：

- https://github.com/Cookie4Cat/cinderx/wiki/JIT-Correctness-Validation-Strategy
- https://github.com/Cookie4Cat/cinderx/wiki/JIT-Optimization-Correctness-Contract

## 基线

在以下基线下审查 CinderX JIT 正确性时使用本策略：

- ARM / AArch64
- CPython 3.14.3 GIL 构建
- cinderx

如果页面或 PR 说明提到更高版本的 CPython，除非它们明确更新了本基线，否则只把这些信息视作实验历史。

## 局部正确性与系统正确性

把 review 拆成两个判断：

- 局部正确性：被修改的 builder、preload、HIR、LIR、codegen、helper、deopt 或 refcount 规则，是否保持了它所属层级应负责的语义。
- 系统正确性：组合后的程序在 JIT on/off 和 gate 覆盖下，是否仍然符合 Python 行为。

本 skill 优先关注局部正确性。Gate 结果是辅助证据，不能替代对应层级的本地证明。

## 阶段映射

| 阶段 | Review 重点 | 典型证据 |
|-------|--------------|------------------|
| Stage 1 - Bytecode builder / preload | Opcode 解释、CPython 3.14 adaptive 状态、inline cache 读取、Python 语义前提 | 触发目标 opcode/cache 状态的 RuntimeTests；builder/preload 形态检查；generic fallback 检查 |
| Stage 2 - HIR | Lowering、guard、helper call、ownership 形态、verifier 假设 | HIR text fixtures、opcode count、guard/fallback 负例、SSA/verifier 证据 |
| Stage 3 - LIR / regalloc | Operand lowering、寄存器约束、live range、materialization | LIR/uop 证据、spill/live range 用例、架构敏感负例 |
| Stage 4 - Codegen / runtime helpers | AArch64 指令语义、helper ABI、flags、宽度、runtime call 副作用 | 覆盖 code shape/helper 语义的 RuntimeTests、AArch64 backend 断言、helper 异常/副作用测试 |
| Stage 5 - Deopt / FrameState / refs | Frame 重建、live refs、owned/borrowed 状态、exception/deopt edge | 覆盖 deopt path、FrameState 内容、refcount 敏感场景的 RuntimeTests |
| Stage 6 - End-to-end Python semantics | JIT on/off 等价性和系统行为 | `test_cinderx`、定向 stdlib 测试；pyperformance 只能作为行为/性能辅助证据 |

## 每个 JIT 改动都要回答的六个问题

对每条被修改的规则，都要能回答：

1. 这个改动由哪个层级负责？
2. 这个层级必须保持哪些 Python 语义或 JIT 层级语义？
3. Fast path 依赖哪些假设？
4. 如果这些假设不成立，哪些 invariant 可能被破坏？
5. 哪些机器检查证明这些 invariant 成立？
6. 哪些正例、负例和端到端测试证明行为正确？

如果这些问题无法回答，这个 PR 的正确性形态还不足以进入 review 通过状态。

## PR 级正确性契约

Review 时要求 PR 提供，或由 reviewer 重建这份契约：

```text
优化内容：
影响阶段：
Python 语义来源：
Fast-path 假设：
保护这些假设的 guards / checks：
Guard 失败行为：
May-raise 点：
Exception-table / protected-region 行为：
副作用 / 内存依赖：
FrameState / deopt 要求：
Refcount 考量：
版本特定差异：
必要测试：
已知非目标：
```

契约字段缺失不自动构成 finding。只有当 diff 的安全性依赖某个字段，而 PR 没有提供代码或测试证据时，才把它作为 finding。

## May-raise 与 exception table 规则

如果某个 lowering 新增、删除、移动、替换或合并了 `may-raise` 点，review 不能只检查异常类型等价。

检查：

- 原始 bytecode offset 是否位于 `co_exceptiontable` 的 protected range 内？
- 原始异常是否应被同一个 Python frame 内的 handler 捕获？
- 新 fast path、helper、guard miss 或 fallback 是否保持了原始 same-frame exception edge？
- 如果无法证明这一点，优化路径是否会在 protected region 内禁用自己，或回到 generic lowering？

核心规则：即使 helper fallback 抛出了正确的异常类型，只要异常绕过了原本应捕获该 bytecode 操作异常的 handler，它仍然是错的。

最小示例形态：

```python
def caught_flip(perm, k):
    try:
        perm[: k + 1] = perm[k::-1]
    except ValueError:
        return "caught"
    return perm
```

如果 JIT folding 把 slice 操作替换成 helper，测试必须证明 helper 抛出的异常仍会被同一 frame 的 `except` 捕获，并且预期 fast path 确实运行过。

## RuntimeTests 硬要求

任何触及 bytecode builder、preload、HIR、LIR、codegen、runtime helper、deopt/FrameState、refcount 敏感行为，或消费 CPython adaptive/specialized opcode 的 JIT 优化 PR，通常都需要新增或更新 `RuntimeTests`。

`test_cinderx`、stdlib tests、pyperformance 和 microbenchmarks 都是辅助证据。它们不能替代被修改 JIT 层级的本地机器检查。

最低 RuntimeTests 证据：

- Fast path 正例要证明目标 opcode、HIR shape、LIR shape、helper call 或 codegen shape 出现。
- Guard miss / fallback 负例要证明无效假设不会使用 fast path。
- Adaptive/specialized opcode 测试要先触发目标 opcode 状态，再验证 JIT 消费了该状态。
- Deopt、FrameState、borrowed/owned refs、may-raise helpers 和 side-effect order 改动要有直接断言。

可接受的例外：

- 纯文档。
- 仅注释。
- 仅测试工具改动。
- 不改变 JIT 行为的重构。

例外理由应在 PR 说明里显式写清楚。

## 证据等级

P0 证据：

- JIT on/off 返回值等价。
- 异常类型和异常时机等价。
- Fast path 正例证据。
- Guard miss / fallback 负例证据。
- 目标函数确实进入 CinderX JIT。
- 如果涉及 adaptive/specialized opcode，要证明目标 opcode 已被触发。

P1 证据：

- HIR shape 或 opcode count 证据。
- Deopt / FrameState 覆盖。
- May-raise helper 异常传播覆盖。
- 针对 helper/fallback 异常的 same-frame protected-region 测试。
- 当 ownership、helper exception edge 或 deopt live refs 被触及时，要有 refcount 敏感覆盖。
- Specialized opcode enabled/disabled 等价性。

P2 证据：

- 针对新增或扩宽 fast path 的随机、property、metamorphic 或 stress 输入。
- 相关时覆盖 monitoring / instrumentation 交互。

## 现有设施

优先使用仓库已有机制，不要先发明新的检查方式：

- HIR text fixtures: `cinderx/RuntimeTests/hir_tests`
- HIR expected update script: `cinderx/TestScripts/update_hir_expected.py`
- HIR SSA verifier: `cinderx/Jit/hir/ssa.cpp`
- HIR stats: `cinderx/Jit/hir/hir_stats.cpp`

## Review 收口规则

只有检查完以下内容后，review 才能说 “no blocker”：

- 被修改层级有局部正确性证据。
- 有风险的 fast path 有正例和负例测试。
- RuntimeTests 覆盖存在，或明确说明不需要。
- 任何系统级测试都被描述为辅助证据，而不是替代局部证明。
