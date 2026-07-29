import json
import tempfile
import unittest
from pathlib import Path

from ai_evals_starter.cli import main


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def test_passing_run_writes_both_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report_json = Path(directory) / "report.json"
            report_md = Path(directory) / "report.md"
            status = main(
                [
                    "run",
                    "--cases",
                    str(ROOT / "examples/cases.jsonl"),
                    "--outputs",
                    str(ROOT / "examples/outputs.passing.jsonl"),
                    "--report-json",
                    str(report_json),
                    "--report-md",
                    str(report_md),
                ]
            )
            self.assertEqual(status, 0)
            self.assertEqual(
                json.loads(report_json.read_text(encoding="utf-8"))["summary"][
                    "pass_rate"
                ],
                1.0,
            )
            self.assertIn("**Decision:** PASS", report_md.read_text(encoding="utf-8"))

    def test_threshold_failure_returns_one_but_writes_reports(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report_json = Path(directory) / "report.json"
            report_md = Path(directory) / "report.md"
            status = main(
                [
                    "run",
                    "--cases",
                    str(ROOT / "examples/cases.jsonl"),
                    "--outputs",
                    str(ROOT / "examples/outputs.failing.jsonl"),
                    "--report-json",
                    str(report_json),
                    "--report-md",
                    str(report_md),
                    "--min-pass-rate",
                    "0.5",
                ]
            )
            self.assertEqual(status, 1)
            self.assertTrue(report_json.exists())
            self.assertIn("**Decision:** FAIL", report_md.read_text(encoding="utf-8"))

    def test_regression_failure_returns_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            status = main(
                [
                    "run",
                    "--cases",
                    str(ROOT / "examples/cases.jsonl"),
                    "--outputs",
                    str(ROOT / "examples/outputs.failing.jsonl"),
                    "--report-json",
                    str(Path(directory) / "report.json"),
                    "--report-md",
                    str(Path(directory) / "report.md"),
                    "--min-pass-rate",
                    "0",
                    "--baseline",
                    str(ROOT / "examples/baseline-report.json"),
                    "--max-pass-rate-drop",
                    "0.1",
                ]
            )
            self.assertEqual(status, 1)


if __name__ == "__main__":
    unittest.main()
