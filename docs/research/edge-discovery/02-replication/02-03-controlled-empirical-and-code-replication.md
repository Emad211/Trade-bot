# Report 2.3 — Controlled Empirical and Code Replication

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Report:** 3 of 5  
**Version:** 1.0  
**Research execution date:** 2026-07-18  
**Status:** `PARTIALLY_COMPLETE — IMPLEMENTATION_VALIDATED; OFFICIAL EMPIRICAL ARTIFACTS PENDING`  
**Parents:** [Report 2.1](02-01-anchor-opposition-code-selection.md) and [Report 2.2](02-02-data-timing-information-contract-reconstruction.md)  
**Machine-readable companion:** [02-03-replication-execution-manifest.yaml](02-03-replication-execution-manifest.yaml)  
**Decision type:** Fail-closed execution report. It records what was actually implemented and tested, what official sources were verified, what could not be acquired, and which empirical verdicts remain legally or technically unavailable.

---

# Executive decision

Report 2.3 has reached an important but deliberately limited milestone.

The project now has tested, production-compatible primitives for:

1. hashing and parsing official factor artifacts;
2. comparing original and maintained factor vintages;
3. computing transparent factor-performance diagnostics;
4. applying a recursively estimated inverse-variance overlay without full-sample leakage;
5. constructing futures returns only within the same contract;
6. recording contract transitions in a separate roll ledger;
7. assigning CFTC data an availability time based on actual release rather than report date;
8. applying historical release overrides for holiday, shutdown, and backlog events;
9. keeping mark price, index price, and last price semantically distinct;
10. resolving effective-dated cryptocurrency instrument specifications;
11. computing explicit two-leg linear spot–derivative PnL after funding and all declared costs;
12. returning machine-readable replication verdicts that can represent pass, fail, inconclusive, blocked-access, pending-license, and invalid-data states.

The implementation was executed locally against deterministic fixtures:

```text
11 tests passed
Python compileall passed
```

This result proves that the implemented invariants behave as specified on controlled examples. It does **not** prove any trading edge, any paper result, or any strategy profitability.

No official numerical paper replication is declared complete in this report because the required binary factor workbooks, licensed expired-futures histories, and author-provided data were not all ingested into immutable project storage during this execution. The assistant environment could verify the official pages and direct file locations, but binary Excel and ZIP retrieval failed at the tool boundary. The correct verdict is therefore source-specific `BLOCKED_BY_SOURCE_ACCESS`, `PENDING_LICENSE`, or `INCONCLUSIVE_DATA_ACCESS`; it is not permission to use a mirror and call the result exact.

The section remains fail-closed:

```yaml
empirical_fitting: false
parameter_tuning: false
strategy_tournament: false
paper_trading: false
live_trading: false
leverage: false
capital_deployment: false
```

Report 2.4 may not begin as a full sensitivity tournament until the public artifacts are ingested and the minimum numerical reconstruction gates in this report pass.

---

# 1. What “execution” means in Report 2.3

Report 2.3 separates four concepts that are often incorrectly merged.

## 1.1 Implementation validation

A formula or invariant is implemented and unit tested on controlled data.

Example:

- a roll gap between March and June contracts must not appear as a daily return;
- a CFTC Tuesday position must not be available until the Friday release;
- inverse-variance scaling must use lagged data;
- a two-leg result must subtract costs.

Status used here:

```text
IMPLEMENTATION_READY
```

## 1.2 Artifact acquisition validation

An official file has been downloaded, hashed, licensed, and stored under the Report 2.2 raw-artifact contract.

Required evidence:

- official source URL;
- retrieval time;
- byte count;
- SHA-256;
- license snapshot;
- unmodified raw bytes;
- parser version;
- schema fingerprint.

## 1.3 Empirical table replication

A published table, figure, regression, factor series, or accounting identity is reconstructed using the correct artifact and the paper-specific protocol.

## 1.4 Economic replication verdict

The replicated result survives the selected opposing evidence and is classified as pass, fail, or inconclusive.

Report 2.3 has completed the first layer and source-verification portion of the second layer. It has not silently promoted those achievements into layers three or four.

---

# 2. Code delivered

The implementation is located at:

```text
src/hybrid_trader/replication/
├── __init__.py
├── artifacts.py
├── cftc.py
├── crypto.py
├── factor_audit.py
├── futures.py
├── runner.py
└── verdicts.py
```

Tests:

