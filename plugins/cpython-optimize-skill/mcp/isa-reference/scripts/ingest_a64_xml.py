#!/usr/bin/env python3
"""Ingest ARM official A64 ISA XML (instructionsection files) into isa.db.

数据源: ARM 官方发布的 ISA_A64_xml_A_profile 包(双层 tar)。
只灌"当前版主目录"根下的指令 XML; diff 基线目录(旧版本)和 xhtml 渲染目录一律不入库,
防止新旧版本混灌。来源可靠性规则见 skills/isa-instruction-lookup/references/source-authority-policy.md。

用法:
  python3 ingest_a64_xml.py --tar <内层tar文件或包含它的目录> [--pdf <对应PDF>] [--db <输出db>]

  --pdf 可选: 读取 PDF 书签(TOC level-2)建立 heading -> 页码 映射, 仅用于人类回溯。
"""

import argparse
import glob
import json
import os
import sqlite3
import sys
import tarfile
import xml.etree.ElementTree as ET
from collections import Counter

CATEGORY_MAP = {
    "general": "base",
    "advsimd": "simd_fp",
    "fpsimd": "simd_fp",
    "float": "simd_fp",
    "sve": "sve",
    "sve2": "sve",
    "mortlach": "sme",
    "mortlach2": "sme",
    "system": "system",
}

SOURCE_DOC = "ISA_A64_xml_A_profile-2026-06_mc"
SOURCE_AUTHORITY = "ARM-official"

SCHEMA = """
CREATE TABLE IF NOT EXISTS instructions (
  id                 INTEGER PRIMARY KEY,
  arch               TEXT NOT NULL,
  xml_file           TEXT NOT NULL,
  heading            TEXT NOT NULL,
  mnemonic           TEXT NOT NULL,
  category           TEXT NOT NULL,
  instr_class        TEXT,
  iclass_names       TEXT,
  brief              TEXT NOT NULL,
  authored           TEXT,
  op_notes           TEXT,
  asm_templates      TEXT,
  bitfields          TEXT,
  decode_pseudocode  TEXT,
  operation_pseudocode TEXT,
  operand_docs       TEXT,
  page_start         INTEGER,
  source_doc         TEXT NOT NULL,
  source_authority   TEXT NOT NULL,
  UNIQUE(arch, xml_file)
);
-- 注: 同一 heading 在不同执行域存在同名变体(如 ABS 的 base/SIMD/SVE 三版, xml 文件不同),
-- 查询时用 heading+category 定位; 页码映射仅对无歧义 heading 填写。
CREATE INDEX IF NOT EXISTS idx_instructions_mnemonic ON instructions(mnemonic);
CREATE INDEX IF NOT EXISTS idx_instructions_category ON instructions(category);

CREATE TABLE IF NOT EXISTS instruction_features (
  instruction_id INTEGER NOT NULL REFERENCES instructions(id),
  feature_expr   TEXT,
  arch_expr      TEXT
);
CREATE INDEX IF NOT EXISTS idx_features_expr ON instruction_features(feature_expr);

CREATE TABLE IF NOT EXISTS ingest_meta (
  key TEXT PRIMARY KEY,
  value TEXT
);

CREATE VIRTUAL TABLE IF NOT EXISTS instructions_fts USING fts5(
  heading, mnemonic, brief, authored,
  content='instructions', content_rowid='id', tokenize='porter unicode61'
);
CREATE TRIGGER IF NOT EXISTS instructions_ai AFTER INSERT ON instructions BEGIN
  INSERT INTO instructions_fts(rowid, heading, mnemonic, brief, authored)
  VALUES (new.id, new.heading, new.mnemonic, new.brief, new.authored);
END;
CREATE TRIGGER IF NOT EXISTS instructions_ad AFTER DELETE ON instructions BEGIN
  INSERT INTO instructions_fts(instructions_fts, rowid, heading, mnemonic, brief, authored)
  VALUES ('delete', old.id, old.heading, old.mnemonic, old.brief, old.authored);
END;
"""


def find_inner_tar(path: str) -> str:
    """接受内层 tar 文件路径, 或包含它的目录。"""
    if os.path.isfile(path):
        return path
    cands = sorted(glob.glob(os.path.join(path, "*.tar")))
    if not cands:
        raise SystemExit(f"no inner .tar found under {path}")
    return cands[0]


def pick_main_dir(t: tarfile.TarFile, tar_stem: str) -> str:
    """主目录 = 与内层 tar 同名的顶层目录; 找不到则取指令 XML 最多的目录。"""
    tops = Counter()
    for m in t.getmembers():
        if m.name.endswith(".xml"):
            tops[m.name.split("/")[0]] += 1
    if tar_stem in tops:
        return tar_stem
    ranked = sorted(tops.items(), key=lambda kv: -kv[1])
    print(f"[warn] dir matching tar stem not found, falling back to {ranked[0][0]}")
    return ranked[0][0]


