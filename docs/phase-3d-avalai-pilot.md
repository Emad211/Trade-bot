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

## Safety boundary

Phase 3D cannot create an order, exposure, leverage, stop, target, wallet action or
prospective paper decision. A successful pilot permits only further prospective data
collection. Predictive use requires a new predeclared experiment with calibration,
ablation, economic-value and Phase 3A robustness gates.
