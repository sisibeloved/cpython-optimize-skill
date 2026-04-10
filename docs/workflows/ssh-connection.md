# 环境获取：SSH 与 tmux

## 目标

稳定接入远程优化环境，并尽量复用连接，不重复开新会话。

注意：
- SSH 只是进入远程宿主机
- 对 CPython/CinderX 主工作流来说，默认下一步应进入 Docker 容器隔离
- 不要把“SSH 上去后直接在裸机做编译/测试”当作默认路径

## 基本流程

1. 配置 SSH 别名，固定主机名、用户和密钥
2. 登录后先确认当前 Agent 的宿主机目录是否独立
3. 优先创建或复用 `tmux` 会话
4. 进入目标 Docker 容器或先启动对应容器
5. 长任务统一在 `tmux` 和容器内执行
6. 断线后优先 `tmux attach`，不要重建上下文

## 推荐习惯

- 每个 Agent 使用独立宿主机目录，例如按项目名、分支名或 Agent 名隔离
- 每个项目固定一个 `tmux` 会话名
- 构建、日志、benchmark、调试分开 pane 或 window
- 重要远端路径写进文档，不靠记忆
- bind mount 前先确认宿主机目录不会覆盖已有工作目录

## 最小命令

```bash
ssh <host>
mkdir -p ~/work/<project>-<agent>
tmux new -s cinderx
tmux attach -t cinderx
```

## 进入远程后的默认动作

优先顺序：
1. 确认宿主机目录独立
2. 确认 Docker 可用
3. 进入或启动目标容器
4. 再开始编译、测试、调试
