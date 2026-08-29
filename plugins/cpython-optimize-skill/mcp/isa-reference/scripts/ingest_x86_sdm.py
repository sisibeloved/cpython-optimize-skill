#!/usr/bin/env python3
"""Ingest Intel SDM Vol.2 instruction pages into isa.db (arch='x86_64').

数据源: Intel 官方 SDM 集合版 PDF (Order 325462)。只取 Vol.2 指令集参考章
(Ch3 A-L / Ch4 M-U / Ch5 V / Ch6 W-Z / Ch7 SMX), 书签 level-5 即指令条目。
Ch8(Xeon Phi 特有) 与 Appendix 不入指令表。

feature 依赖不在本脚本灌(Intel 页内 CPUID 提及弱): 由 ingest_x86_apm.py
从 AMD APM Appendix D(指令<->CPUID flag 权威总表)与页内声明回填。

用法:
  python3 ingest_x86_sdm.py --pdf <Intel_SDM_combined_325462.pdf> [--db <isa.db>]
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import tempfile

import fitz

SOURCE_DOC = "Intel_SDM_combined_325462"
SOURCE_AUTHORITY = "Intel-SDM"

# Vol.2 指令参考页范围: Ch3 p597 起, 止于 Ch8 Xeon Phi (p2799) 前
VOL2_PAGE_RANGE = (597, 2799)

# 书签标题为指令条目的判定: 含长破折号且非编号/附录开头
DASHES = "—–"
SECTION_HEADS = re.compile(
    r"^(Description|Operation|Flags Affected|Intel C/C\+\+ Compiler Intrinsic|"
    r"Numeric Exceptions|SIMD Floating-Point Exceptions|Protected Mode Exceptions|"
    r"Real-Address Mode Exceptions|Virtual-8086 Mode Exceptions|Compatibility Mode Exceptions|"
    r"64-Bit Mode Exceptions|Instruction Operand Encoding|Legacy ISA|Notes)\b")

# opcode 表行(状态机用): 16进制操作码开头; 前缀形态 REX.W + / VEX.NDD.LZ.66.0F38.W0 / 66 / F2 ...
# 尾部立即数/相对跳转后缀: ib..iq(立即数), cb/cw/cd(rel8/16/32 跳转, Jcc/LOOP 族)
OPCODE_LINE = re.compile(
    r"^(?:(?:REX\.[WXLRB]+|(?:VEX|EVEX|XOP)\.[A-Z0-9.]+|NP|F2|F3|66)\s*\+?\s+)*"
    r"(?:[0-9A-F]{2})(?:\s+[0-9A-F]{2})*(?:\s*/[r\d7])?(?:\s+(?:i[bwdqz]|cb|cw|cd))?$")
# 页眉/页脚: 'INSTRUCTION SET REFERENCE, A-L' / 'Vol. 2A 3-175' / '3-176'
HEADER_LINE = re.compile(r"^(INSTRUCTION SET REFERENCE.*|Vol\. ?2[A-D]?\b.*|[0-9]+-[0-9]+)$")
# 表格短标记列: Op/En 值与 Valid/N.E.; 之外的短 token(如 BMI2/SSE2)是 CPUID Feature Flag 列
TABLE_TOKEN = re.compile(r"^(RM|RVM|RVMR|FV|RV|R|M|I|IM|V|N\.E\.|Valid|N/A|V/N\.E\.|V/V|V|N/E|V/N\.E|None)$")
# CPUID feature flag 白名单: 仅新式表(表头含 'CPUID Feature Flag')行组内且在此集合的 token 才入库
KNOWN_FLAGS = {
    "SSE", "SSE2", "SSE3", "SSSE3", "SSE4.1", "SSE4.2", "SSE4A", "3DNow!", "3DNowExt",
    "AVX", "AVX2", "AVX512F", "AVX512DQ", "AVX512IFMA", "AVX512PF", "AVX512ER", "AVX512CD",
    "AVX512BW", "AVX512VL", "AVX512VBMI", "AVX512VBMI2", "AVX512VNNI", "AVX512VPOPCNTDQ",
    "AVX512BITALG", "AVX512VP2INTERSECT", "AVX512FP16", "AVX512BF16", "AVXVNNI", "AVXVNNIINT8",
    "AVXIFMA", "AVX10", "FMA", "FMA4", "F16C", "BMI1", "BMI2", "ADX", "AES", "VAES",
    "PCLMULQDQ", "VPCLMULQDQ", "GFNI", "SHA", "SHA512", "SM3", "SM4", "TBM", "ABM",
    "XOP", "XSAVE", "XSAVEC", "XSAVES", "XSAVEOPT", "MOVBE", "POPCNT", "LZCNT", "RDRAND",
    "RDSEED", "CLZERO", "CLFLUSHOPT", "CLWB", "PREFETCHW", "FSGSBASE", "ERMS", "INVPCID",
    "HLE", "RTM", "MPX", "PKU", "OSPKE", "SGX", "SMEP", "SMAP", "RDPID", "MWAITX",
    "MONITORX", "WBNOINVD", "PCONFIG", "ENQCMD", "UINTR", "HRESET", "WAITPKG", "SERIALIZE",
    "CET", "CETSS", "KL", "WIDEKL", "AMX", "AMXTILE", "AMXINT8", "AMXBF16", "SVM", "LWP",
    "SEV", "SEVES", "SNP", "TSE", "RMPQUERY", "CMPCCXADD", "WRMSRNS", "MSRLIST", "APXF",
    "RAOINT", "AVXNECONVERT", "AVXVNNIINT16",
}
# opcode 表的 7 列表头序列(跨页表格每页重复)
TABLE_HEAD_SEQ = ("Opcode", "Instruction", "Op/", "64-Bit", "Compat/", "Description")


def is_instruction_title(title: str, page: int) -> bool:
    lo, hi = VOL2_PAGE_RANGE
    if not (lo <= page < hi):
        return False
    if re.match(r"^(\d+\.\d|Chapter|Appendix|Table|Figure)", title):
        return False
    return any(d in title for d in DASHES)


def parse_pages(doc, page_start: int, page_end: int, title: str = None, stop_title: str = None):
    """切片页文本, 状态机抽 opcode 表行组 / Description / Operation。
    stop_title 为下一指令书签标题: 遇其标题行立即终止, 防止跨页切片吃进邻指令正文。"""
    text = "\n".join(doc[p].get_text() for p in range(page_start - 1, page_end))
    lines = [l.strip() for l in text.splitlines()]
    stop_first = stop_title.split("—")[0].strip() if stop_title else None

    opcodes, desc_parts, oper_parts = [], [], []
    mode = None          # None/Description/Operation
    table_has_feature = [False]   # 当前表的表头是否含 'CPUID Feature Flag' 列
    i = 0
    n = len(lines)
    while i < n:
        s = lines[i]
        if not s or (title and s == title):
            i += 1
            continue
        if stop_first and (s == stop_title or s == stop_first or s.startswith(stop_first + "—")):
            break  # 下一指令标题行(整行/行首带 em-dash, 兼容长标题折行): 终止全部收集
        if HEADER_LINE.match(s):
            i += 1
            continue

        # 折叠跨页表格表头(最长 10 行内应出现完整列名序列); 记录该表是否含 CPUID Feature Flag 列
        if s.startswith("Opcode") and i + 1 < n and lines[i + 1].startswith("Instruction"):
            head_txt = " ".join(lines[i:min(i + 10, n)])
            table_has_feature[0] = "CPUID" in head_txt
            j = i
            while j < min(i + 10, n) and lines[j] != "Description":
                j += 1
            i = min(j + 1, i + 10)
            continue

        # opcode 表行组: opcode 行 -> syntax 行 -> 短标记(0-3, 含 CPUID feature 列) -> 描述行
        if OPCODE_LINE.match(s) and len(s) <= 28:
            group = {"opcode": s, "syntax": None, "table_desc": None, "feature": None}
            j = i + 1
            short_seen = 0
            while j < n:
                t = lines[j]
                if not t:
                    j += 1
                    continue
                if OPCODE_LINE.match(t) and len(t) <= 28:
                    break
                if group["syntax"] is None and not TABLE_TOKEN.match(t) and not SECTION_HEADS.match(t):
                    group["syntax"] = t
                elif TABLE_TOKEN.match(t):
                    short_seen += 1
                elif group["syntax"] is not None and group["feature"] is None \
                        and table_has_feature[0] and t in KNOWN_FLAGS:
                    group["feature"] = t
                    short_seen += 1
                elif group["syntax"] is not None and (len(t) > 25 or t.endswith(".")):
                    group["table_desc"] = t
                    j += 1
                    break
                if short_seen > 4:
                    break
                j += 1
            opcodes.append(group)
            i = j
            continue

        m = SECTION_HEADS.match(s)
        if m and len(s) < 60:
            mode = m.group(1)
            i += 1
            continue

        if mode == "Description":
            desc_parts.append(s)
        elif mode == "Operation":
            oper_parts.append(s)
        i += 1

    desc = " ".join(desc_parts)
    brief = desc[:300].rsplit(".", 1)
    brief = (brief[0] + ".") if len(brief) > 1 and len(brief[0]) > 40 else desc[:280]
    return {
        "opcodes": opcodes,
        "brief": brief.strip(),
        "authored": desc.strip(),
        "operation_pseudocode": "\n".join(oper_parts).strip(),
    }


def split_title(title: str):
    """'CMOVcc—Conditional Move' -> ('CMOVcc', 'Conditional Move')"""
    for d in DASHES:
        if d in title:
            mn, _, rest = title.partition(d)
            return mn.strip(), rest.strip()
    return title.strip(), None


def guess_category(mnemonic: str) -> str:
    m = mnemonic.upper()
    if re.match(r"^(V|P)[A-Z0-9]", m) and not m.startswith(("POP", "PUSH", "PAUSE", "PREFETCH", "PLDT")):
        return "simd_fp"
    if m.startswith(("X87", "F")) and len(m) > 1 and m[1].isdigit():
        return "simd_fp"
    return "base"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--db", default=os.path.join(os.path.dirname(__file__), "..", "data", "isa.db"))
    args = ap.parse_args()

    doc = fitz.open(args.pdf)
    toc = doc.get_toc()

    # 指令条目: (title, page_start, page_end=下一指令页)
    entries = []
    for idx, (lvl, title, page) in enumerate(toc):
        if lvl == 5 and is_instruction_title(title, page):
            entries.append((title, page))
    # 去重同名(不同编码变体分条书签少见, 保守合并同 title)
    merged = []
    seen = {}
    for title, page in entries:
        if title in seen:
            continue
        seen[title] = page
        merged.append((title, page))
    # 结束页: 下一书签页(不限 level5)或 +8 页封顶
    rows = []
    for j, (title, page) in enumerate(merged):
        nxt = merged[j + 1][1] if j + 1 < len(merged) else page + 4
        # 同页/相邻重复指令收缩
        page_end = nxt
        mn, t2 = split_title(title)
        # 范围放宽到下一指令起始页(保跨页表格完整), 由 stop_title 标题行截断防串扰
        nxt_title = merged[j + 1][0] if j + 1 < len(merged) else None
        parsed = parse_pages(doc, page, min(page_end, page + 8), title=title, stop_title=nxt_title)
        if not parsed["brief"] and not parsed["opcodes"]:
            continue
        rows.append(((
            "x86_64", f"{SOURCE_DOC}#p{page}", title, mn, guess_category(mn),
            None, json.dumps([]),
            parsed["brief"], parsed["authored"], None,
            json.dumps(parsed["opcodes"]), None,
            None, parsed["operation_pseudocode"], None,
            page, SOURCE_DOC, SOURCE_AUTHORITY,
        ), sorted({o["feature"] for o in parsed["opcodes"] if o.get("feature")})))
    print(f"[ingest] instruction entries: {len(rows)}")

    db_path = os.path.abspath(args.db)
    import shutil
    fd, tmp_db = tempfile.mkstemp(suffix=".db")
    os.close(fd); os.unlink(tmp_db)
    # 从目标库复制现有数据再增量(保留 a64), UNC 目标直接锁问题 -> 本地写回拷
    shutil.copyfile(db_path, tmp_db)
    con = sqlite3.connect(tmp_db)
    con.execute("DELETE FROM instruction_features WHERE instruction_id IN (SELECT id FROM instructions WHERE arch='x86_64')")
    con.execute("DELETE FROM instructions WHERE arch='x86_64'")
    n_feat = 0
    for row, feats in rows:
        con.execute(
            """INSERT OR IGNORE INTO instructions (arch, xml_file, heading, mnemonic, category,
               instr_class, iclass_names, brief, authored, op_notes, asm_templates,
               bitfields, decode_pseudocode, operation_pseudocode, operand_docs,
               page_start, source_doc, source_authority)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", row)
        iid = con.execute("SELECT id FROM instructions WHERE arch='x86_64' AND xml_file=?", (row[1],)).fetchone()
        if iid:
            for f in feats:
                con.execute("INSERT INTO instruction_features (instruction_id, feature_expr, arch_expr) VALUES (?,?,?)",
                            (iid[0], f"CPUID:{f}", "Intel-SDM opcode-table feature column"))
                n_feat += 1
    n = con.execute("SELECT COUNT(*) FROM instructions WHERE arch='x86_64'").fetchone()[0]
    from collections import Counter
    cats = Counter(r[0][4] for r in rows)
    con.execute("INSERT OR REPLACE INTO ingest_meta VALUES ('x86_intel_count', ?)", (str(n),))
    con.execute("INSERT OR REPLACE INTO ingest_meta VALUES ('x86_intel_feature_fills', ?)", (str(n_feat),))
    con.commit(); con.close()
    shutil.copyfile(tmp_db, db_path)
    os.unlink(tmp_db)
    print(f"[ingest] x86_64 rows: {n}, categories: {dict(cats)}, feature fills: {n_feat}")
    print(f"[ingest] db: {db_path} ({os.path.getsize(db_path)//1024} KiB)")


if __name__ == "__main__":
    sys.exit(main())
