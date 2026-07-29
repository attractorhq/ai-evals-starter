import tempfile
import unittest
from pathlib import Path

from ai_evals_starter.contracts import DatasetError, load_cases, load_outputs


ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def test_example_contracts_load(self) -> None:
        cases = load_cases(ROOT / "examples/cases.jsonl")
        outputs = load_outputs(ROOT / "examples/outputs.passing.jsonl")
        self.assertEqual([case.id for case in cases], [output.id for output in outputs])

    def test_malformed_json_reports_file_and_line(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "bad.jsonl"
            fixture.write_text('{"id": "broken"\\n', encoding="utf-8")
            with self.assertRaisesRegex(DatasetError, r"bad\.jsonl:1: invalid JSON"):
                load_cases(fixture)

    def test_duplicate_output_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "duplicate.jsonl"
            line = (
                '{"id":"same","output":"ok","citations":[],"latency_ms":1,'
                '"cost_usd":0}\n'
            )
            fixture.write_text(line + line, encoding="utf-8")
            with self.assertRaisesRegex(DatasetError, "duplicate output ID 'same'"):
                load_outputs(fixture)

    def test_negative_budget_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "negative.jsonl"
            fixture.write_text(
                '{"id":"x","input":"x","expect":{"max_cost_usd":-1}}\n',
                encoding="utf-8",
            )
            with self.assertRaisesRegex(DatasetError, "expected a non-negative number"):
                load_cases(fixture)


if __name__ == "__main__":
    unittest.main()