```text
tests/
├── test_replication_cftc.py
├── test_replication_crypto.py
├── test_replication_factor_audit.py
└── test_replication_futures.py
```

The optional dependency group is:

```toml
replication = [
  "openpyxl>=3.1,<4",
]
```

This keeps spreadsheet support explicit rather than making an undeclared runtime assumption.

---

# 3. Source verification and acquisition outcomes

## 3.1 AQR Time Series Momentum original paper data

Official page:

```text
https://www.aqr.com/Insights/Datasets/Time-Series-Momentum-Original-Paper-Data
```

Official file location exposed by the page:

```text
https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/
Time-Series-Momentum-Original-Paper-Data.xlsx
```

Official scope verified from the publisher page:

- monthly factor returns;
- January 1985 through December 2009;
- 12-month lookback;
- one-month holding period;
- equity indices, currencies, commodities, and developed government bonds;
- based on 58 liquid futures and forward instruments.

Acquisition result in the current execution environment:

```text
BLOCKED_BY_SOURCE_ACCESS
```

Reason:

- the official HTML page and direct binary location were verified;
- the crawler reported a binary-response boundary error;
- the container downloader could not retrieve the file;
- no unofficial mirror was substituted.

## 3.2 AQR maintained TSMOM factor data

Official page:

```text
https://www.aqr.com/Insights/Datasets/Time-Series-Momentum-Factors-Monthly
```

Official file location:

```text
https://www.aqr.com/-/media/AQR/Documents/Insights/Data-Sets/
Time-Series-Momentum-Factors-Monthly.xlsx
```

Publisher metadata verified:

- starts January 1985;
- updated monthly;
- page version dated May 29, 2026 during this research freeze;
- same four broad asset classes and 58-instrument construction family.

Acquisition result:

```text
BLOCKED_BY_SOURCE_ACCESS
```

The AQR vintage audit runner is ready but must not emit `PASS` until both official workbook hashes exist.

## 3.3 Moreira–Muir volatility-managed factors

Official paper record verified through NBER Working Paper 22208 and the published Journal of Finance version.

The paper documents inverse-lagged-variance scaling across equity factors and currency carry. The NBER page confirms the paper identity, revision history, and data acknowledgements, but the exact author factor artifact was not ingested during this execution.

Acquisition result:

```text
BLOCKED_BY_SOURCE_ACCESS
```

Formula implementation result:

```text
IMPLEMENTATION_READY
```

The project implementation intentionally estimates the scaling constant only on a declared calibration window and then freezes it. This is a conservative baseline audit. It is not labeled an exact Moreira–Muir reproduction until the paper-specific factor file and exact normalization choices are acquired.

## 3.4 CFTC Commitments of Traders

Official release rule verified:

- reports generally represent Tuesday positions;
- reports are generally released Friday at 3:30 p.m. US Eastern time;
- holidays can delay release;
- report date is not release date.

Official data products verified:

| Family | Dataset ID |
|---|---|
| Legacy Futures Only | `6dca-aqww` |
| Disaggregated Futures Only | `72hh-3qpy` |
| TFF Futures Only | `gpe5-46if` |

The Public Reporting Environment and historical compressed pages were verified as official CFTC sources.

The 2025 federal-appropriations interruption was also verified through the official CFTC historical special announcement. For example, the report dated September 30, 2025 had a new publication date of November 19, 2025. That event is included in the release-override unit test.

Implementation result:

```text
IMPLEMENTATION_READY
```

Bulk data acquisition result in the current environment:

```text
BLOCKED_BY_SOURCE_ACCESS
```

The official API is public, but the current web/container boundary did not return a reusable raw JSON or ZIP artifact. The parser therefore remains validated against controlled Socrata-shaped records and an official historical exception, not against a falsely claimed complete historical download.

## 3.5 Binance public archive

Official source verified:

```text
https://github.com/binance/binance-public-data
https://data.binance.vision/
```

The official repository documents:

- daily and monthly public archives;
- spot and futures files;
- trades, aggregate trades, and klines;
- futures mark-price, index-price, premium-index, funding, and related modules;
- a checksum file beside archive files;
- archive corrections and replacement history;
- a change from millisecond to microsecond timestamps for spot data from January 1, 2025 onward.

These details directly justify the Report 2.2 tests for timestamp-unit changes, checksum replacement, and mark/index separation.

Implementation result:

```text
IMPLEMENTATION_READY
```

