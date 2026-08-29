# Pressure Scenarios

这些场景用于压测 skill 在真实对话中的引导能力。

## 场景 1：用户要在 Kunpeng 上做 CinderX 功能验证

用户话术示例：

> 我想在 Kunpeng 上验证 `regex_compile` 是否真的进了 CinderX JIT，先别看性能。

期望行为：
- 引导加载 `pyperformance-worker-run`、`cinderx-jit-entry-check` 和 `cinderx-hir-dump`
- 优先推荐单个 `run_benchmark.py`
- 明确先开 HIR dump
- 提醒检查 worker 是否真的进入 JIT

## 场景 2：用户要做正式性能对照

用户话术示例：

> 我要比较 stock CPython JIT 和 CinderX 在 Docker 里的 pyperformance 数据。

期望行为：
- 先由 `cinderx-environment-verifier` 调用 `cinderx-env-validate`
- 明确这是 Docker 双线里的 `cpython-baseline`
- 不直接把 `cinderx-test` 调试线当正式对照

## 场景 3：用户说 pyperformance run 异常，但单 benchmark 正常

用户话术示例：

> `python -m pyperformance run` 不对，但我直接跑 `run_benchmark.py` 是正常的。

期望行为：
- 联想到 driver / manager / worker / bench_command 子进程模型
- 引导加载 `pyperformance-worker-run`
- crash 线索明显时加载 `cinderx-gdb-core-triage` 并查看 crash triage reference

## 场景 4：用户要复现 native crash

用户话术示例：

> `bm_logging` 在真实环境 `SIGSEGV`，我想先最小复现，再抓 HIR 和 gdb。

期望行为：
- 优先建议调试线 `cinderx-test`
- 强调单 benchmark worker 入口
- 同时给出 JIT log / HIR / gdb 的取证顺序

## 场景 5：用户要整理实验文档

用户话术示例：

> 这次修复要沉淀成文档，后面给别的 Agent 复用。

期望行为：
- 引导加载 `cinderx-optimization-report` 技能
- 强调背景、复现命令、证据链、根因、修复、回归结果

## 场景 6：用户要分析性能退化

用户话术示例：

> `scimark` 退化了，帮我对比 HIR 和性能，找根因。

期望行为：
- 引导加载 `cinderx-jit-analyst`，使用 `cinderx-jit-entry-check` 和 `cinderx-hir-lir-analyze`
- 区分 JIT 与非 JIT 路线
- 强调先对齐命令口径、解释器和依赖，再比较 HIR / LIR / 机器码

## 场景 7：用户在 Docker 里连续调试

用户话术示例：

> 帮我进容器里调试一下这个 benchmark，先别一条条 `docker exec`。

期望行为：
- 联想到 Docker 调试应优先保留一个长连接交互终端
- 不把反复 `docker exec` 当成主路径
- 引导加载 `cinderx-remote-lab-ops` 和 `cinderx-env-bootstrap`

## 场景 8：用户要做 Docker 正式对照，但先提到了 crash

用户话术示例：

> 这个用例之前在容器里崩过，现在我想正式对比 stock CPython JIT 和 CinderX。

期望行为：
- 先识别"当前目标是正式对照"
- 把路线切到 `cpython-baseline`
- 必要时提醒先在 `cinderx-test` 完成功能确认，再回到基线线

## 场景 9：用户刚 SSH 上远程环境

用户话术示例：

> 我已经 SSH 上 Kunpeng 了，接下来开始编译和测试吧。

期望行为：
- 不默认让用户直接在裸机上开始主工作流
- 先提醒宿主机目录隔离
- 再引导进入 Docker 容器隔离

## 场景 10：用户要创建宿主机工作目录

用户话术示例：

> 我准备在远端建个目录把源码同步上去，然后挂进容器。

期望行为：
- 强调每个 Agent 使用独立宿主机目录
- 避免复用已有目录
- 提醒 bind mount 前先确认挂载源目录边界

## 场景 11：用户要在远端同步代码仓

用户话术示例：

> 我已经在本地改好了，准备把代码同步到 Kunpeng 上。

期望行为：
- 先确认 SSH 能登录
- 优先建议 `rsync`
- 明确同步目标应是当前 Agent 自己的宿主机目录
- 如果远端没装 `rsync`，先提醒安装

