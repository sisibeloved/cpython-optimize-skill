# JIT Correctness Validation Strategy

Source pages:

- https://github.com/Cookie4Cat/cinderx/wiki/JIT-Correctness-Validation-Strategy
- https://github.com/Cookie4Cat/cinderx/wiki/JIT-Optimization-Correctness-Contract

## Baseline

Use this strategy for CinderX JIT correctness review under:

- ARM / AArch64
- CPython 3.14.3 GIL build
- cinderx

Pages or PR notes that mention later CPython versions should be treated as experiment history unless they explicitly update the baseline.

## 局部正确性与系统正确性

Separate the review into two claims:

- Local correctness: the changed builder, preload, HIR, LIR, codegen, helper, deopt, or refcount rule preserves the semantics it owns.
- System correctness: the composed program still matches Python behavior under JIT on/off and gate coverage.

This skill focuses on local correctness first. Gate results are supporting evidence, not a substitute for layer-local proof.

## Stage map

| Stage | Review focus | Typical evidence |
|-------|--------------|------------------|
| Stage 1 - Bytecode builder / preload | Opcode interpretation, CPython 3.14 adaptive state, inline cache intake, Python semantic preconditions | RuntimeTests that trigger the intended opcode/cache state; builder/preload shape checks; generic fallback checks |
| Stage 2 - HIR | Lowering, guards, helper calls, ownership shape, verifier assumptions | HIR text fixtures, opcode count, guard/fallback negative cases, SSA/verifier evidence |
| Stage 3 - LIR / regalloc | Operand lowering, register constraints, live ranges, materialization | LIR/uop evidence, spill/live range cases, architecture-sensitive negative cases |
| Stage 4 - Codegen / runtime helpers | AArch64 instruction semantics, helper ABI, flags, width, runtime call side effects | RuntimeTests for code shape/helper semantics, AArch64 backend assertions, helper exception/side-effect tests |
| Stage 5 - Deopt / FrameState / refs | Frame reconstruction, live refs, owned/borrowed state, exception/deopt edge | RuntimeTests for deopt path, FrameState contents, refcount-sensitive cases |
| Stage 6 - End-to-end Python semantics | JIT on/off equivalence and system behavior | `test_cinderx`, targeted stdlib tests, pyperformance only as supplemental behavior/perf evidence |

## Six questions for every JIT change

For each changed rule, require answers to:

1. Which layer owns the change?
2. What Python or JIT-layer semantics must this layer preserve?
3. What assumptions does the fast path make?
4. What invariants can be broken if the assumptions are false?
5. Which machine checks prove the invariants?
6. Which positive, negative, and end-to-end tests prove the behavior?

If these cannot be answered, the PR is not yet in a reviewable correctness shape.

## PR-level correctness contract

Ask for or reconstruct this contract while reviewing:

```text
Optimization:
Affected stages:
Python semantic source:
Fast-path assumptions:
Guards / checks that protect those assumptions:
Guard failure behavior:
May-raise points:
Exception-table / protected-region behavior:
Side effects / memory dependencies:
FrameState / deopt requirements:
Refcount considerations:
Version-specific differences:
Required tests:
Known non-goals:
```

Missing contract fields are not automatically findings. They become findings when the diff relies on that field to be safe and the PR does not provide code or test evidence.

## May-raise and exception table rule

If a lowering adds, removes, moves, replaces, or merges a `may-raise` point, review more than exception type equivalence.

Check:

- Is the original bytecode offset inside a `co_exceptiontable` protected range?
- Should the original exception be caught by a handler in the same Python frame?
- Does the new fast path, helper, guard miss, or fallback preserve the original same-frame exception edge?
- If that cannot be proven, does the optimized path disable itself or return to generic lowering inside the protected region?

Core rule: a helper fallback that raises the right exception type can still be wrong if the exception bypasses the handler that would have caught the original bytecode operation.

Minimal example shape:

```python
def caught_flip(perm, k):
    try:
        perm[: k + 1] = perm[k::-1]
    except ValueError:
        return "caught"
    return perm
```

If JIT folding replaces the slice operation with a helper, tests must prove the helper-raised exception is still caught by the same-frame `except`, and that the intended fast path actually ran.

## RuntimeTests hard requirement

Any JIT optimization PR that touches bytecode builder, preload, HIR, LIR, codegen, runtime helper, deopt/FrameState, refcount-sensitive behavior, or CPython adaptive/specialized opcode consumption normally needs new or updated `RuntimeTests`.

`test_cinderx`, stdlib tests, pyperformance, and microbenchmarks are supplemental. They do not replace local machine checks for the JIT layer being changed.

Minimum RuntimeTests evidence:

- Fast path positive case proves the target opcode, HIR shape, LIR shape, helper call, or codegen shape appears.
- Guard miss / fallback negative case proves invalid assumptions do not use the fast path.
- Adaptive/specialized opcode tests first trigger the target opcode state, then verify JIT consumption.
- Deopt, FrameState, borrowed/owned refs, may-raise helpers, and side-effect order changes have direct assertions.

Valid exceptions:

- Pure docs.
- Comments only.
- Test-tool-only changes.
- Refactors that do not change JIT behavior.

The exception should be explicit in the PR description.

## Evidence levels

P0 evidence:

- JIT on/off return value equivalence.
- Exception type and timing equivalence.
- Fast path positive evidence.
- Guard miss / fallback negative evidence.
- Target function really entered CinderX JIT.
- If adaptive/specialized opcodes are involved, proof that the target opcode was triggered.

P1 evidence:

- HIR shape or opcode count evidence.
- Deopt / FrameState coverage.
- May-raise helper exception propagation coverage.
- Same-frame protected-region test for helper/fallback exceptions.
- Refcount-sensitive coverage when ownership, helper exception edges, or deopt live refs are touched.
- Specialized opcode enabled/disabled equivalence.

P2 evidence:

- Randomized, property, metamorphic, or stress inputs for new or widened fast paths.
- Monitoring / instrumentation interaction when relevant.

## Existing facilities

Prefer existing repository mechanisms before inventing new checks:

- HIR text fixtures: `cinderx/RuntimeTests/hir_tests`
- HIR expected update script: `cinderx/TestScripts/update_hir_expected.py`
- HIR SSA verifier: `cinderx/Jit/hir/ssa.cpp`
- HIR stats: `cinderx/Jit/hir/hir_stats.cpp`

## Review closeout rule

A review can say "no blocker" only after checking:

- The changed layer has local correctness evidence.
- The risky fast path has positive and negative tests.
- RuntimeTests coverage is present or explicitly unnecessary.
- Any system-level tests are described as supplemental rather than substituting local proof.
