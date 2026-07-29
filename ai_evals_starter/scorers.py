from __future__ import annotations

import json
from typing import Any

from .models import CandidateOutput, EvaluationCase, Score


def score_case(case: EvaluationCase, candidate: CandidateOutput) -> tuple[Score, ...]:
    scores: list[Score] = []
    expected = case.expect

    if expected.exact is not None:
        passed = candidate.output == expected.exact
        scores.append(
            Score(
                name="exact_match",
                passed=passed,
                message="Output matches exactly." if passed else "Output does not match expected text.",
                observed=candidate.output,
                expected=expected.exact,
            )
        )

    if expected.contains:
        missing = [text for text in expected.contains if text not in candidate.output]
        scores.append(
            Score(
                name="contains",
                passed=not missing,
                message=(
                    "All required text is present."
                    if not missing
                    else f"Missing required text: {', '.join(repr(item) for item in missing)}."
                ),
                observed=candidate.output,
                expected=list(expected.contains),
            )
        )

    if expected.structured is not None:
        scores.append(_score_structured(candidate, expected.structured.required_keys, expected.structured.types))

    if expected.citations is not None:
        source_ids = [citation.source_id for citation in candidate.citations]
        enough = len(source_ids) >= expected.citations.min_count
        disallowed = (
            [
                source_id
                for source_id in source_ids
                if source_id not in expected.citations.allowed_sources
            ]
            if expected.citations.allowed_sources
            else []
        )
        passed = enough and not disallowed
        details: list[str] = []
        if not enough:
            details.append(
                f"expected at least {expected.citations.min_count}, received {len(source_ids)}"
            )
        if disallowed:
            details.append(f"disallowed sources: {', '.join(disallowed)}")
        scores.append(
            Score(
                name="citations",
                passed=passed,
                message="Citation requirements pass." if passed else "Citation failure: " + "; ".join(details) + ".",
                observed=source_ids,
                expected={
                    "min_count": expected.citations.min_count,
                    "allowed_sources": list(expected.citations.allowed_sources),
                },
            )
        )

    if expected.max_latency_ms is not None:
        passed = candidate.latency_ms <= expected.max_latency_ms
        scores.append(
            Score(
                name="latency_budget",
                passed=passed,
                message=(
                    "Latency is within budget."
                    if passed
                    else f"Latency exceeds budget by {candidate.latency_ms - expected.max_latency_ms:.3f} ms."
                ),
                observed=candidate.latency_ms,
                expected=expected.max_latency_ms,
            )
        )

    if expected.max_cost_usd is not None:
        passed = candidate.cost_usd <= expected.max_cost_usd
        scores.append(
            Score(
                name="cost_budget",
                passed=passed,
                message=(
                    "Cost is within budget."
                    if passed
                    else f"Cost exceeds budget by ${candidate.cost_usd - expected.max_cost_usd:.6f}."
                ),
                observed=candidate.cost_usd,
                expected=expected.max_cost_usd,
            )
        )

    return tuple(scores)


def _score_structured(
    candidate: CandidateOutput, required_keys: tuple[str, ...], types: dict[str, str]
) -> Score:
    try:
        value = json.loads(candidate.output)
    except json.JSONDecodeError as error:
        return Score(
            name="structured_output",
            passed=False,
            message=f"Output is not valid JSON: {error.msg} at column {error.colno}.",
            observed=candidate.output,
            expected={"required_keys": list(required_keys), "types": types},
        )

    if not isinstance(value, dict):
        return Score(
            name="structured_output",
            passed=False,
            message="Structured output must be a JSON object.",
            observed=type(value).__name__,
            expected={"required_keys": list(required_keys), "types": types},
        )

    missing = [key for key in required_keys if key not in value]
    wrong_types = [
        f"{key} (expected {expected_type})"
        for key, expected_type in types.items()
        if key in value and not _matches_json_type(value[key], expected_type)
    ]
    passed = not missing and not wrong_types
    details: list[str] = []
    if missing:
        details.append(f"missing keys: {', '.join(missing)}")
    if wrong_types:
        details.append(f"wrong types: {', '.join(wrong_types)}")
    return Score(
        name="structured_output",
        passed=passed,
        message="JSON structure passes." if passed else "JSON structure failure: " + "; ".join(details) + ".",
        observed=value,
        expected={"required_keys": list(required_keys), "types": types},
    )


def _matches_json_type(value: Any, expected: str) -> bool:
    checks = {
        "string": lambda item: isinstance(item, str),
        "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
        "boolean": lambda item: isinstance(item, bool),
        "object": lambda item: isinstance(item, dict),
        "array": lambda item: isinstance(item, list),
        "null": lambda item: item is None,
    }
    return checks[expected](value)
