#!/usr/bin/env python3
"""Ingest AMD APM Vol.3 into isa.db (x86_64 侧补充).

两件事:
1. feature 回填(核心价值): AMD 指令页内的 "CPUID FnXXXX[FLAG]" 声明 +
   Appendix D Table D-1 (flag <-> 指令/子集) -> 为已入库 x86_64 指令(含 Intel
   行)填 instruction_features。x86 指令集两家兼容, 此映射对两源指令统一生效,
   但记录 arch_expr 标注来源为 AMD-APM Appendix D / 页内声明。
2. AMD 特有指令入库: Ch3/Ch4 L2 书签中未与 Intel 重叠的指令,
   source_authority='AMD-APM'。

用法:
  python3 ingest_x86_apm.py --pdf <24594_3.38_APM_Vol3.pdf> [--db <isa.db>]
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import tempfile

import fitz

SOURCE_DOC = "AMD_APM_Vol3_24594_r3.38"
SOURCE_AUTHORITY = "AMD-APM"

CH3_RANGE = (123, 419)   # General-Purpose Instruction Reference (L2 指令书签)
CH4_RANGE = (421, 563)   # System Instruction Reference

# 正向 feature 声明: 'CPUID FnXXXX[FLAG] = 1'(Exceptions 表的反向条件是 '= 0', 不得入库)
CPUID_FLAG = re.compile(r"CPUID\s*\n?Fn([0-9A-FX_]+)\[([A-Za-z0-9]+)\]\s*=\s*1")
AMD_PAGE_HEADER = re.compile(r"^(\d+|General-Purpose|System|Instruction Reference|AMD64 Technology|24594—Rev.*|Appendix [A-F].*|[A-Z]\.\d)$")

SECTION_HEADS = re.compile(
    r"^(Operation|Action|Description|Flags Affected|Rflags|Exceptions|Pseudocode|"
    r"Virtual-?Mode|Real-?Address|Protected Mode|Legacy|Compatibility)\b")


def norm_mn(s: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", s.upper())


def page_flags(doc, p0, p1, stop_title=None):
    """扫页内 CPUID 声明。相邻指令共享页面时, 文本截断到下一指令标题行,
    防止吃到邻页指令的声明(如 SETcc 页溢出扫到 SFENCE 的 SSE)。"""
    text = "\n".join(doc[p].get_text() for p in range(p0, p1))
    if stop_title:
        m = re.search(rf"^\s*{re.escape(stop_title.split()[0])}\s*$", text, re.M)
        if m:
            text = text[:m.start()]
    return [(f"Fn{m.group(1)}[{m.group(2)}]", m.group(2)) for m in CPUID_FLAG.finditer(text)]


def parse_amd_page(doc, p0, p1):
    text = "\n".join(doc[p].get_text() for p in range(p0, p1))
    lines = [l.strip() for l in text.splitlines()]
    body, oper = [], []
    mode = "body"
    for s in lines:
        if not s or AMD_PAGE_HEADER.match(s):
            continue
        if SECTION_HEADS.match(s) and len(s) < 40:
            mode = "oper" if s.startswith(("Operation", "Action", "Pseudocode")) else "skip"
            continue
        if s.startswith(("Mnemonic", "Opcode")):
            mode = "skip"
            continue
        if mode == "body":
            body.append(s)
        elif mode == "oper":
            oper.append(s)
    desc = " ".join(body)
    return desc[:280].strip(), "\n".join(oper).strip()


def parse_appendix_d(doc):
    """Table D-1: flag -> 指令名列表(仅可枚举条目)。"""
    text = "\n".join(doc[p].get_text() for p in range(660, 669))
    lines = [l.strip() for l in text.splitlines()]
    mapping = {}
    FUNC_TOKEN = re.compile(r"^(standard|extended|0000_0007_\d)$")
    BIT_TOKEN = re.compile(r"^[ECXBDX]{3}\[\d+\]")
    i, n = 0, len(lines)
    while i < n:
        s = lines[i]
        # flag 名行: 短、无空格、字母数字, 后随指令列表与 function/bit 行
        if (1 < len(s) <= 16 and re.match(r"^[A-Za-z0-9!]+$", s)
                and not FUNC_TOKEN.match(s) and not BIT_TOKEN.match(s)
                and i + 2 < n and FUNC_TOKEN.match(lines[i + 2] or "")):
            flag = s
            instrs_raw = lines[i + 1]
            j = i + 2
            while j < n and not FUNC_TOKEN.match(lines[j] or ""):
                instrs_raw += " " + lines[j]
                j += 1
            # 到 function/bit 为止的行都是 instruction/subset 描述
            for tok in re.split(r"[,/]| or ", instrs_raw):
                tok = tok.strip()
                if tok and re.match(r"^[A-Z][A-Za-z0-9!]{1,10}$", tok):
                    mapping.setdefault(flag, set()).add(tok)
            i = j + 1
            continue
        i += 1
    return mapping


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pdf", required=True)
    ap.add_argument("--db", default=os.path.join(os.path.dirname(__file__), "..", "data", "isa.db"))
    args = ap.parse_args()

    doc = fitz.open(args.pdf)
    toc = doc.get_toc()

    # ---- 1. 页内 flag 声明: heading -> [(cupid_expr, flag)]
    l2 = [(t, p) for l, t, p in toc if l == 2 and (CH3_RANGE[0] <= p < CH3_RANGE[1] or CH4_RANGE[0] <= p < CH4_RANGE[1])]
    # 过滤非指令书签(节号/小写)
    instr_entries = [(t, p) for t, p in l2 if not re.match(r"^\d+\.\d", t)]
    print(f"[apm] instruction bookmarks: {len(instr_entries)}")

    page_flag_map = {}   # norm_mn(heading) -> [(expr, flag)]
    for j, (title, page) in enumerate(instr_entries):
        nxt = instr_entries[j + 1][1] if j + 1 < len(instr_entries) else page + 2
        nxt_stop = instr_entries[j + 1][0].split()[0] if j + 1 < len(instr_entries) else None
        flags = page_flags(doc, page - 1, nxt - 1 if nxt > page else page, stop_title=nxt_stop)
        if flags:
            page_flag_map.setdefault(norm_mn(title.split()[0]), []).extend(flags)

    # ---- 2. Appendix D 表
    d_map = parse_appendix_d(doc)
    print(f"[apm] page-declared: {len(page_flag_map)} mnemonics; Appendix D flags: {len(d_map)}")

    import shutil
    db_path = os.path.abspath(args.db)
    fd, tmp_db = tempfile.mkstemp(suffix=".db")
    os.close(fd); os.unlink(tmp_db)
    shutil.copyfile(db_path, tmp_db)
    con = sqlite3.connect(tmp_db)
    con.row_factory = sqlite3.Row

    # 幂等: 清除本脚本此前写入的行(Intel 行不动)
    con.execute("""DELETE FROM instruction_features WHERE arch_expr NOT LIKE 'Intel-SDM%'
                   AND instruction_id IN (SELECT id FROM instructions WHERE arch='x86_64')""")
    con.execute("DELETE FROM instructions WHERE arch='x86_64' AND source_authority='AMD-APM'")

    # intel 库存: id, heading, mnemonic 归一
    x86 = {norm_mn(r["mnemonic"]): r["id"] for r in
           con.execute("SELECT id, mnemonic, heading FROM instructions WHERE arch='x86_64'")}
    intel_heads = x86.keys()

    # ---- 3a. 页内声明回填
    n_fill = 0
    for mn, flags in page_flag_map.items():
        iid = x86.get(mn)
        if not iid:
            continue
        for expr, flag in set(flags):
            con.execute("INSERT INTO instruction_features (instruction_id, feature_expr, arch_expr) VALUES (?,?,?)",
                        (iid, f"CPUID:{flag}", expr))
            n_fill += 1

    # ---- 3b. Appendix D 回填(未覆盖的)
    n_fill_d = 0
    for flag, instrs in d_map.items():
        for ins in instrs:
            iid = x86.get(norm_mn(ins))
            if not iid:
                continue
            exists = con.execute(
                "SELECT 1 FROM instruction_features WHERE instruction_id=? AND feature_expr=?",
                (iid, f"CPUID:{flag}")).fetchone()
            if not exists:
                con.execute("INSERT INTO instruction_features (instruction_id, feature_expr, arch_expr) VALUES (?,?,?)",
                            (iid, f"CPUID:{flag}", f"AMD-APM AppxD:{flag}"))
                n_fill_d += 1

    # ---- 4. AMD 特有指令入库
    n_new = 0
    for j, (title, page) in enumerate(instr_entries):
        first = title.split()[0]
        if norm_mn(first) in intel_heads:
            continue
        nxt = instr_entries[j + 1][1] if j + 1 < len(instr_entries) else page + 2
        brief, oper = parse_amd_page(doc, page - 1, nxt - 1 if nxt > page else page)
        if not brief:
            continue
        cat = "system" if CH4_RANGE[0] <= page < CH4_RANGE[1] else "base"
        cur = con.execute(
            """INSERT OR IGNORE INTO instructions (arch, xml_file, heading, mnemonic, category,
               instr_class, iclass_names, brief, authored, op_notes, asm_templates,
               bitfields, decode_pseudocode, operation_pseudocode, operand_docs,
               page_start, source_doc, source_authority)
               VALUES ('x86_64',?,?,?,?,NULL,'[]',?,NULL,NULL,'[]',NULL,NULL,?,NULL,?,?,?)""",
            (f"{SOURCE_DOC}#p{page}", title, first, cat, brief, oper, page, SOURCE_DOC, SOURCE_AUTHORITY))
        if cur.rowcount:
            n_new += 1
            iid = cur.lastrowid
            for expr, flag in set(page_flag_map.get(norm_mn(first), [])):
                con.execute("INSERT INTO instruction_features (instruction_id, feature_expr, arch_expr) VALUES (?,?,?)",
                            (iid, f"CPUID:{flag}", expr))

    con.execute("INSERT OR REPLACE INTO ingest_meta VALUES ('x86_amd_only_count', ?)", (str(n_new),))
    con.execute("INSERT OR REPLACE INTO ingest_meta VALUES ('x86_feature_rows', ?)",
                (str(con.execute("SELECT COUNT(*) FROM instruction_features f JOIN instructions i ON i.id=f.instruction_id WHERE i.arch='x86_64'").fetchone()[0]),))
    con.commit()

    total = con.execute("SELECT COUNT(*) FROM instructions WHERE arch='x86_64'").fetchone()[0]
    feat = con.execute("SELECT COUNT(*) FROM instruction_features f JOIN instructions i ON i.id=f.instruction_id WHERE i.arch='x86_64'").fetchone()[0]
    con.close()
    shutil.copyfile(tmp_db, db_path)
    os.unlink(tmp_db)
    print(f"[apm] page-flag fills: {n_fill}, AppD fills: {n_fill_d}, AMD-only instrs: {n_new}")
    print(f"[apm] x86_64 total: {total} instrs, {feat} feature rows")
    print(f"[apm] db: {db_path} ({os.path.getsize(db_path)//1024} KiB)")


if __name__ == "__main__":
    sys.exit(main())
