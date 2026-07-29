from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, Sequence

from .models import CandidateOutput, EvaluationCase


class Generator(Protocol):
    """Adapter implemented by a model provider or existing application."""

    def generate(self, case: EvaluationCase) -> CandidateOutput:
        """Generate one observable candidate result for a case."""


def record_outputs(
    generator: Generator,
    cases: Sequence[EvaluationCase],
    destination: str | Path,
) -> list[CandidateOutput]:
    """Run an explicit recording job and write the v1 candidate JSONL contract."""

    outputs: list[CandidateOutput] = []
    lines: list[str] = []
    for case in cases:
        output = generator.generate(case)
        if output.id != case.id:
            raise ValueError(
                f"Generator returned ID '{output.id}' for case '{case.id}'."
            )
        outputs.append(output)
        lines.append(
            json.dumps(
                {
                    "id": output.id,
                    "output": output.output,
                    "citations": [
                        {
                            key: value
                            for key, value in {
                                "source_id": citation.source_id,
                                "quote": citation.quote,
                            }.items()
                            if value is not None
                        }
                        for citation in output.citations
                    ],
                    "latency_ms": output.latency_ms,
                    "cost_usd": output.cost_usd,
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return outputs
