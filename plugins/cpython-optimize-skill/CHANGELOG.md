# Changelog

本文件记录 `cpython-optimize-skill` 的显著变更，面向使用者和维护者，而不是 git 日志的简单堆砌。

格式基于 [Keep a Changelog 1.1.0](https://keepachangelog.com/zh-CN/1.1.0/)，版本号遵循 [Semantic Versioning](https://semver.org/spec/v2.0.0.html)。

## [1.0.3] - 2026-07-30

### Added

- 在 `design-documentation` skill 新增「特性设计（RFC）」文档类型与模板 `references/feature-rfc-template.md`：作为设计流程最上游（层级 0），在正式设计前对齐动机、目标/非目标、用例、总体方案、技术选型、风险与开放问题；带 `Status`（Draft/Reviewing/Approved/Rejected/Superseded）状态字段并要求关联 Issue/PR。

### Changed

- 重写 `design-documentation` 的 `SKILL.md` 提示词：新增「视图规范与制图约定」统一架构图（框图，决定系统/组件/模块设计元素）、上下文视图（一组逻辑接口）、流程图（单逻辑接口）三类图的元素对应与聚合关系，并定义逻辑元素→代码→构建→交付→部署的模型链。
- 强化「架构设计」「功能设计」的总-分结构：总述给整体重点/边界/交互形式，分述须由总述推理而来；明确功能设计是架构设计架构图的 1 层/2 层展开，两者元素一一对应。

## [1.0.2] - 2026-07-12

### Added

- 新增 `pyperformance-stat-report` skill，用 bundled `scripts/get_stat.py` 把已有的 pyperformance JSON 结果整理成多轮统计对比：支持 `--console-only` 控制台表格、`benchmark_comparison.xlsx` 和分页趋势 PNG（每 20 个用例一张图），并提供 `-b` 按用例过滤、`baseline_time/current_time` ratio 与几何平均语义。该 skill 只读结果，不替代 `pyperformance-result-compare` 对 baseline source、CPU affinity、worker env 和噪声可信度的判断。
- 在 `pyperformance-env-contract.md` 补充 worker venv site-packages 规则：人工创建 candidate 线 venv 后必须把 `pyvenv.cfg` 改成 `include-system-site-packages = true`（给出 `sed` 命令），测 CPython baseline 时保持或改回 `false` 并证明未误继承 CinderX。
- 新增 `tests/test_pyperformance_stat_report.py` 覆盖 console-only、Excel/PNG 生成和 benchmark filter 路径；README 补充 skill 表格条目、目录树和校验命令。

### Changed

- 将 `cinderx-env-validate` 与 pressure scenario 校验中的 pyperformance 版本引用统一更新到 1.13.0。
- 在 `using-cpython-optimize` router 专业 Skill 列表登记 `pyperformance-stat-report`。

## [1.0.1] - 2026-06-23

### Fixed

- 修正 `cpython-baseline` Docker 模板中的 CPython 编译参数，仅保留 `--enable-optimizations --with-lto`。
- 固定 Docker 模板工具链分工：CPython 使用 GCC 12.3.1，CinderX 构建继续使用 GCC 14。
- 将 Claude / Codex marketplace 插件 source 从本地路径切换为 GitHub 仓库子目录，避免本地安装无法升级。

## [1.0.0] - 2026-06-21

首个正式大版本。Agent / Workflow / Skill 三层架构与跨平台差异分析能力完整成形，证据驱动深钻流程沉淀为可复用资产。

### Added

- 新增 `cinderx-jit-review` skill，用于 CinderX JIT PR correctness-first review，覆盖 may-raise、helper fallback、deopt/FrameState、refcount、adaptive opcode、AArch64 codegen、RuntimeTests/test_cinderx/test_kunpeng 证据和 exact comment placement。
- 新增 `cinderx-parallel-pyperformance` skill，将 NUMA/L3-aware 并行 pyperformance 验证沉淀为 8/16 lane 自适应调度、blue-server-53 稳定 profile、CinderX manager/worker venv 注入、SSH 代理和稳定性复跑流程。
- 新增 `cinderx-evidence-table` skill，定义单用例深钻的证据表 E1–E9 三段式结构（What/Verdict/Gate）、每步必贴证据与闭环判据，并规定 ISA/指令集/微架构/硬件层的工具证据和 SPE/IBS 采样可用性探测原则（不绑定特定平台结论）。
- 新增 `cinderx-evidence-analyst` agent，作为证据表唯一负责人，跨层追因（HIR/LIR→机器码→ISA→微架构→硬件），在 E6 接手收口判读，并对穿刺数据可信度负责。
- 新增 `workflow-platform-differential-discovery-deepdive` workflow，按用例深钻（per-case）承载证据驱动流程：12 阶段分派表，E6 为证据采集与收口判读的分界线，与 matrix-first 粗筛 workflow 两层并行。

### Changed

- 为 matrix-first 粗筛 `workflow-platform-differential-discovery` 增加候选用例清单输出契约，作为深钻 workflow 阶段 0 的推荐选例输入（非强制）。
- 在 `using-cpython-optimize` router 登记 `cinderx-evidence-analyst`（Agent 路由）、`workflow-platform-differential-discovery-deepdive`（Workflow 路由）和 `cinderx-evidence-table`（专业 Skill），区分"系统找平台优化点（粗筛）"与"深钻单用例拿可信优化点"两个目标。
- `.claude-plugin/plugin.json` 版本从滞后的 0.8.9 补齐并随本次升到 1.0.0，与 `.codex-plugin/plugin.json`、`package.json` 对齐。

## [0.9.0] - 2026-06-16

### Added

- 新增 `cinderx-fast-validation` 技能，用 repo 外部 `ccache` compiler wrapper 加速 CinderX `setup_release`、release wheel 和 gate 重复验证，并提供可复用的 prelude 安装脚本。
- 新增 `cinderx-interpreter-case-analyze`，用于非 JIT / 解释执行用例分析：要求穿刺证据、分阶段平铺表、函数形状表、autojit gate 策略和不进入 gate 的阶段详细拆解。

### Changed

- 细分单 benchmark 用例分析路径：进入 CinderX JIT 时继续使用 `cinderx-hir-lir-analyze` 分析 HIR、deopt、LIR 和平台差异；未进入 gate 时转入解释执行分析。
- 强化 `validation-skill-router` 的运行时门禁：hook 输出会显式列出建议分派的 Agent 和 `agents/*.md` 路径；`pyperformance run`、worker 与 CinderX benchmark helper 在执行前必须先检查 `pyperformance-env-contract.md`、worker `pyvenv.cfg`、`include-system-site-packages`、CinderX `.pth`、`--inherit-environ` 和 worker 内 JIT 状态。
- 明确 pyperformance 正确运行路径：完成前置环境契约证据后，用 `CPYTHON_OPTIMIZE_HOOK_ACK=1` 重试同一条正式 suite / worker / helper 命令；禁止在未完成证据时提前 ACK 绕过 hook。

## [0.8.9] - 2026-06-08

### Changed

- 新增 `container-tooling-guidance.md` 共享引用，要求容器排障缺少 `gdb`、`ripgrep`、`strace`、`perf`、`binutils` 等工具时先探测网络和包管理器再补装，网络慢时及时反馈，而不是绕开关键取证路径。

## [0.8.8] - 2026-06-03

### Changed

- 强化 `workflow-feature-driven-optimization` 的 TDD 要求：改代码前检查是否需要补充或修改 RuntimeTests 功能用例和 test_cinderx/lib test 集成用例，并要求新增或修改的功能用例使用 Python `unittest` 框架。
- 修正 `cinderx-env-bootstrap` 的 CPython 3.14.3 模板：`/opt/python314` 不再构建共享 libpython，并增加 AArch64 RuntimeTests TLS offset 探测相关的环境校验与清理指引。
- 抽出 `pyperformance-env-contract.md` 共享引用，要求 suite、worker、JIT entry、HIR dump、result compare、regression workflow 和 pyperformance runner/analyst 在正式性能测试前核对 driver/worker 环境变量传递，并证明 worker 内 CinderX `.pth`、venv/site-packages 与 `cinderx.is_initialized()` 等 JIT 生效证据。
- 新增 `pyperformance-affinity-guidance.md` 共享引用，说明 `--affinity` 的 CPU 绑核含义、当前可用 CPU 检查、原始 affinity 到实际 affinity 的映射，以及 A/B 并行 CPU set 不足时的串行降级策略。
- 新增 `baseline-source-contract.md` 共享引用，防止 A/B 测试把远程可用容器里的当前源码直接当 baseline，要求单独证明 baseline commit/ref、source path、dirty 状态、`patchlevel.h`、`SOABI` 和唯一差异轴。
- 将容器内默认 `pip` 镜像源从阿里云切换为华为云 `https://repo.huaweicloud.com/repository/pypi/simple`。

## [0.8.7] - 2026-06-02

### Added

- 为 `validation-skill-router` 增加精准 PreToolUse route：在 CPython/CinderX 仓内识别 `pyperf` / `pyperformance`、`ci_pipeline/run_gate.py`、pyperformance worker 和 CinderX benchmark helper，自动注入对应测试/性能技能提醒。

### Fixed

- 修正 runtime hook 对远程脚本 `EXIT_STATUS=139` / `EXIT_CODE=139` 输出形态的漏匹配，确保 smoke、RuntimeTests 或 pyperformance worker 崩溃时触发 crash triage 提醒。
- 修正 `bash -lc 'grep ...'`、`ssh host 'grep ...'` 等包装后的文档检索误报；即使命令文本缺失，也会按 `path:line:text` grep 输出形态避免命中设计文档里的 `SIGSEGV` / `gdb bt full` 说明文字时触发 crash triage。

## [0.8.6] - 2026-06-02

### Added

- 在 README 新增推荐插件 / 技能 / 工具表，收录 superpowers、compound-engineering-plugin、andrej-karpathy-skills、codex-plugin-cc、codegraph、oh-my-openagent 和 mattpocock/skills。
- 为 `cinderx-env-validate` 增加本地 CPython 仓信任 checklist：remote、commit、dirty 状态、ref、`Include/patchlevel.h`、`sys.version`、`SOABI` 和 include 路径。
- 为 `cinderx-env-bootstrap` 增加网络不佳时的本地来源优先策略：本地 clone、独立 worktree、tarball/cache、已有容器优先，远端下载作为最后选项。
- 增强功能设计文档写法：支持总/分格式，在功能域/功能项前部用通俗语言和 mermaid/表格先讲清外部视角重点，后半部再展开实现细节。

### Changed

- 增强 Python 3.14.3 环境校验的变通能力：本地 CPython 当前 checkout 不符合版本时，先尝试安全切换到本地已有 3.14.3 ref/cache，而不是直接远端下载。
- 要求 `cinderx-environment-verifier` 在需要切换 ref、创建 worktree、fetch tag 或处理 dirty 仓时先反问用户，避免污染当前 checkout。

### Fixed

- 修正 openEuler Dockerfile 模板中的 GCC 14 C++ 包名：使用 `gcc-toolset-14-gcc-c++`，不再使用错误的 `gcc-toolset-14-c++*`。

## [0.8.5] - 2026-05-30

### Added

- 为 `pyperformance-worker-run` 增加规则级 checklist：driver/manager/worker、`bench_command()`、系统 site-packages、`--inherit-environ`、快速 L2 和非 debug 口径。
- 为 `pyperformance-suite-run` 增加正式性能测试命令形态和故障排查：CPU 绑核、warmup、输出路径、环境继承、关闭 HIR/JIT dump 与结果对比。

### Changed

- 统一测试用语：RuntimeTests 是功能测试，test_cinderx/lib test 是集成测试，pyperformance 是性能测试。
- 参考 GitCode issue/wiki 的测试命令形态，抽象为占位命令，不在规则中硬编码具体 pyperformance 用例名或结果文件名。

## [0.8.4] - 2026-05-28

### Added

- 新增 `PreToolUse` validation hook，在 CPython/CinderX 源码仓执行构建、RuntimeTests 功能测试、pyperformance 性能测试或本地安装命令前按命令内容路由技能。
- 增加 `CPYTHON_OPTIMIZE_HOOK_ACK=1` 确认前缀，避免技能确认后重复阻断同一类命令。

### Changed

- 宽匹配 `pip install [options] .` / `python -m pip install [options] .` / `uv pip install [options] .`，将本地 editable/source install 归入环境审计路径。
- 对全量 pyperformance、全量 RuntimeTests 功能测试和会改写环境的本地 pip install 使用 `permissionDecision: deny`，要求先完成环境审计、验证等级和用例范围确认。

## [0.8.3] - 2026-05-28

### Fixed

- 固定环境校验目标为 Python 3.14.3，移除 active skill / agent / workflow 中对更高具体 patchlevel 的引用。
- 将 API/ABI 防误用场景改写为“更高 patchlevel API”，避免 Agent 把错误 patchlevel 当成期望版本。
- 增加校验，禁止 active 文档重新出现错误的 Python patchlevel。

## [0.8.2] - 2026-05-28

### Changed

- 收窄运行中 hook 的匹配范围：只扫描真实工具响应里的 stdout/stderr/output，不再扫描整段 hook payload。

### Fixed

- 为 `git show/log/diff`、`rg`、`sed`、`cat` 等只读查看命令增加观察型命令短路，避免历史记录或文档中的 crash/timeout 触发运行态护栏。
- 新增 runtime hook 回归测试和 pressure scenario 34，确保误报被覆盖，同时保留真实 crash、网络 timeout 和长时间无输出提醒。

## [0.8.1] - 2026-05-27

### Added

- 新增统一 `反问 Gate`：当目标路线、实验轴、高成本动作、运行中异常或证据链缺口无法唯一确定时，要求先反问用户。
- 新增 pressure scenario 32，覆盖必要信息缺失时 `request_user_input` / `AskUserQuestion` 的平台映射和文本降级路径。
- 新增 `clarifying-question-templates.md`，统一结构化反问字段、平台映射、文本降级和 CPython/CinderX 高频模板。

### Changed

- 为 orchestrator、environment verifier、runner、benchmark analyst、crash triager、JIT analyst、platform analyst 补充各自必须反问的缺口。
- 为环境清理、bootstrap、远端操作、A/B slot、pyperformance suite/result、gdb/core、ISA/微架构和验证策略补充反问门禁。

## [0.8.0] - 2026-05-27

### Added

- 新增 `validation-strategy` 子技能，定义 L0-L4 验证阶梯、晋级规则、成本预算和缓存复用原则。
- 新增 `workflow-cross-platform-delta-triage`，用于双平台性能差距根因定位和收益扩散验证。
- 新增 `workflow-feature-driven-optimization`，用于已知特性驱动的代码优化、功能用例和性能验证。
- 新增 `workflow-platform-differential-discovery`，用于系统分析 ISA / 微架构差异并发现优化点。
- 新增 Agent 层：`cinderx-orchestrator`、`cinderx-environment-verifier`、baseline/candidate runner、benchmark analyst、crash triager、JIT analyst、platform analyst。
- 新增 `PostToolUse` 运行中信号 hook，在 Bash 输出出现 CinderX crash、timeout、网络卡顿或远程无输出时注入短提醒。
- 新增 pressure scenarios 19-31 覆盖准确、高效、workflow 分层、Agent 层、运行中 hook 路由和专业 skill 边界。

### Changed

- 将 `using-cpython-optimize` 压薄为 Orchestrator router，明确 Workflow -> Agent -> Skill 三层分发。
- 将 workflow 分为主 Workflow 和 Supporting Workflow，避免旧流程被误用为端到端优化入口。
- 大幅重切专业 skill：拆出 `cinderx-env-validate`、`cinderx-env-clean`、`cinderx-env-bootstrap`、`cinderx-remote-lab-ops`、`cinderx-ab-run-slot`、`pyperformance-worker-run`、`pyperformance-suite-run`、`cinderx-gdb-core-triage`、`cinderx-hir-dump`、`cinderx-isa-microarch-compare` 等 CPython/CinderX 专业动作。

### Removed

- 移除 `SessionStart` 全量注入 hook，避免启动、恢复和压缩后重复消耗 token。

## [0.7.1] - 2026-05-27

### Added

- 增加 CPython/CinderX 编译前 API/ABI 版本门禁，防止目标容器为 Python 3.14.3 时误用更高 patchlevel API。
- 增加远程命令输出契约：首次执行必须保留 stdout/stderr、exit status、日志路径或 tmux pane。
- 增加远程异常耗时处理：网络卡顿需使用 timeout、镜像/代理/DNS 诊断，并在需要决策时询问用户。
- 新增 pressure scenarios 15-18 覆盖上述失败模式。

### Changed

- 强化 `SIGSEGV` / `exit 139` crash triage：优先 `gdb bt full`、core dump、HIR/JIT 证据，禁止用反复加日志替代 native 取证。
- 将 `agents/` 角色文档统一重写为中文，并增加中文模板验证。

## [0.7.0] - 2026-05-26

### Changed

- 仓库改为 marketplace 结构：插件内容移至 `plugins/cpython-optimize-skill/`，根目录仅保留 marketplace 元数据。
- marketplace.json 的 source 路径改为 `./plugins/cpython-optimize-skill`。

### Fixed

- README 中 Codex 安装命令修正为 `codex plugin add <plugin>@<marketplace>` 格式。

## [0.6.1] - 2026-05-24

### Changed

- docker-compose 模板所有路径改为环境变量，消除相对路径依赖。
- 区分用户侧必填变量（CINDERX_ROOT、CPYTHON_ROOT、PYPERFORMANCE_ROOT）和 skill 侧可选变量。

## [0.6.0] - 2026-05-24

### Added

- docker-runtime 技能增加镜像构建规则和网络诊断指引。
- 新增 Codex CLI 插件市场支持（`.agents/plugins/marketplace.json`）。
- 结构验证测试覆盖 `.agents/plugins/` 目录。

### Changed

- 模板目录统一为单一 README（消除冗余的 project-readme.md）。
- 基础镜像升级为 openEuler 24.03 LTS SP3。
- README 安装说明区分 Claude Code 和 Codex CLI。

## [0.5.2] - 2026-05-22

### Changed

- 性能测试基线版本统一为 Python 3.14.3。
- 更新 `cpython-baseline` Dockerfile 中 `PYTHON_VERSION`。
- 同步详细设计模板（用户修订）。

## [0.5.1] - 2026-05-14

### Added

- 新增 `.claude-plugin/marketplace.json` 支持插件市场安装。
- README 添加 emoji 分节。

### Changed

- 精简 README：移除性能口径、Docker 双线等子技能内容，改为入口技能承载。

### Fixed

- 修正 Claude Code 技能调用说明（无 `/skill` 斜杠命令）。

## [0.5.0] - 2026-05-14

### Added

- 新增 `skills/design-documentation/` 子技能。
- 增加架构设计、系统设计、功能设计、详细设计四类标准模板。
- 增加自顶向下设计流程（架构 -> 系统可选 -> 功能 -> 详细）。
- 增加文档类型选择决策流程图、编写原则与格式约定。
- 设计文档统一输出到 `docs/design/`。

### Changed

- 更新引导技能 `using-cpython-optimize`，新增 `design-documentation` 条目。

## [0.4.0] - 2026-05-13

### Added

- 新增 `.claude-plugin/plugin.json`、`.codex-plugin/plugin.json`、`package.json` 插件注册。
- 新增 `hooks/` SessionStart 自动注入引导技能。
- 新增 `skills/using-cpython-optimize/` 引导技能（含决策流程图和 FAQ）。
- 将 6 个工作流迁移为自包含子技能：remote-environment、cpython-build、docker-runtime、pyperformance-test、cinderx-analysis、experiment-documentation。
- 每个子技能自包含 `SKILL.md` 和专属 references/scripts/templates。

### Changed

- 重构为复合技能仓库。
- playbook 内容按主题吸收到对应子技能。
- `docs/` 重新定位为仓库级文档（plans、开发文档）。

### Removed

- 移除旧目录：`docs/workflows/`、`docs/playbooks/`、`references/`、`scripts/`。

## [0.3.0] - 2026-04-13

### Added

- 新增性能口径定义：CPython 解释执行、CPython JIT、CinderX 解释执行、CinderX JIT。
- 明确 `baseline` 的两种含义：口径基线和提交基线。

### Changed

- 明确远程环境工作流：先确认 SSH 可登录，再使用 `rsync` 同步代码仓，再进入 Docker 容器隔离。
- 强化远程宿主机目录隔离约束，避免 bind mount 覆盖已有目录。
- 明确容器内 `pip` 默认应切到国内镜像源，优先华为云。
- 明确 Arm vs x86 属于跨平台对比，必须参数和口径一致。

### Fixed

- 修正 HIR 分析顺序：先确认进入 CinderX JIT，再做热点归因，最终输出必须包含具体 HIR 片段、问题说明和修改方案。
- 明确 dump HIR 时应优先复用真实测试命令，只增减 debug 环境变量。

## [0.2.0] - 2026-04-10

### Added

- 重构为“核心层 + 四平台薄包装”。
- 补齐主工作流：SSH / tmux、构建与强制覆盖安装、`pyperformance` 测试、Docker 运行时隔离、文档规范、用例分析。
- 固化 Docker 双线：`cpython-baseline` 和 `cinderx-test`。
- 收录真实环境命令模板。
- 迁入已验证的 `cinderx-test` 脚本。
- 补齐 FAQ、入口决策表、静态/动态 pressure test。

## [0.1.0] - 2026-04-09

### Added

- 初始化技能仓库脚手架。
- 建立 CPython/CinderX 联合优化技能的基础目录结构。
- 确立以 CinderX 优先的个人工作流定位。
