# 澄清问题参考

仅在缺失事实会改变目标、实验轴、权限或成本时使用；先从仓库、日志和已有产物查证。内部路由、常规参数、日志目录和可逆隔离方案由 Agent 决定。

## 宿主工具

遵循当前宿主的工具可用性和 schema。Codex 的 `request_user_input` 可能只在 Plan 模式开放；有 `request_user_input_async` 时可先询问缺失信息并继续独立工作。Claude Code 可用 `AskUserQuestion`。文本降级使用简短问题，必要时给选项；不要假设某个工具在所有模式可用。

需要结构化记录时可用 `question_id`，无需每次写时间戳和完整问卷。以下只提供有明确阻塞条件的例子。

| question_id | 触发条件 | 问题示例 |
|-------------|----------|----------|
| `experiment_axis` | 查证后仍有两个不同 baseline 含义 | 这次比较 stock CPython 与 CinderX，还是 CinderX 的两个提交？ |
| `environment_target` | 多个环境都匹配，无法判断用户指哪一个 | 这次实验应使用哪个 host/workspace？ |
| `destructive_clean` | 已定位污染，但删除会影响用户产物且未获授权 | 删除指定环境会影响这些产物；是否先备份再清理？ |
| `remote_stall` | 诊断和预算内恢复失败，需要新的资源取舍 | 当前网络路径不可用；是否允许改用该镜像源？ |
| `result_artifacts` | 无法确定输入配对 | 与这份 candidate 配对的 baseline 结果路径是什么？ |
| `scope_budget` | 当前请求不含全量，补跑会明显超出预算 | 相关子集仍有风险，是否扩大到预计耗时约 X 的全量验证？ |

用户回答后沿用该决定。已有构建、测试、复现或环境准备授权不因进入下一阶段而失效；未收到必需答案时不推进依赖该答案的动作，继续不受影响的工作。
