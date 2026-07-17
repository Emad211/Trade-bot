# Phase 3G — prospective semantic maturity monitor

## Purpose

Phase 3G is a governance layer over Phase 3E collection and Phase 3F dataset
construction. It periodically rebuilds the point-in-time semantic dataset from a
fresh public market snapshot and the latest verified prospective semantic state, then
records how far the sample remains from the frozen maturity thresholds.

It never fits a predictive model, selects a trading threshold or writes a prospective
decision.

## Inputs

Every run uses:

- the latest successful Phase 3E longitudinal artifact;
- full verification of document, semantic and provider-call hash chains before use;
- a fresh public Kraken `BTC/USD` 4h snapshot downloaded through CCXT without API
  credentials;
- the existing Phase 2C market/label configuration;
- the default Phase 3F semantic feature and maturity policies.

The Phase 3E artifact run ID, artifact ID and artifact digest are written to the
monitor artifact.

## Maturity registry

Each observation records:

- observation time and workflow run ID;
- source commit;
- market snapshot and semantic dataset SHA-256 values;
- semantic ledger head;
- full Phase 3F maturity assessment;
- exact remaining counts for semantic records, availability dates, active decision
  rows, sources, matured labels and missing target classes;
- the allowed next action.

The registry is newline-delimited JSON with a SHA-256 link to the preceding record.
Workflow run IDs and observation IDs must be unique, observation time must strictly
advance, and any tampering or conflicting duplicate fails closed. Every stored deficit
is recomputed from the embedded frozen policy and maturity assessment during
validation; changing a deficit without changing the signed provenance invalidates the
record.

## Allowed next actions

An immature sample produces:

```text
next_action = continue_prospective_collection
```

A mature sample produces only:

```text
next_action = open_separate_predeclared_research_protocol
```

A mature observation does not run a model. It merely permits creating a new research
issue and protocol whose data cut, hypotheses, models, calibration, ablations and
robustness tests must be declared in advance.

## Schedule

The workflow supports manual runs and executes weekly on Monday at 08:17 UTC, after
the Phase 3E collection window. Prior registry state is restored from the latest
successful Phase 3G artifact and verified before append.

## Artifact policy

Actions artifacts contain:

- the fresh public market snapshot;
- the rebuilt immutable Phase 3F dataset;
- the complete hash-chained maturity registry;
- the current observation and input provenance;
- a checksum inventory.

Git stores implementation and compact reviewed evidence, not weekly raw market or
prospective event archives.

## First verified result

Workflow run `29588884832` completed successfully using only public market data.

- artifact ID: `8410201462`;
- artifact digest:
  `sha256:878dcf408e0ec8b68f2320259b570ab5cba1a68743c2792bca1138960117f22b`;
- Phase 3E input run/artifact: `29575275480` / `8404763802`;
- Phase 3E artifact digest:
  `sha256:41a4afc354faecd4cbbad2a7ef55e6f00e21d48eb904bf4b0f8d8d5cf0f05ba8`;
- observation time: `2026-07-17T14:40:02Z`;
- registry count: `1`;
- registry head:
  `9e434a1d6d9ea25a6816ff1fcc22ab2650b824a0f63b96037fccd34b515c2b19`.

The fresh Kraken market snapshot contained 720 BTC/USD 4h bars and had content SHA:

```text
a93c5b23616c649cb97e0e0dd55626c269e6707e2a203f10ad458bd3fbfdd587
```

The rebuilt semantic dataset contained 618 matured rows and had content SHA:

```text
0e303db3bd9dda8447e588a2d619fc4eb3a42796e4519718354184202ff110ff
```

The maturity verdict remained:

```text
status = insufficient_prospective_sample
next_action = continue_prospective_collection
research_model_fitting_allowed = false
paper_or_live_trading_allowed = false
```

Remaining deficits under the frozen Phase 3F policy were:

- 92 semantic records;
- 29 unique semantic availability dates;
- 50 active semantic decision rows;
- one additional independent source;
- zero matured labeled rows;
- zero missing target classes.

The artifact ZIP digest and all nine checksum entries were independently verified. No
model fitting, threshold selection, prospective decision or trading authorization
occurred.

The evidence artifact was generated on commit
`ef8c910ae1844bab122de34d5db5b851b92cb498`. The finalized implementation, including
strict deficit-integrity validation and the corrected public-snapshot CLI contract,
passed the complete Python 3.11/3.12 CI matrix on commit
`6b8bcba076f0ca6a3ea2b5f006a3609fc3151710`. Compact evidence is retained under
`research/runs/phase3g-maturity-monitor-29588884832/`.

## Safety boundary

The following fields are permanently false in every Phase 3G observation:

```text
model_fitting_executed
threshold_selection_executed
prospective_decisions_created
paper_or_live_trading_allowed
```

Phase 3G cannot establish predictive value, alpha or economic usefulness.
