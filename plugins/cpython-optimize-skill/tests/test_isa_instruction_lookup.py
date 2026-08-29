#!/usr/bin/env python3
"""isa-instruction-lookup 检索质量与数据可靠性回归测试。

核心用例: 优化意图"用条件选择取代比较和分支"必须经 FTS 命中 CSEL 族(Q2 场景)。
运行: python3 tests/test_isa_instruction_lookup.py
"""

from __future__ import annotations

import importlib.util
import sys
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


@unittest.skipUnless(DB.exists(), "isa.db not built; run ingest_a64_xml.py first")
class TestISAInstructionLookup(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.server = load_server()
        cls.con = cls.server.db()

    @classmethod
    def tearDownClass(cls):
        cls.con.close()

    def test_db_basic_integrity(self):
        n = self.con.execute("SELECT COUNT(*) FROM instructions").fetchone()[0]
        self.assertGreater(n, 3000)
        bad = self.con.execute(
            "SELECT COUNT(*) FROM instructions WHERE source_authority NOT IN ('ARM-official','Intel-SDM','AMD-APM')").fetchone()[0]
        self.assertEqual(bad, 0, "non-whitelisted source leaked into db")
        # brief 为空的指令: 官方 PDF 里极少数指令页无独立 Description 段(如 TESTUI)
        nofeat = self.con.execute(
            "SELECT COUNT(*) FROM instructions WHERE brief IS NULL OR brief=''").fetchone()[0]
        self.assertLessEqual(nofeat, 2)

    def test_q2_conditional_select_hits_csel_family(self):
        """优化意图'条件选择取代比较分支' → FTS 'conditional select' 必须命中 CSEL 族。"""
        res = self.server.find_instruction_by_function("conditional select")
        headings = [i["heading"] for i in res["instructions"]]
        for must in ("CSEL", "CSNEG", "CSINV", "CSINC"):
            self.assertIn(must, headings, f"FTS missed {must}; got {headings}")
        self.assertEqual(headings[0], "CSEL", "CSEL must rank first")

    def test_lookup_csel_verbose_payload(self):
        res = self.server.lookup_instruction("CSEL", verbose=True)
        self.assertEqual(res["count"], 1)
        ins = res["instructions"][0]
        self.assertEqual(ins["category"], "base")
        self.assertGreater(ins["page_start"], 0)
        self.assertIn("condition", ins["operation_pseudocode"].lower())
        self.assertTrue(ins["asm_templates"], "missing asm syntax")
        feats = [f["feature_expr"] for f in ins["features"]]
        self.assertTrue(any("FEAT_" in f for f in feats) or not feats)

    def test_lookup_disambiguates_same_name_variants(self):
        res = self.server.lookup_instruction("ABS")
        cats = {i["category"] for i in res["instructions"]}
        self.assertEqual(cats, {"base", "simd_fp", "sve"})
        res_base = self.server.lookup_instruction("ABS", category="base")
        self.assertEqual(res_base["count"], 1)
        feats = [f["feature_expr"] for f in res_base["instructions"][0]["features"]]
        self.assertIn("FEAT_CSSC", feats)

    def test_feature_expr_evaluation(self):
        ev = self.server.eval_feature_expr
        self.assertIs(ev("FEAT_CSSC", {"FEAT_CSSC"}), True)
        self.assertIs(ev("FEAT_CSSC", {"FEAT_LSE"}), False)
        self.assertIs(ev("FEAT_SVE || FEAT_SME", {"FEAT_SME"}), True)
        self.assertIs(ev("(FEAT_SVE || FEAT_SME) && FEAT_BF16", {"FEAT_SVE"}), False)
        self.assertEqual(ev("FEAT_SME2 && (sz == '0' || FEAT_SME_F64F64)", set()), "conditional")

    def test_filter_by_environment(self):
        res = self.server.filter_by_environment(env_features=["FEAT_CSSC"], mnemonic="ABS")
        verdicts = res["ABS"]
        base_abs = [i for i in verdicts["available"] if i["category"] == "base"]
        self.assertTrue(base_abs, "ABS (base) must be available under FEAT_CSSC")
        sve_abs = [i for i in verdicts["unavailable"] if i["category"] == "sve"]
        self.assertTrue(sve_abs, "ABS (sve) must be unavailable without FEAT_SVE")

    def test_equivalent_reports_missing_arch_honestly(self):
        res = self.server.find_equivalent_instruction("CSEL", from_arch="a64", to_arch="riscv64")
        self.assertIn("error", res)
        self.assertIn("not ingested", res["error"])

    def test_x86_lookup_cmovcc(self):
        res = self.server.lookup_instruction("CMOVcc", arch="x86_64")
        self.assertGreaterEqual(res["count"], 1)
        ins = res["instructions"][0]
        self.assertEqual(ins["source_authority"], "Intel-SDM")
        self.assertGreater(ins["page_start"], 0)

    def test_x86_bmi2_feature_family(self):
        with self.con as c:
            rows = [r[0] for r in c.execute(
                """SELECT DISTINCT i.heading FROM instructions i JOIN instruction_features f
                   ON f.instruction_id=i.id WHERE i.arch='x86_64' AND f.feature_expr='CPUID:BMI2'""")]
        heads = {h.split("—")[0] for h in rows}
        for must in ("MULX", "PDEP", "PEXT"):
            self.assertTrue(any(must in h for h in heads), f"BMI2 missing {must}: {heads}")

    def test_cross_platform_csel_to_cmovcc(self):
        """CSEL(a64) 的 x86 侧等价候选必须包含 CMOVcc。"""
        res = self.server.find_equivalent_instruction("CSEL", from_arch="a64", to_arch="x86_64", limit=15)
        heads = [c["heading"] for c in res["candidates"]]
        self.assertTrue(any(h.startswith("CMOVcc") for h in heads),
                        f"CMOVcc not in candidates: {heads[:8]}")

    def test_amd_only_instructions_present(self):
        with self.con as c:
            n = c.execute("SELECT COUNT(*) FROM instructions WHERE arch='x86_64' AND source_authority='AMD-APM'").fetchone()[0]
        self.assertGreater(n, 50, "AMD-APM specific instructions missing")

    def test_fts_query_sanitizes_input(self):
        """恶意输入不得破坏 FTS 语法; 词被引号包裹后作为普通 term 是安全的。"""
        malicious = 'conditional"; DROP TABLE instructions;--'
        res = self.server.find_instruction_by_function(malicious)  # must not raise
        self.assertGreaterEqual(res["count"], 0)
        self.assertIn('"conditional"', res["query"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
