#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "pyperformance-stat-report" / "scripts" / "get_stat.py"


class PyperformanceStatReportTests(unittest.TestCase):
    def test_console_only_compares_common_benchmarks_without_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            baseline = workdir / "baseline.json"
            candidate = workdir / "candidate.json"
            baseline.write_text(
                json.dumps(
                    {
                        "benchmarks": [
                            {"metadata": {"name": "bm_alpha"}, "runs": [{"values": [1.0, 1.2]}]},
                            {"metadata": {"name": "bm_beta"}, "runs": [{"values": [0.002, 0.004]}]},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            candidate.write_text(
                json.dumps(
                    {
                        "benchmarks": [
                            {"metadata": {"name": "bm_alpha"}, "runs": [{"values": [0.5, 0.6]}]},
                            {"metadata": {"name": "bm_beta"}, "runs": [{"values": [0.001, 0.002]}]},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "-c", str(baseline), str(candidate)],
                cwd=workdir,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                env=env,
            )

            self.assertEqual(result.returncode, 0, (result.stderr or "") + (result.stdout or ""))
            self.assertIn("bm_alpha", result.stdout)
            self.assertIn("bm_beta", result.stdout)
            self.assertIn("baseline.json", result.stdout)
            self.assertIn("candidate.json", result.stdout)
            self.assertFalse((workdir / "benchmark_comparison.xlsx").exists())
            self.assertEqual(list(workdir.glob("benchmark_trends_part*.png")), [])


if __name__ == "__main__":
    unittest.main()
