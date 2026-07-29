from __future__ import annotations

import json
from pathlib import Path

from .models import EvaluationReport


def write_json_report(report: EvaluationReport, path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(report.as_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_markdown_report(
    report: EvaluationReport,
    path: str | Path,
    *,
    min_pass_rate: float,
    baseline_pass_rate: float | None,
    max_pass_rate_drop: float,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    decision = report.pass_rate >= min_pass_rate and (
        baseline_pass_rate is None
        or baseline_pass_rate - report.pass_rate <= max_pass_rate_drop
    )
    lines = [
        "# AI evaluation report",
        "",
        f"**Decision:** {'PASS' if decision else 'FAIL'}",
        "",
        f"- Cases: {report.cases_total}",
        f"- Passed: {report.cases_passed}",
        f"- Failed: {report.cases_total - report.cases_passed}",
        f"- Pass rate: {report.pass_rate:.2%}",
        f"- Required pass rate: {min_pass_rate:.2%}",
    ]
    if baseline_pass_rate is not None:
        lines.extend(
            [
                f"- Baseline pass rate: {baseline_pass_rate:.2%}",
                f"- Maximum allowed drop: {max_pass_rate_drop:.2%}",
            ]
        )
    lines.extend(
        [
            "",
            "## Cases",
            "",
            "| Case | Result | Failed checks |",
            "| --- | --- | --- |",
        ]
    )
    for result in report.results:
        failures = "<br>".join(
            _escape(score.message) for score in result.scores if not score.passed
        )
        lines.append(
            f"| `{_escape(result.id)}` | {'pass' if result.passed else '**fail**'} | {failures or '—'} |"
        )

    lines.extend(["", "## Check details", ""])
    for result in report.results:
        lines.extend([f"### {_escape(result.id)}", ""])
        for score in result.scores:
            lines.append(
                f"- {'PASS' if score.passed else 'FAIL'} `{score.name}` — {_escape(score.message)}"
            )
        lines.append("")
    target.write_text("\n".join(lines), encoding="utf-8")


def load_baseline_pass_rate(path: str | Path) -> float:
    source = Path(path)
    try:
        value = json.loads(source.read_text(encoding="utf-8"))
        pass_rate = value["summary"]["pass_rate"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise ValueError(
            f"{source}: baseline must be a JSON report containing summary.pass_rate"
        ) from error
    if (
        isinstance(pass_rate, bool)
        or not isinstance(pass_rate, (int, float))
        or not 0 <= pass_rate <= 1
    ):
        raise ValueError(f"{source}: summary.pass_rate must be between 0 and 1")
    return float(pass_rate)


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;")
