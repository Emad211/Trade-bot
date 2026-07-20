# Report 2.3J — Verified Binance BTCUSDT Public-Data Ephemeral Pilot

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Parent:** [Report 2.3 controlling status](02-03-current-controlling-status.md)  
**Evidence date:** 2026-07-20  
**Status:** `OFFICIAL_ARCHIVES_CHECKSUM_VERIFIED_EPHEMERALLY; SAFE_METADATA_ONLY_STAGED; RAW_RETENTION_NOT_AUTHORIZED`

---

## 1. Decision

The project completed a bounded engineering validation of six official Binance public-data archive objects for `BTCUSDT`, calendar month `2024-01`.

The workflow verified the official ZIP objects and their paired provider `.CHECKSUM` objects in memory. It validated ZIP safety, CRC, exact CSV shape, timestamp range, cadence, row counts, and alignment. It then discarded the raw ZIP and CSV bytes and uploaded only a safe JSON profile containing hashes, byte counts, schema fingerprints, row counts, timestamp bounds, and non-promotional authorization flags.

The completed work establishes:

```text
Official public archive URLs: CONFIRMED
Paired official checksum objects: CONFIRMED
ZIP SHA-256 equals provider checksum: CONFIRMED FOR SIX OBJECTS
ZIP CRC and member safety: CONFIRMED
CSV schema and row counts: CONFIRMED
Five hourly timestamp grids: EXACTLY ALIGNED
Funding schedule: 93 ORDERED UNIQUE OBSERVATIONS
Safe evidence artifact: CONFIRMED
Raw ZIP/CSV bytes uploaded or retained: NO
Derived price/funding rows uploaded or retained: NO
Basis, funding PnL, or returns computed: NO
```

This work does **not** establish:

- a complete Binance point-in-time instrument/version ledger;
- the historical first-publication time of the monthly archives;
- authorization for persistent raw-data retention or redistribution;
- a basis or funding-return calculation;
- a paper-level empirical replication;
- an economic edge.

---

## 2. Fixed pilot scope

```text
Venue/source family:
Binance Public Data

Official host:
data.binance.vision

Official documentation repository:
binance/binance-public-data

README blob identity:
311354cd82a76bcaaec588e6818e6c12644abef0

Symbol:
BTCUSDT

Calendar month:
2024-01

Timestamp unit:
Milliseconds
```

The fixed source identities were:

1. Spot `klines`, interval `1h`;
2. USD-M futures `klines`, interval `1h`;
3. USD-M `markPriceKlines`, interval `1h`;
4. USD-M `indexPriceKlines`, interval `1h`;
5. USD-M `premiumIndexKlines`, interval `1h`;
6. USD-M monthly `fundingRate`.

Each ZIP was paired with the official object at the same URL plus `.CHECKSUM`.

---

## 3. Fail-closed implementation

Implementation:

```text
src/hybrid_trader/replication/binance_public_pilot.py
scripts/validate_binance_btcusdt_public_pilot.py
```

Tests:

```text
tests/test_binance_public_pilot.py
```

Workflow:

```text
.github/workflows/binance-btcusdt-public-ephemeral-pilot.yml
```

The implementation enforces:

- HTTPS only;
- exact allowlisted host `data.binance.vision`;
- redirect host revalidation;
- provider checksum filename binding;
- observed ZIP SHA-256 equality with provider checksum;
- valid ZIP structure and CRC;
- one non-directory member only;
- no encryption;
- no absolute path or path traversal;
- bounded compressed and uncompressed sizes;
- bounded compression ratio;
- exact expected member filename;
- UTF-8 CSV parsing;
- exact positional/header schema;
- expected month and timestamp unit;
- sorted unique timestamps;
- complete hourly coverage for five Kline sources;
- exact alignment of the five hourly timestamp grids;
- fixed funding row count, declared interval, month span, and bounded grid jitter;
- no raw-data file write by the validation program;
- no raw or derived market-data upload by the workflow;
- no automatic promotion to a paper, edge, or trading verdict.

The GitHub-hosted workflow ran Ruff, strict mypy, and twelve bounded unit tests before the official-data validation.

---

## 4. Successful hosted workflow

```text
Workflow:
Binance BTCUSDT Public Ephemeral Pilot

Run ID:
29761078615

Workflow conclusion:
SUCCESS

Head branch:
agent/edge-research-reports

Head commit represented by the workflow run:
26eb72a85427889502a4c761b30486ad6f7c0fed

GitHub pull-request merge commit recorded inside the receipt:
4df4d6b86e1b2fdc0f864d8ef5c3e62369f6830f
```

Every dedicated step completed successfully:

- checkout;
- Python 3.11 setup;
- dependency installation;
- scoped Ruff checks;
- strict mypy;
- twelve unit tests;
- six official ZIP downloads and six checksum downloads;
- ephemeral ZIP/CSV validation;
- independent safe-evidence verification;
- proof that only the safe JSON remained under `build/`;
- safe-evidence artifact upload;
- safe receipt creation and upload.

The success applies only to this dedicated workflow. It does not convert unrelated repository-wide workflow failures into successes.

---

## 5. Safe artifact evidence

### Safe evidence artifact

```text
Artifact ID:
8468794862

Artifact name:
binance-btcusdt-public-safe-evidence-4df4d6b86e1b2fdc0f864d8ef5c3e62369f6830f

Artifact archive digest:
575cc1a07f299dd52f8c1a889c78df4ba3989976e7d4ff33b11d0b38ac3ad344

Retention expiry:
2026-10-18T16:47:15Z
```

The artifact ZIP contains exactly one unencrypted member:

```text
binance-btcusdt-public-ephemeral-pilot-evidence.json
```

Member evidence:

```text
Uncompressed byte count:
8448

SHA-256:
93b8c06ba836a3d61b9fa0fba1b4b377f3518841b2c72db36b96ee6196fede7b
```

### Receipt artifact

```text
Artifact ID:
8468795317

Artifact name:
binance-btcusdt-public-safe-receipt-4df4d6b86e1b2fdc0f864d8ef5c3e62369f6830f

Artifact archive digest:
3bcfc1a5a14170fe1bb636ab1603640a5dfaa222c91bf750c3404c9ca47eaf9c

Retention expiry:
2026-10-18T16:47:15Z
```

The receipt member is:

```text
binance-btcusdt-public-safe-receipt.json

Byte count:
923

SHA-256:
a0654baa54c25fb0f840ef31422e7108f2b9ead4347544fd24ab94f436da3f64
```

The downloaded artifact ZIPs were independently opened outside the Actions runner. They contained only the two expected JSON documents. No `.csv`, source `.zip`, HTML, price row, funding-rate row, or derived basis/return row was present.

A recursive key scan of the safe evidence found no stored `open`, `high`, `low`, `close`, `price`, `volume`, `funding_rate`, or `last_funding_rate` field.

---

## 6. Per-source immutable identities observed ephemerally

| Source ID | ZIP bytes | ZIP / provider SHA-256 | Member bytes | Member SHA-256 | Rows | Header |
|---|---:|---|---:|---|---:|---|
| `SPOT_KLINES` | 43,482 | `cf873a185bd5b24b8e00034e49583fcb49928e0c3a45c6fc27a632a683655417` | 118,568 | `17546488eeffe16aa3ee02c12c1662f0d5c1bc33b4686db8da72a92fe5928cbe` | 744 | No |
| `UM_KLINES` | 38,890 | `bf673f3d10804a951e8bac56dd2473486f113025971d43ebe5258ec40f9bfeb3` | 91,706 | `ac2f326bd322c623e6060233597646ba40ce609d86dc4faeabe2196dc36f20c0` | 744 | Yes |
| `UM_MARK` | 23,278 | `759f86a22dadb455c87a3f90f6a9134c73d24a55a7596f0b96e193b5d45cdb49` | 75,189 | `72308856b3a79bc8ce55eb08b195e232fc989a09c18d7cb1696fb1a07f951911` | 744 | Yes |
| `UM_INDEX` | 22,067 | `31288538f992393fbaa31e3a2a55149330de4658fdafca7bebfb51faf6b3023d` | 76,746 | `2bfbcad584eb6cbd24fa2b156926b204a292b23169fd0c621a4f2f1f9219c60d` | 744 | Yes |
| `UM_PREMIUM` | 16,935 | `169a55033751ee31d3873ad5402aac9c5323ca7481a4345cbd11e0111a30aa48` | 65,462 | `01aec7865b1a9bdd76ae01c2b57364012d79d3c835308901ceb8e20f9c5e623c` | 744 | Yes |
| `UM_FUNDING` | 696 | `3e0d30870672aa8f0f937881056e3cfd55913ae5c780cd50b33f2763aa0ba58e` | 2,562 | `232a13d92487efef8ce0d645301abe611f56eacb70023194b97c038d7a8a2c9b` | 93 | Yes |

For every source, the observed ZIP SHA-256 equaled the checksum supplied by the paired official `.CHECKSUM` object.

---

## 7. Schema evidence

The five Kline objects resolved to the same twelve-field schema fingerprint:

```text
Schema field count:
12

Schema SHA-256:
6b3a48dd8da4061dd7bbc0aeb9b957b1cc4b275459e20963cd09a7f20f3f34cf
```

