#!/usr/bin/env python3
"""isa-reference MCP server.

只读查询 isa.db(ARM 官方 A64 ISA XML ingest 产物; x86 待 Intel SDM / AMD APM ingest)。
数据层与知识层分离: 本 server 只做确定性查询, 决策与编排逻辑在 skill 层。

来源可靠性: 库内数据仅来自 source_authority 白名单(见
skills/isa-instruction-lookup/references/source-authority-policy.md)。
"""

import json
import os
import re
import sqlite3

from mcp.server.fastmcp import FastMCP

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "isa.db")

mcp = FastMCP("isa-reference")

SUMMARY_COLS = "i.id, i.arch, i.heading, i.mnemonic, i.category, i.instr_class, i.brief, i.page_start, i.source_doc, i.source_authority"
FULL_COLS = SUMMARY_COLS + ", i.authored, i.op_notes, i.asm_templates, i.bitfields, i.decode_pseudocode, i.operation_pseudocode, i.operand_docs, i.xml_file"


_CACHE_PATH = None


def db():
    """只读连接。本地路径直连; UNC/网络路径(锁不可用, 如 \\\\wsl.localhost 9P)降级为
    带 mtime 失效的本地缓存副本。"""
    global _CACHE_PATH
    path = os.path.abspath(DB_PATH)
    try:
        con = sqlite3.connect(path)
        con.execute("PRAGMA query_only=1")
        con.execute("SELECT count(*) FROM sqlite_master").fetchone()
        con.row_factory = sqlite3.Row
        return con
    except sqlite3.OperationalError:
        import shutil
        import tempfile
        if _CACHE_PATH is None or not os.path.exists(_CACHE_PATH) \
                or os.path.getmtime(path) > os.path.getmtime(_CACHE_PATH):
            if _CACHE_PATH and os.path.exists(_CACHE_PATH):
                os.unlink(_CACHE_PATH)
            fd, _CACHE_PATH = tempfile.mkstemp(suffix=".isa-reference.db")
            os.close(fd)
            shutil.copyfile(path, _CACHE_PATH)
        con = sqlite3.connect(_CACHE_PATH)
        con.execute("PRAGMA query_only=1")
        con.row_factory = sqlite3.Row
        return con


def row_to_dict(r, verbose=False):
    d = {k: r[k] for k in r.keys() if k not in ("authored", "op_notes", "asm_templates",
                                                "bitfields", "decode_pseudocode",
                                                "operation_pseudocode", "operand_docs")}
    if verbose:
        for k in ("authored", "op_notes", "decode_pseudocode", "operation_pseudocode"):
            d[k] = r[k]
        for k in ("asm_templates", "bitfields", "operand_docs"):
            try:
                d[k] = json.loads(r[k]) if r[k] else None
            except json.JSONDecodeError:
                d[k] = r[k]
    return d


def features_of(con, iid):
    return [{"feature_expr": r["feature_expr"], "arch_expr": r["arch_expr"]}
            for r in con.execute(
                "SELECT feature_expr, arch_expr FROM instruction_features WHERE instruction_id=?", (iid,))]


def ingested_archs(con):
    return [r[0] for r in con.execute("SELECT DISTINCT arch FROM instructions")]


def fts_query(text):
    """自然语言描述 -> FTS5 AND 查询; 单引号转义防止语法注入。"""
    terms = [t.replace('"', "") for t in re.findall(r"[A-Za-z0-9_+-]+", text) if t]
    return " AND ".join(f'"{t}"' for t in terms) if terms else '""'


@mcp.tool()
def lookup_instruction(mnemonic: str, arch: str = "a64", category: str = None,
                       verbose: bool = False) -> dict:
    """精确查一条指令: 返回编码、汇编语法、伪代码、feature 依赖与来源页码。

    mnemonic 接受助记符(如 CSEL)或完整标题(如 'ADD (extended register)')。
    同名指令存在跨执行域变体时(如 ABS 有 base/SIMD/SVE 三版), 用 category 消歧:
    base | simd_fp | sve | sme | system。verbose=True 返回位域与完整伪代码。
    """
    with db() as con:
        sql = f"SELECT {'i.authored, i.op_notes, i.asm_templates, i.bitfields, i.decode_pseudocode, i.operation_pseudocode, i.operand_docs, ' if verbose else ''}{SUMMARY_COLS} FROM instructions i WHERE i.arch=? AND (i.heading=? COLLATE NOCASE OR i.mnemonic=? COLLATE NOCASE)"
        args = [arch, mnemonic, mnemonic]
        if category:
            sql += " AND i.category=?"
            args.append(category)
        sql += " ORDER BY i.heading LIMIT 20"
        rows = con.execute(sql, args).fetchall()
        if not rows:
            return {"error": f"no instruction '{mnemonic}' under arch '{arch}'",
                    "ingested_archs": ingested_archs(con)}
        return {"count": len(rows),
                "instructions": [{**row_to_dict(r, verbose),
                                  "features": features_of(con, r["id"])} for r in rows]}


