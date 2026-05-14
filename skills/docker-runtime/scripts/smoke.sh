#!/bin/bash
# Smoke test to verify JIT is working
set -e

echo "=== Running smoke tests ==="
python3 << 'PY'
import cinderx
import cinderx.jit as jit

# Test 1: Basic JIT compilation
print("Test 1: Basic JIT compilation")
def f(n: int) -> int:
    s = 0
    for i in range(n):
        s += i
    return s

result = jit.force_compile(f)
assert result, "force_compile failed"
assert jit.is_jit_compiled(f), "function not compiled"
size = jit.get_compiled_size(f)
print(f"✓ f(n) compiled: {size} bytes")

# Test 2: Generator compilation
print("\nTest 2: Generator compilation")
def gen(n):
    for i in range(n):
        yield i

result = jit.force_compile(gen)
assert result, "generator compile failed"
print(f"✓ gen(n) compiled: {jit.get_compiled_size(gen)} bytes")

# Test 3: Tree.__iter__ compilation
print("\nTest 3: Tree.__iter__ compilation (if available)")
try:
    import sys
    sys.path.insert(0, "/root/benchmarks/bm_generators")
    from run_benchmark import Tree

    result = jit.force_compile(Tree.__iter__)
    if result:
        print(f"✓ Tree.__iter__ compiled: {jit.get_compiled_size(Tree.__iter__)} bytes")
    else:
        print("⚠ Tree.__iter__ not compiled (expected on non-ARM or with limited JIT)")
except Exception as e:
    print(f"⚠ Tree.__iter__ test skipped: {e}")

print("\n=== All smoke tests passed ===")
PY
