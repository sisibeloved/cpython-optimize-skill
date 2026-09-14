# Container Tooling 指南

容器内测试或排障时，缺少关键工具不要直接绕开目标取证路径。`gdb`、`ripgrep` / `rg`、`strace`、`perf`、`binutils` 等工具缺失时，先评估补装；只有确认无法补装或补装成本不可接受时，才记录原因并使用降级方案。

## 先探测

补装前先输出探测结果：

- 工具是否存在：`command -v gdb rg ripgrep strace perf objdump readelf`。
- 包管理器：`command -v dnf yum apt`。
- 网络和镜像源：DNS、代理、repo 配置、pip mirror、系统包 cache。
- 容器权限：当前用户、是否 root、是否允许写 package cache。
- 耗时护栏：用 `timeout` 包裹 metadata refresh、repo query 或 dry run。

## 再安装

优先用容器内包管理器和已有 cache：

| 系统 | 形态 |
|------|------|
| openEuler / Fedora / CentOS | `dnf install -y gdb ripgrep strace perf binutils`，没有 dnf 时再看 `yum` |
| Debian / Ubuntu | `apt-get update` 后 `apt-get install -y gdb ripgrep strace linux-perf binutils` |
| 离线或网络慢 | 查本地 rpm/deb/cache、宿主机挂载、已有工具目录或让用户提供离线包 |

安装命令必须记录 stdout/stderr、exit status、耗时和日志路径。不要沉默等待。

## 网络慢怎么处理

- metadata 或安装长时间无输出时，及时反馈进度。
- 先检查 DNS、代理、镜像源和 cache，再决定是否继续等待。
- 预算内优先复用 cache 或已有离线包；继续等待沿用进度策略。只有需改变指定镜像、额外权限或超过预算时，才询问切镜像、提供离线包或中止。
- 不要为了避免在线安装而直接放弃 `gdb bt full`、`rg` 检索、`perf` 或 `strace` 取证。

## 降级条件

只有满足以下之一才降级：

- 包管理器不可用且没有离线包/cache。
- 网络不可用，预算内恢复失败，且没有已授权的替代路径。
- 安装会污染正式性能环境，且无法使用临时调试容器或快照。
- 工具与目标内核/发行版不兼容。

降级报告必须写明：缺失工具、探测命令、尝试过的安装命令、失败原因、exit status、耗时、替代方案和证据损失。
