#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
AGENTS = ROOT / "agents"

PROFESSIONAL_SKILLS = [
    "cinderx-env-validate",
    "cinderx-env-clean",
    "cinderx-env-bootstrap",
    "cinderx-remote-lab-ops",
    "cinderx-ab-run-slot",
    "cpython-runtime-test-run",
    "cinderx-smoke-check",
    "pyperformance-worker-run",
    "pyperformance-suite-run",
    "pyperformance-result-compare",
    "pyperformance-stat-report",
    "cinderx-gdb-core-triage",
    "cinderx-hir-dump",
    "cinderx-jit-entry-check",
    "cinderx-hir-lir-analyze",
    "cinderx-interpreter-case-analyze",
    "cinderx-isa-microarch-compare",
    "cinderx-optimization-report",
    "validation-strategy",
]

PROFESSIONAL_AGENTS = [
    "cinderx-orchestrator",
    "cinderx-environment-verifier",
    "pyperformance-baseline-runner",
    "pyperformance-candidate-runner",
    "pyperformance-benchmark-analyst",
    "cinderx-crash-triager",
    "cinderx-jit-analyst",
    "cinderx-platform-analyst",
]

GENERIC_OR_OLD_SKILLS = [
    "remote-environment",
    "remote-workspace",
    "command-observability",
    "docker-runtime",
    "docker-lab-runtime",
    "cpython-build",
    "cpython-build-install",
    "test-execution",
    "pyperformance-test",
    "pyperformance-benchmark",
    "benchmark-result-analysis",
    "native-crash-debugging",
    "cinderx-analysis",
    "cinderx-jit-analysis",
    "platform-differential-analysis",
    "experiment-documentation",
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def skill(name: str) -> str:
    return read(SKILLS / name / "SKILL.md")


def agent(name: str) -> str:
    return read(AGENTS / f"{name}.md")


def require(text: str, needle: str, context: str) -> None:
    if needle not in text:
        raise AssertionError(f"{context} 缺少关键信号: {needle}")


def forbid(text: str, needle: str, context: str) -> None:
    if needle in text:
        raise AssertionError(f"{context} 仍包含泛化或旧边界信号: {needle}")


def require_all(text: str, needles: list[str], context: str) -> None:
    for needle in needles:
        require(text, needle, context)


def main() -> int:
    entry = skill("using-cpython-optimize")
    design_skill = skill("design-documentation")
    function_design_template = read(SKILLS / "design-documentation" / "references" / "function-design-template.md")
    question_templates = read(SKILLS / "using-cpython-optimize" / "references" / "clarifying-question-templates.md")
    skill_texts = {name: skill(name) for name in PROFESSIONAL_SKILLS}
    agent_texts = {name: agent(name) for name in PROFESSIONAL_AGENTS}
    workflows = {
        "lab": skill("workflow-remote-cinderx-lab-setup"),
        "crash": skill("workflow-cinderx-crash-triage"),
        "regression": skill("workflow-pyperformance-regression"),
        "jit": skill("workflow-jit-optimization-analysis"),
        "cross_platform": skill("workflow-cross-platform-delta-triage"),
        "feature": skill("workflow-feature-driven-optimization"),
        "platform": skill("workflow-platform-differential-discovery"),
    }
    active_docs = "\n".join([entry, *workflows.values(), *agent_texts.values()])
    all_active_docs = "\n".join([entry, *workflows.values(), *agent_texts.values(), *skill_texts.values()])
    scenarios = read(ROOT / "tests" / "pressure-scenarios.md")
    review = read(ROOT / "tests" / "dynamic-pressure-review.md")
    runtime_router = read(ROOT / "hooks" / "runtime-skill-router")
    validation_router = read(ROOT / "hooks" / "validation-skill-router")
    pyperformance_env_contract = read(SKILLS / "using-cpython-optimize" / "references" / "pyperformance-env-contract.md")
    pyperformance_affinity_guidance = read(SKILLS / "using-cpython-optimize" / "references" / "pyperformance-affinity-guidance.md")
    baseline_source_contract = read(SKILLS / "using-cpython-optimize" / "references" / "baseline-source-contract.md")
    container_tooling_guidance = read(SKILLS / "using-cpython-optimize" / "references" / "container-tooling-guidance.md")

    for number in range(1, 49):
        require(scenarios, f"场景 {number}", "pressure scenarios")

    for name in PROFESSIONAL_SKILLS:
        require(entry, name, "entry skill professional routing")

    for name in PROFESSIONAL_AGENTS:
        require(entry, name, "entry skill agent routing")

    for old_name in GENERIC_OR_OLD_SKILLS:
        if (SKILLS / old_name).exists():
            raise AssertionError(f"泛化或旧 skill 目录未删除: {old_name}")
        forbid(active_docs, f"`{old_name}`", "active docs")

    forbid(all_active_docs, "3.14" + ".5", "active skill/agent/workflow docs")
    forbid(all_active_docs, "correctness", "active skill/agent/workflow docs terminology")
    forbid(all_active_docs, "Runtime 测试", "active skill/agent/workflow docs terminology")

    if len(entry.splitlines()) > 150:
        raise AssertionError("entry skill 应保持薄 router，当前行数超过 150")

    require_all(
        entry,
        [
            "Orchestrator",
            "Workflow",
            "Agent",
            "Skill",
            "Agent 文档不是原生 Skill 自动触发单元",
            "agents/<agent>.md",
            "environment-verifier",
            "baseline-runner",
            "candidate-runner",
            "crash-triager",
            "三态",
            "可复用",
            "新环境",
            "被破坏",
            "反问 Gate",
            "request_user_input",
            "AskUserQuestion",
            "clarifying-question-templates.md",
        ],
        "entry skill",
    )
    require_all(
        question_templates,
        [
            "question_id",
            "request_user_input",
            "AskUserQuestion",
            "文本降级",
            "workflow_route",
            "validation_level",
            "environment_target",
            "destructive_clean",
            "remote_stall",
            "ab_slot",
            "crash_evidence",
            "result_artifacts",
            "scope_budget",
        ],
        "clarifying question templates",
    )

    for name, text in agent_texts.items():
        require_all(text, ["## 职责", "## 适用场景", "## 可调用技能", "## 反问 Gate", "## 输出要求"], f"{name} agent")

    require_all(
        agent_texts["cinderx-environment-verifier"],
        ["reusable", "needs_bootstrap", "needs_clean_bootstrap", "cinderx-env-validate", "cinderx-env-clean", "cinderx-env-bootstrap", "本地 CPython", "安全切换", "网络不佳", "baseline-source-contract.md", "baseline_source_untrusted"],
        "environment verifier",
    )
    require_all(
        agent_texts["pyperformance-baseline-runner"],
        ["baseline", "CPU set", "pyperformance-suite-run", "cinderx-ab-run-slot", "baseline-source-contract.md", "baseline_source_untrusted"],
        "baseline runner",
    )
    require_all(
        agent_texts["pyperformance-candidate-runner"],
        ["candidate", "CPU set", "pyperformance-suite-run", "cinderx-ab-run-slot"],
        "candidate runner",
    )
    require_all(
        agent_texts["cinderx-jit-analyst"],
        ["cinderx-hir-lir-analyze", "cinderx-interpreter-case-analyze", "解释执行", "非 JIT"],
        "cinderx-jit-analyst",
    )

    require_all(
        runtime_router,
        [
            "cinderx-gdb-core-triage",
            "cinderx-remote-lab-ops",
            "workflow-cinderx-crash-triage",
            "gdb bt full",
            "validation-strategy",
            "extract_command",
            "extract_signal_text",
            "is_observation_command",
            "git\\ show",
            "git\\ log",
            "git\\ diff",
        ],
        "runtime hook router",
    )
    require_all(
        validation_router,
        [
            "PreToolUse",
            "permissionDecision",
            "additionalContext",
            "CPYTHON_OPTIMIZE_HOOK_ACK",
            "using-cpython-optimize",
            "validation-strategy",
            "cinderx-env-validate",
            "pyperformance",
            "pyperf",
            "ci_pipeline/run_gate.py",
            "cpython-runtime-test-run",
            "pyperformance-worker-run",
            "pyperformance-result-compare",
            "pip install",
            "patchlevel.h",
            "pyvenv.cfg",
            "is_pyvenv_cfg_mutation",
            "pyperformance_env_contract_hint",
            "pyperformance-env-contract.md",
            "include-system-site-packages",
            ".pth",
            "--inherit-environ",
            "cinderx.is_initialized()",
            "agent_hint",
            "Agent docs",
            "agents/cinderx-environment-verifier.md",
            "agents/pyperformance-baseline-runner.md",
            "agents/cinderx-jit-analyst.md",
        ],
        "validation hook router",
    )

    require_all(
        skill_texts["cinderx-env-validate"],
        ["目标 Python 版本固定为 `Python 3.14.3`", "SOABI", "patchlevel.h", "cinderx.__file__", "_cinderx", "pyperformance 1.13.0", "GCC", "openEuler", "reusable", "本地 CPython 仓", "3.16.0a0", "安全切换", "git worktree", "git status --short", "git show -s --format=%H", "Include/patchlevel.h", "Py_ENABLE_SHARED", "_Python_LIBRARY_RELEASE", "TLSDESC", "DetectsThreadStateOffset", "tstate_offset = -1", "baseline-source-contract.md", "baseline_source_untrusted"],
        "cinderx-env-validate",
    )
    require_all(
        skill_texts["cinderx-env-clean"],
        ["editable install", "build 目录", "venv", "容器", "pyperformance env", "错版本头文件", "保留 cache", "反问 Gate"],
        "cinderx-env-clean",
    )
    require_all(
        skill_texts["cinderx-env-bootstrap"],
        ["cinderx-test", "cpython-baseline", "Docker 双线", "CinderX editable", "CPython baseline", "pip mirror", "pyperformance", "本地 clone", "worktree", "tarball/cache", "最后选项", "AArch64", "Py_ENABLE_SHARED", "libpython3.14*.so*", "DetectsThreadStateOffset", "container-tooling-guidance.md", "反问 Gate"],
        "cinderx-env-bootstrap",
    )
    require_all(
        skill_texts["cinderx-remote-lab-ops"],
        ["SSH", "tmux", "rsync", "docker compose", "stdout/stderr", "exit status", "timeout", "日志路径", "container-tooling-guidance.md", "补装", "反问 Gate"],
        "cinderx-remote-lab-ops",
    )
    require_all(
        skill_texts["cinderx-ab-run-slot"],
        ["baseline", "candidate", "CPU affinity", "绑核", "结果目录", "不重叠", "并行", "pyperformance-affinity-guidance.md", "baseline-source-contract.md", "baseline_source_untrusted", "反问 Gate"],
        "cinderx-ab-run-slot",
    )
    require_all(
        skill_texts["cpython-runtime-test-run"],
        ["RuntimeTests 功能测试", "test_cinderx/lib test 集成测试", "ci_pipeline/run_gate.py --suite runtime", "CINDERX_LOCAL_RUN_LIBTEST=1", "--suite cinderx_local", "L1 smoke", "L3", "L4", "近千条", "DetectsThreadStateOffset", "TLSDESC", "共享/PIC Python"],
        "cpython-runtime-test-run",
    )
    require_all(
        skill_texts["cinderx-smoke-check"],
        ["import cinderx", "is_initialized", "get_import_error", "最小 JIT", "HIR", "_cinderx"],
        "cinderx-smoke-check",
    )
    require_all(
        skill_texts["pyperformance-worker-run"],
        ["run_benchmark.py", "--worker", "driver", "manager", "bench_command()", "sitecustomize", ".pth", "pyvenv.cfg", "LD_LIBRARY_PATH", "PYTHONPATH", "--inherit-environ", "include-system-site-packages", "系统 site-packages", "cinderx.is_initialized()", "CPYTHON_OPTIMIZE_HOOK_ACK=1", "不能在未完成前置证据时提前加", "bm/test-benchmark", "快速 L2", "非 debug"],
        "pyperformance-worker-run",
    )
    require_all(
        skill_texts["pyperformance-suite-run"],
        ["python -m pyperformance run", "--affinity", "pyperformance-affinity-guidance.md", "--inherit-environ", "-b <benchmark-selector>", "-o <result.json>", "warmup", "loops", "run.json", "subset", "full", "CPYTHON_OPTIMIZE_HOOK_ACK=1", "不能在未完成前置证据时提前加", "非 debug", "关闭 HIR/JIT dump", "--debug-single-value", "pyperf compare_to", "反问 Gate"],
        "pyperformance-suite-run",
    )
    for name in [
        "cinderx-hir-dump",
        "cinderx-jit-entry-check",
        "pyperformance-worker-run",
        "pyperformance-suite-run",
        "pyperformance-result-compare",
        "pyperformance-stat-report",
    ]:
        require(skill_texts[name], "pyperformance-env-contract.md", name)
    require_all(
        skill_texts["pyperformance-stat-report"],
        [
            "get_stat.py",
            "scripts/get_stat.py",
            "-c",
            "--benchmarks",
            "benchmark_comparison.xlsx",
            "benchmark_trends_part",
            "openpyxl",
            "matplotlib",
            "console-only",
            "run.json",
        ],
        "pyperformance-stat-report",
    )
    require(workflows["regression"], "pyperformance-env-contract.md", "workflow-pyperformance-regression")
    require(workflows["jit"], "pyperformance-env-contract.md", "workflow-jit-optimization-analysis")

    for name in [
        "pyperformance-baseline-runner",
        "pyperformance-candidate-runner",
        "pyperformance-benchmark-analyst",
    ]:
        require(agent_texts[name], "pyperformance-env-contract.md", name)
    for name in [
        "pyperformance-baseline-runner",
        "pyperformance-candidate-runner",
        "pyperformance-benchmark-analyst",
    ]:
        require(agent_texts[name], "pyperformance-affinity-guidance.md", name)
    require(skill_texts["pyperformance-result-compare"], "pyperformance-affinity-guidance.md", "pyperformance-result-compare")
    require(workflows["regression"], "pyperformance-affinity-guidance.md", "workflow-pyperformance-regression")
    for name in [
        "cinderx-env-validate",
        "cinderx-ab-run-slot",
        "pyperformance-result-compare",
    ]:
        require(skill_texts[name], "baseline-source-contract.md", name)
    require(agent_texts["cinderx-environment-verifier"], "baseline-source-contract.md", "cinderx-environment-verifier")
    require(agent_texts["pyperformance-baseline-runner"], "baseline-source-contract.md", "pyperformance-baseline-runner")
    require(workflows["regression"], "baseline-source-contract.md", "workflow-pyperformance-regression")
    require_all(
        baseline_source_contract,
        [
            "执行环境可用",
            "baseline 源码可信",
            "不能自动",
            "远程 workspace",
            "baseline_source_verified",
            "baseline_source_untrusted",
            "baseline commit/ref",
            "口径 baseline",
            "提交 baseline",
            "CPython 3.14.3",
            "cpython-baseline",
            "bind mount",
            "git status --short",
            "git show -s --format=%H",
            "patchlevel.h",
            "SOABI",
            "dirty",
            "candidate editable install",
            "只差目标变量",
        ],
        "baseline source contract",
    )
    require_all(
        pyperformance_affinity_guidance,
        [
            "--affinity",
            "CPU 绑核",
            "worker",
            "不是 benchmark 选择器",
            "不能逐字照抄",
            "nproc",
            "lscpu",
            "taskset -pc $$",
            "cpuset",
            "baseline/candidate",
            "相同数量",
            "互不冲突",
            "重分配",
            "串行执行",
        ],
        "pyperformance affinity guidance",
    )
    require_all(
        pyperformance_env_contract,
        [
            "driver",
            "manager",
            "worker",
            "bench_command()",
            ".pth",
            "site-packages",
            "pyvenv.cfg",
            "include-system-site-packages",
            "include-system-site-packages = true",
            "include-system-site-packages = false",
            "pyperformance venv create",
            "sed -i 's/^include-system-site-packages = false/include-system-site-packages = true/'",
            "--inherit-environ",
            "LD_LIBRARY_PATH",
            "PYTHONPATH",
            "PYPERFORMANCE_HOOK_ROOT",
            "PYPERF_HOOK_ROOT",
            "PYTHONJIT",
            "CINDERX_*",
            "import cinderx",
            "_cinderx",
            "cinderx.__file__",
            "cinderx.get_import_error()",
            "cinderx.is_initialized()",
            "driver import",
            "DIAG",
            "baseline/candidate",
            "正式性能数据",
        ],
        "pyperformance env contract",
    )
    require_all(
        skill_texts["pyperformance-result-compare"],
        ["run.json", "speedup.json", "baseline", "candidate", "方差", "噪声", "收益范围", "提交 baseline", "--affinity", "反问 Gate"],
        "pyperformance-result-compare",
    )
    require_all(
        skill_texts["cinderx-gdb-core-triage"],
        ["SIGSEGV", "exit 139", "core dump", "gdb", "bt full", "info registers", "同一真实命令", "日志不能替代", "container-tooling-guidance.md", "补装", "反问 Gate"],
        "cinderx-gdb-core-triage",
    )
    for name in [
        "cinderx-env-bootstrap",
        "cinderx-remote-lab-ops",
        "cinderx-gdb-core-triage",
    ]:
        require(skill_texts[name], "container-tooling-guidance.md", name)
    require_all(
        container_tooling_guidance,
        [
            "gdb",
            "ripgrep",
            "rg",
            "strace",
            "perf",
            "binutils",
            "补装",
            "不要直接绕开",
            "command -v",
            "dnf",
            "yum",
            "apt",
            "DNS",
            "代理",
            "cache",
            "timeout",
            "metadata",
            "dry run",
            "继续等待",
            "切镜像",
            "离线包",
            "exit status",
        ],
        "container tooling guidance",
    )
    require_all(
        skill_texts["cinderx-hir-dump"],
        ["PYTHONJITDUMPFINALHIR", "PYTHONJITLOGFILE", "真实 worker", "HIR dump", "jit.log", "不另造"],
        "cinderx-hir-dump",
    )
    require_all(
        skill_texts["cinderx-jit-entry-check"],
        ["benchmark 本体", "CinderX JIT", "启动期", "第三方包", "compile storm", "jit.log", ".pth", "pyvenv.cfg", "cinderx.is_initialized()"],
        "cinderx-jit-entry-check",
    )
    require_all(
        skill_texts["cinderx-hir-lir-analyze"],
        ["JIT 用例", "HIR", "LIR", "uop", "机器码", "deopt", "frame layout", "调用约定", "平台差异", "修改方案"],
        "cinderx-hir-lir-analyze",
    )
    require_all(
        skill_texts["cinderx-interpreter-case-analyze"],
        [
            "解释执行用例",
            "非 JIT",
            "穿刺证据",
            "分阶段平铺表",
            "CPython JIT baseline",
            "CinderX JIT 优化前",
            "CinderX JIT 优化后",
            "已优化量",
            "剩余 gap",
            "函数形状表",
            "autojit 分类模型",
            "全量函数形状",
            "gate 策略",
            "不进入 gate",
            "阶段详细拆解",
        ],
        "cinderx-interpreter-case-analyze",
    )
    require_all(
        skill_texts["cinderx-isa-microarch-compare"],
        ["Kunpeng", "x86", "ISA", "cache", "分支预测", "SIMD", "barrier", "hugepages", "perf", "反问 Gate"],
        "cinderx-isa-microarch-compare",
    )
    require_all(
        skill_texts["cinderx-optimization-report"],
        ["背景", "复现命令", "环境指纹", "证据链", "根因", "patch", "回归结果"],
        "cinderx-optimization-report",
    )
    require_all(
        design_skill,
        ["功能设计", "总-分结构", "功能域", "功能项", "通俗易懂", "深入浅出", "外部视角", "mermaid", "表格", "后部"],
        "design-documentation",
    )
    require_all(
        function_design_template,
        ["总述", "外部视角", "通俗说明", "mermaid", "表格", "后半部"],
        "function design template",
    )

    workflow_expectations = {
        "lab": ["cinderx-environment-verifier", "cinderx-env-validate", "cinderx-env-bootstrap", "cinderx-smoke-check"],
        "crash": ["cinderx-crash-triager", "cinderx-gdb-core-triage", "cinderx-hir-dump", "pyperformance-worker-run"],
        "regression": ["cinderx-environment-verifier", "pyperformance-baseline-runner", "pyperformance-candidate-runner", "pyperformance-benchmark-analyst"],
        "jit": ["cinderx-jit-analyst", "cinderx-jit-entry-check", "cinderx-hir-lir-analyze", "cinderx-interpreter-case-analyze", "cinderx-hir-dump"],
        "cross_platform": ["cinderx-environment-verifier", "pyperformance-baseline-runner", "pyperformance-candidate-runner", "cinderx-platform-analyst"],
        "feature": [
            "cinderx-environment-verifier",
            "cinderx-jit-analyst",
            "cpython-runtime-test-run",
            "pyperformance-result-compare",
            "TDD",
            "功能用例",
            "集成用例",
            "补充或修改",
            "unittest",
        ],
        "platform": ["cinderx-platform-analyst", "cinderx-isa-microarch-compare", "cinderx-jit-analyst", "pyperformance-result-compare"],
    }
    for workflow_name, needles in workflow_expectations.items():
        require_all(workflows[workflow_name], needles, f"{workflow_name} workflow")

    require_all(
        scenarios,
        [
            "cinderx-env-validate",
            "cinderx-env-clean",
            "cinderx-env-bootstrap",
            "cinderx-ab-run-slot",
            "pyperformance-worker-run",
            "cinderx-gdb-core-triage",
            "cinderx-isa-microarch-compare",
            "request_user_input",
            "AskUserQuestion",
            "clarifying-question-templates.md",
            "validation-skill-router",
            "CPYTHON_OPTIMIZE_HOOK_ACK",
            "RuntimeTests 功能测试",
            "test_cinderx/lib test 集成测试",
            "pyperformance 性能测试",
            "include-system-site-packages",
            "本地 CPython 仓",
            "安全切换",
            "git worktree",
            "总-分结构",
            "外部视角",
            "mermaid",
            "DetectsThreadStateOffset",
            "_Python_LIBRARY_RELEASE",
            "TLSDESC",
            "Py_ENABLE_SHARED",
            "pyperformance-env-contract.md",
            "--inherit-environ",
            "worker env",
            ".pth",
            "pyvenv.cfg",
            "cinderx.is_initialized()",
            "cinderx.get_import_error()",
            "pyperformance-affinity-guidance.md",
            "baseline-source-contract.md",
            "baseline_source_verified",
            "baseline_source_untrusted",
            "container-tooling-guidance.md",
            "补装",
            "cinderx-interpreter-case-analyze",
            "解释执行用例",
            "穿刺证据",
            "分阶段平铺表",
            "函数形状表",
            "gate 策略",
            "Agent docs",
            "agents/<agent>.md",
            "python -m pyperformance run -b",
            "run_benchmark.py --worker",
            "pyperformance-env-contract.md",
            "pyvenv.cfg",
            ".pth",
            "--inherit-environ",
            "cinderx.is_initialized()",
            "cinderx.get_import_error()",
            "cinderx-environment-verifier",
            "cinderx-jit-analyst",
            "include-system-site-packages",
            "CPYTHON_OPTIMIZE_HOOK_ACK=1",
        ],
        "pressure scenarios",
    )
    require_all(
        review,
        ["专业 skill", "Agent 层", "cinderx-env-validate", "cinderx-ab-run-slot", "cinderx-gdb-core-triage", "PreToolUse"],
        "dynamic pressure review",
    )

    print("pressure scenario validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
