# Report 2.3 — Cboe VX Public Pilot Controlling Addendum

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Status date:** 2026-07-19  
**Status:** `PUBLIC_CONTRACT_ENGINEERING_VERIFIED; LICENSE_RETENTION_TIMING_AND_PRICE_LINKAGE_OPEN`

This document is the controlling status for the owner-accessible Cboe VX source path. It supplements the broader [Report 2.3 controlling status](02-03-current-controlling-status.md), the [owner-accessible source pivot](02-03-owner-accessible-exchange-native-source-pivot.md), and the detailed [Cboe VX evidence report](02-03-cboe-vx-public-contract-pilot-evidence.md).

## Controlling decision

```text
Source authority: Cboe Futures Exchange
Product: VX futures
Engineering pilot: VERIFIED
Raw retention: INCOMPLETE
Internal research license: PENDING_FORMAL_LICENSE_INTERPRETATION
Historical settlement availability timing: NOT VERIFIED
Canonical price linkage: NOT AUTHORIZED
Returns: NOT AUTHORIZED
```

Public reachability, parser success, and exact hashes do not by themselves authorize retention, price linkage, or return computation.

## Verified source identities

```text
VX_2022-09-21.csv | U (Sep 2022) | 15819 bytes
a74598b17c5e92b068ee46ee38aefdfe8423d62153bee7d879ff4eddc2fbb626

VX_2022-10-19.csv | V (Oct 2022) | 15850 bytes
270abe0333366e5395d88d6e56da51fa403962f03229d119a8208ece339c778d

Schema SHA-256:
7ec53b473b1418928b26414f98e433de7886cf501fedc56a31e70a7a913af3f2
```

The source provides separate `Close` and `Settle` fields. The parser preserves both and validates `Change` against the change in `Settle`.

## Verified deterministic pilot

```text
Pilot version: CBOE_VX_PUBLIC_CONTRACT_LEVEL_PILOT_V1
Window: 2022-09-01 through 2022-09-30
Contracts: 2
Rows: 35
Pilot CSV byte count: 12340
Pilot CSV SHA-256:
ebe1326a06bc7c11a96e4ca2d489ddba74c73965653991017a958e6ce6f13ad0
Manifest byte count: 2153
Manifest SHA-256:
6b04d359de6030f11dcdc49cd8c1a401448879f472dbcf0b3d172e5d905f6b34
```

The pilot is contract-level. It does not create a continuous series, back adjustment, roll-gap return, strategy PnL, or empirical verdict.

## Hosted verification

```text
Workflow: Cboe VX Public Contract Pilot
Run ID: 29696828324
Conclusion: SUCCESS
Branch commit: 6fc082c5e8465a695cd95db3e763e2545a554b43
Pull-request merge-test commit: 20d6a59b707da4aaf9d6226562b41fffaa651a35
```

Verified scope:

- Ruff passed;
- strict mypy passed;
- eight parser tests passed;
- exact official files were acquired;
- raw byte counts and SHA-256 identities matched;
- contract identities, dates, schema, and settlement reconciliation passed;
- current Cboe terms pages were retrieved and hashed;
- restricted raw, derived-price, and terms content was deleted before artifact upload;
- the safe evidence bundle was independently downloaded and rehashed.

## Safe evidence artifacts

```text
Safe evidence artifact ID: 8445247846
Digest: f87327eb392cc84baeb0dd33669becc0837d0a4972586dcf7ee83dd7b17c360b
Safe receipt artifact ID: 8445247974
Digest: 8a62084dcae1a1d788ac2ce16a1b191f501172731775648a2229f3b7cf8f0c91
Retention expiry: 2026-10-17
Storage: ACTIONS_SAFE_EVIDENCE_ONLY_RETENTION_90_DAYS
```

Independent inspection confirmed that neither artifact contains CSV, HTML, a `VX_*` file, or derived price rows. This is not raw immutable storage.

## Negative evidence retained

The date-parameterized daily settlement endpoint returned a 38-byte header-only CSV for `2022-09-16` and no data rows. It is rejected for historical 2022 settlement acquisition.

```text
SHA-256: fb3907637b20ec51927e44bd0c06628cc47fb9cde8f317c743131a779dbaf39d
Quarantine run: 29696287344
```

The exploratory raw-upload workflow was retired after the permanent safe-evidence workflow passed.

## Current authorization

```yaml
cboe_source_engineering: true
exact_parser_maintenance: true
schema_and_formula_testing: true
license_research: true
historical_availability_research: true
private_storage_contract_design: true
contract_selection_contract_design: true
raw_publication: false
raw_long_term_retention: false
canonical_price_linkage: false
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

## Next controlling gate

Issue `#44` owns:

```text
CBOE_VX_LICENSE_RETENTION_AND_HISTORICAL_AVAILABILITY_GATE
```

It must resolve internal-research and retention rights, compliant private immutable storage if permitted, historical settlement `available_at`, explicit CFTC-to-VX contract selection, expiry and roll-boundary handling without roll-gap PnL, and a no-lookahead same-contract price-linkage proposal.

The result must be either `GO_PRIVATE_RETENTION_AND_TIMING_CONTRACT` or `BLOCKED_LICENSE_OR_TIMING`. Neither result is an economic-edge pass.

## Final controlling verdict

```text
OWNER-ACCESSIBLE OFFICIAL SOURCE: CONFIRMED
EXACT CONTRACT ACQUISITION DURING RUN: CONFIRMED
EXACT PARSER: CONFIRMED
CLOSE / SETTLE SEPARATION: CONFIRMED
CONTINUOUS OR BACK-ADJUSTED SERIES: NOT USED
SAFE EVIDENCE HANDLING: CONFIRMED
RAW RETENTION: INCOMPLETE
LICENSE INTERPRETATION: OPEN
HISTORICAL AVAILABILITY TIMING: OPEN
CANONICAL PRICE LINKAGE: NOT AUTHORIZED
RETURNS: NOT AUTHORIZED
PAPER REPLICATION: NOT COMPLETE
ECONOMIC EDGE: NOT ESTABLISHED
EDGE-FUT-POSITION-001: INCONCLUSIVE
REPORT 2.4: BLOCKED
```