## 场景 12：用户要 dump HIR 分析性能问题

用户话术示例：

> 我想抓一下 HIR 看看这个 benchmark 为什么退化。

期望行为：
- 优先复用真实测试命令
- 只增减 debug 环境变量
- 不鼓励先跑一条简化命令再看另一份 HIR

## 场景 13：用户要比较不同性能口径

用户话术示例：

> 我现在要比较 CPython JIT、CinderX 解释执行和 CinderX JIT。

期望行为：
- 先明确四种性能口径
- 明确哪些变量属于启用变量，哪些属于调试变量
- 避免把 dump 变量混进正式性能口径

## 场景 14：用户要做 HIR 优化分析

用户话术示例：

> 帮我看下这个函数的 HIR，有没有优化点。

期望行为：
- 先确认真的进入了 CinderX JIT
- 先做热点归因
- 输出里必须贴具体 HIR 片段
- 明确指出片段的问题
- 再给出修改方案

## 场景 15：编译时误用目标环境没有的 Python API

用户话术示例：

> 容器里是 Python 3.14.3，但编译失败时 Agent 选了更高 patchlevel 才有的 API。

期望行为：
- 先以目标解释器和容器内头文件为版本事实源
- 记录 `sys.version`、`SOABI`、`patchlevel.h` 或等价证据
- 不引用目标环境没有的 API 来修 3.14.3 环境的编译问题
- API/ABI 不一致时先停下来修环境或改兼容实现

## 场景 16：测试中出现段错误

用户话术示例：

> 单测跑到一半 SIGSEGV 了，之前 Agent 一直在加日志重跑。

期望行为：
- 识别 `SIGSEGV` / `exit 139` / `core dumped` 后切入 crash triage
- 先保留真实复现命令和退出信号
- 优先用 `gdb` / core dump 抓 `bt full`，JIT 相关再叠加 HIR dump / jit.log
- 不把反复加日志当作 native crash 的主路径

## 场景 17：远程命令没有可靠输出

用户话术示例：

> SSH 到远端跑命令经常没有输出，Agent 发现没输出后又加日志重复跑同一条。

期望行为：
- 第一次远程执行就设计 stdout/stderr、exit status 和日志路径
- 长任务使用 `tmux` / `tee` / `tail` 复用已有输出
- 无输出时先查进程、日志、退出码和 tmux pane
- 不为了补输出盲目重复执行同一条有副作用的命令

## 场景 18：远程耗时操作异常卡住

用户话术示例：

> 远端 pip / git / 网络下载慢得不正常，Agent 就一直等。

期望行为：
- 区分正常长编译和异常网络卡顿
- 网络相关命令要有超时、镜像源或缓存策略
- 长时间无新增输出时先诊断 DNS/代理/连接/进度
- 需要继续等待、换镜像、跳过或让用户处理时及时询问用户

## 场景 19：根据双平台性能差距定位优化点

用户话术示例：

> Kunpeng 和 x86 上同一个 benchmark 差距很大，帮我找根因并试一个优化点。

期望行为：
- 引导加载 `workflow-cross-platform-delta-triage` 和 `validation-strategy`
- 先排除环境漂移，再讨论 ISA / 微架构 / JIT lowering 差异
- 不默认跑全量 pyperformance，先用单 benchmark 和相关小集合验证
- 优化后说明收益范围、无收益范围和下一阶验证条件

## 场景 20：根据已知特性做性能优化

用户话术示例：

> 我知道这个特性会减少某条慢路径，帮我改代码并补用例验证收益。

期望行为：
- 引导加载 `workflow-feature-driven-optimization` 和 `validation-strategy`
- 先写清特性、预期影响路径和受影响用例
- 按 TDD 要求检查是否需要补充或修改 RuntimeTests 功能用例和 test_cinderx/lib test 集成用例；不需要时写明理由
- 新增或修改的功能用例必须使用 Python `unittest` 框架，不能只写 pytest 风格或脚本式断言
- 先补功能/行为用例和必要集成用例，再做目标性能验证
- 只有通过低阶验证后，才晋级到相关子集或全量验证

## 场景 21：系统性寻找平台差异优化点

用户话术示例：

