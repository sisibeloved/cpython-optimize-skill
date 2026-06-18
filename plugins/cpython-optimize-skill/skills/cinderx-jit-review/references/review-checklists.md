# CinderX JIT Review 检查清单

在阅读 diff 和 `jit-correctness-validation-strategy.md` 之后使用本文件。这些小节列的是常见失败模式，不是完整风险分类。选择与补丁匹配的小节检查，同时仍要 review diff 暴露出的任何新型正确性风险。

## 通用入口检查

检查：

- 具体优化的是哪个 Python 操作或 CPython opcode？
- 新规则由哪个 CinderX 层级负责？
- Fast path 相比 CPython 自身 specialization predicate，是更窄、相等，还是更宽？
- 每个假设失败时会发生什么？
- PR 是否证明了优化路径确实运行？

缺失时的 finding 口径：

- 在接受宽泛端到端证据前，要求提供小型正确性契约和定向 RuntimeTests。

## May-raise / helper fallback

触发条件：

- 新增 helper call。
- 折叠 bytecode 序列。
- 替换 generic operation。
- 移动 guard、`CheckNeg`、`CheckExc`、`CallStatic` 或 runtime call。
- 任意 fast path、guard miss 或 fallback 可能抛异常。

检查：

- 优化后的操作是否保持异常类型和异常时机？
- 原始 bytecode offset 是否位于 `co_exceptiontable` 的 protected range 内？
- 抛出的异常是否仍能到达 same-frame 的 `try` / `except` / `finally` / `with` handler？
- Helper 是否保持异常发生前已经出现的副作用？
- 是否有 protected-region 负例测试，而不仅是 uncaught exception 测试？

缺失时的 finding 口径：

- 要求增加 RuntimeTests，把 may-raise 路径放在 same-frame protected region 内，并证明 handler 会捕获异常。
- 要求提供 HIR/opcode 证据，证明使用的是 helper fast path，而不是 generic fallback。
- 如果无法证明 same-frame exception edge，要求在 protected region 内使用 generic lowering。

## Adaptive / specialized opcode 读取

触发条件：

- 代码读取 CPython specialized opcode、adaptive cache、inline cache operand、oparg、version tag、descriptor pointer、slot offset 或 specialized stack effect。

检查：

- `unspecialize()` 后的 base opcode 是什么？
- Inline cache size 和 stack effect 是否仍匹配 base opcode 规则？
- 代码信任的是哪个 CPython specialization predicate？
- CinderX 是保持、收窄还是扩宽了该 predicate？
- 每个 cache operand 在 compile time 就有效，还是只有 runtime guard 检查后才有效？
- Raw cached pointer 在 runtime helper 验证前是否被当作 opaque value 处理？
- Raw offset 在转成 field load 前是否做了 range check？

缺失时的 finding 口径：

- 要求增加 RuntimeTests：先强制触发目标 specialized opcode，再验证 HIR shape 或 fallback。
- 要求增加 cache operand stale、borrowed、结构无效，或代表 object-header offset 而不是 instance-field offset 的负例。
- 不要接受“CPython 已经 specialized 了”作为每个 cached operand 都能安全 compile-time dereference 的证明。

## Guard / fallback 边界

触发条件：

- 新增 exact-type guard。
- 新增 primitive guard。
- 收窄或扩宽可接受的输入族。
- Fast path 依赖 list、tuple、int、bool、dict、descriptor、slot、index、length 或 shape 稳定性。

检查：

- 所有 fast-path 假设是否在使用前都被保护？
- Guard failure 是否回到正确的 generic operation？
- Fallback 是否保持 Python 异常、返回值和副作用？
- Subclass、custom dunder、custom `__index__`、negative index、huge int、mutation 或 side-effecting descriptor 是否会逃离 fast path？

缺失时的 finding 口径：

- 要求增加负向 RuntimeTests，证明无效假设不会使用 fast path。
- 要求覆盖边界场景的 JIT on/off 等价性，而不只是普通输入。

## 副作用顺序

触发条件：

- 重排 load/store。
- Container mutation。
- Attribute store/load。
- Descriptor access。
- Helper 合并多个 Python-visible operation。
- 操作可能通过 dunder、descriptor、`__index__`、comparison、iteration、import 或 property access 调用 Python 代码。

检查：

- Python-visible callback 是否仍按同一顺序调用？
- 如果早期副作用修改了 operand，fast path 是否重新检查所需状态？
- 如果 helper 合并多个操作，它是否保持异常前的 partial side effects？
- 是否有 side-effecting 负例测试证明行为，而不只是纯输入的返回值？

缺失时的 finding 口径：

