# Phase 3G prospective maturity-monitor evidence

This directory records compact, independently verified evidence from the first
successful Phase 3G governance-only maturity observation.

## Identity

- Workflow run: `29588884832`
- Artifact ID: `8410201462`
- Artifact digest:
  `sha256:878dcf408e0ec8b68f2320259b570ab5cba1a68743c2792bca1138960117f22b`
- Artifact source commit: `ef8c910ae1844bab122de34d5db5b851b92cb498`
- Final validated implementation commit:
  `6b8bcba076f0ca6a3ea2b5f006a3609fc3151710`
- Final validation CI run: `29589388420`

The artifact was generated before the final deficit-tamper validator was added. The
recorded deficits were independently recomputed and were already correct. The final
implementation subsequently passed the complete CI matrix with the stronger validator
that rejects any stored deficit inconsistent with the frozen maturity policy.

## Verified inputs

- Phase 3E workflow run: `29575275480`
- Phase 3E artifact ID: `8404763802`
- Phase 3E artifact digest:
  `sha256:41a4afc354faecd4cbbad2a7ef55e6f00e21d48eb904bf4b0f8d8d5cf0f05ba8`
- Market source: public `ccxt:kraken:BTC/USD`
- Observation time: `2026-07-17T14:40:02Z`

The restored Phase 3E state passed document, semantic, provider-call and non-activation
verification before use.

## Fresh market snapshot

- Dataset ID: `btc-usd-4h-a93c5b23616c`
- Content SHA-256:
  `a93c5b23616c649cb97e0e0dd55626c269e6707e2a203f10ad458bd3fbfdd587`
- Rows: `720`
- Event range: `2026-03-19T12:00:00Z` to `2026-07-17T08:00:00Z`
- Availability end: `2026-07-17T12:00:30Z`

No exchange credentials or trading permissions were used.

## Rebuilt semantic dataset

- Dataset ID: `semantic-0e303db3bd9d`
- Content SHA-256:
  `0e303db3bd9dda8447e588a2d619fc4eb3a42796e4519718354184202ff110ff`
- Candidate and matured rows: `618`
- Positive/negative labels: `305 / 313`
- Relevant semantic records: `8`
- Semantic availability dates: `1`
- Unique sources: `1`
- Active semantic decision rows: `0`

## Maturity verdict and deficits

```text
status = insufficient_prospective_sample
next_action = continue_prospective_collection
research_model_fitting_allowed = false
paper_or_live_trading_allowed = false
```

Remaining observations under the frozen Phase 3F policy:

- semantic records: `92`;
- availability dates: `29`;
- active decision rows: `50`;
- independent sources: `1`;
- matured labeled rows: `0`;
- missing target classes: `0`.

The registry contains one observation with head:

```text
9e434a1d6d9ea25a6816ff1fcc22ab2650b824a0f63b96037fccd34b515c2b19
```

## Verification

The downloaded ZIP digest matched GitHub exactly. Every one of the nine top-level
checksum entries was independently recomputed and matched. No model fitting,
threshold selection, prospective decision or paper/live trading authorization
occurred.
