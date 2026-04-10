# 用例分析

## JIT 路线

分析顺序：

1. 确认是否真的进入 CinderX JIT
2. 抓 HIR
3. 抓 LIR
4. 看最终机器码或 trampoline
5. 必要时结合 `gdb`、core dump、deopt 信息

重点关注：
- HIR 是否退化
- pass 前后形态是否变化
- deopt idx、frame layout、调用约定是否异常

## 非 JIT 路线

分析顺序：

1. 字节码
2. uop
3. 机器码

重点关注：
- opcode / uop 形态差异
- 是否退回慢路径
- 是否存在启动期或 import-time 噪声

## 对比原则

- 先对齐命令口径
- 再对齐解释器和依赖
- 再比较性能
- 最后比较 HIR/LIR/机器码