@mcp.tool()
def find_instruction_by_function(description: str, arch: str = "a64", limit: int = 10) -> dict:
    """按功能描述模糊检索指令(FTS 全文匹配 brief/authored)。

    适用于"想找做某件事的指令"但不知道助记符的场景, 如 description='conditional
    select' 命中 CSEL/CSINC/CSINV/CSNEG。描述应使用英文功能术语;
    优化意图(如'取代比较和分支')请先查 skill 的 optimization-intent-map.md 再用术语检索。
    """
    with db() as con:
        q = fts_query(description)
        rows = con.execute(
            f"""SELECT {SUMMARY_COLS} FROM instructions_fts f
                JOIN instructions i ON i.id=f.rowid
                WHERE instructions_fts MATCH ? AND i.arch=? ORDER BY rank LIMIT ?""",
            (q, arch, limit)).fetchall()
        return {"query": q, "count": len(rows),
                "instructions": [{**row_to_dict(r), "features": features_of(con, r["id"])}
                                 for r in rows]}


@mcp.tool()
def find_equivalent_instruction(mnemonic: str, from_arch: str = "a64",
                                to_arch: str = "x86_64", limit: int = 10) -> dict:
    """跨架构等价指令检索: 用 from_arch 侧指令的功能描述在 to_arch 侧做全文匹配。

    返回的是'候选等价指令', 精确等价性判断(语义/flag/副作用差异)由调用方
    结合双方伪代码完成。to_arch 未入库时明确报缺, 不编造结果。
    """
    with db() as con:
        archs = ingested_archs(con)
        if to_arch not in archs:
            return {"error": f"arch '{to_arch}' not ingested; available: {archs}",
                    "hint": "x86_64 requires Intel SDM / AMD APM ingest (planned)"}
        src = con.execute(
            f"SELECT {SUMMARY_COLS} FROM instructions i WHERE i.arch=? AND (i.heading=? COLLATE NOCASE OR i.mnemonic=? COLLATE NOCASE) LIMIT 1",
            (from_arch, mnemonic, mnemonic)).fetchone()
        if src is None:
            return {"error": f"source instruction '{mnemonic}' not found under '{from_arch}'"}
        # 跨架构词面通常只部分重叠('conditional move' vs 'conditional select'):
        # 优先用 heading 标题部分('CMOVcc—Conditional Move' -> 'Conditional Move')做查询——
        # 它是语义最浓缩的词; 无标题才退回 brief 实词。OR 连接、rank 排序,
        # 精确等价由调用方比对双方伪代码判定
        STOP = {"each", "of", "the", "a", "an", "and", "or", "in", "on", "if", "to", "for",
                "with", "is", "are", "this", "that", "by", "from", "into", "value", "values",
                "it", "its", "not", "these", "one", "two", "new", "as", "at", "be", "can",
                "instructions", "instruction", "performs", "operation", "operand", "operands",
                "uses", "using", "register", "registers", "memory", "bits", "bit"}
        title_part = ""
        for dash in ("—", "–", " - "):
            if dash in src["heading"]:
                title_part = src["heading"].split(dash, 1)[1]
                break
        source_text = title_part if title_part else (src["brief"] or "")
        mn = src["mnemonic"].lower()
        words, seen = [], set()
        for w in source_text.split():
            w = w.strip(".,;:()")
            if len(w) < 3 or w.lower() in seen or w.lower() in STOP or w.lower() in mn:
                continue
            seen.add(w.lower())
            words.append(w)
        q = " OR ".join(f'"{w}"' for w in words) if words else '""'
        rows = con.execute(
            f"""SELECT {SUMMARY_COLS} FROM instructions_fts f
                JOIN instructions i ON i.id=f.rowid
                WHERE instructions_fts MATCH ? AND i.arch=? ORDER BY rank LIMIT ?""",
            (q, to_arch, limit)).fetchall()
        return {"source": row_to_dict(src), "query": q, "count": len(rows),
                "candidates": [{**row_to_dict(r), "features": features_of(con, r["id"])}
                               for r in rows]}


