# Report 2.3 — Provider-Gate Controlling Addendum

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Status date:** 2026-07-19  
**Status:** `PROVIDER_REQUIREMENTS_VERIFIED; PRIMARY_CANDIDATE_SELECTED; AUTHENTICATED_PRICE_LINKAGE_NOT_COMPLETE`

This addendum is the controlling status for the provider-specific price-linkage gate. It supplements the broader [Report 2.3 controlling status](02-03-current-controlling-status.md) and supersedes any earlier wording that could imply a provider was accepted merely because a product root or dataset candidate was identified.

Detailed evidence:

- [Provider candidate and point-in-time price-linkage evidence](02-03-provider-price-linkage-candidate-evidence.md)
- [Machine-readable provider candidate evidence](02-03-provider-price-linkage-candidate-evidence.yaml)
- [Provider candidate contract](02-03-provider-price-linkage-candidate-contract.yaml)
- [Official provider and exchange-native source registry](02-03-provider-price-linkage-official-sources.json)
- [Durable compressed provider candidate plan](02-03-provider-candidate-plan.csv.gz.b64)

---

## Controlling decision

```text
Primary technical integration candidate:
DATABENTO

Accepted provider:
none

Authenticated provider probe executed:
false

Purchase authorized:
false
```

Databento was selected only as the first provider to test because one candidate interface can theoretically cover ordinary products from CME/CBOT, ICE Futures U.S., and CFE.

Candidate selection is not provider acceptance.

---

## Verified plan identity

```text
Plan version:
CFTC_TFF_2022_09_13_DATABENTO_CANDIDATE_PLAN_V1

Rows:
54

Byte count:
28918

SHA-256:
cd2430c7fdd0b3a68a1093925d755c242081372fbe41668cc53436893c274062
```

Coverage of the 47 ordinary historical screen-tradable roots:

```text
GLBX.MDP3: 43
IFUS.IMPACT: 3
XCBF.PITCH: 1
```

Excluded or special rows remain:

```text
Non-tradable consolidated aggregates: 3
Historical later-delisted products: 2
Nonstandard execution product: 1
Technical-symbol-pending product: 1
```

---

## Representative authenticated probe

The project generated a probe request for:

```text
ZN — GLBX.MDP3 — ZN.FUT
ES — GLBX.MDP3 — ES.FUT
NIY — GLBX.MDP3 — NIY.FUT
DX — IFUS.IMPACT — DX.FUT
VX — XCBF.PITCH — VX.FUT
```

These parent symbols are candidate lookup inputs only.

They are not accepted provider contract identifiers.

The probe requires:

- dataset and schema discovery;
- 2022 dataset range and condition;
- point-in-time parent-to-child resolution;
- definition records;
- final actual settlement statistics;
- cost before download;
- license snapshot;
- request and response hashes;
- immutable storage identity.

Probe state:

```text
Authentication required:
DATABENTO_API_KEY

Maximum authorized cost:
USD 0.00

Execution status:
BLOCKED_MISSING_AUTHENTICATED_ACCOUNT_AND_EXPLICIT_COST_APPROVAL
```

---

## Hosted verification

```text
Workflow:
CFTC TFF 2022 Provider Candidate Plan

Run ID:
29687144619

Conclusion:
SUCCESS
```

Passed scope:

- Ruff;
- strict mypy;
- seven provider-plan tests;
- deterministic plan construction;
- contract and source-registry hash checks;
- 54-row coverage checks;
- GLBX/IFUS/XCBF candidate-count checks;
- aggregate and special-case checks;
- zero-price-authorization checks;
- bundle and receipt upload.

Artifacts:

```text
Plan bundle ID:
8442435407

Plan bundle digest:
d23721a77dc1c16e434df6cb4fdf4491ab1c9f3698be344d26182662dac0b5cc

Receipt ID:
8442435528

Receipt digest:
9084ecc59f80dbe23d063e9f8fdd957c202cb568a1de6b999fd73182718d5465

Expiry:
2026-10-17
```

Both artifact ZIP digests and all three internal file hashes were independently recomputed after download.

---

## Fail-closed authorization

```yaml
provider_requirements_contract: true
primary_provider_candidate_selected: true
authenticated_metadata_probe_design: true
exchange_native_cross_check_design: true

provider_accepted: false
purchase_authorized: false
authenticated_provider_probe_executed: false
provider_contract_ids: 0
price_linkage_authorized_rows: 0
returns_computation: false
empirical_fitting: false
strategy_tournament: false
paper_trading: false
live_trading: false
leverage: false
capital_deployment: false
report_2_4_full_authorization: false
```

No root-symbol resemblance may be converted into a price series.

No OHLCV bar may be used as a substitute for official settlement.

No consolidated CFTC row may receive a direct price series.

---

## Remaining gate

The next gate is:

```text
AUTHENTICATED_ZERO_PURCHASE_PROVIDER_METADATA_PROBE
```

It must either:

1. produce verified point-in-time metadata, definition, settlement, cost, and license evidence for the five representative roots; or
2. reject Databento as the primary provider candidate and record the failure.

The next gate must not download paid bulk data and must not spend credits or cash without a separate explicit authorization.

---

## Final controlling verdict

```text
PROVIDER REQUIREMENTS CONTRACT: CONFIRMED
PRIMARY TECHNICAL CANDIDATE: DATABENTO_SELECTED_NOT_ACCEPTED
THEORETICAL ORDINARY-ROOT COVERAGE: CONFIRMED_47
HOSTED PROVIDER-PLAN WORKFLOW: PASS
INDEPENDENT ARTIFACT REHASH: PASS
AUTHENTICATED PROVIDER EVIDENCE: NOT ACQUIRED
PROVIDER CONTRACT IDENTIFIERS: ZERO
PRICE-LINKAGE-AUTHORIZED ROWS: ZERO
RETURNS AUTHORIZED: NO
PAPER REPLICATION: NOT COMPLETE
ECONOMIC EDGE: NOT ESTABLISHED
EDGE-FUT-POSITION-001: INCONCLUSIVE
REPORT 2.4: BLOCKED
```
