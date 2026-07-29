from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from .contracts import DatasetError, load_cases, load_outputs
from .evaluator import evaluate
from .reporting import (
    load_baseline_pass_rate,
    write_json_report,
    write_markdown_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-evals",
        description="Evaluate recorded AI outputs with deterministic scorers.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="run an offline evaluation")
    run.add_argument("--cases", required=True, help="v1 evaluation case JSONL")
    run.add_argument("--outputs", required=True, help="v1 candidate output JSONL")
    run.add_argument("--report-json", default="reports/eval-report.json")
    run.add_argument("--report-md", default="reports/eval-report.md")
    run.add_argument("--min-pass-rate", type=_rate, default=1.0)
    run.add_argument("--baseline", help="previous v1 JSON report")
    run.add_argument("--max-pass-rate-drop", type=_rate, default=0.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cases = load_cases(args.cases)
        outputs = load_outputs(args.outputs)
        report = evaluate(cases, outputs)
        baseline = (
            load_baseline_pass_rate(args.baseline) if args.baseline is not None else None
        )
        write_json_report(report, args.report_json)
        write_markdown_report(
            report,
            args.report_md,
            min_pass_rate=args.min_pass_rate,
            baseline_pass_rate=baseline,
            max_pass_rate_drop=args.max_pass_rate_drop,
        )
    except (DatasetError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    failures: list[str] = []
    if report.pass_rate < args.min_pass_rate:
        failures.append(
            f"pass rate {report.pass_rate:.2%} is below required {args.min_pass_rate:.2%}"
        )
    if (
        baseline is not None
        and baseline - report.pass_rate > args.max_pass_rate_drop
    ):
        failures.append(
            f"pass-rate drop {baseline - report.pass_rate:.2%} exceeds allowed "
            f"{args.max_pass_rate_drop:.2%}"
        )

    print(
        f"{report.cases_passed}/{report.cases_total} cases passed "
        f"({report.pass_rate:.2%}). Reports: {args.report_json}, {args.report_md}"
    )
    for failure in failures:
        print(f"FAIL: {failure}", file=sys.stderr)
    return 1 if failures else 0


def _rate(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("expected a number between 0 and 1") from error
    if not 0 <= parsed <= 1:
        raise argparse.ArgumentTypeError("expected a number between 0 and 1")
    return parsed