> 帮我系统分析代码和平台 ISA / 微架构差异，找可能优化点，再看哪些用例收益。

期望行为：
- 引导加载 `workflow-platform-differential-discovery` 和 `validation-strategy`
- 先建立代码路径、平台差异点和 benchmark 覆盖矩阵
- 优先低成本扫描，不直接进入三小时全量性能实验
- 每个候选点绑定预期收益用例，再分层验证收益扩散范围

## 场景 22：顶层任务不应误入子流程

用户话术示例：

> 这次是端到端找优化收益，不只是看 HIR 或跑一次正式对照。

期望行为：
- 先在主 Workflow 中选择用户目标入口
- 把 `workflow-jit-optimization-analysis` 识别为 Supporting Workflow，只在需要单用例 JIT 证据时调用
- 把 `workflow-pyperformance-regression` 识别为 Supporting Workflow，只在 L3/L4 正式性能验证时调用
- 不用 supporting workflow 取代主 Workflow

## 场景 23：长任务中运行时信号触发 skill 提醒

用户话术示例：

> 一个定位任务跑了很久，中间还经历过上下文压缩。后来 Bash 输出里突然出现 Segmentation fault，但自然语言已经不会重新触发技能了。

期望行为：
- `PostToolUse` runtime hook 捕获 `SIGSEGV` / `exit 139` / `EXIT_STATUS=139` / `core dump` 等工具输出信号
- hook 只注入短 `additionalContext` 提醒，不重新塞入完整 `using-cpython-optimize`
- Agent 根据提醒加载 `workflow-cinderx-crash-triage`，回到 `gdb bt full`、core dump、HIR dump 证据链
- 遇到 `timeout`、网络卡顿或远程无输出时提醒加载 `cinderx-remote-lab-ops` 并及时询问用户

## 场景 24：crash 取证应进入 CinderX 专业 skill

用户话术示例：

> 单测 SIGSEGV 了，不要再只加日志，我需要可定位的 native 证据。

期望行为：
- 加载 `cinderx-gdb-core-triage`，而不是把 crash 逻辑塞在 pyperformance 或 JIT 分析里
- 保留同一条真实命令、退出信号、core dump 和 `gdb bt full`
- JIT 相关时再叠加 HIR dump / jit.log
- `cinderx-remote-lab-ops` 负责命令输出、日志路径和 exit status

## 场景 25：远程命令输出契约应独立复用

用户话术示例：

> 远端命令没输出，但这个任务不是单纯 SSH 配置问题。

期望行为：
- 加载 `cinderx-remote-lab-ops`，不要使用泛化命令观测 skill
- 首次执行就定义 stdout/stderr、日志路径、exit status、tmux pane
- 对 timeout、异常耗时、网络卡顿和无输出使用同一套诊断规则
- 输出契约必须绑定到 CPython/CinderX lab 的 host、workspace、container line 和 tmux pane

## 场景 26：RuntimeTests 功能测试和集成测试需要独立测试原子 skill

用户话术示例：

> 这次先跑相关 RuntimeTests 功能测试和 test_cinderx/lib test 集成测试，不需要 pyperformance 性能测试。

期望行为：
- 加载 `cpython-runtime-test-run` 处理单元测试、RuntimeTests 功能测试、test_cinderx/lib test 集成测试和聚合测试
- 根据 `validation-strategy` 选择 L1 / L3 / L4，不默认跑近千条全量 Runtime
- 失败重跑必须复用原命令和产物路径
- 不把功能测试/集成测试塞进 pyperformance worker 或 suite skill

## 场景 27：正式性能结果解读应独立于跑分命令

用户话术示例：

> 我已经有 baseline/run.json 和 candidate/run.json，帮我判断收益是否可信。

期望行为：
- 加载 `pyperformance-result-compare`，而不是重新进入 pyperformance 跑分
- 明确 baseline、candidate、speedup.json、方差、噪声和异常用例
- 输出收益范围、无收益范围、未验证范围
- 需要补跑时再加载 `pyperformance-worker-run` 或 `pyperformance-suite-run`

## 场景 28：平台差异分析应独立于 JIT 细节

用户话术示例：

> 帮我系统看 Kunpeng 和 x86 的 ISA / 微架构差异，先别陷进某个 HIR pass。

