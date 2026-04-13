# Changelog

本文件记录 `cpython-optimize-skill` 的版本演进。

## v0.3.0

- 明确远程环境工作流：
  - 先确认 SSH 可登录
  - 再使用 `rsync` 同步代码仓
  - 再进入 Docker 容器隔离
- 强化远程宿主机目录隔离约束，避免 bind mount 覆盖已有目录
- 明确容器内 `pip` 默认应切到国内镜像源，优先阿里云或华为云
- 明确 dump HIR 时应优先复用真实测试命令，只增减 debug 环境变量
- 新增性能口径定义：
  - `CPython 解释执行`
  - `CPython JIT`
  - `CinderX 解释执行`
  - `CinderX JIT`
- 明确 `baseline` 的两种含义：
  - 口径基线
  - 提交基线
- 明确 Arm vs x86 属于跨平台对比，必须参数和口径一致
- 修正 HIR 分析顺序：
  - 先确认进入 CinderX JIT
  - 再做热点归因
  - 最终输出必须包含具体 HIR 片段、问题说明和修改方案

## v0.2.0

- 重构为“核心层 + 四平台薄包装”
- 补齐主工作流：
  - SSH / tmux
  - 构建与强制覆盖安装
  - `pyperformance` 测试
  - Docker 运行时隔离
  - 文档规范
  - 用例分析
- 固化 Docker 双线：
  - `cpython-baseline`
  - `cinderx-test`
- 收录真实环境命令模板
- 迁入已验证的 `cinderx-test` 脚本
- 补齐 FAQ、入口决策表、静态/动态 pressure test

## v0.1.0

- 初始化技能仓库脚手架
- 建立 CPython/CinderX 联合优化技能的基础目录结构
- 确立以 CinderX 优先的个人工作流定位
