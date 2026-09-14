# 动态对话级 Pressure Test 记录

这是既有版本的历史记录，不代表 2026-09-14 调整后的模型实测结果。当前期望见 `pressure-scenarios.md`，当前确定性验证见 `test_*_skill_router.py`；历史记录中的全链路 Agent 加载、重复确认和 fetch 审批不作为现行规则。

## 目标

验证 skill 在真实用户问法下，是否能把人快速引导到正确路线，而不是只在文档静态结构上“看起来覆盖了”。

## 本轮场景

1. Kunpeng 上验证 benchmark 是否真的进 CinderX JIT
2. Docker 内做 stock CPython JIT vs CinderX 正式对照
3. `pyperformance run` 异常但单 benchmark 正常
4. 真实环境 native crash 复现
5. 文档沉淀
6. 性能退化分析
7. Docker 内连续调试，不想反复 `docker exec`
8. Docker 里既提 crash 又要正式对照
9. 容器 Python 3.14.3 却误用更高 patchlevel API
10. 单元/功能/性能测试中出现 SIGSEGV 后反复加日志
11. 远程命令无输出导致重复执行同一条命令
12. 远程网络操作异常耗时却无限等待
13. 根据双平台性能差距定位根因和优化点
14. 根据已知特性实施优化并补充用例
15. 系统分析 ISA / 微架构差异寻找优化机会
16. 顶层端到端优化任务不应误入单用例 JIT 或正式跑分子流程
17. 长任务或上下文压缩后，运行中 Bash 输出出现 crash/timeout 仍应触发 skill 提醒
18. 环境 verifier 三态：可复用、新环境、被破坏环境
19. A/B 并行跑分：baseline/candidate 分 slot 和绑核
20. 技能必须保持 CPython/CinderX 专业动作，不退回泛化入口
21. 写完 CPython/CinderX 代码后，验证/本地安装命令应在执行前按命令内容触发技能
22. pyperformance 正式性能测试前，需要区分 RuntimeTests 功能测试、test_cinderx/lib test 集成测试和 pyperformance 性能测试
23. 本地 CPython checkout 是非目标版本时，应先安全切换到本地 3.14.3 来源，不直接远端下载

## 当前结论

### 已覆盖较好

- `cinderx-test` 与 `cpython-baseline` 的双线区分
- `run_benchmark.py` vs `python -m pyperformance run` 的入口区分
- HIR dump 应先开后关
- `driver / manager / worker / bench_command` 进程模型
- 文档沉淀的最小结构

### 本轮新增补强

- Docker 调试优先保留一个长连接交互终端
- 不把反复 `docker exec` 当作主调试路径
- 当用户同时提到 crash 和正式对照时，要先判断“当前目标”，避免只盯着历史 crash 线走偏
- SSH 进入远程环境后，默认下一步不是裸机主工作流，而是先确认宿主机目录隔离，再进入 Docker
- bind mount 之前，必须先确认宿主机目录边界，避免多个 Agent 共享写入
- 编译前增加 API/ABI 版本门禁，防止用目标环境没有的更高 patchlevel API 修 Python 3.14.3
- crash 取证改为 gdb/core/HIR 优先，日志只能补充，不能替代 native 证据
- 远程命令首跑必须有输出契约，避免无输出后重复执行有副作用命令
- 远程网络卡顿要先诊断 timeout、代理、DNS、镜像源，并在需要决策时询问用户
- 新增验证阶梯：L0 静态审计、L1 最小功能验证、L2 单 benchmark、L3 小集合、L4 全量验证
- 新增成本预算约束，防止调试循环默认进入近千条 RuntimeTests 功能测试或近三小时 pyperformance 性能测试全量
- 新增三条优化 workflow：双平台差距、已知特性驱动、平台差异系统发现
- Workflow 分为主 Workflow 和 Supporting Workflow
- 顶层任务先选用户目标入口，再按阶段调用 supporting workflow
- 明确先主流程，后子流程，避免用单用例 JIT 分析或正式跑分流程取代端到端优化流程
- 移除启动时全量注入，改为 PostToolUse runtime hook 捕获 crash、timeout、远程无输出等运行中信号
- runtime hook 只注入短提醒，引导加载 `workflow-cinderx-crash-triage`、`cinderx-gdb-core-triage`、`cinderx-remote-lab-ops` 和 `validation-strategy`
- 新增 Agent 层：orchestrator 只做分发，environment verifier 做三态判断，runner/analyst/triager 接管阶段
- 新原子层收窄为专业 skill：`cinderx-env-validate`、`cinderx-ab-run-slot`、`cinderx-gdb-core-triage`、`pyperformance-worker-run`、`cinderx-isa-microarch-compare`
- 删除泛化入口，避免把任意项目都能套用的 skill 放进 CPython/CinderX 专业仓
- 新增 PreToolUse validation hook：按 Bash 命令内容识别 CPython/CinderX 构建、RuntimeTests 功能测试、pyperformance 性能测试和 `pip install [options] .`
- 高成本或改写环境的验证命令先阻断并要求环境审计/验证策略确认，已确认时用 `CPYTHON_OPTIMIZE_HOOK_ACK=1` 避免重复阻断
- 新增三类测试术语：RuntimeTests 是功能测试，test_cinderx/lib test 是集成测试，pyperformance 是性能测试
- pyperformance 规则级 checklist 增加 driver/manager/worker、`bench_command()`、系统 site-packages、`--inherit-environ`、CPU 绑核和非 debug 正式运行口径
- 从 GitCode issue/wiki 的测试命令中抽象出命令形态，但文档只保留 `<benchmark-selector>`、`<result.json>` 等占位
- 本地 CPython 仓当前不是 3.14.3 时，先查 remote、commit、dirty 状态、ref 和 `Include/patchlevel.h`，优先用 `git worktree` / cache 安全切换
- 网络不佳时优先复用本地 clone、worktree、tarball/cache 或已有容器源码；fetch/download 需要用户确认

## 结论

当前 skill 已经能支持第一轮真实对话级路由，但后续如果继续迭代，最值得补的是：

- 对“容器里有代理 / 没代理”这种环境前置条件的显式提醒
- 把远程输出契约沉淀成可复用包装脚本
- 后续可把验证阶梯实现成 CinderX 专用 runner，自动生成命令、产物目录和晋级记录
- 后续可按真实误报情况继续收敛 runtime hook 的触发模式
