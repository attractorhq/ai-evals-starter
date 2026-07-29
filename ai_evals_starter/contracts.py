from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .models import (
    CandidateOutput,
    Citation,
    CitationExpectation,
    EvaluationCase,
    Expectations,
    StructuredExpectation,
)


class DatasetError(ValueError):
    """An actionable JSONL contract violation."""


def load_cases(path: str | Path) -> list[EvaluationCase]:
    values = _load_jsonl(path)
    cases = [_parse_case(value, path, line) for line, value in values]
    _require_unique_ids((case.id for case in cases), path, "case")
    if not cases:
        raise DatasetError(f"{path}: dataset must contain at least one case")
    return cases


def load_outputs(path: str | Path) -> list[CandidateOutput]:
    values = _load_jsonl(path)
    outputs = [_parse_output(value, path, line) for line, value in values]
    _require_unique_ids((output.id for output in outputs), path, "output")
    return outputs


def _load_jsonl(path: str | Path) -> list[tuple[int, dict[str, Any]]]:
    source = Path(path)
    try:
        lines = source.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise DatasetError(f"{source}: cannot read file: {error}") from error

    values: list[tuple[int, dict[str, Any]]] = []
    for line_number, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as error:
            raise DatasetError(
                f"{source}:{line_number}: invalid JSON: {error.msg} at column {error.colno}"
            ) from error
        if not isinstance(value, dict):
            raise DatasetError(f"{source}:{line_number}: each line must be a JSON object")
        values.append((line_number, value))
    return values


def _parse_case(value: dict[str, Any], path: str | Path, line: int) -> EvaluationCase:
    context = f"{path}:{line}"
    _allowed(value, {"id", "input", "expect", "tags"}, context)
    case_id = _string(value, "id", context)
    if "input" not in value:
        raise DatasetError(f"{context}: missing required field 'input'")
    expect_value = _object(value, "expect", context)
    _allowed(
        expect_value,
        {"exact", "contains", "structured", "citations", "max_latency_ms", "max_cost_usd"},
        f"{context}.expect",
    )

    exact = _optional_string(expect_value, "exact", f"{context}.expect")
    contains = _string_list(expect_value.get("contains", []), f"{context}.expect.contains")
    structured = _parse_structured(expect_value.get("structured"), context)
    citations = _parse_citations(expect_value.get("citations"), context)
    max_latency = _optional_non_negative(expect_value, "max_latency_ms", f"{context}.expect")
    max_cost = _optional_non_negative(expect_value, "max_cost_usd", f"{context}.expect")
    if all(
        item is None or item == ()
        for item in (exact, contains, structured, citations, max_latency, max_cost)
    ):
        raise DatasetError(f"{context}.expect: configure at least one scorer")

    tags = _string_list(value.get("tags", []), f"{context}.tags")
    return EvaluationCase(
        id=case_id,
        input=value["input"],
        expect=Expectations(
            exact=exact,
            contains=contains,
            structured=structured,
            citations=citations,
            max_latency_ms=max_latency,
            max_cost_usd=max_cost,
        ),
        tags=tags,
    )


def _parse_output(value: dict[str, Any], path: str | Path, line: int) -> CandidateOutput:
    context = f"{path}:{line}"
    _allowed(value, {"id", "output", "citations", "latency_ms", "cost_usd"}, context)
    citations_value = value.get("citations", [])
    if not isinstance(citations_value, list):
        raise DatasetError(f"{context}.citations: expected an array")
    citations: list[Citation] = []
    for index, item in enumerate(citations_value):
        item_context = f"{context}.citations[{index}]"
        if not isinstance(item, dict):
            raise DatasetError(f"{item_context}: expected an object")
        _allowed(item, {"source_id", "quote"}, item_context)
        citations.append(
            Citation(
                source_id=_string(item, "source_id", item_context),
                quote=_optional_string(item, "quote", item_context),
            )
        )
    return CandidateOutput(
        id=_string(value, "id", context),
        output=_string(value, "output", context, allow_empty=True),
        citations=tuple(citations),
        latency_ms=_required_non_negative(value, "latency_ms", context),
        cost_usd=_required_non_negative(value, "cost_usd", context),
    )


def _parse_structured(value: Any, context: str) -> StructuredExpectation | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise DatasetError(f"{context}.expect.structured: expected an object")
    structured_context = f"{context}.expect.structured"
    _allowed(value, {"required_keys", "types"}, structured_context)
    required = _string_list(value.get("required_keys", []), f"{structured_context}.required_keys")
    types_value = value.get("types", {})
    if not isinstance(types_value, dict):
        raise DatasetError(f"{structured_context}.types: expected an object")
    valid_types = {"string", "number", "boolean", "object", "array", "null"}
    types: dict[str, str] = {}
    for key, expected_type in types_value.items():
        if not isinstance(key, str) or expected_type not in valid_types:
            raise DatasetError(
                f"{structured_context}.types: keys must map to one of {sorted(valid_types)}"
            )
        types[key] = expected_type
    return StructuredExpectation(required_keys=required, types=types)


def _parse_citations(value: Any, context: str) -> CitationExpectation | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise DatasetError(f"{context}.expect.citations: expected an object")
    citation_context = f"{context}.expect.citations"
    _allowed(value, {"min_count", "allowed_sources"}, citation_context)
    min_count = value.get("min_count", 1)
    if isinstance(min_count, bool) or not isinstance(min_count, int) or min_count < 0:
        raise DatasetError(f"{citation_context}.min_count: expected a non-negative integer")
    allowed = _string_list(value.get("allowed_sources", []), f"{citation_context}.allowed_sources")
    return CitationExpectation(min_count=min_count, allowed_sources=allowed)


def _require_unique_ids(ids: Iterable[str], path: str | Path, kind: str) -> None:
    seen: set[str] = set()
    for item_id in ids:
        if item_id in seen:
            raise DatasetError(f"{path}: duplicate {kind} ID '{item_id}'")
        seen.add(item_id)


def _allowed(value: dict[str, Any], keys: set[str], context: str) -> None:
    unexpected = sorted(set(value) - keys)
    if unexpected:
        raise DatasetError(f"{context}: unexpected field(s): {', '.join(unexpected)}")


def _string(
    value: dict[str, Any], key: str, context: str, *, allow_empty: bool = False
) -> str:
    item = value.get(key)
    if not isinstance(item, str) or (not allow_empty and not item.strip()):
        qualifier = "a string" if allow_empty else "a non-empty string"
        raise DatasetError(f"{context}.{key}: expected {qualifier}")
    return item


def _optional_string(value: dict[str, Any], key: str, context: str) -> str | None:
    if key not in value:
        return None
    return _string(value, key, context, allow_empty=True)


def _object(value: dict[str, Any], key: str, context: str) -> dict[str, Any]:
    item = value.get(key)
    if not isinstance(item, dict):
        raise DatasetError(f"{context}.{key}: expected an object")
    return item


def _string_list(value: Any, context: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        raise DatasetError(f"{context}: expected an array of non-empty strings")
    return tuple(value)


def _optional_non_negative(
    value: dict[str, Any], key: str, context: str
) -> float | None:
    if key not in value:
        return None
    return _required_non_negative(value, key, context)


def _required_non_negative(value: dict[str, Any], key: str, context: str) -> float:
    item = value.get(key)
    if isinstance(item, bool) or not isinstance(item, (int, float)) or item < 0:
        raise DatasetError(f"{context}.{key}: expected a non-negative number")
    return float(item)
