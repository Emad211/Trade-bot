# Report 2.3 — Controlling Status Addendum for Issue #57

**Status date:** 2026-07-21  
**Scope:** OKX executable-price, order/fill lifecycle, latency, spread/slippage, and cost-aggregation semantics  
**Precedence:** This addendum supersedes earlier Report 2.3 statements that described executable-price and cost semantics as undefined. Owner fee rates, real execution inputs, numerical costs, PnL, returns, and trading remain blocked.

## Gate outcome

```text
Issue #57: CLOSED — GO_OKX_EXECUTABLE_PRICE_AND_COST_SEMANTICS_CONTRACT
```

Independent blocker:

```text
BLOCKED_OWNER_FEE_OR_EXECUTION_INPUTS
```

## Verified evidence

```text
Workflow run: 29841870117
Triggering head: c509ac0a93629a0a77319fbd0298a0be23aad318
Permissions: contents read-only
Conclusion: SUCCESS
Ruff / lint / mypy: PASS
Scoped tests: 22 PASS
Artifact: 8499736417
Artifact digest: sha256:3367ac39c72b69f01c80ecdfbbe31276f9defcdff4373434d790144caf241d47
Evidence SHA-256: 0a65fcf91393decbb1032840791af5c4dcc7c0228a0ece7105bffb529e86d930
Real order request: false
Private trading endpoint: false
```

## Admitted semantic readiness

```yaml
buy_uses_best_ask: true
sell_uses_best_bid: true
midpoint_is_reference_only: true
last_mark_index_are_not_implicit_executable_prices: true
limit_price_is_not_fill_price: true
acknowledgement_is_not_execution: true
cancel_ack_is_not_final_state: true
partial_fill_quantity_weighting: true
residual_quantity_preserved: true
maker_taker_from_actual_fill: true
clock_units_explicit: true
fill_chronology_uses_fillTime: true
direction_aware_slippage: true
provider_cache_nonmonotonicity_preserved: true
cost_component_double_count_rejection: true
mixed_currency_level_and_horizon_rejection: true
owner_fee_snapshot_required: true
funding_formula_version_required: true
instrument_version_required: true
```

## Executable-price contract

```text
BUY executable quote: BEST_ASK
SELL executable quote: BEST_BID
Midpoint: reference only
Last / mark / index: non-executable by default
Order limit: constraint, not fill price
Unfilled quantity: no fabricated execution price
```

## Lifecycle and timing contract

```text
Acknowledgement: not execution
Cancellation acknowledgement: not final cancellation state
Maker/taker role: actual fill execution field
Partial fills: quantity weighted
Client/gateway unit: microseconds
Provider order/fill unit: milliseconds
Gateway receive: inTime
Gateway send: outTime
Order create/update: cTime / uTime
Fill match: fillTime
```

Negative, reordered, or mixed-unit clocks fail closed. Acknowledgement time cannot replace `fillTime`.

## Cost-component boundary

The model distinguishes spread, slippage, implementation shortfall, impact, adverse selection, latency, opportunity cost, trading fee, funding, liquidation/settlement cashflows, and position realized PnL.

It rejects:

```text
full and half spread both counted
implementation shortfall plus decomposed components
position aggregate plus fee/funding re-added
mixed currency without conversion
mixed aggregation level without transform
mixed horizon without transform
duplicate component or reconciliation key
fee without owner-account snapshot
funding without formula-version identity
```

## Remaining blocker state

```text
Owner fee snapshot: BLOCKED_OWNER_READ_ONLY_CREDENTIALS
Real order/book/fill inputs: NOT_ADMITTED
Numerical transaction costs: NOT AUTHORIZED
Basis / funding PnL / returns: NOT AUTHORIZED
Report 2.4: BLOCKED
```

## Explicit non-authorization

```yaml
real_order_placement: false
real_order_amendment: false
real_order_cancellation: false
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
leverage: false
capital_deployment: false
report_2_4_authorized: false
```

A semantic GO is not a numerical cost pass, paper-replication pass, or economic-edge pass. All six hypothesis verdicts remain `INCONCLUSIVE`.