@mcp.tool()
def list_features(arch: str = "a64") -> dict:
    """列出某架构已入库的所有 feature 表达式及依赖它们的指令数。

    A64 的 feature_expr 为 FEAT_xxx 布尔表达式(如 'FEAT_SVE || FEAT_SME'),
    语义: 实现任一满足分支即可用该指令。
    """
    with db() as con:
        rows = con.execute(
            """SELECT f.feature_expr, COUNT(DISTINCT f.instruction_id) n
               FROM instruction_features f JOIN instructions i ON i.id=f.instruction_id
               WHERE i.arch=? GROUP BY f.feature_expr ORDER BY n DESC""",
            (arch,)).fetchall()
        return {"arch": arch, "count": len(rows),
                "features": [{"feature_expr": r["feature_expr"], "instructions": r["n"]}
                             for r in rows]}


_FEAT_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def eval_feature_expr(expr: str, env_features: set):
    """求值 feature 布尔表达式。返回 True/False 或 'conditional'(表达式含非 FEAT 变量,
    如操作数字段 sz, 需结合具体编码判断)。表达式仅来自官方 XML, 标识符白名单 FEAT_*。"""
    idents = set(_FEAT_IDENT.findall(expr))
    if any(not i.startswith("FEAT_") for i in idents):
        return "conditional"
    py = expr.replace("&&", " and ").replace("||", " or ")
    py = re.sub(r"!(?=[A-Za-z_(])", " not ", py)
    env = {i: (i in env_features) for i in idents}
    return bool(eval(py, {"__builtins__": {}}, env))


@mcp.tool()
def filter_by_environment(env_features: list, arch: str = "a64",
                          mnemonic: str = None, limit: int = 50) -> dict:
    """给定目标环境已实现的 feature 列表, 判定指令可用性。

    env_features 形如 ['FEAT_CSSC','FEAT_LSE','FEAT_SVE2'](来自 /proc/cpuinfo
    或 ID_AA64* 系统寄存器解读, 见 cinderx-env-validate)。
    对全部指令返回 available/conditional/unavailable 统计; 传入 mnemonic 时
    只判定该指令。conditional 表示该指令的可用性还依赖操作数取值, 需人工判读。
    """
    env = set(env_features or [])
    with db() as con:
        sql = f"""SELECT {SUMMARY_COLS}, GROUP_CONCAT(f.feature_expr, char(31)) fe FROM instructions i
                  LEFT JOIN instruction_features f ON f.instruction_id=i.id"""
        where = ["i.arch=?"]
        args = [arch]
        if mnemonic:
            where.append("(i.heading=? COLLATE NOCASE OR i.mnemonic=? COLLATE NOCASE)")
            args += [mnemonic, mnemonic]
        sql += " WHERE " + " AND ".join(where) + " GROUP BY i.id ORDER BY i.heading LIMIT ?"
        args.append(limit if mnemonic else 5000)
        stats = {"available": [], "conditional": [], "unavailable": []}
        for r in con.execute(sql, args):
            exprs = [e.strip() for e in (r["fe"] or "").split("\x1f") if e.strip()]
            if not exprs:
                verdict = "available"  # baseline, 无条件可用
            else:
                results = [eval_feature_expr(e, env) for e in exprs]
                # 多行 feature 记录任一满足即可(官方 XML 同指令多 variant)
                if any(v is True for v in results):
                    verdict = "available"
                elif "conditional" in results:
                    verdict = "conditional"
                else:
                    verdict = "unavailable"
            stats[verdict].append({k: r[k] for k in ("heading", "mnemonic", "category", "brief", "page_start")})
        return {"arch": arch, "env_features": sorted(env),
                "counts": {k: len(v) for k, v in stats.items()},
                **({mnemonic: stats} if mnemonic else {"instructions": stats})}


if __name__ == "__main__":
    mcp.run()
