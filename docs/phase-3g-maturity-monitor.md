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
advance, and any tampering or conflicting duplicate fails closed.

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

## Safety boundary

The following fields are permanently false in every Phase 3G observation:

```text
model_fitting_executed
threshold_selection_executed
prospective_decisions_created
paper_or_live_trading_allowed
```

Phase 3G cannot establish predictive value, alpha or economic usefulness.