期望行为：
- 加载 `cinderx-isa-microarch-compare`
- 先建立 ISA、微架构、perf、cache、分支预测、SIMD、lowering 和 benchmark 覆盖矩阵
- 只有定位到 JIT lowering 或 HIR/LIR 形态差异时，再加载 `cinderx-hir-lir-analyze`
- 每个候选优化点绑定预期收益用例和最小验证命令

## 场景 29：环境 verifier 三态决策

用户话术示例：

> 这个 Kunpeng 环境之前用过，但不知道还能不能复用。

期望行为：
- `cinderx-environment-verifier` 先调用 `cinderx-env-validate`
- 可复用返回 `reusable`
- 新环境返回 `needs_bootstrap` 并调用 `cinderx-env-bootstrap`
- 被破坏环境返回 `needs_clean_bootstrap`，先 `cinderx-env-clean` 再 bootstrap

## 场景 30：A/B 并行跑分需要 CinderX slot 分配

用户话术示例：

> baseline 和 candidate 可以并行跑，只要别抢同一批 CPU。

期望行为：
- orchestrator 调用 `cinderx-ab-run-slot`
- baseline 交给 `pyperformance-baseline-runner`
- candidate 交给 `pyperformance-candidate-runner`
- CPU affinity / 绑核、结果目录、tmux pane、容器线都不冲突

## 场景 31：技能必须是 CPython/CinderX 专业动作

用户话术示例：

> 这个仓不是通用性能优化工具箱，别给我泛化 skill。

期望行为：
- 使用 `cinderx-env-validate`、`pyperformance-worker-run`、`cinderx-gdb-core-triage` 等专业 skill
- 不再出现 `command-observability`、`test-execution`、`native-crash-debugging` 这类泛化入口
- skill 触发词必须包含 CPython/CinderX、pyperformance、HIR/LIR、SOABI、Kunpeng/x86 等领域对象

## 场景 32：必要信息缺失时必须反问

用户话术示例：

> 远端环境好像坏了，直接帮我清一下，然后跑正式性能吧。

期望行为：
- 先识别这是清理环境和 L4 性能验证两个高成本/可能破坏性动作
- 环境句柄、要清理的 workspace、baseline/candidate、benchmark 范围不明确时触发反问
- Codex 可用时使用 `request_user_input`，Claude Code 可用时使用 `AskUserQuestion`
- 工具不可用时退化为文本选择题，不直接清理或启动全量 pyperformance

## 场景 33：反问必须复用结构化模板

用户话术示例：

> 我不确定要先跑哪个平台，也不确定是否要全量 pyperformance，你自己看着办。

期望行为：
- 读取 `clarifying-question-templates.md`
- 先问最高风险缺口，例如 `workflow_route` 或 `validation_level`
- 每个问题有稳定 `question_id`、短 `header`、2-3 个互斥选项和推荐项
- Codex / Claude Code / 文本降级的字段口径一致

## 场景 34：查看历史记录不应触发运行态 crash 护栏

用户话术示例：

> 先用 `git show` 看一下上个提交改了什么。

期望行为：
- `git show`、`git log -p`、`git diff` 等历史/差异查看即使输出旧文档里的 `SIGSEGV`、`exit 139`、`core dump`，也不触发 crash triage 提醒
- `rg`、`sed`、`cat` 等只读文本查看命令输出 hook 文档或压力场景里的触发词时，也不触发运行态护栏
- `bash -lc 'grep ...'`、`ssh host 'grep ...'` 等包装后的文档检索命中 `SIGSEGV` / `gdb bt full` 说明文字时，也不触发 crash triage 提醒
- 即使 hook 没拿到原始命令，只要触发词都出现在 `path:line:text` 形式的源码/文档检索命中行里，也不触发 crash triage 提醒
- 真正执行 RuntimeTests 功能测试、pyperformance 性能测试、pip/git 下载或远端命令时，stdout/stderr 出现 crash、timeout 或长时间无输出仍然触发对应提醒

## 场景 35：验证命令执行前应按命令内容触发技能

用户话术示例：

> 我没显式调用 skill，刚改完 CinderX 代码，准备跑 `python -m pyperformance run` 或 `pip install --no-build-isolation -e .`。