Historical archive ingestion result:

```text
NOT_EXECUTED_IN_THIS_ENVIRONMENT
```

No crypto empirical verdict is issued.

## 3.6 OKX public market data and rules

Official API documentation verified:

- public market-data endpoints do not require authentication;
- independent service caches can return a later request with an earlier observation;
- candles include a `confirm` flag;
- history candles are separately paginated;
- public endpoints cover funding-rate history, mark price, index data, open interest, and instruments;
- fills distinguish system record time from actual fill time;
- official changelog records a historical market-data batch endpoint introduced in September 2025.

Implementation result:

```text
IMPLEMENTATION_READY
```

Historical archive ingestion result:

```text
NOT_EXECUTED_IN_THIS_ENVIRONMENT
```

The code treats incomplete candles, current metadata projected backward, and system-time ordering as hard failures.

---

# 4. Implemented factor-file audit

## 4.1 Artifact parser

`artifacts.py` supports CSV and Excel artifacts and refuses silent layout guessing.

For Excel:

1. load the selected sheet without a header;
2. search a bounded prefix for a date-bearing header row;
3. normalize column names deterministically;
4. reject a workbook with no recognizable date header;
5. preserve raw bytes outside the parser;
6. hash the original file before deriving results.

## 4.2 Date normalization

The parser accepts common monthly forms such as:

```text
YYYY-MM-DD
YYYYMM
Excel-compatible date values
```

It converts them to UTC month-end timestamps. Unparseable values produce an exception with examples; they are not dropped silently.

## 4.3 Vintage comparison

`compare_factor_vintages` requires:

- a date column in each input;
- no duplicate dates;
- a nonempty overlap;
- common numerical factor columns;
- at least two overlapping values per compared factor.

For each factor it returns:

```yaml
column:
overlap_count:
correlation:
mean_absolute_difference:
max_absolute_difference:
changed_count:
```

This enables detection of historical revision between the original and maintained workbooks.

## 4.4 Performance diagnostics

`annualized_metrics` returns:

- observation count;
- annualized mean;
- annualized volatility;
- annualized Sharpe ratio;
- maximum drawdown;
- skewness;
- excess kurtosis;
- positive-month fraction.

These are descriptive replication outputs. They are not sufficient promotion metrics.

## 4.5 Runner verdict discipline

`run_aqr_vintage_audit` emits a `PASS` only after it receives two actual files and computes their SHA-256 hashes. A page description alone cannot trigger a factor verdict.

---

# 5. Implemented volatility-management audit

## 5.1 Formula

The baseline implementation uses:

```text
lagged_variance_t = variance(return_{t-L}, ..., return_{t-1})
raw_weight_t      = 1 / lagged_variance_t
managed_return_t  = frozen_scale × raw_weight_t × return_t
```

## 5.2 Leakage protection

The scaling constant is estimated only on a declared calibration prefix.

It is then frozen for later observations.

The function rejects:

- lookback below two observations;
- calibration shorter than the variance lookback;
- nonpositive leverage caps;
- an unusable calibration variance;
- implicit full-sample calibration.

## 5.3 Required future empirical variants

When the official factor data are acquired, Report 2.3 must produce at least:

1. unmanaged factor metrics;
2. paper-style managed factor metrics;
3. recursively calibrated managed factor metrics;
4. matched-volatility comparison;
5. uncapped and capped leverage variants;
6. gross and net-of-cost variants;
7. calibration and evaluation periods shown separately;
8. managed-only and optimal-combination results separately;
9. Moreira–Muir, Kang–Kwon, and DeMiguel-style contracts under separate experiment IDs.

No best overlay may be selected in Report 2.3.

---

# 6. Implemented futures return audit

## 6.1 Same-contract rule

The futures module groups observations by native contract identifier before computing a return.

At a contract transition:

```text
old contract last price = 101
new contract first price = 110
```

The value `110 / 101 - 1` is not emitted as a return.

The first observation of the new contract has no within-contract previous price and therefore receives a missing return.

## 6.2 Roll ledger

Contract selection transitions produce a separate record:

```yaml
product_id:
decision_time:
old_contract_id:
new_contract_id:
```

Execution prices, fees, spread, and slippage can be joined later under the Report 2.2 roll schema.

## 6.3 Test result

The test fixture contains an intentionally large cross-contract gap. The implementation correctly excludes it while retaining the within-contract returns.

