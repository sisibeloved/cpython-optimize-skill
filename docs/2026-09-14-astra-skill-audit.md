# GPT-6 Astra 技能与提示词审计

日期：2026-09-14。发布对比基线：`5abbab4`（v1.1.0）。初始本地审计基于 `e154546` 的 32 个技能；发布前已合入远端更新，以下统计覆盖最终的 35 个技能。

参考 Eric Provencher 于 2026-09-11 发布的 [Rethinking skills and prompts for GPT-6 Astra](https://learn.chatgpt.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)。本文据此检查描述触发范围、按需加载、过度流程、决策边界与完成条件；下面的具体改法和测量来自本仓审计。

## 修改与理由

| 本仓原有行为 | 调整 |
|--------------|------|
| 35 个描述中包含较长的实现细节与宽泛触发词 | 描述集中于任务、输入与必要边界；保留全部技能名 |
| 所有入口倾向经过 Orchestrator → Workflow → Agent | 单项任务直达技能；角色索引移入按需 reference，Workflow 支持主 Agent 顺序执行 |
| 编译、安装、L3、创建 worktree 或网络等待容易重复询问 | 沿用已有授权与预算；只对目标不明、未授权破坏性操作、共享影响或额外成本询问 |
| 提交/报告可能触发 L4，文档修改可能带出全套设计流程 | 测试由受影响行为决定；设计只加载相关模板，固定完整格式按用户或项目要求采用 |
| hook 对定向 pyperformance/worker 一律 deny，并注入多个角色路径 | 定向命令使用环境证据提醒；结果比较只路由结果分析；不注入 Agent 清单 |
| 复合命令只处理第一个匹配动作 | 对已解析的命令片段优先返回 deny，避免定向测试掩盖后续全量/环境改写 |
| 历史压力记录容易被当作当前行为证明 | 标注历史记录；更新当前期望并增加 49–54 场景，区分静态覆盖与模型实测 |

根目录 [AGENTS.md](../AGENTS.md) 记录本仓路径、按改动读取材料和本地验证范围。它用于维护插件，实验约束仍放在所属技能。

## 保留的实验约束

- Python 3.14.3、ABI、头文件和既有 AArch64 TLS 形态检查。
- baseline source 的独立身份、干净来源、安装隔离与唯一差异轴；`reusable` 不等于 `baseline_source_verified`。
- 真实 worker 的 `.pth`、`pyvenv.cfg`、`--inherit-environ`、CinderX 初始化和 benchmark 本体 JIT 证据。
- A/B 的 CPU、容器、build dir、日志与结果隔离，以及正式数据的非 debug 口径。
- crash 的真实命令、native 栈/core；E1–E9 的证据、置信度和穿刺判读。
- 全量、范围不明 helper、环境改写的 hook 前置检查。ACK 仅表示已完成适用检查，不代表工具验证了事实或用户授权。

环境指纹变化后重查受影响证据。门禁限制相关实验和结论，独立的取证与分析可以继续。

## 可复核的静态规模

字符数按 Python `len(str)` 统计，不是 token 数或模型成本。技能描述不包含 `description: ` 前缀，行数包含 frontmatter。

| 指标 | 修改前 | 修改后 |
|------|-------:|-------:|
| 技能数量 | 35 | 35 |
| 所有 description 总字符数 | 4,444 | 2,097 |
| 最长 description 字符数 | 441 | 85 |
| 所有 SKILL.md 总行数 | 1,800 | 1,637 |
| 总入口行数 | 81 | 49 |
| 设计文档入口行数 | 146 | 34 |
| 验证策略行数 | 67 | 39 |

描述总字符数减少约 53%。总入口以外新增了按需角色索引和设计视图规范；表中行数不代表整个插件包大小，也不代表每次任务实际加载量。远端新增的 ISA 查询、编译器理论、统计报告、RFC 模板与设计图约束均已保留。

复核描述统计，可在仓库根目录执行：

```python
from pathlib import Path
import re
import subprocess

base = "v1.1.0"
paths = sorted(Path("plugins/cpython-optimize-skill/skills").glob("*/SKILL.md"))
before = [subprocess.check_output(["git", "show", f"{base}:{p}"], text=True) for p in paths]
after = [p.read_text() for p in paths]
for label, texts in [("before", before), ("after", after)]:
    descriptions = [re.search(r"^description: (.*)$", text, re.M).group(1) for text in texts]
    print(label, len(texts), sum(map(len, descriptions)), max(map(len, descriptions)))
```

## 验证与限制

初始本地检出的四项检查全部通过。发布合并后运行布局、压力场景静态覆盖、运行时 hook、执行前 hook、ISA 查询、ISA 数据质量与统计报告回归；另用官方 `skill-creator/scripts/quick_validate.py` 校验全部 35 个技能。缺少的测试工具安装到仓库外临时 venv，没有修改宿主插件缓存；ISA 运行依赖约束见下段。

发布验证发现现有 ISA 服务的 FastMCP 接口与 MCP 2.x 不兼容，补充 `mcp/isa-reference/requirements.txt` 将运行依赖限定为 `mcp>=1,<2`；使用该兼容环境重跑 ISA 测试。本次不迁移 MCP 服务 API。

执行前 hook 回归使用临时 CPython 目录与 JSON 输入，验证：仓外/只读不触发、定向命令提醒后继续、worker 证据提示、只读结果不路由跑分、全量/安装/venv 改写保留检查、ACK 重试和复合命令优先级。测试不会执行被描述的构建、安装或 benchmark 命令。

保留 v1.1.0 的 ISA 场景 47–48，新增行为场景顺延为 49–54，覆盖只读比较、授权持续有效、局部文档修改、破坏性边界、部分证据缺失与单 Agent 执行。这些是待用于真实模型运行的验收场景，本次没有进行 GPT-6 Astra 与旧提示词的多轮 A/B 评测，不能据静态字符减少声称成功率、延迟或 token 成本改善。

本次修改仓库源文件，不更新宿主已安装的插件缓存，不运行远程 lab、CinderX 构建或性能测试。hook 仍是命令启发式路由，不是通用 shell 安全解析器或实验事实验证器。
