# Phase 3F — point-in-time semantic dataset and maturity gate

## Purpose

Phase 3F converts the longitudinal prospective semantic ledger into deterministic
features aligned to market decision rows. It exists to prevent a common research
error: assigning an event to the time it claims to describe rather than the time the
research system actually completed semantic inference.

For feature inclusion, only this timestamp is used:

```text
SemanticEventRecord.available_at = inference_completed_at
```

`signal.event_time_utc` and document publication time remain descriptive metadata and
never move a feature into an earlier decision row.

## Predeclared feature contract

The default backward windows are 4, 24 and 72 hours. Each window contains:

- total, bullish, bearish and neutral event counts;
- mean direction balance;
- source-quality/confidence/severity-weighted direction;
- mean and maximum severity;
- mean and maximum novelty;
- mean confidence and source quality;
- unique source count;
- capped age of the most recent observable event.

The default asset policy includes `BTC` and `MARKET`. Feature columns are returned in
a stable order and every numeric output must be finite.

## Label and as-of contract

A market row is eligible only when:

```text
decision_time <= as_of
label_available_at <= as_of
```

Rows whose outcomes were not yet observable are excluded rather than backfilled.
Open-to-Open label semantics remain those defined in the existing Phase 2B label
contract.

## Immutable dataset

A dataset directory contains:

```text
semantic-dataset/
├── data.csv.gz
├── manifest.json
└── maturity.json
```

The gzip payload is deterministic and content-addressed. The manifest records:

- market snapshot SHA-256;
- document and semantic ledger heads;
- semantic record counts;
- `as_of` cutoff;
- feature specification and its SHA-256;
- source commit;
- exact market, semantic and target columns;
- decision and label availability ranges;
- maturity assessment.

Conflicting rewrites and any payload/manifest mismatch fail closed.

## Maturity gate

Default minimums are deliberately conservative:

- 100 relevant semantic records;
- 30 unique semantic availability dates;
- 50 decision rows with active semantic windows;
- two unique sources;
- 500 matured labeled rows;
- both target classes observed.

If any requirement fails, the machine-readable verdict is:

```text
status = insufficient_prospective_sample
research_model_fitting_allowed = false
paper_or_live_trading_allowed = false
```

Even a mature result permits only a separately predeclared research experiment. Phase
3F never authorizes paper or live trading.

## First evidence design

The first fixed evidence intentionally pairs a market snapshot ending on 2026-07-13
with a prospective semantic ledger observed on 2026-07-17. Every semantic event count
must therefore be zero for every market decision row. A nonzero value would prove
historical backfill leakage and causes the workflow to fail.

The expected first verdict is insufficient prospective sample. No model is fitted,
no threshold is selected and the prospective decision ledger remains untouched.

## Final verified result

The final exact-head workflow run `29586581122` used source commit
`c1248daadb0313261c565c88291a77bb5b1926d6` and produced artifact `8409259039` with
digest:

```text
sha256:d1d4ba1b34370667aeab95e9c3ba0dd5f58d2085550963a93843863537a00f6b
```

Independent post-download verification established:

- all six top-level checksum entries matched their files;
- dataset ID `semantic-157007b0519c`;
- canonical dataset content SHA-256
  `157007b0519c122d4a2851c5d4164e5dbcc3d828a5bfcd8067a3a840e7d6d3f6`;
- market snapshot SHA-256
  `fa8c7f3ddc75baa7fccc8b835b47c4bb75ca3e8dbdc208a27428d513da40f144`;
- 7,632 candidate and matured labeled rows;
- 3,915 positive and 3,717 negative targets;
- eight relevant prospective semantic records;
- one relevant availability date and one relevant source;
- zero decision rows containing an observable semantic event;
- zero total semantic event counts across every historical market row;
- no decision or label timestamp later than the declared `as_of`;
- no model fitting and no prospective decision.

The maturity assessment correctly returned:

```text
status = insufficient_prospective_sample
research_model_fitting_allowed = false
paper_or_live_trading_allowed = false
```

The full Python 3.11/3.12 CI matrix, Ruff, strict Mypy, optional ML and clean-wheel
package smoke all passed on the same source commit. Compact reviewed evidence is
retained under `research/runs/phase3f-semantic-dataset-29586581122/`; the deterministic
full dataset remains in its digest-addressed GitHub Actions artifact.
