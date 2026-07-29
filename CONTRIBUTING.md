# Contributing

Open an issue before changing a JSONL contract or scorer meaning. Keep scorers
deterministic and provider-neutral; provider integrations belong in user code,
not the offline core.

Run `python -m unittest discover -v` and
`python -m compileall -q ai_evals_starter tests`. Include success, boundary, and
failure tests with behavior changes.

Follow the [Code of Conduct](CODE_OF_CONDUCT.md). Contributions are accepted
under Apache-2.0.
