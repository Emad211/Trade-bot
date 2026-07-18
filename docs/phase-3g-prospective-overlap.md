# Phase 3G — prospective market and semantic overlap

Phase 3G aligns a current public BTC market snapshot with the verified prospective
semantic ledger. It measures overlap and sample maturity only; it does not fit a
predictive model.

## Market contract

Each run requires two independent public spot venues, an explicit UTC cutoff and only
fully available 4-hour bars. Per-source snapshots, failures, missing bars, gaps and
cross-venue spread/correlation statistics are retained in immutable artifacts.

## Temporal contract

Semantic features enter a row only when:

```text
semantic.available_at <= decision_time
```

Market targets enter only when their label availability is no later than the run
cutoff. Publication or claimed event times never move a feature backward.

## Maturity trajectory

Every run appends one self-hashing entry bound to the market snapshot, semantic
dataset, semantic ledger head, source commit and cutoff. Dataset IDs are unique and
cutoffs must strictly increase. A previous trajectory is accepted only after its
chain is verified.

## First real run

Workflow run `29641882329` succeeded with:

- 719 complete bars from both Bitstamp and OKX;
- zero missing or irregular bars;
- return correlation `0.9996495643`;
- 8 prospective semantic records;
- 677 matured labeled rows;
- 3 decision rows with observable semantic features;
- zero semantic values in the 674 rows before first semantic availability.

The sample remains `insufficient_prospective_sample`. Research model fitting and all
trading actions remain disabled.

The full artifact ID is `8428867389` with digest
`sha256:47ffbb2a4656c0a59945c673586f2e0fc06181036c663a06e23facf6c7d74cd6`.
Compact reviewed evidence is stored under
`research/runs/phase3g-overlap-29641882329/`.
