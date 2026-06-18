# CinderX JIT Review Checklists

Use this file after reading the diff and `jit-correctness-validation-strategy.md`. These sections are common failure modes, not an exhaustive taxonomy. Pick the sections that match the patch, and still review any novel correctness risk exposed by the diff.

## General intake

Check:

- What exact Python operation or CPython opcode is being optimized?
- Which CinderX layer owns the new rule?
- Is the fast path narrower than, equal to, or wider than CPython's own specialization predicate?
- What happens when each assumption fails?
- Does the PR prove the optimized path actually runs?

Finding when missing:

- Ask for a small correctness contract and targeted RuntimeTests before accepting broad end-to-end evidence.

## May-raise / helper fallback

Trigger:

- New helper call.
- Folded bytecode sequence.
- Replaced generic operation.
- Moved guard, `CheckNeg`, `CheckExc`, `CallStatic`, or runtime call.
- Any fast path, guard miss, or fallback can raise.

Check:

- Does the optimized operation preserve exception type and timing?
- Is the original bytecode offset in a `co_exceptiontable` protected range?
- Does the raised exception still reach the same-frame `try` / `except` / `finally` / `with` handler?
- Does the helper preserve side effects that occur before the exception?
- Is there a protected-region negative test, not just an uncaught exception test?

Finding when missing:

- Ask for RuntimeTests where the may-raise path sits inside a same-frame protected region and the handler catches the exception.
- Ask for HIR/opcode evidence that the helper fast path was used, not generic fallback.
- If same-frame exception edge cannot be proven, ask for generic lowering inside protected regions.

## Adaptive / specialized opcode intake

Trigger:

- Code reads CPython specialized opcode, adaptive cache, inline cache operand, oparg, version tag, descriptor pointer, slot offset, or specialized stack effect.

Check:

- What is the base opcode after `unspecialize()`?
- Does inline cache size and stack effect still match the base opcode rules?
- Which CPython specialization predicate is being trusted?
- Does CinderX preserve, narrow, or widen that predicate?
- Is each cache operand valid at compile time, or only after runtime guard checks?
- Are raw cached pointers treated as opaque values until a runtime helper validates them?
- Are raw offsets range-checked before turning into field loads?

Finding when missing:

- Ask for RuntimeTests that first force the target specialized opcode, then verify the HIR shape or fallback.
- Ask for negative tests where cache operands are stale, borrowed, structurally invalid, or represent object-header offsets rather than instance-field offsets.
- Do not accept "CPython specialized it" as proof that every cached operand is safe for compile-time dereference.

## Guard / fallback boundary

Trigger:

- New exact-type guard.
- New primitive guard.
- Narrowed or widened accepted input family.
- Fast path relies on list, tuple, int, bool, dict, descriptor, slot, index, length, or shape stability.

Check:

- Are all fast-path assumptions protected before use?
- Does guard failure return to the correct generic operation?
- Does fallback preserve Python exceptions, return values, and side effects?
- Does a subclass, custom dunder, custom `__index__`, negative index, huge int, mutation, or side-effecting descriptor escape the fast path?

Finding when missing:

- Ask for negative RuntimeTests that prove invalid assumptions do not use the fast path.
- Ask for JIT on/off equivalence on boundary cases, not just normal inputs.

## Side-effect order

Trigger:

- Reordered loads/stores.
- Container mutation.
- Attribute store/load.
- Descriptor access.
- Helper combines multiple Python-visible operations.
- Operation can call Python code through dunder, descriptor, `__index__`, comparison, iteration, import, or property access.

Check:

- Are Python-visible callbacks still called in the same order?
- If an early side effect mutates an operand, does the fast path re-check required state?
- If helper combines operations, does it preserve partial side effects before an exception?
- Does a side-effecting negative test prove behavior, not only return value for pure inputs?

Finding when missing:

- Ask for a test with mutation or callback between the assumptions and the use site.
- Ask for side-effect order assertions when helper replacement hides multiple bytecodes behind one runtime call.