This is an implementation pass, not an empirical trend or carry pass.

---

# 7. Implemented CFTC audit

## 7.1 Standard release calculation

For a report date, the baseline rule calculates the Friday of the same reporting week at 15:30 `America/New_York`, then converts it to UTC.

Timezone conversion uses the standard library `zoneinfo`, preserving daylight-saving transitions.

## 7.2 Historical override

The API accepts an effective override map:

```python
report_date -> timezone-aware actual release datetime
```

This is mandatory for:

- holidays;
- federal shutdowns;
- publication backlogs;
- special CFTC announcements;
- any verified nonstandard release.

## 7.3 Availability

```text
available_at = actual_release_time + parser_delay
```

A negative parser delay is rejected.

A row whose availability does not follow its report date is rejected.

## 7.4 Semantic family

Every normalized table requires an explicit family label. The implementation does not infer that Legacy, Disaggregated, TFF, Supplemental, Futures Only, and Combined data are interchangeable.

## 7.5 Position pressure

The helper computes:

```text
(long - short) / (long + short)
```

with nonnegative-position validation and undefined output when the denominator is zero.

## 7.6 Remaining empirical work

After official raw acquisition:

- validate all dataset IDs and field names;
- retain original IDs and market codes;
- compare compressed files against PRE API records;
- build release histories from current calendars and special announcements;
- label older inferred releases conservatively;
- test corrections and duplicate IDs;
- link CFTC market codes to licensed price instruments;
- only then build speculative-pressure portfolios.

---

# 8. Implemented crypto derivatives audit

## 8.1 Effective-dated instrument versions

Each instrument version contains:

- venue;
- native instrument ID;
- effective interval;
- instrument type;
- base, quote, and settlement currencies;
- multiplier;
- linear/inverse/quanto classification;
- tick size;
- lot size.

The resolver requires exactly one valid version at a timestamp. Zero or multiple matches are hard failures.

## 8.2 Basis semantics

The implemented basis is explicitly:

```text
mark_price / index_price - 1
```

Both series must be positive and finite.

The function cannot accidentally substitute last trade price because the inputs are named separately.

## 8.3 Linear two-leg accounting

The first supported deterministic contract is a linear derivative.

Components:

```text
spot PnL
derivative PnL
funding cashflow
trading fees
spread
slippage
financing
collateral opportunity cost
transfer cost
orphan-leg loss
stablecoin haircut
venue haircut
```

Net PnL is the sum of the two legs and funding less every declared cost.

## 8.4 Unsupported contracts

Inverse and quanto contracts are modeled in instrument metadata but do not share the linear PnL formula. They require separate formula implementations and tests before use.

This is intentional. Treating an inverse contract as linear is a Report 2.2 hard failure.

---

# 9. Test execution record

Local environment:

```text
Python 3.11-compatible source
pandas
numpy
pydantic
openpyxl present for workbook support
```

Command:

```bash
PYTHONPATH=/mnt/data/report23/src pytest -q /mnt/data/report23/tests
```

Result:

```text
...........
11 passed in 0.18s
```

Compilation command:

```bash
python -m compileall -q src tests
```

Result:

```text
PASS
```

Ruff was not installed in the isolated execution container, so no claim of a Ruff pass is made. Repository CI must run Ruff, mypy, pytest, and coverage after the branch is integrated with a normal development environment.

---

# 10. Test-to-invariant mapping

| Test | Invariant |
|---|---|
| factor vintage revision | overlapping historical revisions are visible |
| annual metrics | drawdown and non-Gaussian diagnostics are generated |
| lagged variance | scaling cannot use contemporaneous/future variance |
| futures roll gap | cross-contract gap is not PnL |
| roll ledger | every contract transition is explicit |
| standard CFTC release | Tuesday data uses Friday 15:30 ET baseline |
| CFTC override | shutdown/backlog release replaces normal schedule |
| negative parser delay | impossible availability assumptions fail |
| instrument resolution | metadata is effective-dated |
| mark/index basis | price semantics stay distinct |
| two-leg PnL | all declared costs reduce net PnL |

---

# 11. Machine-readable verdict matrix

## 11.1 `EDGE-FUT-TREND-001`

```yaml
implementation: IMPLEMENTATION_READY
factor_audit: BLOCKED_BY_SOURCE_ACCESS
raw_exact_replication: PENDING_LICENSE
empirical_verdict: INCONCLUSIVE
```

