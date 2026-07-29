from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Citation:
    source_id: str
    quote: str | None = None


@dataclass(frozen=True)
class CitationExpectation:
    min_count: int = 1
    allowed_sources: tuple[str, ...] = ()


@dataclass(frozen=True)
class StructuredExpectation:
    required_keys: tuple[str, ...] = ()
    types: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Expectations:
    exact: str | None = None
    contains: tuple[str, ...] = ()
    structured: StructuredExpectation | None = None
    citations: CitationExpectation | None = None
    max_latency_ms: float | None = None
    max_cost_usd: float | None = None


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    input: Any
    expect: Expectations
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class CandidateOutput:
    id: str
    output: str
    citations: tuple[Citation, ...] = ()
    latency_ms: float = 0
    cost_usd: float = 0


@dataclass(frozen=True)
class Score:
    name: str
    passed: bool
    message: str
    observed: Any = None
    expected: Any = None


@dataclass(frozen=True)
class CaseResult:
    id: str
    passed: bool
    scores: tuple[Score, ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvaluationReport:
    schema_version: str
    cases_total: int
    cases_passed: int
    pass_rate: float
    results: tuple[CaseResult, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "summary": {
                "cases_total": self.cases_total,
                "cases_passed": self.cases_passed,
                "cases_failed": self.cases_total - self.cases_passed,
                "pass_rate": self.pass_rate,
            },
            "cases": [result.as_dict() for result in self.results],
        }
