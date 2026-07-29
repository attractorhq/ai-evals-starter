import unittest
from pathlib import Path

from ai_evals_starter.contracts import DatasetError, load_cases, load_outputs
from ai_evals_starter.evaluator import evaluate
from ai_evals_starter.models import CandidateOutput


ROOT = Path(__file__).resolve().parents[1]


class EvaluatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cases = load_cases(ROOT / "examples/cases.jsonl")

    def test_passing_fixture_covers_inclusive_budget_boundaries(self) -> None:
        report = evaluate(
            self.cases, load_outputs(ROOT / "examples/outputs.passing.jsonl")
        )
        self.assertEqual(report.pass_rate, 1.0)
        refund = next(result for result in report.results if result.id == "refund-window")
        self.assertTrue(all(score.passed for score in refund.scores))
        self.assertEqual(
            {score.name for score in refund.scores},
            {"contains", "citations", "latency_budget", "cost_budget"},
        )

    def test_failures_are_actionable(self) -> None:
        report = evaluate(
            self.cases, load_outputs(ROOT / "examples/outputs.failing.jsonl")
        )
        self.assertEqual(report.cases_passed, 0)
        messages = "\n".join(
            score.message
            for result in report.results
            for score in result.scores
            if not score.passed
        )
        self.assertIn("not valid JSON", messages)
        self.assertIn("disallowed sources", messages)
        self.assertIn("exceeds budget", messages)

    def test_missing_candidate_is_a_dataset_error(self) -> None:
        outputs = load_outputs(ROOT / "examples/outputs.passing.jsonl")[:-1]
        with self.assertRaisesRegex(DatasetError, "missing output ID"):
            evaluate(self.cases, outputs)

    def test_extra_candidate_is_a_dataset_error(self) -> None:
        outputs = load_outputs(ROOT / "examples/outputs.passing.jsonl")
        outputs.append(
            CandidateOutput(id="extra", output="", latency_ms=0, cost_usd=0)
        )
        with self.assertRaisesRegex(DatasetError, "have no case"):
            evaluate(self.cases, outputs)


if __name__ == "__main__":
    unittest.main()
