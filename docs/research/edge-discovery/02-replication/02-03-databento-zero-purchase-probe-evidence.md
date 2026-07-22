# Report 2.3G — Databento Authenticated Zero-Purchase Probe Gate Evidence

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Parent:** [Provider-gate controlling addendum](02-03-provider-gate-controlling-addendum.md)  
**Evidence date:** 2026-07-19  
**Status:** `PROBE_IMPLEMENTATION_VERIFIED; AUTHENTICATED_EXECUTION_BLOCKED_MISSING_REPOSITORY_SECRET`

---

## 1. Decision

The authenticated, zero-purchase Databento metadata-probe implementation and its hosted execution workflow are now complete and verified.

The hosted gate evaluation did **not** contact Databento because the repository did not expose an Actions secret named:

```text
DATABENTO_API_KEY
```

The controlling execution result is:

```text
BLOCKED_MISSING_DATABENTO_API_KEY
```

This is a fail-closed operational blocker. It is not:

- authenticated provider evidence;
- a failed Databento entitlement check;
- provider rejection;
- provider acceptance;
- a data purchase;
- a market-data download;
- a provider contract-chain result;
- price-linkage authorization;
- a return or strategy result.

---

## 2. Implementation identity

Committed implementation:

```text
src/hybrid_trader/replication/databento_metadata_probe.py
scripts/run_databento_zero_purchase_probe.py
tests/test_databento_metadata_probe.py
.github/workflows/databento-zero-purchase-metadata-probe.yml
```

Probe identity:

```text
DATABENTO_CFTC_TFF_2022_09_13_ZERO_PURCHASE_METADATA_PROBE_V1
```

Pinned provider client:

```text
databento==0.81.0
```

Candidate-plan identity:

```text
Plan version:
CFTC_TFF_2022_09_13_DATABENTO_CANDIDATE_PLAN_V1

Rows:
54

SHA-256:
cd2430c7fdd0b3a68a1093925d755c242081372fbe41668cc53436893c274062
```

The implementation rejects a changed candidate-plan hash, row count, duplicate reporting code, or nondeterministic ordering.

---

## 3. Zero-purchase boundary

The client is limited to provider metadata, symbology, and pre-download cost-estimation operations.

Designed operations:

```text
metadata.list_datasets
metadata.list_schemas
metadata.list_fields
metadata.list_unit_prices
metadata.get_dataset_range
metadata.get_dataset_condition
metadata.get_cost
symbology.resolve
```

Forbidden operations include:

```text
timeseries.get_range
batch.submit_job
bulk market-data download
credit or cash expenditure
```

The workflow and independent verifier require:

```text
purchase_authorized: false
time_series_download_executed: false
batch_download_submitted: false
provider_contract_id_count: 0
price_linkage_authorized_rows: 0
returns_authorized: false
provider_accepted: false
```

The maximum authorized cost is:

```text
USD 0.00
```

---

## 4. Representative probe contract

The request contains five representative parent-symbol candidates:

| CFTC code | Root | Dataset candidate | Parent lookup key |
|---|---|---|---|
| `043602` | `ZN` | `GLBX.MDP3` | `ZN.FUT` |
| `13874A` | `ES` | `GLBX.MDP3` | `ES.FUT` |
| `240743` | `NIY` | `GLBX.MDP3` | `NIY.FUT` |
| `098662` | `DX` | `IFUS.IMPACT` | `DX.FUT` |
| `1170E1` | `VX` | `XCBF.PITCH` | `VX.FUT` |

Probe windows:

```text
Definition window:
2022-09-01 through 2022-10-01

Settlement-statistics window:
2022-09-16 through 2022-09-17
```

These parent symbols remain lookup inputs only. They are not accepted provider contract identifiers.

---

## 5. Hosted execution evidence

```text
Workflow:
Databento Zero-Purchase Metadata Probe

Run ID:
29690453120

Conclusion:
SUCCESS

Branch commit that triggered the trusted run:
b7c23b1d0826066cc20e5e18b68687ac236f9b17

Pull-request merge-test commit recorded in the receipt:
7c59ad7b6eecd0f70fc9e7c3b17f5721e28695af
```

Every permanent workflow step passed:

- checkout and Python 3.11 setup;
- installation of the project and pinned Databento client;
- repository Ruff rules;
- strict mypy;
- seven zero-purchase probe tests;
- gate evaluation;
- independent file-hash and non-purchase verification;
- evaluation-bundle upload;
- staging-receipt creation and upload;
- non-promotional workflow summary.

A prior run stopped at Ruff because two suppression comments referenced a rule not enabled by the repository configuration. The exact diagnostic was captured. Only those unused comments were removed; no provider operation, gate, or business rule was relaxed.

---

## 6. Actual gate result

The probe summary is:

```text
Execution status:
BLOCKED_MISSING_DATABENTO_API_KEY

Authenticated:
false

Authenticated metadata probe executed:
false

Provider operations executed:
0

Entitled datasets established:
0

Metadata gates passed:
0

Representative provider responses acquired:
0
```

The installed provider client was not initialized with an account credential. No provider entitlement or API behavior was inferred from the missing secret.

---

## 7. Durable request identity

The blocked evaluation still emitted a deterministic request contract for the next authorized run.

