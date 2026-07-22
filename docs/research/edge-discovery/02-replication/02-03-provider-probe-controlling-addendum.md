# Report 2.3 — Provider-Probe Controlling Addendum

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Status date:** 2026-07-19  
**Status:** `PROBE_IMPLEMENTATION_AND_HOSTED_GATE_VERIFIED; AUTHENTICATION_BLOCKED_MISSING_DATABENTO_API_KEY`

This document is the controlling status for the authenticated provider-probe gate. It supplements the broader [Report 2.3 controlling status](02-03-current-controlling-status.md) and supersedes the "next gate not yet executed" wording in the earlier [provider-gate addendum](02-03-provider-gate-controlling-addendum.md).

Detailed evidence:

- [Databento zero-purchase probe evidence](02-03-databento-zero-purchase-probe-evidence.md)
- [Machine-readable probe evidence](02-03-databento-zero-purchase-probe-evidence.yaml)
- [Provider candidate evidence](02-03-provider-price-linkage-candidate-evidence.md)
- [Provider candidate contract](02-03-provider-price-linkage-candidate-contract.yaml)

---

## Controlling decision

```text
Primary technical candidate:
DATABENTO

Accepted provider:
none

Probe implementation:
CONFIRMED

Permanent hosted workflow:
CONFIRMED

Authenticated provider probe:
NOT EXECUTED

Blocking condition:
MISSING DATABENTO_API_KEY REPOSITORY SECRET
```

The missing secret does not prove that Databento lacks coverage, entitlement, acceptable data quality, or pricing. It only proves that the authenticated account gate could not begin.

Databento remains:

```text
SELECTED_NOT_ACCEPTED
```

---

## Verified hosted result

```text
Workflow:
Databento Zero-Purchase Metadata Probe

Run ID:
29690453120

Workflow conclusion:
SUCCESS

Gate execution status:
BLOCKED_MISSING_DATABENTO_API_KEY
```

The workflow conclusion is green because the gate evaluator correctly produced and independently verified a fail-closed blocker artifact. It is not an authenticated-provider pass.

Passed scope:

- installation of `databento==0.81.0`;
- Ruff;
- strict mypy;
- seven zero-purchase tests;
- request-contract generation;
- missing-secret detection;
- no-purchase invariant verification;
- output-file hashing;
- bundle and receipt upload.

---

## Verified non-operations

```text
Provider API operations executed: 0
Time-series downloads executed: 0
Batch jobs submitted: 0
Credits or cash authorized: USD 0.00
Provider contract IDs written: 0
Price-linkage-authorized rows: 0
Returns authorized: false
Provider accepted: false
```

No account entitlement, dataset coverage, definition record, settlement record, cost quote, or license term was inferred.

---

## Artifact identity

```text
Gate-evaluation bundle artifact:
8443402212

Bundle digest:
9986a215890528eb33c049ccb8e33f2dddc0e65843745f7ec5711f6d8f68030a

Receipt artifact:
8443402318

Receipt digest:
905ec0ee010077e90f4211bda944440569ecf3814e3a507cc906ba78a91b1db7

Retention expiry:
2026-10-17
```

The artifact ZIP digests and all internal request, evidence, and summary hashes were independently recomputed after download.

Storage remains:

```text
ACTIONS_ARTIFACT_STAGED_RETENTION_90_DAYS
```

It is not approved immutable provider-response storage.

---

## Required secure operator action

The repository must be configured with an Actions secret named exactly:

```text
DATABENTO_API_KEY
```

The key must not be placed in:

- source code;
- workflow YAML;
- Git history;
- an issue or pull-request comment;
- a research report;
- a chat message.

After secret configuration, rerun:

```text
Databento Zero-Purchase Metadata Probe
```

The rerun must retain:

```text
maximum authorized cost: USD 0.00
purchase authorized: false
time-series download authorized: false
batch download authorized: false
```

---

## Next evidence gate

The next authenticated run must produce evidence for the five representative candidates:

```text
ZN — GLBX.MDP3 — ZN.FUT
ES — GLBX.MDP3 — ES.FUT
NIY — GLBX.MDP3 — NIY.FUT
DX — IFUS.IMPACT — DX.FUT
VX — XCBF.PITCH — VX.FUT
```

Required evidence:

- account-visible datasets;
- available schemas;
- 2022 dataset range;
- 2022 dataset condition;
- point-in-time parent resolution;
- provider definition fields;
- availability of final actual settlement statistics;
- zero-purchase cost estimate;
- request and response hashes;
- license and redistribution snapshot.

The authenticated result must either:

1. qualify Databento for a separately reviewed minimal-data proposal; or
2. reject or remediate Databento as the primary candidate.

An authenticated metadata pass will still not authorize a purchase or return computation.

---

## Fail-closed authorization

```yaml
provider_probe_implementation: true
permanent_hosted_workflow: true
secure_secret_configuration: true
rerun_metadata_only_probe: true

provider_accepted: false
authenticated_probe_executed: false
purchase_authorized: false
time_series_download_authorized: false
batch_download_authorized: false
provider_contract_identifiers: 0
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

---

## Final controlling verdict

```text
PROBE IMPLEMENTATION: CONFIRMED
PERMANENT HOSTED WORKFLOW: PASS
RUFF / MYPY / TESTS: PASS
ZERO-PURCHASE INVARIANTS: PASS
AUTHENTICATED ACCOUNT SECRET: MISSING
AUTHENTICATED PROVIDER OPERATIONS: ZERO
PROVIDER ACCEPTED: NO
PROVIDER CONTRACT IDENTIFIERS: ZERO
PRICE-LINKAGE-AUTHORIZED ROWS: ZERO
RETURNS AUTHORIZED: NO
PAPER REPLICATION: NOT COMPLETE
ECONOMIC EDGE: NOT ESTABLISHED
EDGE-FUT-POSITION-001: INCONCLUSIVE
REPORT 2.4: BLOCKED
```