The actual admitted Kline header contract is:

```text
open_time
open
high
low
close
volume
close_time
quote_volume
count
taker_buy_volume
taker_buy_quote_volume
ignore
```

The funding object resolved to:

```text
Schema field count:
3

Schema SHA-256:
72939a3c139771592367cd4891e53d9fb997c04d8c3f7f1399cbc77c88e5a8e1
```

Funding header contract:

```text
calc_time
funding_interval_hours
last_funding_rate
```

The schema fingerprints describe the observed January 2024 artifact versions. A future provider object with changed bytes or schema must receive a new artifact identity and validation decision.

---

## 8. Timestamp and cadence findings

### Five hourly sources

Each hourly object contained:

```text
Rows:
744

First open timestamp:
1704067200000

Last open timestamp:
1706742000000

Cadence:
3600000 milliseconds

Cadence breaks:
0
```

The Spot, futures trade, mark, index, and premium-index timestamp grids were exactly equal.

### Funding source

```text
Rows:
93

First calculation timestamp:
1704067200000

Last calculation timestamp:
1706716800000

Declared funding interval:
8 hours

Rows with a nonzero difference from the fixed monthly eight-hour grid:
15

Maximum absolute grid jitter:
3 milliseconds

Material cadence failures:
0
```

The parser compares each raw funding timestamp to its expected monthly eight-hour grid position. It permits at most `±3` milliseconds for this fixed artifact version. It does not normalize or rewrite any timestamp. A difference exceeding three milliseconds remains a hard failure.

This is an empirical contract for the identified January 2024 funding archive. It is not automatically generalized to another symbol, month, market, or provider version.

---

## 9. Retention and license classification

The official `binance/binance-public-data` README identifies the project as MIT-licensed and documents programmatic ZIP downloads with paired checksum files. However, this pilot deliberately does not convert that repository statement into a blanket legal conclusion about every possible retention, redistribution, derived-data, or jurisdictional use.

Current classification:

```text
Ephemeral in-memory technical validation: COMPLETED
Provider checksum verification: COMPLETED
Safe hash/profile retention: COMPLETED
Raw ZIP/CSV retention by this workflow: NO
Raw redistribution: NO
Formal data-terms review for persistent research storage: PENDING
Historical archive available_at: NOT ESTABLISHED
Point-in-time contract/version metadata: NOT COMPLETE
```

Because Binance documents that archive objects may be updated, the observed hashes are retained as the exact identities of the objects seen by this run. A later retrieval must not silently inherit these identities.

---

## 10. Authorization consequence

This evidence authorizes:

```yaml
continued_public_source_metadata_review: true
recheck_of_the_same_six_checksums: true
safe_hash_and_schema_profile_retention: true
formal_terms_and_retention_review: true
point_in_time_instrument_metadata_design: true
historical_archive_availability_research: true
```

It does not authorize:

```yaml
persistent_raw_archive_retention: false
raw_redistribution: false
basis_computation: false
funding_pnl_computation: false
return_computation: false
empirical_fitting: false
parameter_tuning: false
strategy_tournament: false
paper_trading: false
live_trading: false
leverage: false
capital_deployment: false
report_2_4_full_authorization: false
```

---

## 11. Final controlling verdict

```text
OFFICIAL BINANCE ARCHIVE IDENTITIES: CONFIRMED FOR SIX FIXED OBJECTS
PAIRED PROVIDER CHECKSUMS: CONFIRMED
ZIP/CSV TECHNICAL VALIDATION: PASS
FIVE HOURLY GRIDS: EXACTLY ALIGNED
FUNDING GRID: PASS WITH 15 RECORDED NONZERO JITTERS, MAX 3 MS
SAFE METADATA ARTIFACT: CONFIRMED
RAW OR DERIVED MARKET ROWS STORED: NO
RAW RETENTION AUTHORIZATION: NOT GRANTED
HISTORICAL AVAILABLE_AT: NOT COMPLETE
POINT-IN-TIME INSTRUMENT METADATA: NOT COMPLETE
BASIS / FUNDING PNL / RETURNS: NOT COMPUTED
PAPER REPLICATION: NOT COMPLETE
ECONOMIC EDGE: NOT ESTABLISHED
EDGE-CRYPTO-BASIS-001: INCONCLUSIVE
EDGE-CRYPTO-RV-001: INCONCLUSIVE
REPORT 2.4: BLOCKED
```

The next valid work is limited to permission/retention analysis, point-in-time instrument metadata, archive publication-time semantics, and independent public-source cross-check design. It is not a signal or strategy experiment.