- 要求增加在假设建立和使用点之间发生 mutation 或 callback 的测试。
- 当 helper replacement 把多个 bytecode 隐藏到一个 runtime call 后面时，要求增加 side-effect order 断言。

## Deopt / FrameState

触发条件：

- 新增可能 deopt 的 guard。
- 相对 stack/object state 移动 guard。
- 修改 `FrameState`。
- 新增可能 deopt 或 throw 的 helper 或 lowering。
- 修改 inliner、live value、frame layout 或 exception edge。

检查：

- `FrameState` 是否重建出解释器预期的同一份 Python stack 和 locals？
- Live refs 是否以正确 ownership materialize？
- Deopt 相对 Python-visible side effects 的前后顺序是否正确？
- Exception 和 deopt edges 是否挂在正确的 bytecode 语义上？

缺失时的 finding 口径：

- 要求增加 RuntimeTests，在相关值 live 之后强制触发 guard failure 或 deopt。
- 要求检查重建后的 locals/stack，或检查 deopt resume 后的行为。

## Refcount / ownership

触发条件：

- Borrowed/owned 关系变化。
- Refcount insertion 看到新的 HIR shape。
- 新增、删除或重排 may-raise helper/runtime call。
- Container mutation、attribute store、element replacement，或 helper owns/transfers references。
- Deopt point 存在 live owned refs。
- Immortal object incref/decref skip path 变化。

检查：

- 补丁是否解释了 refcount 考量为什么适用或不适用？
- 当 immortal no-op 可能隐藏 ownership bug 时，测试是否使用 mortal sentinel objects？
- 跨 helper exception 和 deopt edges 时，live refs 是否仍然正确？
- Refcount insertion 是否仍能看到预期 ownership shape？

缺失时的 finding 口径：

- 要求增加 Stage 2/Stage 5 风格的 RuntimeTests，覆盖 PR 实际修改的 ownership transition。
- 如果测试只覆盖 immortal constants，要求增加 mortal object 用例。

## AArch64 codegen / runtime helper ABI

触发条件：

- 修改 codegen、assembler、uop、branch、compare、helper call、patching、trampoline 或 runtime ABI。

检查：

- Call 和 deopt point 处是否保持 SP alignment？
- Caller/callee-saved registers 是否被正确遵守？
- W/X register widths 对 sign/zero extension 和 pointer values 是否正确？
- NZCV flags 是否被保持，或只在安全时 clobber？
- Branch ranges、code patching 和 icache flush 要求是否已处理？
- Helper ABI 是否匹配 argument/result ownership 和 exception conventions？
- Deopt/unwind metadata 是否仍能把 generated code 映射到正确的 Python frame state？

缺失时的 finding 口径：

- 要求增加 RuntimeTests 或 backend assertions，暴露精确 instruction/helper shape。
- 当改动是 AArch64-only 或 platform-sensitive 时，要求增加架构特定覆盖。

## 测试面

不同测试承担不同目的：

- `RuntimeTests`：局部 JIT contract，以及 HIR/LIR/codegen/helper/deopt/refcount 的机器检查。
- `test_cinderx`：CinderX 下的系统级 Python 行为。
- `test_kunpeng`：ARM64/openEuler 或 Kunpeng-specific 行为，常被折叠进更大的 CinderX test runner，而不是作为单独 top-level gate 打印。
- pyperformance / microbenchmarks：性能和有限行为信号；永远不足以单独证明局部正确性。

缺失时的 finding 口径：

- 如果 PR 改变 JIT 行为但只有 `test_cinderx`、pyperformance 或 benchmark 证据，要求补 RuntimeTests。
- 如果改动是平台特定的，而测试只在普通本地环境运行，要求补相关 ARM64/openEuler/Kunpeng gate，或说明为什么不需要。
- 如果 gate 输出把 `test_kunpeng` 隐藏在汇总计数里，要把 suite inclusion 和 top-level output 命名分开澄清。

## 负例测试矩阵

选择与 fast path 匹配的维度：

- exact type -> subclass
- builtin operation -> custom dunder
- expected primitive/index type -> bool、huge int、custom `__index__`
- in-bounds -> out-of-bounds、empty container、negative boundary
- normal return -> exception path
- stable object -> mutated object
- pure operation -> side-effecting operation
- monomorphic input -> changed runtime input type
- JIT on -> JIT off equivalence
- specialized opcode enabled -> disabled equivalence
- trusted structural operand -> structurally invalid operand
- unprotected opcode -> opcode inside protected region
- helper-raised exception escapes -> same-frame handler catches it

目标不是让 fast path 在每个负例里都保持激活。目标是证明当假设不成立时，fast path 不会被应用。