## Deopt / FrameState

Trigger:

- New guard that can deopt.
- Moved guard relative to stack/object state.
- Changed `FrameState`.
- New helper or lowering that can deopt or throw.
- Inliner, live value, frame layout, or exception edge changes.

Check:

- Does `FrameState` reconstruct the same Python stack and locals the interpreter expects?
- Are live refs materialized with correct ownership?
- Does deopt happen before or after Python-visible side effects in the correct order?
- Are exception and deopt edges attached to the right bytecode semantics?

Finding when missing:

- Ask for RuntimeTests that force guard failure or deopt after the relevant values are live.
- Ask for checks on reconstructed locals/stack or behavior after deopt resumes.

## Refcount / ownership

Trigger:

- Borrowed/owned relationship changes.
- Refcount insertion sees a new HIR shape.
- New, removed, or reordered may-raise helper/runtime call.
- Container mutation, attribute store, element replacement, or helper owns/transfers references.
- Deopt point has live owned refs.
- Immortal object incref/decref skip path changes.

Check:

- Does the patch explain why refcount considerations are applicable or not applicable?
- Are mortal sentinel objects used when immortal no-op could hide ownership bugs?
- Are live refs still correct across helper exception and deopt edges?
- Does refcount insertion still see the intended ownership shape?

Finding when missing:

- Ask for Stage 2/Stage 5 style RuntimeTests that cover the ownership transition actually changed by the PR.
- Ask for a mortal object case when only immortal constants are tested.

## AArch64 codegen / runtime helper ABI

Trigger:

- Codegen, assembler, uop, branch, compare, helper call, patching, trampoline, or runtime ABI changes.

Check:

- Is SP alignment preserved at calls and deopt points?
- Are caller/callee-saved registers respected?
- Are W/X register widths correct for sign/zero extension and pointer values?
- Are NZCV flags preserved or clobbered only when safe?
- Are branch ranges, code patching, and icache flush requirements handled?
- Does helper ABI match argument/result ownership and exception conventions?
- Does deopt/unwind metadata still map generated code to the right Python frame state?

Finding when missing:

- Ask for RuntimeTests or backend assertions that expose the exact instruction/helper shape.
- Ask for architecture-specific coverage when the change is AArch64-only or platform-sensitive.

## Test surface

Use tests for distinct purposes:

- `RuntimeTests`: local JIT contract, HIR/LIR/codegen/helper/deopt/refcount machine checks.
- `test_cinderx`: system-level Python behavior under CinderX.
- `test_kunpeng`: ARM64/openEuler or Kunpeng-specific behavior, often folded into larger CinderX test runners rather than printed as a separate top-level gate.
- pyperformance / microbenchmarks: performance and limited behavior signal; never enough alone for local correctness.

Finding when missing:

- If the PR changes JIT behavior and has only `test_cinderx`, pyperformance, or benchmark evidence, ask for RuntimeTests.
- If the change is platform-specific and tests run only on generic local environment, ask for the relevant ARM64/openEuler/Kunpeng gate or justify why it is not required.
- If gate output hides `test_kunpeng` inside aggregate counts, clarify suite inclusion separately from top-level output naming.

## Negative test matrix

Choose dimensions that match the fast path:

- exact type -> subclass
- builtin operation -> custom dunder
- expected primitive/index type -> bool, huge int, custom `__index__`
- in-bounds -> out-of-bounds, empty container, negative boundary
- normal return -> exception path
- stable object -> mutated object
- pure operation -> side-effecting operation
- monomorphic input -> changed runtime input type
- JIT on -> JIT off equivalence
- specialized opcode enabled -> disabled equivalence
- trusted structural operand -> structurally invalid operand
- unprotected opcode -> opcode inside protected region
- helper-raised exception escapes -> same-frame handler catches it

The goal is not to keep the fast path active in every negative case. The goal is to prove the fast path is not applied when its assumptions are false.