def txt(el) -> str:
    return "".join(el.itertext()).strip() if el is not None else ""


def paras(el) -> str:
    if el is None:
        return ""
    return "\n".join("".join(p.itertext()).strip() for p in el.findall(".//para")).strip()


def parse_instruction(xml_name: str, data: str):
    root = ET.fromstring(data)
    if root.tag != "instructionsection":
        return None

    heading = txt(root.find("heading"))

    docvars = root.find("docvars")
    mnemonic = heading.split()[0] if heading else xml_name
    instr_class = None
    if docvars is not None:
        for dv in docvars.findall("docvar"):
            if dv.get("key") == "mnemonic":
                mnemonic = dv.get("value")
            elif dv.get("key") == "instr-class":
                instr_class = dv.get("value")
    category = CATEGORY_MAP.get(instr_class, instr_class or "base")

    desc = root.find("desc")
    brief = paras(desc.find("brief") if desc is not None else None)
    authored = paras(desc.find("authored") if desc is not None else None)
    op_notes = paras(root.find("operationalnotes"))

    iclass_names, asm_templates, bitfields, features = [], [], [], []
    decode_parts, operation_parts = [], []

    for ps in root.iter("ps_section"):
        for p in ps.findall("ps"):
            section = p.get("rep_section") or p.get("secttype") or ""
            body = txt(p.find("pstext"))
            if not body:
                continue
            if section == "decode":
                decode_parts.append(f"-- {p.get('name')}\n{body}")
            else:
                operation_parts.append(f"-- {p.get('name')}\n{body}")

    for iclass in root.iter("iclass"):
        name = iclass.get("name")
        if name:
            iclass_names.append(name)
        for av in iclass.findall("./arch_variants/arch_variant"):
            features.append((av.get("feature"), av.get("name")))
        for rd in iclass.findall("regdiagram"):
            boxes = []
            for box in rd.findall("box"):
                bits = "".join(c.text or "x" for c in box.findall("c"))
                boxes.append({
                    "name": box.get("name"),
                    "hibit": int(box.get("hibit")),
                    "width": int(box.get("width") or 1),
                    "bits": bits,
                })
            bitfields.append({"psname": rd.get("psname"), "boxes": boxes})
        for enc in iclass.findall("encoding"):
            asm = enc.find("asmtemplate")
            asm_templates.append({
                "name": enc.get("name"),
                "label": enc.get("label"),
                "bitdiffs": enc.get("bitdiffs"),
                "syntax": "".join(asm.itertext()).strip() if asm is not None else None,
            })

    # 顶层 arch_variant(不在 iclass 内的罕见情形)
    for av in root.findall("./classes/arch_variants/arch_variant"):
        pass  # classes 下直接挂 arch_variants 的情形已由 iclass 迭代覆盖

    operand_docs = []
    for exp in root.iter("explanation"):
        sym = exp.find("symbol")
        acct = exp.find("account")
        if sym is None:
            continue
        operand_docs.append({
            "symbol": "".join(sym.itertext()).strip(),
            "encoded_in": acct.get("encodedin") if acct is not None else None,
            "doc": paras(acct.find("intro") if acct is not None else None),
        })

    commit = root.findtext("commit_id")
    ts = root.findtext("timestamp")

    return {
        "xml_file": xml_name,
        "heading": heading,
        "mnemonic": mnemonic,
        "category": category,
        "instr_class": instr_class,
        "iclass_names": sorted(set(iclass_names)),
        "brief": brief,
        "authored": authored,
        "op_notes": op_notes,
        "asm_templates": asm_templates,
        "bitfields": bitfields,
        "decode_pseudocode": "\n\n".join(decode_parts),
        "operation_pseudocode": "\n\n".join(operation_parts),
        "operand_docs": operand_docs,
        "features": features,
        "commit_id": commit,
        "timestamp": ts,
    }


def norm(s: str) -> str:
    return " ".join(s.lower().split())


