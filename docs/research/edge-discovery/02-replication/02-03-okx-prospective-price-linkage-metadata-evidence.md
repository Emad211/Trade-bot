# Verified OKX Prospective Price-Linkage Metadata Pilot

**Issue:** #53  
**Outcome:** `GO_PROSPECTIVE_OKX_PRICE_LINKAGE_METADATA_PILOT`  
**Status date:** 2026-07-21  
**Collection mode:** `PROSPECTIVE_ONLY`

## 1. Purpose

This pilot freezes current official source identities, schemas, clocks, and safe-retention boundaries for four OKX public market-data sources required by future research on `EDGE-CRYPTO-BASIS-001` and `EDGE-CRYPTO-RV-001`.

The pilot does not retain prices and does not authorize any calculation.

## 2. Verified workflow

```text
Workflow: OKX Prospective Price Linkage Metadata Pilot
Run ID: 29828971655
Triggering head: 0f8af9f62ef6ebe65777117f9b014fc1332a413f
Permissions: contents read-only
Conclusion: SUCCESS
Formatting: PASS
Lint: PASS
Mypy: PASS
Adversarial tests: 12 PASS
Bounded live probe: PASS
Independent safe-evidence verifier: PASS
```

Artifact:

```text
Artifact ID: 8494458677
Artifact digest: sha256:9442a7cab8d7bd2b400505676e73fef08fbf1ee90f5ff136b45b38ed16806dad
Evidence bytes: 9322
Evidence SHA-256: 478d6b113ef618752e3ada8ddf3cbadd3fd10cecd7ee2771c21ae6eafd2b7a6d
```

## 3. Verified source identities

| Source | Endpoint | Identity | Schema fields | Schema SHA-256 |
|---|---|---|---:|---|
| Spot ticker | `/api/v5/market/ticker?instId=BTC-USDT` | `SPOT / BTC-USDT` | 16 | `a0efda49b5a0800771ceb73e426c7ea32649d12ec43296cc9a08f4864dbd2c78` |
| Swap ticker | `/api/v5/market/ticker?instId=BTC-USDT-SWAP` | `SWAP / BTC-USDT-SWAP` | 16 | `a0efda49b5a0800771ceb73e426c7ea32649d12ec43296cc9a08f4864dbd2c78` |
| Mark price | `/api/v5/public/mark-price?instType=SWAP&instId=BTC-USDT-SWAP` | `SWAP / BTC-USDT-SWAP` | 4 | `6bf8819de4ac4a636c639c06322c30591d1834517402895b9b830916d0bbbe3f` |
| Index ticker | `/api/v5/market/index-tickers?instId=BTC-USDT` | `BTC-USDT` | 8 | `9aa78fdea927d6e3737b088b7a504f68be1b444aec4fe63acee5222d3ee7ef12` |

The linkage contract distinguishes the traded spot instrument, traded swap instrument, mark-price identity, and index identity. Name similarity is not treated as executable linkage.

## 4. Provider timestamp evidence

Request order:

```text
spot ticker
swap ticker
mark price
index ticker
```

Provider-timestamp order:

```text
swap ticker
spot ticker
index ticker
mark price
```

```text
Provider timestamps monotonic in request order: false
Provider timestamp spread: 1116 ms
Provider timestamp after response: false for all four sources
```

This behavior is retained as a cache/timing diagnostic. Provider timestamps are not rewritten, sorted into request order, or assumed monotonic across sources or repeated requests.

## 5. Safe-retention proof

The parser validated market-value fields as finite decimals in memory, but the retained evidence contains none of the following values:

```text
last
bid / ask
mark price
index price
volume
ordered price rows
raw response bodies
```

Retained evidence is limited to:

```text
source and endpoint identity
query-parameter names
HTTP and application status
content type and byte count
response SHA-256
exact schema fields and schema SHA-256
instrument/index identity fields
provider timestamp
request, response, and research clocks
timestamp-age diagnostics
source-health status
```

## 6. Admitted scope

The GO authorizes only:

```text
prospective metadata probing
source identity monitoring
schema monitoring
provider timestamp monitoring
cache-behavior diagnostics
source-health monitoring
safe hash and metadata retention
```

## 7. Explicit non-authorization

```text
Historical backfill: false
Persistent raw market values: false
Basis computation: false
Funding PnL: false
Returns: false
Transaction-cost estimation: false
Empirical fitting: false
Parameter tuning: false
Strategy testing: false
Paper/live trading: false
Leverage: false
Capital deployment: false
Report 2.4: blocked
Economic edge: not established
```

The next gate must separately resolve whether bounded private retention of synchronized spot, swap, mark, and index values is permitted and technically controlled. This metadata GO cannot be used as a substitute for that retention and sampling gate.
