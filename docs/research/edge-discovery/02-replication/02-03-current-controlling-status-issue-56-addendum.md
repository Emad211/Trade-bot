# Report 2.3 — Controlling Status Addendum for Issue #56

**Status date:** 2026-07-21  
**Scope:** OKX account fee, fill, funding-bill, position aggregate, and funding-formula accounting contract  
**Precedence:** This addendum supersedes earlier Report 2.3 statements about OKX fee/accounting readiness wherever they conflict. Unrelated source, retention, historical-blocker, and non-authorization statements remain unchanged.

## Gate outcome

```text
Issue #56: CLOSED — GO_OKX_FEE_AND_FUNDING_ACCOUNTING_CONTRACT
```

Independent unresolved blocker:

```text
BLOCKED_ACCOUNT_SPECIFIC_FEE_SNAPSHOT
```

The GO authorizes only the tested accounting schema, chronology, reconciliation, aggregation, sign, currency, and formula-version rules. It does not authorize assumed fees, an owner-account request, transaction-cost estimation, PnL, returns, strategy testing, or trading.

## Verified workflow and evidence

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
Real account request performed: false
```

```text
Artifact ID: 8498218083
Artifact digest: sha256:f2e130d28a154be8428d4aa105b10cf808a78fcf9a6cb3d936546bf1d241cb13
Evidence bytes: 3,655
Evidence SHA-256: 726268d913d2e6e5ae27b04295bac08e8f1a1e4a21a7b71e7cba6d4c7014c2c6
```

Durable evidence:

- `02-03-okx-fee-and-funding-accounting-contract-evidence.json`
- `02-03-okx-fee-and-funding-accounting-contract-evidence.yaml`
- `02-03-okx-fee-and-funding-accounting-contract-evidence.md`
- `02-03-okx-fee-and-funding-accounting-contract-gate.yaml`

## Account-fee contract

The account-specific fee-rate endpoint is authenticated and read-only:

```text
GET /api/v5/account/trade-fee
```

The exact admitted query contracts are:

```text
SPOT: instType=SPOT, instId=BTC-USDT
SWAP: instType=SWAP, instFamily=BTC-USDT
```

Frozen semantics:

```text
Positive maker/taker rate: rebate
Negative maker/taker rate: commission
Fee level: owner-account-specific
Generic Lv1 example: not an owner snapshot
Zero-fee exception coverage in Open API: not guaranteed
Assumed fee rate: prohibited
```

## Fill chronology and fee-currency contract

Per-fill records remain at `PER_FILL` aggregation level.

```text
Trade chronology: fillTime
Record-generation time: ts
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

A SWAP fill does not authorize inference of an account fee rate.

## Funding-bill contract

Funding cashflows remain `PER_BILL` records with provider subtypes:

```text
173: funding fee expense
174: funding fee income
```

They remain separate from trading fee, fill PnL, liquidation penalty, settled PnL, and position aggregates. Provider amount signs are preserved.

## Position aggregate and double-count protection

The provider position relationship is frozen as:

```text
realizedPnl = pnl + fee + fundingFee + liqPenalty + settledPnl
```

The project must not add per-fill fees or funding bills to this position aggregate again.

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
Conservative admission boundary: 2026-06-04
Interval factor: 8/N
Fixed interest rate: 0.0001
Supported N: 1, 2, 4, 8 hours
```

This formula is not projected backward into March 2022. A migration-window observation remains ambiguous unless the provider formula identity is known.

## Owner-account blocker

A real account-specific fee snapshot requires:

```text
owner-controlled read-only credentials
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

No generic fee article, public fee table, or synthetic rate may substitute for the owner snapshot.

## Admitted authorization

```yaml
fee_accounting_schema: true
fill_chronology_contract: true
fee_currency_contract: true
funding_bill_subtype_contract: true
position_reconciliation_contract: true
double_count_rejection: true
funding_formula_version_lineage: true
synthetic_accounting_validation: true
```

## Explicit non-authorization

```yaml
owner_account_fee_snapshot: false
assumed_fee_rates: false
real_account_request_in_ci: false
credentials_in_repository: false
account_values_in_public_evidence: false
historical_fee_tier_backfill: false
current_funding_formula_backfill: false
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

All six hypothesis verdicts remain `INCONCLUSIVE`. The next metadata-level work may define executable-price, spread, slippage, market-impact, and cost-aggregation contracts, but no numerical cost or return may be computed until owner fee rates and real execution inputs are admitted.