期望行为：
- `PreToolUse` 的 `validation-skill-router` 挂在 `Bash` 上，但脚本内部按命令内容做低成本过滤
- 只在 CPython/CinderX 源码仓中匹配构建、Runtime、pyperformance、pyperf、CinderX run_gate、pyperformance worker/helper 和本地 `pip install [options] .`
- 定向 Runtime、test_cinderx/lib test 集成测试、subset pyperformance、pyperf compare 和 worker/helper 注入 `using-cpython-optimize`、`validation-strategy` 及对应原子 skill 的 `additionalContext`，本次命令继续执行
- 全量 pyperformance、全量 RuntimeTests 功能测试或会改写环境的本地 pip install 先 `permissionDecision: deny`，要求完成环境审计、验证等级和范围确认
- 已确认检查后可用 `CPYTHON_OPTIMIZE_HOOK_ACK=1` 前缀重试，避免重复阻断

## 场景 36：pyperformance 正式测试前必须提醒三类测试与 worker 口径

用户话术示例：

> 这次要做非 debug 的正式性能验证，先别抓 HIR，只要跑目标集合并给出能提交的自验证结果。

期望行为：
- 先把自验证拆成三类：RuntimeTests 功能测试、test_cinderx/lib test 集成测试、pyperformance 性能测试
- RuntimeTests 功能测试使用 `ci_pipeline/run_gate.py --suite runtime` 形态，test_cinderx/lib test 集成测试使用 `CINDERX_LOCAL_RUN_LIBTEST=1` 与 `--suite cinderx_local` 形态
- pyperformance 前确认 driver/manager/worker/`bench_command()` 子进程链，不能用交互式 import 代替 worker 结果
- CinderX worker 要确认 `include-system-site-packages = true` 或等价的系统 site-packages 继承；Python baseline 要确认不会误继承 CinderX 安装
- 正式性能命令必须包含 CPU 绑核、warmup、输出路径和 `--inherit-environ`，至少继承代理、`LD_LIBRARY_PATH`、插件/JIT 关键变量
- 非 debug 正式运行必须关闭 HIR/JIT dump、`--debug-single-value` 和临时诊断变量；快速 L2 可用 bm/test-benchmark 脚本，但不能把它当最终正式数据
- 文档规则不硬编码具体 pyperformance 用例名或输出文件名，只使用 `<benchmark-selector>`、`<result.json>` 这类占位

## 场景 37：本地 CPython 仓不是 3.14.3 时应尝试安全切换

用户话术示例：

> 本地 `/opt/Codex/cpython` 当前是 3.16.0a0，不符合 Python 3.14.3。外部网络不稳定，别急着远端下载源码，先看本地能不能切到 3.14.3。

期望行为：
- `cinderx-env-validate` 不把“当前 checkout 是 3.16.0a0”直接等价为“本地 CPython 不可信”
- 先检查本地仓的 `git remote -v`、`git status --short`、`git show -s --format=%H`、`git tag/branch/ref` 和 `Include/patchlevel.h`
- 如果本地存在 3.14.3 ref/tag/branch/cache，优先用 `git worktree` 独立 worktree 或专用目录切换，不污染用户当前 checkout
- 切换后用目标解释器、`Include/patchlevel.h`、`sys.version`、`SOABI` 和 include 路径重新校验，校验通过才可作为 baseline 事实源
- 如果本地仓有未提交改动、ref 不存在、dirty 状态无法隔离或需要联网 fetch，必须询问用户，而不是自动 `git checkout`、自动下载或自动清理
- 外部网络不佳时优先复用本地 clone、worktree、tarball/cache 和已有容器；远端下载只作为最后选项

## 场景 38：功能设计文档应使用总-分结构先讲清外部视角重点

用户话术示例：

> 写功能设计时别一上来就堆实现细节。每个功能域和功能项前面先用通俗语言讲清它解决什么、谁关心、边界和价值，再把细节放后半部展开。

期望行为：
- 加载 `design-documentation`
- 功能设计文档采用总-分结构：每个功能域、功能项先总述，再分节展开实现、接口、DFX 和影响点
- 功能域/功能项前部用通俗易懂、深入浅出的语言突出重点
- 前部整理外部视角最关心的点：目标用户/系统、核心能力、输入输出、边界、收益、风险、验收口径
- 前部可以辅以 mermaid 图形或表格，帮助读者快速理解流程、关系、状态或差异
- 后半部再展开实现思路、实现设计、接口定义、DFX、需求分配等细节

