# 寄存器分配

来源：Cooper & Torczon《Engineering a Compiler》2nd ed，Ch13：
§13.3 Local Allocation（PDF p709）、§13.4 Global Allocation（p718）、
§13.5 Advanced Topics（p738，含 SSA/chordal 与 linear scan 的关系）。
Chaitin 见 PDF p731、Briggs 见 p732。页码为 PDF 页，印刷页 ≈ PDF−25。

## 问题定义

把无限虚拟名字映射到有限物理寄存器；放不下的值 spill 到栈内存。
分配质量直接表现为代码里 load/store 密度与 move 数量。spill 代价的三个度量
（§13.4 开篇）：执行时间、代码体积、数据体积——大多数分配器以执行时间为目标。

## 经典算法谱系

- **局部分配（§13.3，p709）**：top-down（按引用计数优先级保留整块）与
  bottom-up（前向扫描，寄存器不够时 spill "最远下次使用"的值）两种；
  bottom-up 因允许一寄存器复用多值而更优。
- **图着色（§13.4，p718）**：
  - 冲突图：活跃区间重叠的虚拟寄存器连边；着色数 ≤ 物理寄存器数即可全分配。
  - Chaitin（p731）：简化-溢出-选择，溢出候选是高度数节点，迭代重跑。
  - Briggs 改进（p732）：保守/乐观着色，减少不必要的 spill。
  - 质量最好，代价高，AOT 编译器主力。
- **线性扫描（linear scan）**：不在本书 2e 正文（PBQP 同），书只在 §13.5.2
  （p738）点出其原理——用简单区间近似全局活跃区间，形成区间图
  （interval graph，可线性时间着色）。快，**JIT 的标准选择**（编译时间预算
  硬约束）。出处：Poletto & Sarkar, PLDI 1999。
- **SSA 上的分配（§13.5.2，p738）**：SSA 名字建的冲突图是 chordal graph，
  k-着色可 O(|V|+|E|) **精确求解**（启发式可能用更多寄存器）——这是
  "SSA 简化分配器"的理论根据；需要 spill 时仍走传统路径。
- **PBQP**（Partitioned Boolean Quadratic Programming）：本书 2e 未覆盖，
  出处 Scholz & Eckstein 2002；LLVM 曾采用。定位：指令选择+分配联合建模，
  质量介于线性扫描与图着色之间。

## 关键概念（读 spill 报告时用）

- **活跃区间（live range，§13.4，p719 起）**：从最后定义到下次使用之间需要
  保值的区间；区间越长越可能冲突。
- **live range splitting**：把长区间切成多段，段间走内存——降冲突但加
  load/store；线性扫描质量的核心杠杆。
- **coalescing（合并，§13.4，p733–737）**：消除 move——把"同一值经 move
  传递"的两个虚拟名字分到同一物理寄存器。SSA 下 φ 消解产生的 move 是
  coalescing 的主要目标。**激进 coalescing 会加剧图着色难度**（Briggs 的
  保守合并判据即为此，p737 附近）。
- **caller/callee-saved**：被调方保存 vs 调用方保存寄存器的约定——
  调用密集代码里 callee-saved 保存/恢复的开销、跨调用活跃区间的寄存器选择
  都是可见的代码形态。A64 的具体寄存器分组以
  `isa-instruction-lookup` 与 AAPCS64 约定为准。

## 判读"为什么 spill"的检查顺序

1. 活跃区间是否被调度/内联拉长（联动 `instruction-scheduling.md`）。
2. 压力峰值在哪个程序点：找出同时活跃的虚拟寄存器数量最大的位置。
3. 是否大量无 coalesce 的 move（φ 消解或拷贝传播失败）。
4. 物理寄存器被固定占用（平台保留寄存器、调用约定强制参数寄存器）。
5. JIT 预算是否限制了迭代轮次（线性扫描单遍 vs 图着色多轮）。

## 边界

指令的具体编码与 ABI 细节不在本文；引用时区分"理论框架（本文）"与
"平台事实（isa-instruction-lookup 查询结果）"。

## 落地查证

- spill 判读涉及的具体 load/store 指令形态 → `lookup_instruction`。
- 平台寄存器分组（A64 AAPCS64 的 caller/callee-saved）→ `lookup_instruction` 查
  相关指令的 operand 文档，引用时带 source_doc+页码。
