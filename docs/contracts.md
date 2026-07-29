# JSONL contracts

The case, output, and report contracts have schema version `1.0`. Unknown JSONL
fields are rejected so typos cannot silently disable a check. Additive fields
will remain optional within version 1; incompatible changes require version 2.

## Evaluation case

Required fields:

- `id`: unique, non-empty string used to join the output.
- `input`: any JSON value passed to a generator adapter.
- `expect`: object configuring at least one scorer.

Optional `tags` is an array of strings. `expect` supports:

| Field | Value | Pass condition |
| --- | --- | --- |
| `exact` | string | Output equals the string. |
| `contains` | string array | Output contains every string. |
| `structured.required_keys` | string array | Output is a JSON object with all keys. |
| `structured.types` | object | Named keys have the configured JSON types. |
| `citations.min_count` | non-negative integer | At least this many citations exist. |
| `citations.allowed_sources` | string array | Every citation uses an allowed source. |
| `max_latency_ms` | non-negative number | Observed latency is at or below the budget. |
| `max_cost_usd` | non-negative number | Observed cost is at or below the budget. |

Supported structured types are `string`, `number`, `boolean`, `object`,
`array`, and `null`.

## Candidate output

Every output requires:

- `id`: ID of exactly one case.
- `output`: generated text, including serialized JSON for structured checks.
- `citations`: array of objects with `source_id` and optional `quote`.
- `latency_ms`: non-negative observed end-to-end latency.
- `cost_usd`: non-negative observed cost in US dollars.

Missing, duplicate, and extra IDs are errors. Use zero for an unpriced local
fixture rather than omitting an observed field.

## Report

The JSON report contains `schema_version`, a `summary`, and case-level results.
Each score records its name, pass state, message, observed value, and expected
value. The Markdown report renders the same decision for reviewers.

Costs are plain JSON numbers for interoperability. For financial accounting,
use a decimal representation outside this lightweight test contract.