Reason:

- audit code and tests exist;
- official AQR pages and file locations are verified;
- official workbook bytes were not acquired;
- raw 58-instrument data remain licensed/incomplete.

## 11.2 `EDGE-RISK-POLICY-001`

```yaml
implementation: IMPLEMENTATION_READY
public_factor_artifact: BLOCKED_BY_SOURCE_ACCESS
commodity_exact_replication: PENDING_LICENSE
empirical_verdict: INCONCLUSIVE
```

## 11.3 `EDGE-FUT-CARRY-001`

```yaml
same_contract_engine: IMPLEMENTATION_READY
roll_ledger: IMPLEMENTATION_READY
maturity_curve_data: PENDING_LICENSE
empirical_verdict: INCONCLUSIVE
```

## 11.4 `EDGE-FUT-POSITION-001`

```yaml
release_time_engine: IMPLEMENTATION_READY
public_api_metadata: VERIFIED
bulk_raw_artifact: BLOCKED_BY_SOURCE_ACCESS
licensed_price_linkage: PENDING_LICENSE
empirical_verdict: INCONCLUSIVE
```

## 11.5 `EDGE-CRYPTO-BASIS-001`

```yaml
instrument_version_engine: IMPLEMENTATION_READY
basis_formula: IMPLEMENTATION_READY
chi_exact_data: INCONCLUSIVE_DATA_ACCESS
public_constructive_archive: NOT_INGESTED
empirical_verdict: INCONCLUSIVE
```

## 11.6 `EDGE-CRYPTO-RV-001`

```yaml
linear_two_leg_accounting: IMPLEMENTATION_READY
inverse_accounting: NOT_IMPLEMENTED
quanto_accounting: NOT_IMPLEMENTED
historical_archive: NOT_INGESTED
paper_execution: NOT_AUTHORIZED
empirical_verdict: INCONCLUSIVE
```

---

# 12. Why no paper is marked “replicated” yet

A paper is not replicated because:

- its abstract was read;
- its equations were retyped;
- a synthetic test passed;
- a public page confirms the sample period;
- a modern alternative dataset was found;
- a similar strategy ran successfully.

A paper-level replication requires:

1. the correct source artifact;
2. a recorded license state;
3. a checksum;
4. the exact universe and sample;
5. paper-specific formula versions;
6. table-level outputs;
7. a tolerance contract;
8. discrepancy explanations;
9. opposing-paper tests;
10. a final pass, fail, or inconclusive verdict.

None of these requirements is relaxed because a source download was inconvenient.

---

# 13. Acquisition blockers

## 13.1 Tool-bound binary retrieval

The official AQR pages expose the Excel download locations, but the web crawler returned an internal binary fetch error and the isolated downloader did not retrieve the bytes.

This is an environment limitation, not evidence that the files do not exist.

## 13.2 CFTC raw export

The CFTC pages and Socrata dataset IDs are verified. The current tool environment did not persist the JSON/CSV/ZIP response as a reusable raw artifact.

## 13.3 Traditional futures licenses

Raw exact reconstruction requires a source capable of supplying:

- expired contracts;
- settlement histories;
- open interest and volume;
- notice and last-trade dates;
- contract specification history;
- vendor-native mappings;
- correction history;
- permissible derived use.

No purchase is authorized until field coverage and rights are confirmed.

## 13.4 Author-provided artifacts

Chi et al. and several other anchor studies require author or institutional access for exact source data. An unanswered request cannot be interpreted as permission to substitute.

---

# 14. Required next execution batch inside Report 2.3

Report 2.3 remains open for empirical artifacts. The next execution batch is finite.

## Batch A — AQR official factor ingestion

1. download original workbook manually or from an environment able to retrieve the official binary;
2. download maintained workbook;
3. save raw bytes without modification;
4. record AQR terms-of-use tab and page snapshot;
5. compute SHA-256;
6. run `run_aqr_vintage_audit`;
7. emit overlap revision table;
8. report paper-sample and post-sample metrics separately.

## Batch B — Moreira–Muir public factor ingestion

1. locate official author factor file and internet appendix;
2. record provenance and license;
3. reproduce unmanaged and managed factor summary tables;
4. rerun with recursive calibration and leverage caps;
5. compare in-sample and real-time variants;
6. record deviations from the paper.

## Batch C — CFTC acquisition

