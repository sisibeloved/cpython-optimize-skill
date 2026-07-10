#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "pyperformance-stat-report" / "scripts" / "get_stat.py"


def load_script_module():
    spec = importlib.util.spec_from_file_location("pyperformance_stat_report_get_stat", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_result(path: Path, benchmarks: dict[str, float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "benchmarks": [
                    {"metadata": {"name": name}, "runs": [{"values": [value]}]}
                    for name, value in benchmarks.items()
                ]
            }
        ),
        encoding="utf-8",
    )


@contextmanager
def working_directory(path: Path):
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


class PyperformanceStatReportTests(unittest.TestCase):
    def run_script(self, args: list[str], workdir: Path) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=workdir,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            env=env,
        )

    def assert_no_report_artifacts(self, workdir: Path) -> None:
        self.assertFalse((workdir / "benchmark_comparison.xlsx").exists())
        self.assertEqual(list(workdir.glob("benchmark_trends_part*.png")), [])

    def test_console_only_compares_common_benchmarks_without_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            baseline = workdir / "baseline.json"
            candidate = workdir / "candidate.json"
            write_result(baseline, {"bm_alpha": 1.1, "bm_beta": 0.003})
            write_result(candidate, {"bm_alpha": 0.55, "bm_beta": 0.0015})

            result = self.run_script(["-c", str(baseline), str(candidate)], workdir)

            self.assertEqual(result.returncode, 0, (result.stderr or "") + result.stdout)
            self.assertIn("bm_alpha", result.stdout)
            self.assertIn("bm_beta", result.stdout)
            self.assertIn("baseline.json", result.stdout)
            self.assertIn("candidate.json", result.stdout)
            self.assertRegex(
                result.stdout,
                r"性能对比\s+NA\s+1\.0000\s+2\.0000",
            )
            self.assert_no_report_artifacts(workdir)

    def test_documented_absolute_script_and_repeated_benchmarks_from_unrelated_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report_dir = root / "report-output"
            report_dir.mkdir()
            baseline = root / "inputs" / "baseline" / "run.json"
            candidate = root / "inputs" / "candidate" / "run.json"
            write_result(baseline, {"bm_alpha": 1.0, "bm_beta": 2.0})
            write_result(candidate, {"bm_alpha": 0.5, "bm_beta": 1.0})

            result = self.run_script(
                [
                    "-c",
                    "-b",
                    "bm_beta",
                    "-b",
                    "bm_alpha",
                    str(baseline),
                    str(candidate),
                ],
                report_dir,
            )

            self.assertEqual(result.returncode, 0, (result.stderr or "") + result.stdout)
            benchmark_rows = [line for line in result.stdout.splitlines() if line.startswith("bm_")]
            self.assertEqual([line.split()[0] for line in benchmark_rows], ["bm_beta", "bm_alpha"])
            self.assertIn(str(Path("baseline") / "run.json"), result.stdout)
            self.assertIn(str(Path("candidate") / "run.json"), result.stdout)
            self.assert_no_report_artifacts(report_dir)

    def test_invalid_baseline_is_not_replaced_by_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            baseline = workdir / "baseline.json"
            candidate = workdir / "candidate.json"
            baseline.write_text("{not-json", encoding="utf-8")
            write_result(candidate, {"bm_alpha": 0.5})

            result = self.run_script(["-c", str(baseline), str(candidate)], workdir)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("baseline", result.stdout)
            self.assertIn("加载失败", result.stdout)
            self.assertNotIn("Benchmark", result.stdout)
            self.assert_no_report_artifacts(workdir)

    def test_empty_baseline_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            baseline = workdir / "baseline.json"
            candidate = workdir / "candidate.json"
            baseline.write_text("{}", encoding="utf-8")
            write_result(candidate, {"bm_alpha": 0.5})

            result = self.run_script(["-c", str(baseline), str(candidate)], workdir)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("baseline", result.stdout)
            self.assertIn("没有可用 benchmark 数据", result.stdout)
            self.assertNotIn("Benchmark", result.stdout)
            self.assert_no_report_artifacts(workdir)

    def test_requires_two_valid_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            baseline = workdir / "baseline.json"
            empty_candidate = workdir / "candidate.json"
            write_result(baseline, {"bm_alpha": 1.0})
            empty_candidate.write_text("{}", encoding="utf-8")

            single_result = self.run_script(["-c", str(baseline)], workdir)
            filtered_result = self.run_script(
                ["-c", str(baseline), str(empty_candidate)], workdir
            )

            self.assertNotEqual(single_result.returncode, 0)
            self.assertIn("至少需要两个 JSON", single_result.stdout)
            self.assertNotEqual(filtered_result.returncode, 0)
            self.assertIn("至少还需要一个有效 candidate", filtered_result.stdout)
            self.assert_no_report_artifacts(workdir)

    def test_rejects_equivalent_paths_to_same_physical_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            nested = workdir / "nested"
            nested.mkdir()
            baseline = workdir / "baseline.json"
            equivalent_path = nested / ".." / "baseline.json"
            write_result(baseline, {"bm_alpha": 1.0})

            result = self.run_script(
                ["-c", str(baseline), str(equivalent_path)], workdir
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("重复 JSON 输入", result.stdout)
            self.assertIn("指向同一物理文件", result.stdout)
            self.assert_no_report_artifacts(workdir)

    def test_default_mode_supports_25_inputs_and_excel_column_aa(self) -> None:
        try:
            from openpyxl import load_workbook
        except ImportError:
            self.skipTest("openpyxl is required for the default report mode")

        module = load_script_module()
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            json_files = []
            for index in range(25):
                result_path = workdir / f"run{index:02}.json"
                write_result(result_path, {"bm_alpha": 1.0 + index / 100.0})
                json_files.append(result_path)

            with working_directory(workdir), mock.patch.object(
                module, "import_pyplot", return_value=object()
            ), mock.patch.object(
                module, "plot_trends_paginated", return_value=[]
            ) as plot_mock, redirect_stdout(io.StringIO()):
                returncode = module.main([str(path) for path in json_files])

            self.assertEqual(returncode, 0)
            workbook = load_workbook(workdir / "benchmark_comparison.xlsx", read_only=False)
            try:
                worksheet = workbook.active
                self.assertEqual(worksheet["AA1"].value, "run24.json")
                self.assertEqual(worksheet["C3"].value, 1.0)
                self.assertEqual(worksheet["AA3"].value, 0.8065)
                self.assertIsNotNone(worksheet.column_dimensions["AA"].width)
            finally:
                workbook.close()
            self.assertEqual(plot_mock.call_args.args[2][-1], "run24.json")

    def test_real_agg_plot_generates_multiple_png_pages(self) -> None:
        try:
            import matplotlib
        except ImportError:
            self.skipTest("matplotlib is required for real PNG generation")

        matplotlib.use("Agg", force=True)
        module = load_script_module()
        plt = module.import_pyplot()
        common_benchmarks = ["bm_alpha", "bm_beta", "bm_gamma"]
        valid_files = ["baseline.json", "candidate.json"]
        file_labels = valid_files
        perf_ratios = {
            "baseline.json": {name: 1.0 for name in common_benchmarks},
            "candidate.json": {name: 2.0 for name in common_benchmarks},
        }

        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(io.StringIO()):
            base_name = Path(tmp) / "benchmark_trends"
            png_paths = module.plot_trends_paginated(
                common_benchmarks,
                valid_files,
                file_labels,
                perf_ratios,
                [1.0, 2.0],
                plt,
                benchmarks_per_page=2,
                base_name=base_name,
                announce=False,
            )

            self.assertEqual([path.name for path in png_paths], [
                "benchmark_trends_part1.png",
                "benchmark_trends_part2.png",
            ])
            self.assertTrue(all(path.stat().st_size > 0 for path in png_paths))

    def test_dependency_failure_happens_before_any_artifact_write(self) -> None:
        module = load_script_module()
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            baseline = workdir / "baseline.json"
            candidate = workdir / "candidate.json"
            write_result(baseline, {"bm_alpha": 1.0})
            write_result(candidate, {"bm_alpha": 0.5})

            with working_directory(workdir), mock.patch.object(
                module, "import_openpyxl", return_value=object()
            ), mock.patch.object(
                module, "import_pyplot", side_effect=SystemExit("broken matplotlib")
            ), mock.patch.object(module, "save_excel") as save_excel_mock, redirect_stdout(
                io.StringIO()
            ):
                with self.assertRaises(SystemExit):
                    module.main([str(baseline), str(candidate)])

            save_excel_mock.assert_not_called()
            self.assert_no_report_artifacts(workdir)

    def test_rerun_removes_stale_higher_numbered_plot_pages(self) -> None:
        module = load_script_module()
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            baseline = workdir / "baseline.json"
            candidate = workdir / "candidate.json"
            write_result(baseline, {"bm_alpha": 1.0})
            write_result(candidate, {"bm_alpha": 0.5})
            (workdir / "benchmark_trends_part1.png").write_bytes(b"old-page-1")
            (workdir / "benchmark_trends_part2.png").write_bytes(b"old-page-2")
            (workdir / "benchmark_trends_preview.png").write_bytes(b"unrelated")

            def write_staged_excel(*args, **kwargs) -> None:
                Path(kwargs["xlsx_path"]).write_bytes(b"new-xlsx")

            def write_one_page(*args, **kwargs) -> list[Path]:
                png_path = Path(f"{kwargs['base_name']}_part1.png")
                png_path.write_bytes(b"new-page-1")
                return [png_path]

            with working_directory(workdir), mock.patch.object(
                module, "import_openpyxl", return_value=object()
            ), mock.patch.object(
                module, "import_pyplot", return_value=object()
            ), mock.patch.object(
                module, "save_excel", side_effect=write_staged_excel
            ), mock.patch.object(
                module, "plot_trends_paginated", side_effect=write_one_page
            ), redirect_stdout(io.StringIO()):
                returncode = module.main([str(baseline), str(candidate)])

            self.assertEqual(returncode, 0)
            self.assertEqual((workdir / "benchmark_comparison.xlsx").read_bytes(), b"new-xlsx")
            self.assertEqual((workdir / "benchmark_trends_part1.png").read_bytes(), b"new-page-1")
            self.assertFalse((workdir / "benchmark_trends_part2.png").exists())
            self.assertTrue((workdir / "benchmark_trends_preview.png").exists())

    def test_generation_failure_preserves_previous_complete_report(self) -> None:
        module = load_script_module()
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            baseline = workdir / "baseline.json"
            candidate = workdir / "candidate.json"
            write_result(baseline, {"bm_alpha": 1.0})
            write_result(candidate, {"bm_alpha": 0.5})
            old_xlsx = workdir / "benchmark_comparison.xlsx"
            old_page_1 = workdir / "benchmark_trends_part1.png"
            old_page_2 = workdir / "benchmark_trends_part2.png"
            old_xlsx.write_bytes(b"old-xlsx")
            old_page_1.write_bytes(b"old-page-1")
            old_page_2.write_bytes(b"old-page-2")

            def write_staged_excel(*args, **kwargs) -> None:
                Path(kwargs["xlsx_path"]).write_bytes(b"new-xlsx")

            def fail_during_plot(*args, **kwargs) -> list[Path]:
                staged_page = Path(f"{kwargs['base_name']}_part1.png")
                staged_page.write_bytes(b"partial-new-page")
                raise OSError("simulated savefig failure")

            with working_directory(workdir), mock.patch.object(
                module, "import_openpyxl", return_value=object()
            ), mock.patch.object(
                module, "import_pyplot", return_value=object()
            ), mock.patch.object(
                module, "save_excel", side_effect=write_staged_excel
            ), mock.patch.object(
                module, "plot_trends_paginated", side_effect=fail_during_plot
            ), redirect_stdout(io.StringIO()) as output:
                returncode = module.main([str(baseline), str(candidate)])

            self.assertEqual(returncode, 1)
            self.assertIn("已保留原有完整报告", output.getvalue())
            self.assertEqual(old_xlsx.read_bytes(), b"old-xlsx")
            self.assertEqual(old_page_1.read_bytes(), b"old-page-1")
            self.assertEqual(old_page_2.read_bytes(), b"old-page-2")
            self.assertEqual(list(workdir.glob(".pyperformance-stat-report-*")), [])

    def test_publish_failure_rolls_back_previous_report(self) -> None:
        module = load_script_module()
        with tempfile.TemporaryDirectory() as tmp:
            workdir = Path(tmp)
            staging_dir = workdir / "staging"
            staging_dir.mkdir()
            staged_xlsx = staging_dir / "benchmark_comparison.xlsx"
            staged_page = staging_dir / "benchmark_trends_part1.png"
            staged_xlsx.write_bytes(b"new-xlsx")
            staged_page.write_bytes(b"new-page-1")
            old_xlsx = workdir / "benchmark_comparison.xlsx"
            old_page = workdir / "benchmark_trends_part1.png"
            old_xlsx.write_bytes(b"old-xlsx")
            old_page.write_bytes(b"old-page-1")
            real_replace = os.replace

            def fail_new_png_publish(source, destination) -> None:
                if Path(source) == staged_page:
                    raise OSError("simulated publish failure")
                real_replace(source, destination)

            with working_directory(workdir), mock.patch.object(
                module.os, "replace", side_effect=fail_new_png_publish
            ):
                with self.assertRaises(OSError):
                    module.publish_report_set(staged_xlsx, [staged_page])

            self.assertEqual(old_xlsx.read_bytes(), b"old-xlsx")
            self.assertEqual(old_page.read_bytes(), b"old-page-1")


if __name__ == "__main__":
    unittest.main()
