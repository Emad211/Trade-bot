# Report 2.3 — Verified OKX Executable-Price and Cost-Semantics Contract

**Status date:** 2026-07-21  
**Issue:** #57  
**Outcome:** `GO_OKX_EXECUTABLE_PRICE_AND_COST_SEMANTICS_CONTRACT`  
**Independent blocker:** `BLOCKED_OWNER_FEE_OR_EXECUTION_INPUTS`

## Scope

This gate freezes price identities, order/fill lifecycle, timestamp units, latency decomposition, partial-fill accounting, slippage signs, order-book metadata, and non-overlapping cost components before any numerical transaction-cost, PnL, return, or strategy calculation.

The GO outcome authorizes only the tested semantic model and synthetic validation. It does not authorize an assumed fee rate, a real order, a private trading endpoint call, numerical costs, returns, or trading.

## Verified workflow

```text
Workflow: OKX Executable Price and Cost Semantics Contract
Run ID: 29841870117
Triggering head: c509ac0a93629a0a77319fbd0298a0be23aad318
Permissions: contents read-only
Conclusion: SUCCESS
```

```text
Ruff format: PASS
Ruff lint: PASS
Mypy strict: PASS
Scoped tests: 22 PASS
Synthetic evidence generator: PASS
Independent safe-evidence verifier: PASS
Real order request performed: false
Private trading endpoint called: false
```

Safe artifact:

```text
Artifact ID: 8499736417
Artifact digest: sha256:3367ac39c72b69f01c80ecdfbbe31276f9defcdff4373434d790144caf241d47
Evidence bytes: 4,269
Evidence SHA-256: 0a65fcf91393decbb1032840791af5c4dcc7c0228a0ece7105bffb529e86d930
```

The artifact contains no real price, size, book, fill, spread, fee, account, PnL, return, or credential value.

## Executable-price identities

The model keeps the following identities distinct:

```text
decision reference
best bid
best ask
midpoint
last trade
order limit
mark
index
individual fill
weighted-average fill
position/accounting price
```

Frozen rules:

```text
BUY executable quote: best ask
SELL executable quote: best bid
Midpoint: reference only
Last/mark/index: non-executable by default
Limit price: order constraint, not fill price
Acknowledgement: not execution
Cancellation acknowledgement: not final cancellation state
Unfilled quantity: no fabricated price
```

## Order and fill lifecycle

Admitted order identities:

```text
market
limit
post_only
IOC
FOK
optimal_limit_ioc
```

Maker/taker is taken from actual fill execution fields rather than inferred from order type. Partial fills retain every fill identity, fill time, price, quantity, liquidity role, and residual quantity. Weighted-average fill price is quantity weighted and is absent when the order has no fills.

A successful order or batch acknowledgement is not treated as proof of execution, cancellation, or item-level success.

## Clock and latency contract

```text
Client/gateway unit: microseconds
Provider order/fill unit: milliseconds
Gateway receive: inTime
Gateway send: outTime
Order create: cTime
Order update: uTime
Fill matching: fillTime
```

Non-overlapping latency components:

```text
client decision → submit
submit → gateway in
gateway processing = outTime - inTime
gateway out → client receive
decision → first fill
decision → last fill
order live duration
```

Negative, reordered, or mixed-unit clocks fail closed. Acknowledgement time never substitutes for `fillTime`.

## Slippage and spread contract

Direction-aware adverse signs:

```text
BUY: execution - reference
SELL: reference - execution
```

A slippage observation requires an explicit reference identity and reference time. Midpoint may be an admitted reference but is not an executable quote. Maker status does not imply zero spread or favorable execution. Partial-fill execution uses quantity weighting; unfilled quantity receives no invented execution price.

## Book and cache contract

The book contract requires source/version identity, provider time, research availability, depth, aggregation mode, tick size, and ELP/speed-bump eligibility. Checksum and sequence are preserved when available.

A staleness threshold must be an explicit future parameter; it cannot be hidden in code. Source gaps and errors are failures, not market nulls.

OKX's independent-cache behavior is preserved: provider timestamps may be non-monotonic in request order, and the project does not reorder or rewrite them.

## Cost-component and double-counting contract

Distinct components include:

```text
quoted half/full spread
arrival slippage
implementation shortfall
market impact
adverse selection
latency delay
opportunity cost
trading fee
funding cashflow
liquidation cashflow
settlement cashflow
position realized PnL
```

The model rejects:

```text
full and half spread both counted
implementation shortfall plus its decomposed components
position realized PnL plus fee/funding re-added
mixed currency without conversion
mixed aggregation level without reconciliation transform
mixed horizon without transform
duplicate component or reconciliation identity
trading fee without owner fee snapshot
funding without formula-version identity
```

## Owner-input blocker

Numerical execution costs remain blocked until both are admitted:

```text
owner-account-specific fee snapshot
real prospective order/book/fill inputs under an authorized execution experiment
```

Current state:

```text
Owner fee snapshot: BLOCKED_OWNER_READ_ONLY_CREDENTIALS
Real execution inputs: NOT_ADMITTED
Numerical transaction-cost estimate: NOT AUTHORIZED
```

## Explicit non-authorization

```yaml
real_order_request: false
private_trading_endpoint: false
owner_credentials_in_repository: false
real_book_or_fill_in_public_evidence: false
assumed_fee_rates: false
basis_computation: false
funding_pnl_computation: false
returns_computation: false
transaction_cost_estimation: false
empirical_fitting: false
strategy_testing: false
paper_trading: false
live_trading: false
capital_deployment: false
report_2_4_authorized: false
```

All six hypothesis verdicts remain `INCONCLUSIVE`.
