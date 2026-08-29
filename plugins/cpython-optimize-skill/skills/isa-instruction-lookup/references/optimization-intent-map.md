# A64 / x86-64 优化意图 → 指令族映射

FTS 只能匹配字面术语，匹配不了优化意图（"取代分支""无分支代码"不在手册描述里）。
本表把常见优化意图翻译成功能术语/指令族，供 `find_instruction_by_function` 与
`find_equivalent_instruction` 检索前使用；跨平台列给出对侧等价族。
人工提炼，随实践扩充；新增条目前须先用 MCP 工具验证该族指令确实在库。

| 优化意图 | 功能术语(FTS 用) | A64 指令族 | x86-64 指令族 |
|---|---|---|---|
| 用条件选择取代比较+分支、无分支代码、条件置值 | conditional select / conditional move | CSEL / CSINC / CSINV / CSNEG / CSET / CSETM | CMOVcc / SETcc（Jcc 是被取代对象） |
| 条件比较合成、多条件合并短路 | conditional compare | CCMP / CCMN | 无直接等价（复合 Jcc 判定） |
| 位反转、前导零计数、popcount | bit reverse / count leading / popcount | RBIT / CLZ / CLS；CNT(SIMD)、CNT/CTZ(FEAT_CSSC) | BSWAP（字节序）/ BSR / LZCNT / POPCNT / TZCNT |
| 位域提取/插入、无符号扩展移位 | bitfield move | UBFM / SBFM / BFXIL / EXTR | SHRD / SARX / SHLX / SHRX（BMI2）/ BEXTR |
| 位掩码并行置放/提取 | parallel bits deposit / extract | 无直接等价（AND/LSL 序列） | PDEP / PEXT（BMI2） |
| 内存序、屏障、预取 | barrier / acquire release | DMB / DSB / ISB / PRFM；LDAR / STLR / LDAPR | MFENCE / SFENCE / LFENCE；LOCK 前缀 |
| 原子操作、无锁 | atomic memory operation | FEAT_LSE: LDADD / SWP / CAS 族；LL/SC: LDAXR+STLXR | LOCK 前缀: LOCK ADD/XCHG/CMPXCHG；XADD |
| 向量化循环控制、零开销循环 | while loop predicate | WHILELT / WHILEGE 族 + CTERMEQ,CTERMNE | 无直接等价（软件展开） |
| 谓词置位、掩码生成 | predicate initialize / mask | PTRUE / PTRUES / PFALSE；RDFFR | KREG 族（AVX-512: KAND/KOR/KTEST） |
| gather/scatter、首触fault-first | gather / first fault | LD1(scalar plus vector) 族、LDFF1 族 | VGATHER*（AVX2/AVX-512）/ VPGATHER |
| 表驱动查表 | table vector lookup | TBL / TBX；FEAT_LUT: LUTI4 | 无直接等价（pshufb 近似: PSHUFB） |
| 饱和运算 | saturating | SQADD / UQADD / SQSUB / SQDMULH 族 | PADDB 等（MMX/SSE 饱和形态有限） |
| 点积、矩阵乘加速 | dot product | SDOT / UDOT（FEAT_DotProd）；FMLA 族 | DPPS / DPPD；PMADDWD；AMX（Tile） |
| 哈希/CRC/加密加速 | CRC / cryptographic | CRC32 族（FEAT_CRC32）；AESD/AESE/PMULL 族 | CRC32（SSE4.2）；AESENC/AESDEC 族 |

用法：意图 → 查本表得功能术语与对侧族 → `find_instruction_by_function("<术语>")` 或
`find_equivalent_instruction(<助记符>, from_arch, to_arch)` → `lookup_instruction(<助记符>,
verbose=True)` 取伪代码/语法/操作数文档 → **比对伪代码确认语义假设、核对语法与操作数
约束** → 引用时带 `source_doc`+`page_start`。

**候选检索跨 category/feature 不设限**：优化替换经常跨执行域——popcount 是 base
需求但最优解在 SIMD 的 CNT 或 FEAT_CSSC 的 CNT/CTZ；SVE 指令可替换 base 指令序列
（一条 WHILExx+谓词 load 替代整段标量循环）。分类和 feature 只回答"部署时目标机器
能不能用"，回答不了"语义是否一致、是否有更优写法"——后者靠伪代码比对。
`find_equivalent_instruction` 返回的是词面候选（如 CMOVcc 的 a64 侧候选可能混入
MOV 族），**精确等价性必须比对双方 operation_pseudocode 后下结论**；本表的
"对侧族"列是权威答案，机器候选用于发现遗漏。
