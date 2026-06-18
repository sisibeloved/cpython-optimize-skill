---
name: cinderx-jit-review
description: Use when reviewing CinderX JIT pull requests, merge requests, or patches for correctness risks, validation gaps, RuntimeTests/test_cinderx/test_kunpeng coverage, exact review comment placement, or correctness-contract evidence around bytecode builder, preload, HIR, LIR, codegen, runtime helpers, deopt, FrameState, refcount, adaptive/specialized opcodes, may-raise behavior, helper fallback, side-effect order, or AArch64 backend semantics.
---

# CinderX JIT Review

## 定位

对 CinderX JIT PR 做 correctness-first code review。优先找会改变 Python 语义、JIT 层级契约、exception edge、deopt/refcount、specialized opcode 消费、helper fallback 或验证边界的风险。

这个 skill 不是性能调优流程。性能收益只能作为背景；review 结论先回答“这次 JIT 改动如何证明没有改坏语义”。

## 必读材料

每次完整 review 前读取：

- `references/jit-correctness-validation-strategy.md`：分层正确性策略、may-raise / exception table、RuntimeTests 硬要求。
- `references/review-checklists.md`：按风险类型检查 helper、deopt、refcount、adaptive opcode、side effect、AArch64 codegen 和覆盖证据。

如果只回答一个局部问题，也至少读取对应 reference 中的相关小节；不要只凭通用 C++ 或 Python 经验下结论。

## 开放性原则

把本 skill 当作 review 下限，不当作风险全集。先从具体 diff、调用链、执行时机、异常边、ownership、平台约束和测试证据出发，再用 references 补充已知高风险模式。

- 如果 diff 暴露了 references 没列出的新风险，也要按 correctness-first review 输出 finding。
- 不要因为某个问题不属于 may-raise、deopt、refcount、adaptive opcode 或 AArch64 checklist，就跳过它。
- 当新风险反复出现时，在 review 结束后建议把它沉淀回 `references/review-checklists.md`，但不要等文档更新后才指出问题。
- 明确区分“本 skill 没覆盖”和“这个 PR 没风险”；前者不能推出后者。

## Review 顺序

1. 明确 review 对象。
   - 确认 repo、base/head、PR/MR 编号、diff 范围和目标分支。
   - 如果是 GitCode PR，优先 review `refs/merge-requests/<id>/head` 和 `refs/merge-requests/<id>/merge`，不要只看分支 tip。

2. 判定改动层级。
   - Bytecode builder / preload。
   - HIR lowering、optimization pass、guard、verifier。
   - LIR、regalloc、uop。
   - Codegen、AArch64 backend、runtime helper。
   - Deopt、FrameState、frame layout、live refs。
   - RuntimeTests、`test_cinderx`、`test_kunpeng`、gate/tooling。

3. 写出本次 correctness contract。
   - 这次优化依赖的 Python 语义前提是什么？
   - 哪些前提由 guard、verifier、helper contract 或 codegen invariant 保护？
   - 前提失效时如何 fallback、deopt 或回到解释器语义？
   - 哪些机器检查证明 fast path 命中、fallback 正确、JIT on/off 等价？

4. 按风险 checklist 做第二遍 review。
   - `may-raise` 点是否被新增、删除、移动、合并或替换？
   - 是否消费 CPython adaptive / specialized opcode 或 inline cache？
   - 是否改变 helper call、side-effect 顺序、container mutation、attribute access、descriptor 行为？
   - 是否改变 borrowed / owned ref、refcount insertion 输入、deopt live refs？
   - 是否改变 AArch64 寄存器、NZCV flags、W/X 宽度、SP alignment、branch/code patching、deopt mapping？

5. 审查验证面。
   - JIT 行为改动通常必须有 `RuntimeTests` 机器检查；`test_cinderx`、pyperformance、microbenchmark 不能替代局部 lowering/pass/codegen 契约。
   - `test_cinderx` 证明系统级 Python 行为，不能单独证明 HIR/LIR/codegen fast path 命中。
   - `test_kunpeng` 用于 ARM64/openEuler 相关路径时，检查是否覆盖目标 specialized opcode、helper、AArch64 或 platform-sensitive 行为。
   - 纯文档、注释、测试工具或不改变 JIT 行为的重构可以没有 RuntimeTests，但 PR 说明应显式解释。

6. 输出 review findings。
   - Findings 必须排在最前面，按严重度排序。
   - 每条 finding 必须包含 severity、文件/行号、风险、缺失证据或建议修复。
   - 用户问“在哪评论”时，先给 exact file/line placement 和 P1/P2，再给解释。
   - 如果没有 blocker，也要说明剩余验证缺口和你没有覆盖的风险面。

## Severity 口径

- P1：可能导致错误语义、异常传播错误、crash、silent wrong result、deopt/refcount 破坏，或 PR 缺少证明核心 fast path 正确性的 RuntimeTests。
- P2：覆盖不足、contract 描述不清、负例缺失、平台 gate 表达不完整，或存在高风险但当前 diff 里尚未证明会出错。
- P3：文档、命名、维护性、review 可读性问题，不应遮住 correctness findings。

不要把“测试缺失”自动降级。若缺失测试正是证明核心 JIT 语义所必需的证据，应按 correctness 风险定级。

## 输出模板

```text
Findings
- [P1] <file>:<line> <title>
  <why this can break Python/JIT semantics>
  Required evidence or fix:
  <specific RuntimeTests/test_cinderx/test_kunpeng or code change>
  Suggested comment:
  <ready-to-paste review comment>

Open Questions / Assumptions
- <only if needed>

Validation Notes
- Reviewed diff: <base..head or PR/MR refs>
- Local checks run: <commands or not run>
- Remaining risk: <short>
```

Keep the final answer concise, but keep enough technical detail for the user to paste the review comment without another round trip.
