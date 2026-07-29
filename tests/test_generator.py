import tempfile
import unittest
from pathlib import Path

from ai_evals_starter.contracts import load_cases, load_outputs
from ai_evals_starter.generator import record_outputs
from ai_evals_starter.models import CandidateOutput, EvaluationCase


class FixtureGenerator:
    def generate(self, case: EvaluationCase) -> CandidateOutput:
        return CandidateOutput(
            id=case.id,
            output="recorded",
            latency_ms=1,
            cost_usd=0,
        )


class GeneratorTests(unittest.TestCase):
    def test_adapter_records_a_valid_output_contract(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cases_path = Path(directory) / "cases.jsonl"
            cases_path.write_text(
                '{"id":"one","input":"hello","expect":{"exact":"recorded"}}\n',
                encoding="utf-8",
            )
            destination = Path(directory) / "nested/outputs.jsonl"
            cases = load_cases(cases_path)
            record_outputs(FixtureGenerator(), cases, destination)
            outputs = load_outputs(destination)
            self.assertEqual(outputs[0].output, "recorded")


if __name__ == "__main__":
    unittest.main()