```text
Request filename:
probe-request.json

Byte count:
1676

SHA-256:
1ee06f9135ac2a7b7e750b52a6eef92e1607ae9e02837769d508400a9c257210
```

The request explicitly records:

```text
metadata_only: true
purchase_authorized: false
time_series_download_authorized: false
batch_download_authorized: false
max_authorized_cost_usd: 0.0
required schemas: definition, statistics
```

No API key or secret value is written to the request, evidence, logs, manifest, summary, or receipt.

---

## 8. Evaluation-file identities

```text
probe-evidence.json
Byte count: 2816
SHA-256: f7eacf6c4acad8a0e62ad38e0ef61a4b571ddff465527de0f2d6f446d9d3524f

probe-summary.json
Byte count: 410
SHA-256: 571531604f08bb5596cc984dbff85b3a3b64c83fc228dd7ff2a1be253ad41332
```

Manifest identity:

```text
probe-manifest.json

Files covered by the manifest:
probe-request.json
probe-evidence.json
probe-summary.json
```

All manifest hashes and byte counts were independently rechecked in the hosted workflow and again after downloading the artifact outside the runner.

---

## 9. Actions artifact evidence

### 9.1 Gate-evaluation bundle

```text
Artifact ID:
8443402212

Artifact digest:
9986a215890528eb33c049ccb8e33f2dddc0e65843745f7ec5711f6d8f68030a

Retention expiry:
2026-10-17
```

### 9.2 Receipt

```text
Artifact ID:
8443402318

Artifact digest:
905ec0ee010077e90f4211bda944440569ecf3814e3a507cc906ba78a91b1db7

Retention expiry:
2026-10-17
```

Both artifact ZIP digests were independently recomputed after download and matched GitHub's recorded digests.

Storage classification:

```text
ACTIONS_ARTIFACT_STAGED_RETENTION_90_DAYS
```

This is not approved long-term immutable provider-response storage.

---

## 10. Current provider evidence state

```text
Primary technical candidate:
DATABENTO

Accepted provider:
none

Repository secret present during verified run:
false

Authenticated API request executed:
false

Dataset entitlements verified:
false

2022 dataset ranges verified:
false

2022 dataset conditions verified:
false

Parent-to-child symbology verified:
false

Definition records acquired:
false

Final actual settlement statistics acquired:
false

Cost quote acquired:
false

License snapshot acquired:
false

Provider contract identifiers populated:
0

Price-linkage-authorized rows:
0

Returns authorized:
false

Purchase authorized:
false
```

Databento remains `SELECTED_NOT_ACCEPTED`.

---

## 11. Required operator action

The next authenticated run requires adding the API key as a GitHub Actions repository secret named exactly:

```text
DATABENTO_API_KEY
```

The key must never be pasted into:

- source code;
- commit history;
- a GitHub issue or pull-request comment;
- workflow YAML;
- research reports;
- chat messages.

After the secret is configured, the same workflow must be rerun without changing the zero-cost or no-download invariants.

---

## 12. Next acceptance or rejection decision

The next run must either:

1. produce authenticated metadata-only evidence for the five representative roots while spending nothing; or
2. produce an explicit provider rejection/remediation record.

Provider acceptance remains prohibited until the evidence includes:

- account-visible datasets and schemas;
- dataset range and condition over the frozen 2022 windows;
- point-in-time parent-to-child resolution;
- definition records with lifecycle and contract-specification fields;
- availability of final, actual settlement statistics;
- a cost estimate before any data request;
- license and redistribution evidence;
- request and response hashes;
- approved immutable storage identity.

Even authenticated metadata success will not authorize a paid download, price series, or return. It will only authorize a separately reviewed minimal-data acquisition proposal.

---

## 13. Evidence classification

```text
Probe implementation: CONFIRMED
Permanent hosted workflow: CONFIRMED
Pinned provider client installation: CONFIRMED
Ruff: PASS
Strict mypy: PASS
Zero-purchase tests: PASS_7
Non-purchase invariants: PASS
Request contract: CONFIRMED
Evaluation artifacts: CONFIRMED
Independent artifact rehash: CONFIRMED
Repository API secret: MISSING_AT_VERIFIED_RUN
Authenticated provider operations: ZERO
Provider account entitlement: NOT VERIFIED
Provider contract-chain evidence: NOT ACQUIRED
Provider settlement evidence: NOT ACQUIRED
Provider cost evidence: NOT ACQUIRED
Provider license snapshot: NOT ACQUIRED
Provider accepted: NO
Price-linkage authorization: ZERO_ROWS
Returns authorization: NOT GRANTED
Paper replication pass: NOT GRANTED
Economic edge: NOT ESTABLISHED
```

---

## 14. Authorization consequence

This milestone authorizes:

- secure repository-secret configuration outside Git history;
- rerunning the same metadata-only workflow;
- hashing authenticated metadata requests and responses;
- rejecting Databento if the representative metadata gate fails.

It does not authorize:

- placing an API key in chat or Git;
- spending provider credits or cash;
- submitting batch jobs;
- downloading time-series data;
- accepting Databento as the provider;
- writing provider contract IDs into the canonical registry;
- assigning prices;
- computing returns;
- empirical fitting;
- Report 2.4;
- paper or live trading;
- leverage;
- capital deployment.

`EDGE-FUT-POSITION-001` remains empirically `INCONCLUSIVE`.
