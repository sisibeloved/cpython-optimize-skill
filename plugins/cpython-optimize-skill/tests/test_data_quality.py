#!/usr/bin/env python3
"""isa.db 全量数据质量回归: 串扰/FTS 同步/来源白名单/页码域/空字段。

固化自一次性全量诊断中零误报的检查项。带误报的检查(opcode 表首词族匹配、
"古老指令不应挂 feature"、跨指令 brief 相似度)不固化——多助记符标题、
cc 类标题和合法 feature 挂载(CMOV/LAHF/POPCNT/BMI2)会造成假阳性。
运行: python3 tests/test_data_quality.py
"""

from __future__ import annotations

import importlib.util
import re
import sqlite3
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "mcp" / "isa-reference" / "src" / "server.py"
DB = ROOT / "mcp" / "isa-reference" / "data" / "isa.db"


def load_server():
    spec = importlib.util.spec_from_file_location("isa_reference_server", SERVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(DB.exists(), "isa.db not built; run ingest scripts first")
class TestDataQuality(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = load_server()
        cls.con = cls.server.db()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()

    def test_pseudocode_cross_contamination(self):
        """切片串扰回归(SETcc 类): 串扰只可能来自同来源、页序紧邻的下一条指令,
        故只对紧邻下一条的伪代码开头段做尾部包含检测。页不相邻的指纹重叠
        (如 FSAVE 内嵌 FINIT 的重置序列)是官方伪代码的真实重复, 不算串扰。"""
        for arch in ("a64", "x86_64"):
            rows = self.con.execute(
                """SELECT id, heading, page_start, source_authority, operation_pseudocode
                   FROM instructions WHERE arch=? ORDER BY source_authority, page_start""", (arch,)).fetchall()
            for i, r in enumerate(rows):
                ps = r["operation_pseudocode"] or ""
                if len(ps) < 200 or i + 1 >= len(rows):
                    continue
                nxt = rows[i + 1]
                if nxt["source_authority"] != r["source_authority"]:
                    continue
                nxt_ps = (nxt["operation_pseudocode"] or "").strip()
                if len(nxt_ps) < 80:
                    continue
                fp = re.sub(r"\s+", " ", nxt_ps[:120])
                flat = re.sub(r"\s+", " ", ps)
                if fp in flat[150:]:
                    self.fail(f"[{arch}] '{r['heading']}' 伪代码尾部包含紧邻下一条 "
                              f"'{nxt['heading']}' 的开头段(切片串扰)")

    def test_fts_row_sync(self):
        n_instr = self.con.execute("SELECT COUNT(*) FROM instructions").fetchone()[0]
        n_fts = self.con.execute("SELECT COUNT(*) FROM instructions_fts").fetchone()[0]
        self.assertEqual(n_instr, n_fts, "FTS 外部内容表与主表行数失同步")

    def test_source_authority_whitelist(self):
        bad = self.con.execute(
            "SELECT COUNT(*) FROM instructions WHERE source_authority NOT IN"
            " ('ARM-official','Intel-SDM','AMD-APM')").fetchone()[0]
        self.assertEqual(bad, 0)

    def test_page_ranges(self):
        bad = self.con.execute("""SELECT COUNT(*) FROM instructions WHERE
            (arch='x86_64' AND source_authority='Intel-SDM' AND (page_start<597 OR page_start>=2799))
         OR (arch='x86_64' AND source_authority='AMD-APM' AND (page_start<123 OR page_start>=563))
         OR (arch='a64' AND page_start IS NOT NULL AND (page_start<15 OR page_start>5200))""").fetchone()[0]
        self.assertEqual(bad, 0, "存在页码超出该来源 PDF 指令区间的行")

    def test_empty_brief_budget(self):
        # 官方 PDF 中极少数指令页无独立 Description 段(如 TESTUI)
        n = self.con.execute(
            "SELECT COUNT(*) FROM instructions WHERE brief IS NULL OR brief=''").fetchone()[0]
        self.assertLessEqual(n, 2)

    def test_no_inverse_cpuid_conditions(self):
        """AMD 页内反向异常条件('CPUID Fn...[x]=0')不得作为 feature 入库。"""
        bad = self.con.execute(
            "SELECT COUNT(*) FROM instruction_features WHERE feature_expr LIKE '%=0%'").fetchone()[0]
        self.assertEqual(bad, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
