# Baseline Source 契约

远程 SSH、tmux、Docker 容器或 pyperformance 可运行，只能说明执行环境可用，不能自动说明 baseline 源码可信。A/B 测试的 baseline 必须有独立事实源；远程 workspace 里的现成源码不能因为容器可用就被当成 baseline。

## Baseline 必须证明什么

| 项 | 必须证据 |
|----|----------|
| baseline 身份 | 口径 baseline 与提交 baseline 分开说明：例如 CPython 解释执行、CPython JIT、CinderX JIT，以及 baseline commit/ref |
| 源码来源 | 用户指定的 baseline commit/ref、CPython 3.14.3 release source、干净 git worktree、可信 tarball/cache，或 `cpython-baseline` 容器 bind mount 指向的明确源码 |
| 版本一致 | 目标解释器、`patchlevel.h`、`SOABI`、include 路径和源码版本一致 |
| 仓库状态 | `git status --short` 为空或污染项已解释；`git show -s --format=%H`、`git describe --tags --always --dirty` 可记录 |
| A/B 差异轴 | baseline/candidate 只差目标变量，不能混入不同 Python 版本、错版 CinderX、candidate editable install 或环境残留 |

## 禁止行为

- 只因为远程容器、tmux pane 或 Docker compose 可用，就把远程 workspace 当前源码当 baseline fact source。
- baseline ref 不明、dirty 状态未解释、`patchlevel.h` / `SOABI` 不符、容器 bind mount 指向不明时继续跑正式 A/B。
- baseline 误继承 candidate 的 CinderX `.pth`、`PYTHONPATH`、editable install、JIT hook 或 `CINDERX_*` 变量。
- 把环境 verifier 的 `reusable` 当成 baseline source verified。`reusable` 表示环境能复用，不表示源码已经适合作为 baseline。

## 判定

- `baseline_source_verified`：baseline commit/ref、源码路径、版本、dirty 状态和唯一差异轴都可证明。
- `baseline_source_untrusted`：执行环境可用，但 baseline 源码可信性缺失或失败。此时不能进入正式 A/B 或 `pyperf compare_to` 可信结论。

## 失败时怎么做

返回 `baseline_source_untrusted`，并给出最小修复路径：
- 先从任务和已有记录查证 baseline commit/ref 与口径 baseline；含义仍不明确时再让用户指定。
- 在远程环境创建干净 git worktree，再校验 `git status --short` 和 `git show -s --format=%H`。
- 重建或修复 `cpython-baseline` 容器 bind mount，确认它指向 CPython 3.14.3 baseline source。
- 清理 baseline 侧 candidate editable install、`.pth`、`PYTHONPATH` 和 JIT hook 污染。

## 输出要求

报告中写明：口径 baseline、提交 baseline、baseline source path、commit/ref、`git status --short`、`patchlevel.h`、`SOABI`、容器 bind mount、是否 dirty、是否存在 candidate editable install 污染，以及 baseline/candidate 是否只差目标变量。