1. pull official PRE API data by dataset ID;
2. pull matching historical compressed files;
3. checksum both;
4. compare overlapping records;
5. build actual release ledger;
6. apply 2025 shutdown/backlog overrides;
7. validate family separation and market-code stability.

## Batch D — Binance/OKX archive audit

1. freeze provider path lists;
2. download archive checksums before archives;
3. verify Binance timestamp unit by epoch;
4. retain replacement/update logs;
5. download effective-dated instrument metadata and rule snapshots;
6. validate OKX candle confirmation;
7. separate mark, index, premium, funding, and last prices;
8. emit coverage and gap tables before constructing any signal.

## Batch E — licensed futures procurement decision

Obtain field-level quotes and choose:

```text
BUY
REQUEST_AUTHOR_DATA
REDESIGN_AS_CONSTRUCTIVE
DEFER
STOP
```

for each exact study separately.

---

# 15. Gate for closing Report 2.3

Report 2.3 may change from `PARTIALLY_COMPLETE` to `COMPLETE` only when all minimum public gates pass:

1. official AQR original and maintained artifacts are hashed;
2. AQR overlap and post-sample audit is generated;
3. one official Moreira–Muir factor artifact is hashed and audited, or the track is formally classified as unavailable;
4. CFTC PRE data are acquired from at least one official family and cross-checked against an official compressed file;
5. the CFTC release ledger includes known exceptional releases;
6. Binance or OKX official archive bytes and checksums are ingested for a small frozen pilot interval;
7. all red-team tests pass on the acquired data;
8. every unavailable exact paper receives a formal `PENDING_LICENSE` or `INCONCLUSIVE_DATA_ACCESS` verdict;
9. all outputs have source and formula lineage;
10. CI passes on the committed implementation.

Until then, Report 2.4 is not authorized as a full economic sensitivity analysis.

---

# 16. Binding decisions

1. Implementation tests are not empirical replications.
2. Source metadata verification is not raw artifact acquisition.
3. Official binary retrieval failure produces `BLOCKED_BY_SOURCE_ACCESS`.
4. An unofficial mirror cannot inherit official-source identity.
5. AQR factor audit remains blocked until official workbook hashes exist.
6. AQR processed factors can never substitute for raw 58-instrument reconstruction.
7. Moreira–Muir formula implementation is a baseline audit, not an exact paper result.
8. A volatility scaling constant must be calibrated on a declared past window.
9. Full-sample normalization is prohibited in real-time tests.
10. Futures returns are computed within native contract IDs.
11. Cross-contract price gaps are not returns.
12. Every roll is a separate ledger event.
13. CFTC report date and release date remain distinct.
14. CFTC release overrides are mandatory when official exceptions exist.
15. CFTC report families remain separate.
16. Binance archive checksum files are required.
17. Binance timestamp units are effective-dated.
18. OKX incomplete candles are excluded from confirmatory features.
19. OKX service-cache non-monotonicity must be handled.
20. Fill time, system record time, and exchange time remain distinct.
21. Crypto instrument specifications are effective-dated.
22. Mark, index, premium, and last prices remain separate.
23. Linear, inverse, and quanto PnL formulas remain separate.
24. The linear two-leg implementation includes funding and all declared costs.
25. Paper execution remains unauthorized.
26. No hypothesis receives an economic pass in this report version.
27. All six hypotheses currently retain an `INCONCLUSIVE` empirical verdict.
28. Negative and blocked results are permanent research memory.
29. Report 2.3 remains open until the minimum acquisition gates pass.
30. Accuracy of identity and timing takes priority over speed of obtaining a Sharpe ratio.

---

# Final decision

The project has moved from research design to a tested replication implementation without violating the source and exactness rules established in Reports 2.1 and 2.2.

That is real progress: the code can now detect several classes of false edge before a strategy result is produced.

It would be scientifically incorrect, however, to claim that the selected papers have already been numerically replicated. The required official and licensed artifacts are not yet all present in immutable storage.

Current verdict:

```text
CODE AND INVARIANT IMPLEMENTATION: PASS
OFFICIAL PUBLIC ARTIFACT INGESTION: PARTIAL / BLOCKED IN CURRENT ENVIRONMENT
LICENSED EXACT REPLICATION: PENDING
EMPIRICAL EDGE VERDICT: INCONCLUSIVE FOR ALL SIX HYPOTHESES
REPORT 2.4 AUTHORIZATION: NOT YET GRANTED
```