## 场景 39：AArch64 RuntimeTests TLS offset 失败应识别为 Python 构建形态问题

用户话术示例：

> RuntimeTests 里 `DetectsThreadStateOffset` 失败，`_Python_LIBRARY_RELEASE=/opt/python314/lib/libpython3.14.so`，`_PyThreadState_GetCurrent@plt`，真实函数体是 TLSDESC，最后 `tstate_offset = -1`。

期望行为：
- 不先归因到 AutoJIT 新代码或构建命令错误
- 加载 `cinderx-env-validate` 检查 `/opt/python314` 的 `Py_ENABLE_SHARED`、`CONFIG_ARGS`、`LIBRARY`、`LDLIBRARY`、CMake `_Python_LIBRARY_RELEASE`
- 判断共享/PIC Python 导致 AArch64 `_PyThreadState_GetCurrent` 变成 PLT/TLSDESC 形态，不满足 CinderX TLS offset 探测假设
- 返回 `needs_clean_bootstrap` 或 `needs_bootstrap`，要求用非共享 libpython 的 CPython 3.14.3 重建 RuntimeTests 环境
- `cinderx-env-bootstrap` 的 `/opt/python314` 模板不能构建共享 libpython，并要自检 `Py_ENABLE_SHARED` 与 `libpython3.14*.so*`

## 场景 40：pyperformance 性能测试前必须核对环境变量契约

用户话术示例：

> 我调用 `pyperformance-suite-run` 跑性能，后来才发现 `PYTHONPATH` 和 `PYTHONJITAUTO` 只传给了 driver，worker 没继承，导致结果不可信。

期望行为：
- `pyperformance-suite-run`、`pyperformance-worker-run`、`pyperformance-result-compare` 和 `workflow-pyperformance-regression` 都引用 `pyperformance-env-contract.md`
- 正式运行前列出 driver env、`--inherit-environ`、worker env、helper 变量和 baseline/candidate 唯一差异轴
- 判断是否启用 CinderX JIT 时必须看真实 worker：确认 CinderX `.pth` 安装在 worker 可见的 `site-packages`，记录 `pyvenv.cfg` 的 `include-system-site-packages` 或等价 `PYTHONPATH` 传递
- 检查代理、`LD_LIBRARY_PATH`、`PYTHONPATH`、`PYPERFORMANCE_HOOK_ROOT` / `PYPERF_HOOK_ROOT`、`PYTHONJIT*`、`CINDERX_*`、`DIAG` 等变量是否传到真实 worker
- worker 内必须能证明 `import cinderx` / `_cinderx`、`cinderx.__file__`、`cinderx.get_import_error()` 和 `cinderx.is_initialized()` 符合 CinderX JIT 口径；只看 driver import 或交互式 import 不算数
- 如果环境变量只到 driver、worker 缺失或 baseline/candidate 除目标变量外不一致，不能输出可信 pyperformance 收益结论
- 正式非 debug 结果不得混入 HIR/JIT dump、`DIAG=1`、`JIT_LOG_FILE` 或 `--debug-single-value`

## 场景 41：真实 pyperformance 命令里的 --affinity 需要按当前 CPU 资源变通

用户话术示例：

> 我给了真实测试命令 `python -m pyperformance run --affinity=262 ...`，但测试环境没有这么多 CPU 核，Agent 不要死抠必须完全一致。

期望行为：
- `pyperformance-suite-run`、`cinderx-ab-run-slot`、baseline/candidate runner 和 regression workflow 都引用 `pyperformance-affinity-guidance.md`
- 说明 `--affinity` 是 pyperf/pyperformance 的 CPU 绑核参数，用于限制 worker 进程运行在哪些 CPU 上，降低调度噪声，不是 benchmark 选择器或必须逐字照抄的语义参数
- 先用 `nproc`、`lscpu`、`taskset -pc $$` 或容器 cpuset 信息确认当前可用 CPU，再把用户命令中的 affinity 映射到当前可用 CPU
- 目标是保持可比性：baseline/candidate 使用相同数量、同类位置、互不冲突的 CPU set；当前机器没有原命令对应核号时，应重分配可用 CPU 并记录映射理由
- 不能因为无法使用原始高核号就停止；只有可用 CPU 不足以保证 A/B 隔离或正式口径时，才询问用户串行执行、降低验证等级或更换环境

