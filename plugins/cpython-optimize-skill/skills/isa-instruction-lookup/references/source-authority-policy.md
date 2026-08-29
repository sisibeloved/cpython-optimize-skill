# 来源可靠性白名单

跨平台对比（`cinderx-isa-microarch-compare`）的可信度取决于两侧知识来源可靠性对等。
本文件是 isa.db 数据准入的唯一规则，ingest 脚本与人工补录都必须遵守。

## 允许入库的来源

| arch | source_authority | 具体来源 | 形态 |
|---|---|---|---|
| a64 | ARM-official | ARM 官方 ISA_A64_xml_A_profile 2026-06 发布包 | 官方 XML（instructionsection） |
| x86_64 | Intel-SDM | Intel SDM Vol.1+2ABCD+3ABCD 集合版（Order 325462, rev 050） | 官方 PDF（TOC 指令级书签） |
| x86_64 | AMD-APM | AMD APM Vol.3（Doc 24594, rev 3.38, 2026-07） | 官方 PDF（feature 声明 + Appendix D） |

## 硬规则

1. `source_authority` 只允许上表枚举值。第三方汇编文档、博客、cheatsheet、
   LLM 生成的指令描述**一律不入库**，哪怕"看起来对"。
2. 同一 arch 只允许一个 active 版本的手册数据。新版 ingest 前先删除旧版行
   （ingest 脚本按 arch 全量重建，天然满足）。
3. 每条记录必须携带 `source_doc`；页码（page_start）缺失时检索结果须提示
   "无页码回溯"而不是编造页码。
4. x86 侧 Intel 与 AMD 重叠指令以 Intel SDM 为 primary，AMD 特有/AMD 行为差异
   以 APM 为准并在引用时注明来源。
5. 库外知识（博客、perf 实测、TRM 延迟数据）可以进入**分析结论**，但必须
   标注"未经库验证"，不得与库内数据混排为同一可信级别。
