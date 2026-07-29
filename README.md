# AI Evals Starter

A minimal, provider-neutral Python starter for testing AI outputs in CI.

It evaluates recorded outputs with deterministic scorers for matching,
structured-output validity, citations, latency, and cost. Reports are written
as JSON and Markdown with case-level failures and regression thresholds.

The starter uses only the Python standard library at runtime. The included
fixtures and CI need no API keys, model provider, paid service, or network
connection.

## Quick start

Requirements: Python 3.10 or newer.

```bash
python -m ai_evals_starter run \
  --cases examples/cases.jsonl \
  --outputs examples/outputs.passing.jsonl \
  --report-json reports/eval-report.json \
  --report-md reports/eval-report.md \
  --min-pass-rate 1.0
```

The command exits zero. To inspect actionable failures and a non-zero exit:

```bash
python -m ai_evals_starter run \
  --cases examples/cases.jsonl \
  --outputs examples/outputs.failing.jsonl \
  --report-json reports/failing.json \
  --report-md reports/failing.md
```

Malformed JSONL, duplicate or missing IDs, invalid fields, failed thresholds,
and excessive regression all produce clear errors and non-zero exit codes.

## Contracts

Each line is one JSON object. IDs join cases to candidate outputs and must be
unique. See [docs/contracts.md](docs/contracts.md) for the stable `v1` fields.

A case configures only the scorers it needs:

```json
{"id":"refund-window","input":"How long do I have?","expect":{"contains":["30 days"],"citations":{"min_count":1,"allowed_sources":["returns-policy"]},"max_latency_ms":800,"max_cost_usd":0.01}}
```

A recorded output contains the observable result:

```json
{"id":"refund-window","output":"Returns are accepted within 30 days.","citations":[{"source_id":"returns-policy"}],"latency_ms":420,"cost_usd":0.003}
```

## Regression gates

`--min-pass-rate` sets the absolute case pass-rate threshold. Add a previous
JSON report with `--baseline` and set `--max-pass-rate-drop` to limit regression:

```bash
python -m ai_evals_starter run \
  --cases examples/cases.jsonl \
  --outputs examples/outputs.passing.jsonl \
  --baseline examples/baseline-report.json \
  --max-pass-rate-drop 0.02
```

Thresholds are inclusive: a pass rate equal to the minimum, or a latency/cost
equal to its budget, passes.

## Connect a generator

The CLI intentionally consumes recorded outputs so ordinary test runs remain
offline and reproducible. Implement the small
[`Generator`](ai_evals_starter/generator.py) protocol to connect a provider or
your existing application, then call `record_outputs` in an explicitly
credentialed recording job. Keep the resulting fixture under review and run
the evaluator offline in CI.

## Development

```bash
python -m unittest discover -v
python -m compileall -q ai_evals_starter tests
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and
[SUPPORT.md](SUPPORT.md). Licensed under [Apache-2.0](LICENSE).