## 场景 42：远程容器可用不等于源码可作为 baseline

用户话术示例：

> Agent 检查远程环境容器可用后，直接把环境上的源码当成 baseline 跑 A/B，这不对。

期望行为：
- `cinderx-env-validate`、`cinderx-ab-run-slot`、`pyperformance-baseline-runner`、`pyperformance-result-compare` 和 regression workflow 都引用 `baseline-source-contract.md`
- 明确区分“执行环境可用”和“baseline 源码可信”：Docker/SSH/tmux 可用只能返回环境可执行，不能自动把远程 workspace 源码当 baseline fact source
- baseline 必须有用户指定或技能可验证的事实源：baseline commit/ref、CPython 3.14.3 release source、`cpython-baseline` 容器 bind mount、干净 git worktree、`patchlevel.h`、`git status --short`、`git show -s --format=%H`
- 远程源码若 dirty、ref 不明、patchlevel/SOABI 不符、容器 bind mount 指向不明或混入 candidate editable install，不能作为 baseline；应返回 `baseline_source_untrusted` 并询问用户指定 baseline、创建干净 worktree 或重建 baseline 环境
- 只有返回 `baseline_source_verified` 后，baseline runner 才能进入正式 pyperformance A/B
- A/B 结果报告必须写明口径 baseline、提交 baseline、baseline source path、commit/ref、dirty 状态和是否与 candidate 只差目标变量

## 场景 43：容器排障缺工具时应先评估补装而不是绕开

用户话术示例：

> 容器里没有 `gdb` 或 `rg`，Agent 直接改用日志和 grep 绕过去了，效率很低。

期望行为：
- `cinderx-remote-lab-ops`、`cinderx-env-bootstrap` 和 `cinderx-gdb-core-triage` 都引用 `container-tooling-guidance.md`
- 缺少 `gdb`、`ripgrep` / `rg`、`strace`、`perf`、`binutils` 等关键排障工具时，先判断是否能补装；不要直接绕开 native crash、文本检索或 perf 取证路径
- 补装前先探测网络和包管理器状态：`command -v dnf/yum/apt`、镜像源、DNS、代理、cache、`timeout` 包裹的 metadata/install dry run
- 网络慢或 metadata 长时间无输出时，及时反馈并询问继续等待、切镜像、复用 cache、离线包或中止，不要沉默等待
- 若确实无法补装，才记录原因并使用降级方案；报告必须写明缺失工具、探测命令、安装命令、耗时/exit status 和替代方案

## 场景 44：非 JIT / 解释执行用例需要独立分析格式

用户话术示例：

> 这个 pyperformance 用例没有进入 CinderX JIT gate，但 CinderX JIT 模式比 CPython JIT baseline 慢，帮我分析差距和优化空间。

期望行为：
- `workflow-jit-optimization-analysis` 先用 `cinderx-jit-entry-check` 判定是否进入 JIT；进入 JIT 才继续 `cinderx-hir-lir-analyze` 的 HIR、deopt、LIR 和平台差异分析
- 未进入 JIT 或主要解释执行时，切到 `cinderx-interpreter-case-analyze`，不能硬套 HIR/LIR 结论
- 解释执行分析必须先拿穿刺证据，再输出分阶段平铺表，对比 CPython JIT baseline、CinderX JIT 优化前、CinderX JIT 优化后、已优化量和剩余 gap
- 分阶段平铺表之后必须给函数形状表：基于 autojit 分类模型列出全量函数形状、热度、字节码形态、动态特性、gate 策略和不进入 gate 的原因
- 只要存在不进入 gate 的函数，就做阶段详细拆解，说明发现、分类、gate、拒绝、解释执行 fallback、运行时开销各阶段的证据和下一步优化点

## 场景 45：hook 提醒必须显式注入 Agent 文档路径

用户话术示例：

> 技能里写了 Agent，但实际运行时没看到 Agent 触发。

