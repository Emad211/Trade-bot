# Phase 2C real-data execution

Phase 2C moves from synthetic pipeline validation to a reproducible public-data
research run. It still cannot place orders or accept exchange credentials.

## Scientific contract

The checked-in `configs/phase2c_btc_4h.yaml` freezes:

- observation cutoff and start time;
- two independent spot sources;
- derivative source contracts;
- event and availability policies;
- latency assumptions;
- model matrix;
- large-move definition;
- promotion gates.

Changing the plan after inspecting final-test results creates a new plan SHA and a
new experiment. The previous null or failed record remains in the append-only
registry.

## Dataset audit

`audit-snapshots` verifies each immutable snapshot and reports:

- expected versus observed bars;
- missing bars and longest outage;
- null and non-finite values;
- availability latency;
- cross-venue return correlation and direction agreement;
- close-price spread and relative price-ratio dispersion.

Cross-venue disagreement is evidence to inspect, not a value to silently average
away.

## Tail and concentration report

`phase2c-report` adds metrics that average accuracy can hide:

- compounded and median fold return;
- positive-fold rate;
- best/worst fold;
- share of absolute fold return concentrated in one fold;
- performance conditional on the largest absolute BTC moves;
- exposure during large positive and negative moves;
- 1x, 1.5x and 2x cost resilience;
- predeclared promotion-gate results.

A passed gate labels a model as a *research candidate*. It is not approval for
capital deployment.

## Registry

`registry-append` records completed, null, failed and blocked experiments in a
hash-chained JSONL ledger. This prevents selective deletion of disappointing
results and records artifact hashes next to the immutable plan and dataset hashes.

## GitHub workflow

`.github/workflows/phase2c-real-data.yml` is an isolated public-data workflow. It
collects a short recent smoke window from two venues, audits the snapshots, runs a
sealed benchmark and uploads all artifacts. Network or venue failures are recorded
as blocked evidence and do not alter core CI results.
