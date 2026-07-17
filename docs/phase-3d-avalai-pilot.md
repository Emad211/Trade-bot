# Phase 3D — bounded prospective AvalAI pilot

## Purpose

Phase 3D measures whether the AvalAI semantic layer can operate prospectively over
real public feeds with bounded cost, deterministic deduplication and complete audit
metadata. It is a data-quality gate, not a trading experiment.

## Predeclared pilot

The workflow derives its policy from the canonical Phase 3C provider configuration
and applies these temporary limits:

- one release item from Bitcoin Core;
- one release item from Geth;
- at most two new provider calls;
- at most 4,000 total tokens;
- no failed provider calls;
- no call may exceed four attempts;
- both sources must succeed;
- the same capture is repeated over persistent state and must produce zero additional
  provider calls.

The exact provider remains pinned to `gpt-5-mini-2025-08-07` through the Responses
API with strict structured output.

## Assessment

`hybrid_trader.phase3d` reads the capture manifests, provider manifests, call ledger
and semantic ledger. It reports:

- source and semantic-record counts;
- provider successes, failures and retry attempts;
- input, output and total tokens;
- mean and maximum provider latency;
- direction counts and mean confidence, novelty and severity;
- first-run and repeat-run call counts;
- decision-ledger and credential-pattern status.

A passing assessment writes `phase3d_assessment.json` and a checksum. Any failed
rule returns a machine-readable reason and exits non-zero.

## Real pilot result

The first bounded pilot completed successfully in workflow run `29572947781`.

- artifact ID: `8403844430`;
- artifact digest:
  `sha256:541a2390427af6917214a5053747f7d64a284a1ba02ab71a730e58bd796bdb3f`;
- assessment ID:
  `26c5d094b8184051b3fd518455b676c15c941a1c193be3fe2feb3bce6fae1a7b`;
- required source success: 2 of 2;
- first-run provider calls: 2;
- repeated-run provider calls: 0;
- successful/failed calls: 2 / 0;
- maximum attempts: 1;
- total tokens: 2,435 of the 4,000-token ceiling;
- mean/maximum latency: 3.49 / 4.42 seconds;
- semantic records: 2;
- directions: one neutral and one bullish;
- prospective decisions: 0;
- detected credential patterns: 0.

Independent post-download inspection verified every top-level and nested checksum.
The repeated capture preserved the same document, semantic and call-ledger heads and
created no additional AvalAI call. Compact evidence is committed under
`research/runs/phase3d-avalai-pilot-29572947781/`; raw feed payloads and provider
trace records remain only in the digest-addressed Actions artifact.

## Safety boundary

Phase 3D cannot create an order, exposure, leverage, stop, target, wallet action or
prospective paper decision. The passing result permits only further prospective data
collection. It does not demonstrate predictive value, calibration, alpha or economic
usefulness. Predictive use requires a new predeclared experiment with calibration,
ablation, economic-value and Phase 3A robustness gates.
