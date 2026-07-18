# Phase 3H — deterministic relevance filtering and semantic source diversity

## Purpose

Phase 3H expands the prospective public-source universe without allowing broad feeds
to consume semantic-provider calls on unrelated documents. It remains a data-quality
and source-diversity phase. It does not fit a predictive model or create a paper/live
trading decision.

## Relevance contract

Each source may declare normalized include and exclude phrases. The filter examines
only the feed title and summary before semantic inference.

- exclusion matches take precedence;
- an unfiltered source remains backward compatible and accepts every parsed item;
- a filtered source accepts an item only when an include term is present and no
  exclusion term is present;
- every accept/reject result is self-hashing and records policy identity, matched
  terms and a deterministic reason;
- rejected documents never enter the document ledger, semantic ledger or AvalAI call
  ledger;
- relevance decisions and their checksum are persisted with the capture manifest.

The document text remains untrusted. Prompt-like text inside a feed cannot override
source policy or the structured-output contract.

## Public-source probe

The credential-free probe tests retrieval, parser behavior and relevance policy before
any provider call. The current candidates are:

- Bitcoin Core releases — required BTC primary source;
- Geth releases — optional ETH source;
- Bitcoin Optech newsletters — BTC-specialized independent source;
- Federal Reserve monetary-policy releases — official MARKET source;
- SEC press releases — optional BTC/MARKET broad source with relevance filtering.

A successful probe does not automatically authorize semantic calls. The live pilot
must also pass the bounded provider, source-diversity and asset-diversity gates.

## Source-balanced provider budget

The legacy `global_order` selection policy remains the default for backward
compatibility. Phase 3H explicitly selects `source_round_robin`.

Accepted, missing semantic work is ordered deterministically within each source and
then interleaved by the source order in the frozen configuration. This prevents one
large feed from consuming the complete per-run provider budget while preserving the
existing hard pre-call limit.

Documents that exceed the budget remain in the document ledger and are eligible for
later semantic recovery. Rejected documents are not treated as pending work.

## Bounded live pilot gate

The pilot restores the latest verified Phase 3E compact state and permits at most four
new AvalAI calls. It requires:

- no failed calls and no call above the retry ceiling;
- total token use within the frozen budget;
- at least two successful capture sources;
- at least two sources and two assets in the new semantic delta;
- Bitcoin Optech and Federal Reserve in the new semantic delta;
- BTC and MARKET in the new semantic delta;
- at least one persisted relevance rejection;
- no provider call for a source with zero accepted documents;
- no duplicate extraction key from prior state;
- an empty prospective decision ledger;
- no credential-shaped material in compact state or artifacts.

`phase3h_assessment.json` records the machine-readable result. A passing result permits
continued diversified prospective collection only.

## Safety boundary

Phase 3H cannot authorize additional unbounded provider activity, model fitting,
threshold selection, paper trading or live trading. Predictive use still requires a
mature Phase 3F/3G dataset and a separately predeclared Phase 3A robustness protocol.
