from __future__ import annotations

from collections.abc import Sequence

from .contracts import DatasetError
from .models import CandidateOutput, CaseResult, EvaluationCase, EvaluationReport
from .scorers import score_case


def evaluate(
    cases: Sequence[EvaluationCase], outputs: Sequence[CandidateOutput]
) -> EvaluationReport:
    output_by_id = {output.id: output for output in outputs}
    case_ids = {case.id for case in cases}
    output_ids = set(output_by_id)
    missing = sorted(case_ids - output_ids)
    extra = sorted(output_ids - case_ids)
    problems: list[str] = []
    if missing:
        problems.append(f"missing output ID(s): {', '.join(missing)}")
    if extra:
        problems.append(f"output ID(s) have no case: {', '.join(extra)}")
    if problems:
        raise DatasetError("; ".join(problems))

    results: list[CaseResult] = []
    for case in cases:
        scores = score_case(case, output_by_id[case.id])
        results.append(
            CaseResult(
                id=case.id,
                passed=all(score.passed for score in scores),
                scores=scores,
            )
        )
    passed = sum(result.passed for result in results)
    return EvaluationReport(
        schema_version="1.0",
        cases_total=len(results),
        cases_passed=passed,
        pass_rate=passed / len(results),
        results=tuple(results),
    )
