# Report 2.3 — Verified OKX Fee, Fill, Funding-Bill, and Accounting Contract

**Status date:** 2026-07-21  
**Issue:** #56  
**Outcome:** `GO_OKX_FEE_AND_FUNDING_ACCOUNTING_CONTRACT`  
**Independent blocker:** `BLOCKED_ACCOUNT_SPECIFIC_FEE_SNAPSHOT`

## Scope

This gate freezes the accounting identities and anti-double-counting rules required before any trading-fee, funding-PnL, return, or transaction-cost calculation.

The GO outcome authorizes only the tested data model and synthetic accounting validation. It does not authorize an assumed fee rate, a real account request, cost estimation, PnL, returns, or trading.

## Verified workflow

```text
Workflow: OKX Fee and Funding Accounting Contract
Run ID: 29838156447
Triggering head: c2a8141b630b79641555d7868efe45f7eaa30d67
Permissions: contents read-only
Conclusion: SUCCESS
```

```text
Ruff format: PASS
Ruff lint: PASS
Mypy strict: PASS
Scoped tests: 11 PASS
Synthetic evidence generator: PASS
Independent safe-evidence verifier: PASS
Real account request: false
```

Safe artifact:

```text
Artifact ID: 8498218083
Artifact digest: sha256:f2e130d28a154be8428d4aa105b10cf808a78fcf9a6cb3d936546bf1d241cb13
Evidence bytes: 3,655
Evidence SHA-256: 726268d913d2e6e5ae27b04295bac08e8f1a1e4a21a7b71e7cba6d4c7014c2c6
```

The artifact contains no credentials, account IDs, orders, fills, bills, prices, sizes, fee amounts, funding amounts, balances, or PnL values.

## Account-specific fee-rate contract

The frozen account-rate endpoint is:

```text
GET /api/v5/account/trade-fee
Permission: Read
Authentication: required
```

The admitted query contracts are intentionally different:

```text
SPOT: instType=SPOT, instId=BTC-USDT
SWAP: instType=SWAP, instFamily=BTC-USDT
```

The contract preserves:

```text
Positive maker/taker rate: rebate
Negative maker/taker rate: commission
Fee level: account-specific
Generic Lv1 examples: not an owner-account snapshot
Zero-fee exceptions: not guaranteed to appear in Open API
Assumed fee rate: prohibited
```

No real account-specific fee snapshot was acquired because the connected environment has no owner-controlled read-only credentials.

## Per-fill contract

Per-fill records are held at aggregation level `PER_FILL`.

```text
Trade chronology: fillTime
Record generation time: ts
ts replaces fillTime: false
Fee currency: explicit
Fee currency inferred from quote currency: false
Liquidity role: execType when applicable
```

Reconciliation identities are mandatory:

```text
tradeId
ordId
billId
```

A fee-rate field is not assumed to be available across all product types. In particular, a SWAP fill cannot be used to infer an account fee rate.

## Funding-bill contract

Funding cashflows are held at aggregation level `PER_BILL` and retain their provider subtype:

```text
173: funding fee expense
174: funding fee income
```

They remain separate from:

```text
trading fee
fill PnL
position fee aggregate
liquidation penalty
settled PnL
```

The provider amount sign is preserved and is not rewritten into a project-specific sign convention.

## Position aggregate contract

The provider-level relationship is frozen as:

```text
realizedPnl = pnl + fee + fundingFee + liqPenalty + settledPnl
```

This field is a `POSITION_AGGREGATE`. The project must not add per-fill fees or funding bills to this aggregate a second time.

The accounting layer rejects:

```text
mixed aggregation levels without a declared transform
mixed currencies without a conversion contract
duplicate reconciliation keys
re-adding fill fees to position realizedPnl
re-adding funding bills to position realizedPnl
```

## Funding-formula version boundary

The admitted current formula version is:

```text
Formula ID: OKX_PERPETUAL_FUNDING_8_OVER_N_2026_V1
Source publication: 2026-05-29
Migration start: 2026-06-01
Conservative full-admission boundary: 2026-06-04
Interval factor: 8/N
Fixed interest rate: 0.0001
Supported N: 1, 2, 4, 8 hours
```

This formula is not projected backward into March 2022. Observations during a migration window require provider formula identity or remain ambiguous.

## Synthetic validation

The tests prove:

```text
Exact SPOT and SWAP fee queries: PASS
Charge/rebate sign preservation: PASS
Fee-currency non-inference: PASS
fillTime chronology: PASS
Funding subtype separation: PASS
Position reconciliation: PASS
Double-count rejection: PASS
Formula-version boundary: PASS
```

All synthetic monetary values stay inside tests and are absent from public evidence.

## Owner-account blocker

A real snapshot requires a separate owner-side action with:

```text
read-only API credentials
withdrawal permission disabled
trading permission disabled
owner-controlled secret storage
confirmed regional endpoint
explicit owner confirmation
```

Current state:

```text
Real account request performed: false
Actual account fee rates acquired: false
Owner snapshot status: BLOCKED_OWNER_READ_ONLY_CREDENTIALS
```

## Explicit non-authorization

```yaml
assumed_fee_rates: false
account_fee_snapshot: false
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

All admitted hypothesis verdicts remain `INCONCLUSIVE`.