def pdf_toc_pages(pdf_path: str):
    """PDF 书签 level-2 -> 页码 映射(规范化标题)。"""
    try:
        import fitz
    except ImportError:
        print("[warn] PyMuPDF not installed, skipping page mapping")
        return {}
    pages = {}
    for lvl, title, page in fitz.open(pdf_path).get_toc():
        if lvl == 2:
            pages.setdefault(norm(title), page)
    return pages


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tar", required=True, help="inner tar file or dir containing it")
    ap.add_argument("--pdf", help="optional PDF for heading->page mapping")
    ap.add_argument("--db", default=os.path.join(os.path.dirname(__file__), "..", "data", "isa.db"))
    args = ap.parse_args()

    inner = find_inner_tar(args.tar)
    tar_stem = os.path.splitext(os.path.basename(inner))[0]
    print(f"[ingest] tar: {inner}")
    print(f"[ingest] main dir: {tar_stem}")

    pages = pdf_toc_pages(args.pdf) if args.pdf else {}
    if pages:
        print(f"[ingest] pdf toc level-2 entries: {len(pages)}")

    db_path = os.path.abspath(args.db)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    # UNC/网络路径上 SQLite 锁不可用(如 \\wsl.localhost 9P): 先写本地临时库, 成功后拷回目标
    import shutil
    import tempfile
    tmp_fd, tmp_db = tempfile.mkstemp(suffix=".db")
    os.close(tmp_fd)
    os.unlink(tmp_db)
    con = sqlite3.connect(tmp_db)
    con.executescript(SCHEMA)

    t = tarfile.open(inner, "r:")
    main_dir = pick_main_dir(t, tar_stem)
    rows, feat_rows, commits, misses = [], [], Counter(), 0

    members = [m for m in t.getmembers()
               if m.name.endswith(".xml")
               and m.name.startswith(main_dir + "/")
               and "/" not in m.name[len(main_dir) + 1:]]  # 仅主目录根下, 排除 xhtml/ 与 diff/
    print(f"[ingest] candidate xml under main dir root: {len(members)}")

    for m in members:
        f = t.extractfile(m)
        if f is None:
            continue
        data = f.read().decode("utf-8", "replace")
        if "<instructionsection" not in data:
            continue
        rec = parse_instruction(m.name.rsplit("/", 1)[-1], data)
        if rec is None or not rec["heading"] or not rec["brief"]:
            misses += 1
            continue
        commits[rec["commit_id"]] += 1
        page = pages.get(norm(rec["heading"]))
        rows.append((
            "a64", rec["xml_file"], rec["heading"], rec["mnemonic"], rec["category"],
            rec["instr_class"], json.dumps(rec["iclass_names"]),
            rec["brief"], rec["authored"], rec["op_notes"],
            json.dumps(rec["asm_templates"]), json.dumps(rec["bitfields"]),
            rec["decode_pseudocode"], rec["operation_pseudocode"],
            json.dumps(rec["operand_docs"]),
            page, SOURCE_DOC, SOURCE_AUTHORITY,
        ))
        feat_rows.append((rec["xml_file"], rec["features"]))
    feats_by_file = dict(feat_rows)

    # 同名 heading(跨执行域变体)不填页码, 避免误指
    hc = Counter(r[2] for r in rows)
    rows = [r[:15] + (r[15] if hc[r[2]] == 1 else None,) + r[16:] for r in rows]

    con.execute("DELETE FROM instruction_features WHERE instruction_id IN (SELECT id FROM instructions WHERE arch='a64')")
    con.execute("DELETE FROM instructions WHERE arch='a64'")

    cur = con.cursor()
    for row in rows:
        cur.execute(
            """INSERT INTO instructions (arch, xml_file, heading, mnemonic, category,
               instr_class, iclass_names, brief, authored, op_notes, asm_templates,
               bitfields, decode_pseudocode, operation_pseudocode, operand_docs,
               page_start, source_doc, source_authority)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", row)
        feats = feats_by_file.get(row[1], [])
        for feat, archx in feats:
            if feat or archx:
                cur.execute(
                    "INSERT INTO instruction_features (instruction_id, feature_expr, arch_expr) "
                    "SELECT id, ?, ? FROM instructions WHERE arch='a64' AND heading=?",
                    (feat, archx, row[2]))

    meta = {
        "a64_source_doc": SOURCE_DOC,
        "a64_source_authority": SOURCE_AUTHORITY,
        "a64_commit_id": commits.most_common(1)[0][0] if commits else None,
        "a64_instruction_count": str(len(rows)),
        "a64_page_mapped": str(sum(1 for r in rows if r[15])),
        "a64_baseline_count": "computed_at_query_time",
    }
    con.executemany("INSERT OR REPLACE INTO ingest_meta (key, value) VALUES (?,?)", meta.items())
    con.commit()

    cats = Counter(r[4] for r in rows)
    withfeat = sum(1 for _, fl in feat_rows if fl)
    print(f"[ingest] instructions: {len(rows)} (skipped {misses})")
    print(f"[ingest] categories: {dict(cats)}")
    print(f"[ingest] with arch_variant: {withfeat}, baseline: {len(rows) - withfeat}")
    print(f"[ingest] page-mapped: {meta['a64_page_mapped']}")
    con.close()

    shutil.copyfile(tmp_db, db_path)
    os.unlink(tmp_db)
    print(f"[ingest] db: {db_path} ({os.path.getsize(db_path)//1024} KiB)")


if __name__ == "__main__":
    sys.exit(main())
