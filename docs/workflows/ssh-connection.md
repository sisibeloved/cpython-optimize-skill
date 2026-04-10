# 环境获取：SSH 与 tmux

## 目标

稳定接入远程优化环境，并尽量复用连接，不重复开新会话。

## 基本流程

1. 配置 SSH 别名，固定主机名、用户和密钥
2. 登录后优先创建或复用 `tmux` 会话
3. 长任务统一在 `tmux` 内执行
4. 断线后优先 `tmux attach`，不要重建上下文

## 推荐习惯

- 每个项目固定一个 `tmux` 会话名
- 构建、日志、benchmark、调试分开 pane 或 window
- 重要远端路径写进文档，不靠记忆

## 最小命令

```bash
ssh <host>
tmux new -s cinderx
tmux attach -t cinderx
```