期望行为：
- `using-cpython-optimize` 明确说明 Agent 文档不是原生 Skill 自动触发单元，主 Agent 必须按 `agents/<agent>.md` 显式读取
- `validation-skill-router` 的 additionalContext / deny reason 不只写 skill，还要写建议分派的 Agent 和 `Agent docs`
- pyperformance 正式运行提示 baseline/candidate runner；pyperformance worker 提示 `cinderx-environment-verifier` 和 `cinderx-jit-analyst`；结果比较提示 `pyperformance-benchmark-analyst`；环境改写提示 `cinderx-environment-verifier`
- Agent 未自动出现时，Agent 应按 hook 提供的 `agents/*.md` 路径读取角色文档，而不是假设系统会自动触发

## 场景 46：运行 pyperformance 前必须触发 worker venv / pyvenv.cfg 检查

用户话术示例：

> Agent 上来直接跑 `python -m pyperformance run -b ...`，没有检查 worker venv 的 `pyvenv.cfg` 和 CinderX `.pth`。

期望行为：
- `validation-skill-router` 对 `python -m pyperformance run` 的 full/subset、pyperformance `run_benchmark.py --worker` 和 CinderX benchmark helper 先 deny，不让它们在缺证据时直接执行
- deny reason 必须提醒读取 `pyperformance-env-contract.md`，并检查 worker venv、`pyvenv.cfg`、`include-system-site-packages`、CinderX `.pth`、`--inherit-environ`、worker 内 `cinderx.is_initialized()` / `cinderx.get_import_error()`
- hook 输出必须建议 `cinderx-environment-verifier`，pyperformance worker/helper 还要建议 `cinderx-jit-analyst`
- 完成前置证据后，用 `CPYTHON_OPTIMIZE_HOOK_ACK=1` 重试原命令
- 只读查看 `pyvenv.cfg` 可以不阻断；写入、替换或打开写模式仍必须先走环境校验

## 场景 47：纯理论咨询落到具体指令时必须查 isa-reference MCP

用户话术示例：

> 讲讲把解释器热点里的 compare+branch 换成条件选择值不值得，原理和两个平台的落地方式。

注意：话术**不含**页码/出处/规格等查证要求——这是本场景的关键，测试的是技能材料
自身的兜底约束，而非任务要求的驱动。

期望行为：
- 理论部分可只依据 `compiler-optimization-theory` 的 references（控制依赖→数据依赖、
  误预测代价、块合并收益），但**一旦答案出现具体助记符/编码/feature 断言**
  （CSEL/CMOVcc/CPUID/FEAT 等），必须伴随 `mcp__isa-reference__*` 工具调用
- **查证内容导向**（核心判据）：查证主体是语义与用法——方案对指令行为的每条
  语义假设必须引用该指令 `operation_pseudocode` 的对应行比对；用法断言（写法、
  操作数约束、编码陷阱）必须对应 `asm_templates`/`operand_docs` 条目。
  **只回答"是 base 类/无 feature 依赖"不构成查证**——分类只用于同名消歧、
  feature/`filter_by_environment` 只在环境部署判定时使用
- **候选检索跨 category/feature 不设限**：优化替换经常跨执行域（base 需求用
  SIMD 满足），更优写法发现按语义检索候选后必须逐个比对伪代码确认语义一致
- 落地形态应先查 `optimization-intent-map.md` 的跨平台族对照，机器候选仅作补充
- 执行方式：spawn 子代理读技能材料后作答，核对其自报 MCP 调用与答案中的
  伪代码引用/页码是否与 isa.db 一致（防虚构）；材料剥离钩子后作对照组

## 场景 48：读教材提炼文档后做指令族选型必须查库

用户话术示例：

> 我在评 CinderX 的一个 codegen 改动，涉及把分支改成条件选择，帮我从调度理论上判断合理性。

期望行为：
- 读 `instruction-scheduling.md` 的依赖类型与判读框架（理论层）
- 涉及 if-conversion 的具体指令（CSEL/CCMP/CMOVcc/SETcc）时，按文末"落地查证"
  小节调用 `lookup_instruction` 等工具，引用带 source_doc+页码
- 延迟/吞吐数字不得出自 ISA 库（库无微架构性能数据），需走 perf 证据并明示
