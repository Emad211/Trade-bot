# Report 2.2 — Data, Timing, and Information-Contract Reconstruction

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Report:** 2 of 5  
**Version:** 1.0  
**Research freeze date:** 2026-07-18  
**Status:** Complete  
**Parent:** [Report 2.1](02-01-anchor-opposition-code-selection.md)  
**Parent manifest:** [Report 2.1 replication selection manifest](02-01-replication-selection-manifest.yaml)  
**Machine-readable companions:**

- [Data-contract manifest](02-02-data-contract-manifest.yaml)
- [Source and license registry](02-02-source-license-registry.yaml)
- [Instrument and point-in-time universe manifest](02-02-instrument-universe-manifest.yaml)
- [Lineage and timing schema](02-02-lineage-timing-schema.yaml)

**Decision type:** Binding data-acquisition, timing, lineage, return-construction, licensing, and exactness contract for Reports 2.3–2.5.

---

# Executive decision

Report 2.2 freezes the information boundary for every replication admitted in Report 2.1. It does not estimate a trading model, produce a strategy backtest, select a parameter, or authorize paper or live execution.

The core decision is:

> A datum is usable only when the project can prove what it represented, which instrument and venue it referred to, when the underlying event occurred, when the value was published, when the project could have received it, whether it was later revised, and which immutable raw artifact produced the derived value.

Five distinctions are binding.

1. **Economic time is not availability time.** A Tuesday position report released on Friday cannot be used on Tuesday.
2. **A continuous price series is not a transaction ledger.** Back-adjustment may support charting or signal construction but cannot create executable profit.
3. **A public download is not automatically unrestricted data.** Provider terms, redistribution restrictions, and derived-data clauses remain part of the research contract.
4. **A modern public reconstruction is not an exact replication of a licensed historical study.** It receives a separate experiment identity and verdict.
5. **A historical value is not immutable merely because it was downloaded once.** Providers may correct, replace, or reinterpret files; checksums, retrieval times, and revision lineage are mandatory.

Report 2.2 establishes four acquisition tracks:

| Track | Scope | Decision |
|---|---|---|
| `PUBLIC_FACTOR_AUDIT` | AQR and other official factor files | `GO_DATA_ONLY` |
| `PUBLIC_REGULATOR_PIPELINE` | CFTC reports and release-time reconstruction | `GO_DATA_ONLY` |
| `LICENSED_FUTURES_EXACT` | Expired contract histories, settlements, curves, OI, volume, and vendor mappings | `GO_CONDITIONAL_ON_LICENSE_AND_FIELDS` |
| `PUBLIC_CRYPTO_CONSTRUCTIVE` | Binance and OKX raw public archives and APIs | `GO_DATA_ONLY_AS_NEW_EXPERIMENT` |

No empirical fitting is authorized until the acquisition artifacts pass the adversarial data tests defined here.

---

# 1. Scope and non-scope

## 1.1 In scope

This report defines:

1. the global temporal ontology;
2. immutable raw-record requirements;
3. source, license, and redistribution classes;
4. paper-by-paper instrument manifests;
5. point-in-time universe rules;
6. futures contract-chain and roll semantics;
7. same-contract return construction;
8. CFTC report-time and revision semantics;
9. factor-data vintage rules;
10. cryptocurrency instrument and venue semantics;
11. funding, mark, index, liquidation, margin, and collateral records;
12. cost, financing, and capital-accounting inputs;
13. raw-to-derived lineage;
14. formula and schema versioning;
15. exact-versus-constructive replication boundaries;
16. acquisition go/no-go decisions;
17. immutable research cutoffs;
18. adversarial data-quality tests;
19. the handoff contract for Report 2.3.

## 1.2 Out of scope

This report does not:

- fit a predictive model;
- optimize a lookback period;
- select a portfolio threshold;
- calculate a final Sharpe ratio;
- compare candidate strategies;
- open an exchange connection;
- create orders;
- simulate paper fills;
- deploy capital;
- promote any hypothesis.

Any code written at this stage may only acquire, validate, normalize, version, or audit data.

---

# 2. Global temporal ontology

Every raw, normalized, and derived record must carry a timing envelope. A single `timestamp` field is prohibited.

## 2.1 Required clocks

| Field | Definition |
|---|---|
| `event_time` | When the economic or market event occurred |
| `observation_start` | Start of the measurement interval |
| `observation_end` | End of the measurement interval |
| `exchange_time` | Time assigned by the venue or exchange |
| `report_as_of_time` | Economic cutoff represented by a report |
| `scheduled_release_time` | Release time expected under the official calendar |
| `actual_release_time` | First verified public release |
| `source_update_time` | Provider-declared modification time, when available |
| `retrieved_at` | Time the project received or downloaded the artifact |
| `ingested_at` | Time the artifact entered immutable storage |
| `normalized_at` | Time parsing and normalization completed |
| `available_at` | Earliest time the value was eligible for a decision |
| `decision_time` | Time a strategy would evaluate the value |
| `order_submit_time` | Time an order would be transmitted |
| `exchange_ack_time` | Exchange acknowledgement time |
| `fill_time` | Economic execution time of a fill |
| `system_record_time` | Time a venue or project system wrote the record |
| `revision_effective_time` | Time a corrected value replaced a prior version |

All times are stored as timezone-aware UTC nanoseconds. Original local timestamps and timezone identifiers are preserved in source metadata.

## 2.2 Availability function

For any datum `x`:

```text
available_at(x)
=
max(
  actual_release_time,
  minimum_feasible_retrieval_time,
  processing_complete_time
)
```

For files obtained retrospectively, the project distinguishes:

- `historical_public_availability`: when a real-time user could first have obtained the information;
- `project_retrieval_time`: when this project actually downloaded it.

Historical backtests use the first. Prospective records use the second plus actual processing delay.

If actual release time is unknown, the value receives one of these states:

- `VERIFIED_RELEASE`;
- `SCHEDULE_INFERRED_RELEASE`;
- `DATE_ONLY_RELEASE`;
- `UNKNOWN_RELEASE`.

Only `VERIFIED_RELEASE` and predeclared conservative `SCHEDULE_INFERRED_RELEASE` records may enter confirmatory tests. `DATE_ONLY_RELEASE` and `UNKNOWN_RELEASE` records are excluded or delayed by a conservative policy frozen before testing.

## 2.3 Interval-close rule

A bar, candle, monthly return, daily settlement, or report-period statistic becomes usable only after the interval is complete and the provider has made the finalized value available.

Examples:

- an incomplete cryptocurrency candle with `confirm=0` is not usable;
- a monthly factor is unavailable until the month closes and the source publishes the file;
- a daily settlement is not available at the exchange trading timestamp merely because trades occurred during the day;
- a funding payment is not recognized before its settlement timestamp;
- a report dated Tuesday but released Friday is unavailable until Friday.

## 2.4 Decision clock

Each experiment must declare exactly one decision clock:

```yaml
decision_clock:
  timezone: "UTC"
  cadence: "monthly_close|weekly_release|daily_close|hourly_boundary|event_driven"
  decision_delay: "ISO-8601 duration"
  price_reference: "next_open|next_bar_vwap|next_settlement|order_book_snapshot"
  stale_after: "ISO-8601 duration"
```

Changing the decision clock creates a new experiment identity.

---

# 3. Immutable raw-data envelope

Every acquired object must be stored before transformation.

## 3.1 Raw artifact record

```yaml
raw_artifact:
  artifact_id: "content-addressed identifier"
  source_id: "registry identifier"
  source_object_key: "provider path or request fingerprint"
  request_parameters: {}
  response_headers: {}
  retrieved_at: "UTC timestamp"
  provider_update_time: "UTC timestamp or null"
  media_type: "text/csv|application/json|application/zip|..."
  compression: "none|zip|gzip|..."
  byte_size: 0
  sha256: "hex digest"
  license_snapshot_id: "license registry version"
  parser_version: "semantic version"
  schema_fingerprint: "hash"
  supersedes_artifact_id: null
  retrieval_status: "SUCCESS|PARTIAL|FAILED"
```

## 3.2 Immutability

Raw artifacts are append-only. A provider replacement does not overwrite the old file. It creates a new artifact with:

- a new checksum;
- retrieval time;
- source update time;
- relationship to the superseded artifact;
- a change summary;
- downstream invalidation list.

## 3.3 Request fingerprint

API responses must include a canonical request fingerprint derived from:

- HTTP method;
- normalized endpoint;
- sorted query parameters;
- body hash;
- authentication scope without secrets;
- pagination cursor;
- requested timezone;
- requested market and instrument identifiers.

## 3.4 No secret leakage

API keys, cookies, account IDs, wallet addresses, and private headers are excluded from research artifacts. Authentication scope is represented by a non-secret class such as:

- `PUBLIC_ANONYMOUS`;
- `PUBLIC_REGISTERED`;
- `PAID_MARKET_DATA`;
- `PRIVATE_ACCOUNT`;
- `AUTHOR_PROVIDED`.

---

# 4. Data licensing and provenance classes

## 4.1 License classes

| Code | Meaning |
|---|---|
| `PUBLIC_DOMAIN_OR_GOVERNMENT` | Public government data subject to official terms |
| `PUBLIC_DOWNLOAD_PROVIDER_TERMS` | Public download with provider usage or redistribution restrictions |
| `OPEN_SOURCE_CODE_LICENSE` | Source code governed by an explicit open-source license |
| `ACADEMIC_AUTHOR_TERMS` | Author-supplied data or supplement with specified academic-use terms |
| `LICENSE_REQUIRED` | Commercial data license required |
| `AUTHOR_PERMISSION_REQUIRED` | Availability only by author request or permission |
| `UNKNOWN_TERMS_NO_USE` | Terms not established; data cannot enter confirmatory work |
| `INTERNAL_DERIVED_RESTRICTED` | Derived artifacts whose redistribution is constrained by upstream terms |

## 4.2 Required license snapshot

For each source, store:

- canonical source name;
- provider;
- URL or endpoint family;
- access date;
- terms document checksum;
- allowed uses;
- attribution requirements;
- redistribution restrictions;
- derived-data restrictions;
- retention restrictions;
- geographic or account restrictions;
- termination or update rules;
- contact or procurement path.

A source changing its terms creates a new `license_snapshot_id`.

## 4.3 Public does not mean redistributable

The project may store and use a publicly downloadable file while still being prohibited from redistributing the file or a reconstructable derivative. Therefore:

- Git commits contain schemas, checksums, code, and small non-reconstructive summaries;
- restricted raw files remain outside Git;
- manifest entries reference content hashes and secure storage locations;
- generated evidence packages are checked against upstream license rules.

---

# 5. Source and license decisions

## 5.1 AQR factor data

**Purpose:** public factor-series audit for `EDGE-FUT-TREND-001`.

Contract:

- source is the official AQR data library;
- original-paper TSMOM monthly factor file covers the published historical factor window;
- maintained factor data are a later vintage and must be stored separately;
- each download receives a checksum and retrieval time;
- the spreadsheet's terms are snapshotted;
- factor files cannot substitute for raw instrument replication;
- revisions between vintages are diffed.

Decision: `GO_DATA_ONLY_PUBLIC_FACTOR_AUDIT`.

## 5.2 NBER and author supplements

**Purpose:** paper, appendix, formula, and public factor acquisition.

Contract:

- record working-paper and final-publication versions separately;
- store DOI, NBER number, publication date, revision date, and checksum;
- formulas are versioned if the working and published papers differ;
- author data remain under author terms.

Decision: `GO_DOCUMENT_AND_SUPPLEMENT_ACQUISITION`.

## 5.3 CFTC

**Purpose:** point-in-time positioning data.

Contract:

- government source;
- report date is not release time;
- regular release is generally Friday for Tuesday positions;
- actual holiday and exceptional release schedules override the regular rule;
- historical corrections and replacement files are versioned;
- report category and classification methodology are stored;
- legacy, supplemental, disaggregated, and traders-in-financial-futures datasets are never silently merged.

Decision: `GO_PUBLIC_REGULATOR_PIPELINE`.

## 5.4 CME, ICE, LME, Refinitiv, Bloomberg, Commodity Research Bureau, and similar vendors

**Purpose:** exact contract-level traditional-futures replication.

Contract:

- exact fields and historical depth must be quoted before purchase;
- expired contracts, settlements, corrections, contract specifications, volume, OI, first/last trade dates, and corporate/exchange rule changes are mandatory;
- generic continuous series alone are insufficient;
- redistribution and derived-data rights must be reviewed;
- vendor identifiers require an explicit mapping to exchange identifiers.

Decision: `GO_CONDITIONAL_ON_LICENSE_AND_FIELD_AUDIT`.

## 5.5 Binance public archives and APIs

**Purpose:** constructive cryptocurrency replication and contract-data audit.

Contract:

- use official public archives as the primary bulk source;
- preserve archive checksums and provider update logs;
- treat provider file replacement as a new revision;
- preserve raw trades, aggregate trades, klines, mark-price klines, index-price klines, premium-index data, funding records, and contract metadata separately;
- normalize timestamp units by source epoch and product;
- do not assume a permanent eight-hour funding interval;
- snapshot instrument and funding rules.

Decision: `GO_DATA_ONLY_AS_CONSTRUCTIVE_EXPERIMENT`.

## 5.6 OKX historical data and APIs

**Purpose:** constructive multi-venue cryptocurrency replication.

Contract:

- historical download availability differs by dataset and start date;
- snapshot instrument definitions including listing and expiry times, contract value, multiplier, settlement currency, tick, lot, and margin fields;
- store `formulaType`, funding interval, interest component, impact margin, and effective rule times;
- incomplete candles are excluded;
- fills are ordered by economic fill time, not only system-record time;
- websocket instrument updates are captured prospectively.

Decision: `GO_DATA_ONLY_AS_CONSTRUCTIVE_EXPERIMENT`.

---

# 6. Futures contract identity

A futures instrument is not identified by a root ticker alone.

## 6.1 Canonical contract key

```yaml
futures_contract_key:
  venue_id: "exchange MIC or canonical venue"
  product_id: "stable exchange product identifier"
  contract_code: "native listed contract code"
  maturity_year_month: "YYYY-MM"
  last_trade_date: "date or null"
  first_notice_date: "date or null"
  delivery_start_date: "date or null"
  delivery_end_date: "date or null"
  settlement_type: "CASH|PHYSICAL"
  quote_currency: "ISO or canonical asset"
  settlement_currency: "ISO or canonical asset"
  contract_multiplier: "decimal"
  price_unit: "provider unit"
  tick_size: "decimal"
  source_version: "identifier"
```

The root ticker, vendor generic number, or "front contract" label is not a stable contract identifier.

## 6.2 Contract specification history

For each contract or product, store effective-dated changes in:

- multiplier;
- tick size;
- settlement procedure;
- trading hours;
- delivery rules;
- price limits;
- margin class;
- listed months;
- exchange migration;
- symbol;
- currency;
- settlement benchmark.

Historical calculations use the specification effective at the event time.

---

# 7. Futures contract-chain and roll contract

## 7.1 Three separate objects

The system must maintain:

1. **raw contract observations**;
2. **contract-chain selection state**;
3. **roll transactions**.

They are not merged into one continuous price field.

## 7.2 Raw contract observations

Each observation contains:

```yaml
contract_observation:
  contract_key: {}
  trading_date: "date"
  session_id: "exchange session"
  settlement_price: "decimal or null"
  close_price: "decimal or null"
  open_interest: "integer or null"
  volume: "integer or null"
  data_status: "PRELIMINARY|FINAL|CORRECTED"
  source_artifact_id: "hash"
  available_at: "timestamp"
```

## 7.3 Chain-selection state

For each product and decision time:

```yaml
chain_state:
  product_id: "id"
  decision_time: "timestamp"
  ordered_contracts:
    - contract_key: {}
      days_to_last_trade: 0
      days_to_first_notice: 0
      open_interest: null
      volume: null
      eligible: true
      exclusion_reasons: []
  selected_front_contract: {}
  selected_second_contract: {}
  selected_third_contract: {}
  selection_rule_id: "versioned rule"
```

## 7.4 Permitted roll rules

A paper replication must implement the paper's declared rule exactly when possible. Independent constructive tests may use predeclared alternatives:

- `FIXED_CALENDAR_BEFORE_DELIVERY`;
- `FIRST_BUSINESS_DAY_OF_DELIVERY_MONTH`;
- `N_DAYS_BEFORE_FIRST_NOTICE`;
- `N_DAYS_BEFORE_LAST_TRADE`;
- `OPEN_INTEREST_CROSSOVER`;
- `VOLUME_CROSSOVER`;
- `MOST_LIQUID_WITH_PERSISTENCE`;
- `PAPER_SPECIFIC_BIMONTHLY_CHAIN`.

Every roll rule receives a distinct `selection_rule_id`.

## 7.5 Roll ledger

```yaml
roll_event:
  product_id: "id"
  old_contract_key: {}
  new_contract_key: {}
  decision_time: "timestamp"
  old_exit_reference: "settlement|open|vwap|quote"
  new_entry_reference: "settlement|open|vwap|quote"
  old_exit_price: "decimal"
  new_entry_price: "decimal"
  quantity_old: "decimal"
  quantity_new: "decimal"
  fees: "decimal"
  spread_cost: "decimal"
  slippage: "decimal"
  selection_rule_id: "id"
  source_lineage: []
```

The price difference between the old and new contracts is not itself profit or loss unless a spread position was actually held.

---

# 8. Return-construction contract

## 8.1 Same-contract return

For a held contract `T`:

```text
R[t,t+1,T] = F[t+1,T] / F[t,T] - 1
```

Both prices must refer to the same contract identifier.

## 8.2 Portfolio PnL

```text
PnL
= sum(quantity × (exit_price - entry_price))
- fees
- spread
- slippage
- financing
+ collateral_income
+ funding
```

The project stores returns and currency PnL separately.

## 8.3 Continuous adjusted series

Allowed uses:

- visualization;
- certain predeclared signal calculations;
- approximate long-history diagnostics;
- comparison with published generic-index factors.

Forbidden uses:

- executable PnL;
- roll profit;
- margin calculation;
- fill simulation;
- cash-and-carry accounting;
- final economic verdict.

## 8.4 Fully collateralized return

A study using fully collateralized futures must explicitly state:

- collateral notional;
- collateral yield source;
- margin balance;
- excess cash;
- reinvestment timing;
- currency conversion;
- whether reported futures returns are excess returns or total returns.

---

# 9. Paper and hypothesis data contracts

# 9.1 `EDGE-FUT-TREND-001`

## 9.1.1 Public factor audit

Source: official AQR TSMOM factor files.

Required fields:

- factor date;
- asset-class factor returns;
- aggregate factor return;
- file vintage;
- source checksum;
- retrieval time;
- terms snapshot.

Use:

- verify published factor statistics;
- extend post-publication performance;
- compare original and maintained vintages.

Not sufficient for:

- asset-level predictive regressions;
- exact roll audit;
- same-contract PnL;
- vendor correction analysis.

## 9.1.2 Exact raw reconstruction

Target:

- the 58-instrument futures and forwards universe used by the anchor;
- paper sample through December 2009;
- exact vendor histories and currency-forward construction where used.

Status:

- `GO_CONDITIONAL_ON_LICENSE`;
- exact symbol list and vendor identifiers must be extracted from the official paper appendix and vendor metadata before acquisition;
- no substitute universe may inherit the original experiment ID.

## 9.1.3 Modern constructive universe

A separate modern multi-asset futures experiment may include liquid:

- equity-index futures;
- government-bond and interest-rate futures;
- currency futures;
- commodity futures.

Eligibility at each decision date requires:

- listed and tradable contract;
- valid contract specification;
- sufficient lookback;
- non-stale settlement;
- valid roll candidate;
- minimum liquidity;
- no retrospective survivor selection.

## 9.1.4 Immutable variants

The following are separate experiments:

- sign of 12-month own return;
- historical-mean benchmark;
- equal-notional;
- inverse-volatility weighted;
- zero-investment long/short balanced;
- same-contract versus generic-factor audit.

They may not be combined after observing results.

---

# 9.2 `EDGE-RISK-POLICY-001`

## 9.2.1 Upstream dependency

No overlay data contract becomes active until the upstream return series is:

- frozen;
- versioned;
- free of look-ahead;
- accompanied by cost and turnover;
- assigned an immutable checksum.

## 9.2.2 Public factor track

Sources may include official author data and established factor libraries. Each factor requires:

- economic definition;
- long and short leg definition;
- publication and revision vintage;
- daily or monthly return frequency;
- treatment of missing observations;
- cost status;
- self-financing status.

## 9.2.3 Commodity exact track

Kang and Kwon's commodity replication requires licensed daily settlement histories for the declared 44-contract universe, January 1979–December 2017, with the paper's monthly contract-selection rule:

> At the end of month `t`, select the nearest contract whose maturity is later than the end of month `t+1`, avoiding a roll during the holding month.

A public generic series is not an exact substitute.

## 9.2.4 Real-time volatility record

For each decision month:

```yaml
volatility_state:
  upstream_series_id: "frozen series"
  estimation_end: "timestamp strictly before decision"
  estimator_id: "versioned formula"
  lookback_window: "fixed duration"
  realized_variance: "decimal"
  forecast_variance: "decimal or null"
  scaling_constant_source: "recursive only"
  uncapped_weight: "decimal"
  cap: "decimal"
  final_weight: "decimal"
  turnover_increment: "decimal"
```

Full-sample normalization constants are forbidden in confirmatory out-of-sample tests.

## 9.2.5 No-trade policy

A no-trade or abstention overlay must store:

- upstream desired position;
- current position;
- expected turnover;
- expected all-in cost;
- threshold;
- uncertainty buffer;
- decision;
- counterfactual trade;
- realized implementation shortfall.

Changing the threshold after seeing outcomes creates a new experiment.

---

# 9.3 `EDGE-FUT-CARRY-001`

## 9.3.1 Exact paper tracks

The exact Szymanowska and Boons–Prado tracks require licensed maturity-specific futures histories and paper-specific chain rules.

Necessary fields include:

- first, second, and where required third nearby contracts;
- end-of-period prices;
- contract maturity;
- contract-specific holding returns;
- bimonthly or monthly paper period;
- proxy-spot construction where specified;
- curve slope and curvature;
- roll eligibility;
- portfolio assignment;
- transaction-cost fields.

## 9.3.2 Modern availability constraints

The modern data audit must explicitly report when basis cannot be constructed because:

- the second nearby is absent;
- contract history is too short;
- maturity spacing is irregular;
- a price is stale;
- one contract is illiquid;
- vendor generic mappings change.

Missing second-nearby contracts are not imputed from future observations.

## 9.3.3 Primitive signals

The following remain separate:

- normalized basis or carry;
- nearby versus second-nearby slope;
- basis momentum;
- change in slope;
- curvature;
- simple momentum;
- average commodity factor.

Any combination is tested only after primitive outputs are frozen.

---

# 9.4 `EDGE-FUT-POSITION-001`

## 9.4.1 CFTC report types

Report families remain distinct:

- Legacy futures-only;
- Legacy futures-and-options combined;
- Supplemental Commodity Index Trader;
- Disaggregated;
- Traders in Financial Futures.

A category change is not treated as a continuous semantic series without a documented bridge.

## 9.4.2 CFTC timing

Required fields:

```yaml
cot_release:
  report_type: "id"
  market_code: "CFTC code"
  report_as_of_date: "Tuesday date or actual report date"
  scheduled_release_time: "UTC timestamp"
  actual_release_time: "UTC timestamp or inferred status"
  source_file_version: "id"
  revised: false
  release_status: "VERIFIED|SCHEDULE_INFERRED|EXCEPTION"
```

Regular Friday release timing is a default schedule, not proof of actual historical release. Holidays, government shutdowns, backlogs, and corrections override it.

## 9.4.3 Position fields

Preserve:

- long;
- short;
- spreading;
- total open interest;
- reportable and nonreportable;
- trader count;
- category;
- futures-only versus combined;
- units;
- concentration fields when used.

## 9.4.4 Public-release decision rule

A position record becomes eligible only after:

```text
available_at = actual_release_time + parser_delay
```

If only a scheduled release is reconstructable, a conservative delay policy is used and labeled.

## 9.4.5 Historical category uncertainty

Backcast classifications, methodology changes, and provider remapping receive explicit uncertainty flags. The project does not assume that a modern category has identical economic meaning throughout the historical sample.

## 9.4.6 Negative control

Fixed-income futures remain a required negative control for speculative-pressure claims. Open-interest growth is reported separately and is not silently treated as speculative pressure.

---

# 9.5 `EDGE-CRYPTO-BASIS-001`

## 9.5.1 Licensed anchor boundary

Chi et al.'s exact experiment uses licensed 1Token data sourced from OKEx:

- minute spot and current-quarter futures;
- 12 cryptocurrencies;
- 2017-11-13 through 2021-03-31;
- point-in-time listing-dependent universe;
- current-quarter roll at the declared exchange time;
- lookbacks 1, 3, 5, and 7 at daily, weekly, and monthly frequencies.

Status: `INCONCLUSIVE_EXACT_REPLICATION_PENDING_LICENSE_OR_AUTHOR_DATA`.

## 9.5.2 Exact 12-asset anchor universe

- ADA
- BCH
- BSV
- BTC
- DOT
- EOS
- ETC
- ETH
- LINK
- LTC
- TRX
- XRP

Membership is date-dependent. An asset cannot enter before its actual listed instrument is available.

## 9.5.3 Public constructive experiment

The public Binance/OKX study receives a new identity and may use:

- spot;
- linear perpetual;
- dated futures where complete histories exist;
- funding;
- mark price;
- index price;
- premium index;
- OI;
- liquidations where provenance is adequate;
- trades and order-book data only within documented coverage.

The universe is determined point in time from:

- listing time;
- active status;
- valid instrument metadata;
- minimum trailing volume/depth;
- maximum spread;
- sufficient history;
- no known data outage;
- settlement and collateral eligibility.

Today's top assets are never projected backward.

---

# 9.6 `EDGE-CRYPTO-RV-001`

## 9.6.1 Instrument pair identity

Each relative-value position specifies:

```yaml
rv_pair:
  spot_venue: "venue"
  spot_instrument_id: "native id"
  derivative_venue: "venue"
  derivative_instrument_id: "native id"
  derivative_type: "PERPETUAL|DATED_FUTURE"
  contract_form: "LINEAR|INVERSE|QUANTO"
  margin_currency: "asset"
  settlement_currency: "asset"
  collateral_assets: []
  hedge_ratio_formula_id: "version"
```

Two nominally identical BTC instruments on different venues are distinct.

## 9.6.2 Funding ledger

Each funding record stores:

- instrument;
- interval start and end;
- payment timestamp;
- announced rate;
- realized rate;
- formula type;
- premium component;
- interest component;
- cap/floor;
- interval length;
- position notional;
- settlement currency;
- payment amount;
- source and formula versions.

Funding interval is data, not a constant.

## 9.6.3 Mark and index ledger

Store separately:

- last trade price;
- mark price;
- index price;
- premium index;
- liquidation reference;
- unrealized-PnL reference;
- realized-PnL reference.

No substitution is permitted without a named experiment variant.

## 9.6.4 Capital path

A two-leg result includes:

- spot purchase cash;
- derivative initial margin;
- maintenance margin;
- variation margin;
- collateral haircut;
- borrowing;
- financing;
- funding;
- transfer delay;
- trapped capital;
- fees;
- spread;
- slippage;
- liquidation;
- ADL;
- insurance-fund effect;
- settlement-currency return;
- venue default haircut.

## 9.6.5 Stage authorization

Historical data acquisition and deterministic accounting are authorized. Paper execution remains unauthorized in Report 2.2.

Decision: `GO_DATA_AND_ACCOUNTING_ONLY`.

---

# 10. Cryptocurrency instrument-version contract

## 10.1 Effective-dated instrument metadata

```yaml
crypto_instrument_version:
  venue_id: "id"
  instrument_id: "native id"
  effective_from: "timestamp"
  effective_to: "timestamp or null"
  instrument_type: "SPOT|MARGIN|SWAP|FUTURES"
  base_currency: "asset"
  quote_currency: "asset"
  settlement_currency: "asset or null"
  contract_value: "decimal or null"
  contract_multiplier: "decimal or null"
  contract_value_currency: "asset or null"
  linearity: "LINEAR|INVERSE|QUANTO|NA"
  tick_size: "decimal"
  lot_size: "decimal"
  minimum_order_size: "decimal"
  listing_time: "timestamp"
  expiry_time: "timestamp or null"
  funding_interval: "duration or null"
  margin_modes: []
  source_artifact_id: "hash"
```

## 10.2 Rule-change ledger

Every announcement or API schema change that affects:

- funding;
- tick size;
- lot size;
- margin tiers;
- contract value;
- index constituents;
- mark formula;
- settlement;
- leverage;
- trading status

creates a new effective-dated rule version.

## 10.3 Candle confirmation

An exchange candle is usable only when finalized. Incomplete records remain raw but are excluded from confirmatory feature construction.

## 10.4 Timestamp units

Timestamp unit is declared per dataset and epoch. Milliseconds, microseconds, and nanoseconds may not be inferred from magnitude without a source rule plus validation.

---

# 11. Point-in-time universe contract

## 11.1 Eligibility state

At each decision time:

```yaml
universe_member:
  experiment_id: "id"
  decision_time: "timestamp"
  canonical_instrument_id: "id"
  eligible: true
  inclusion_reasons: []
  exclusion_reasons: []
  listing_age: "duration"
  lookback_complete: true
  data_fresh: true
  volume_metric: "decimal"
  spread_metric: "decimal"
  open_interest_metric: "decimal or null"
  borrow_available: "bool or null"
  short_available: "bool"
  source_lineage: []
```

## 11.2 Prohibited universe construction

The following are prohibited:

- current constituents applied historically;
- current exchange listings applied before listing;
- exclusion of delisted or failed assets without a recorded exit;
- volume filters calculated with future volume;
- liquidity thresholds tuned on final results;
- replacement of missing historical metadata with current metadata;
- removal of instruments because they hurt performance.

## 11.3 Universe revisions

A revised listing date or instrument status creates a new universe version and invalidates affected derived artifacts.

---

# 12. Source-to-derived lineage graph

Every derived record must be reproducible by traversing a directed acyclic graph.

## 12.1 Node types

- `RAW_ARTIFACT`;
- `RAW_RECORD`;
- `NORMALIZED_RECORD`;
- `INSTRUMENT_VERSION`;
- `UNIVERSE_STATE`;
- `CONTRACT_CHAIN_STATE`;
- `ROLL_EVENT`;
- `FEATURE`;
- `LABEL`;
- `PORTFOLIO_WEIGHT`;
- `COST_ESTIMATE`;
- `PNL_COMPONENT`;
- `EVIDENCE_TABLE`;
- `VERDICT`.

## 12.2 Edge types

- `PARSED_FROM`;
- `NORMALIZED_FROM`;
- `MAPPED_TO`;
- `AVAILABLE_AFTER`;
- `SELECTED_BY`;
- `ROLLED_TO`;
- `DERIVED_FROM`;
- `CORRECTED_BY`;
- `SUPERSEDES`;
- `AGGREGATED_FROM`;
- `VALIDATED_BY`;
- `EXCLUDED_BY`.

## 12.3 Lineage rule

No evidence table or verdict may depend on a node lacking:

- source checksum;
- formula version;
- timing envelope;
- instrument identity;
- experiment identity.

## 12.4 Lineage invalidation

When a raw source is corrected, downstream nodes are marked:

- `UNAFFECTED`;
- `RECOMPUTE_REQUIRED`;
- `VERDICT_INVALIDATED`.

Recomputation creates a new evidence version; it does not mutate the prior evidence.

---

# 13. Formula and schema versioning

## 13.1 Formula registry

Each transformation has:

```yaml
formula:
  formula_id: "stable name"
  version: "semantic version"
  expression: "human-readable equation"
  implementation_commit: "git SHA"
  input_schema_ids: []
  output_schema_id: "id"
  effective_from: "date"
  supersedes: null
  tests: []
```

## 13.2 Changes requiring a new formula version

- return denominator change;
- log versus simple return;
- annualization convention;
- risk-free-rate convention;
- roll rule;
- funding interval;
- basis sign;
- price reference;
- volatility lookback;
- missing-value handling;
- outlier treatment;
- rank breakpoints;
- exchange time boundary;
- collateral treatment.

## 13.3 Schema drift

A source schema fingerprint is computed from field names, data types, nested paths, and enum values. Unexpected drift fails closed.

---

# 14. Cost, financing, margin, and collateral contract

## 14.1 Cost components

Every experiment declares which components apply:

- exchange commission;
- clearing fee;
- regulatory fee;
- broker commission;
- maker/taker fee;
- bid-ask spread;
- slippage;
- market impact;
- borrow fee;
- financing rate;
- funding payment;
- roll fee;
- delivery fee;
- conversion fee;
- transfer fee;
- withdrawal fee;
- collateral opportunity cost;
- stablecoin haircut;
- venue haircut;
- failed-order cost;
- orphan-leg cost.

## 14.2 Effective-dated fee schedule

Fee schedules are instrument-, venue-, tier-, and time-specific. Current fees cannot be applied historically without a declared approximation.

## 14.3 Margin state

```yaml
margin_state:
  account_model: "CROSS|ISOLATED|PORTFOLIO|TRADITIONAL_FCM"
  timestamp: "timestamp"
  instrument_id: "id"
  initial_margin: "decimal"
  maintenance_margin: "decimal"
  variation_margin: "decimal"
  collateral_balance: "decimal"
  collateral_currency: "asset"
  haircut: "decimal"
  liquidation_threshold: "decimal"
  margin_rule_version: "id"
```

## 14.4 Capital efficiency is not free return

A leveraged or margined strategy reports:

- return on gross notional;
- return on posted capital;
- return on total committed capital;
- return after reserve liquidity;
- maximum liquidity call;
- capital locked by venue and settlement asset.

No strategy is declared superior solely because it divides PnL by a smaller margin denominator.

---

# 15. Exact versus constructive boundaries

## 15.1 Exact replication identity

An exact experiment must preserve:

- paper universe;
- sample;
- source class;
- instrument definition;
- timing;
- return contract;
- signal;
- rebalance;
- portfolio construction;
- cost assumptions;
- statistical method.

A material substitution creates a new identity.

## 15.2 Permitted labels

| Label | Meaning |
|---|---|
| `EXACT_PUBLIC_READY` | Exact inputs publicly obtainable and contract frozen |
| `EXACT_LICENSED_READY` | Exact contract known and licensed fields obtained |
| `EXACT_PENDING_LICENSE` | Exact contract known; data not yet acquired |
| `NEAR_EXACT_FACTOR_AUDIT` | Official processed factors available; raw construction incomplete |
| `CONSTRUCTIVE_PUBLIC_READY` | New public-data experiment with frozen distinct identity |
| `INCONCLUSIVE_DATA_ACCESS` | Exact data unavailable; no exact verdict |
| `NO_GO_DATA_INTEGRITY` | Data cannot meet timing or lineage requirements |

## 15.3 No inheritance of verdict

A successful constructive experiment does not turn a failed or inaccessible exact replication into a pass. The verdicts remain separate.

---

# 16. Acquisition decision matrix

| Hypothesis | Exact track | Public/constructive track | Report 2.2 decision |
|---|---|---|---|
| `EDGE-FUT-TREND-001` | Raw MOP universe and vendor data | AQR factor audit and distinct modern futures universe | `GO_PUBLIC_AUDIT`; `EXACT_PENDING_LICENSE` |
| `EDGE-RISK-POLICY-001` | Commodity raw histories for Kang–Kwon | Public author/factor data for Moreira–Muir-style audit | `GO_PUBLIC_AUDIT`; commodity exact `PENDING_LICENSE` |
| `EDGE-FUT-CARRY-001` | Maturity-specific settlement curves | Limited formula and field-feasibility prototypes | `EXACT_PENDING_LICENSE`; no public exact verdict |
| `EDGE-FUT-POSITION-001` | Fan price universe plus CFTC | CFTC timing pipeline with separate price prototype | `GO_CFTC`; price exact `PENDING_LICENSE` |
| `EDGE-CRYPTO-BASIS-001` | Chi 1Token/OKEx archive | New Binance/OKX multi-venue experiment | exact `INCONCLUSIVE_PENDING_ACCESS`; constructive `GO_DATA_ONLY` |
| `EDGE-CRYPTO-RV-001` | De Blasis historical reconstruction where sources permit | Binance/OKX accounting and rule-history study | `GO_DATA_AND_ACCOUNTING_ONLY`; paper execution prohibited |

## 16.1 Traditional-futures procurement gate

Before license purchase, a vendor must confirm:

1. expired contract depth;
2. settlement and close histories;
3. first notice and last trade dates;
4. listed month schedules;
5. OI and volume;
6. corrections and vintages;
7. currency and multiplier history;
8. exchange product mappings;
9. API or bulk reproducibility;
10. derived-data and publication rights;
11. quote and budget;
12. whether one license covers trend, carry, and positioning.

## 16.2 Author-data requests

Requests must ask for:

- exact raw or processed files;
- code;
- data dictionary;
- vendor identifiers;
- sample cutoffs;
- correction history;
- permitted academic use;
- redistribution restrictions;
- checksums if available.

An unanswered request does not justify substituting another dataset under the same experiment identity.

---

# 17. Immutable cutoffs and vintages

## 17.1 Historical replication cutoff

Each paper uses its published sample cutoff. Extensions are separate panels and artifact IDs.

## 17.2 Post-publication extension cutoff

The first extension vintage is frozen at the first successful acquisition after Report 2.2. Later downloads are new vintages.

## 17.3 Constructive cryptocurrency cutoff

Historical public crypto files are frozen by:

- provider path list;
- per-file checksum;
- retrieval date;
- provider update-log snapshot;
- instrument-rule snapshot.

## 17.4 Prospective cutoff

Prospective collection starts only after:

- protocol hash;
- source registry hash;
- formula registry hash;
- instrument manifest hash;
- environment lock.

Report 2.2 does not start prospective trading.

---

# 18. Adversarial data-quality tests

## 18.1 Universal tests

1. duplicate primary keys;
2. out-of-order timestamps;
3. non-monotonic sequence IDs;
4. timezone round-trip failure;
5. timestamp-unit mismatch;
6. values after `available_at`;
7. future-filled missing data;
8. schema drift;
9. file checksum replacement;
10. implausible price or return;
11. stale repeated values;
12. zero or negative prices where invalid;
13. inconsistent currencies;
14. mismatched multiplier;
15. orphan instrument identifiers;
16. sample row-count drift;
17. missing source lineage;
18. parser non-determinism.

## 18.2 Futures-specific tests

1. return crosses contract IDs without a roll event;
2. roll creates artificial PnL;
3. selected contract is past first notice or last trade;
4. maturity ordering is invalid;
5. second nearby equals first nearby;
6. OI or volume crossover uses future values;
7. generic-series return differs materially from contract ledger;
8. multiplier changes without version update;
9. settlement marked preliminary but treated final;
10. missing delivery-month contract;
11. contract symbol reused for another maturity;
12. vendor generic mapping changes silently.

## 18.3 CFTC-specific tests

1. report used before actual release;
2. Tuesday date treated as Friday availability;
3. holiday release ignored;
4. shutdown/backlog release backfilled;
5. futures-only mixed with futures-and-options;
6. legacy mixed with disaggregated;
7. market-code remapping;
8. corrected file overwrites original;
9. category totals fail consistency checks;
10. reportable positions exceed open interest without documented field semantics.

## 18.4 Crypto-specific tests

1. millisecond/microsecond confusion;
2. incomplete candle used;
3. funding interval assumed rather than observed;
4. mark and last price swapped;
5. index price missing while mark is present;
6. instrument metadata applied outside effective dates;
7. listing date after first observed trade or vice versa;
8. archive gap;
9. provider replacement without checksum change record;
10. duplicate trade IDs;
11. sequence gap;
12. negative or impossible OI;
13. settlement currency mismatch;
14. inverse contract treated as linear;
15. funding sign reversed;
16. fill records sorted by system time instead of fill time;
17. cross-venue clocks misaligned;
18. delisted instrument retained after termination;
19. current top-volume universe projected backward;
20. stablecoin value assumed exactly one without a declared benchmark.

## 18.5 Red-team leak injection

The validation suite must deliberately inject:

- a future settlement;
- a CFTC report shifted to Tuesday;
- a candle with `confirm=0`;
- a future listing record;
- a back-adjusted roll jump used as PnL;
- a revised file replacing an original;
- a funding interval change;
- a contract multiplier change.

The pipeline passes only if each injection is rejected and logged.

---

# 19. Required storage zones

```text
data/
├── raw/
│   ├── public/
│   ├── licensed/
│   └── author_provided/
├── immutable_manifests/
├── normalized/
├── instrument_master/
├── contract_chains/
├── universe_states/
├── timing_ledgers/
├── revision_ledgers/
├── derived/
├── evidence/
└── quarantine/
```

Git stores schemas, manifests, code, hashes, and permitted small evidence. Large or restricted data remain in controlled object storage.

---

# 20. Required dataset-level metadata

Every dataset release contains:

```yaml
dataset_release:
  dataset_id: "id"
  version: "version"
  experiment_ids: []
  created_at: "timestamp"
  source_artifact_ids: []
  source_registry_hash: "hash"
  license_registry_hash: "hash"
  instrument_manifest_hash: "hash"
  timing_schema_hash: "hash"
  formula_registry_hash: "hash"
  code_commit: "git SHA"
  environment_lock_hash: "hash"
  row_count: 0
  min_event_time: "timestamp"
  max_event_time: "timestamp"
  min_available_at: "timestamp"
  max_available_at: "timestamp"
  quality_test_report: "artifact id"
  known_limitations: []
  redistribution_class: "class"
```

---

# 21. Data go/no-go gates

## Gate D1 — source identity

Fail if provider, endpoint, or artifact identity cannot be proven.

## Gate D2 — legal and license

Fail if terms are unknown or use is not permitted.

## Gate D3 — instrument identity

Fail if records cannot be mapped to effective-dated instruments and contracts.

## Gate D4 — temporal integrity

Fail if `available_at` cannot be reconstructed to the required confidence.

## Gate D5 — return integrity

Fail if executable returns require cross-contract price differences without roll transactions.

## Gate D6 — universe integrity

Fail if membership is not point in time.

## Gate D7 — revision integrity

Fail if corrections overwrite history without a ledger.

## Gate D8 — cost and capital completeness

Fail if the economic claim requires unavailable fee, financing, margin, collateral, or funding inputs.

## Gate D9 — reproducibility

Fail if another clean environment cannot regenerate normalized artifacts from raw checksums and code.

## Gate D10 — exactness honesty

Fail if a substituted dataset is labeled exact.

---

# 22. Handoff to Report 2.3

Report 2.3 may begin only after the following artifacts exist for the target replication:

1. source artifacts acquired;
2. licenses approved;
3. instrument identifiers mapped;
4. contract chain built;
5. timing ledger complete;
6. raw checksums frozen;
7. formula versions frozen;
8. quality tests passed;
9. exactness label assigned;
10. experiment protocol hash created.

The first permitted empirical sequence is:

1. AQR factor audit for `EDGE-FUT-TREND-001`;
2. Moreira–Muir public factor audit for `EDGE-RISK-POLICY-001`;
3. CFTC release-time and category parser validation;
4. public Binance/OKX data completeness and rule-version audit;
5. licensed data acquisition decision for traditional futures.

No parameter search or strategy tournament begins in Report 2.3. The goal is exact table reconstruction and direct opposing tests.

---

# 23. Binding decisions

1. A single timestamp field is prohibited.
2. `available_at` is the decision boundary.
3. Report date and release time are different.
4. CFTC Tuesday positions are unavailable until their actual public release.
5. Historical release times may be inferred only under a labeled conservative policy.
6. Raw files are append-only.
7. Provider replacements create revisions, not overwrites.
8. Current instrument metadata cannot be projected backward.
9. Continuous adjusted futures prices cannot produce executable PnL.
10. Every futures PnL record must preserve a contract ID.
11. Every roll must appear in a roll ledger.
12. The old-to-new contract price gap is not a trading return by itself.
13. Fully collateralized and margin-capital returns are separately reported.
14. AQR factor files support a public audit, not exact raw replication.
15. Traditional-futures exact replication remains conditional on licensed expired-contract data.
16. CFTC acquisition may begin immediately.
17. CFTC report families remain semantically distinct.
18. Position classification uncertainty is retained.
19. Chi et al. exact replication remains pending licensed data.
20. Binance/OKX reconstruction receives a new experiment identity.
21. Funding interval and formula are effective-dated data.
22. Mark, index, and last prices are distinct.
23. Linear, inverse, and quanto contracts are distinct.
24. Paper execution of crypto relative value remains unauthorized.
25. Cost, margin, collateral, and financing are part of the dataset contract.
26. License terms and redistribution rights are versioned.
27. Every derived value has raw lineage and a formula version.
28. Every source correction triggers downstream invalidation analysis.
29. Red-team leak injections are mandatory.
30. Empirical fitting remains disabled until Report 2.3 prerequisites pass.

---

# Final decision

Report 2.2 is complete when the human report and machine-readable companions are committed and internally consistent.

The project now has a binding definition of:

- what each datum represents;
- when it becomes usable;
- how instruments and universes are identified;
- how futures rolls and returns are separated;
- how regulator releases and corrections are handled;
- how cryptocurrency contract rules are versioned;
- how costs and capital are represented;
- which replications are exact, licensed, constructive, or inconclusive;
- and which data tracks may proceed.

The next permissible work is controlled acquisition, validation, and exact empirical reconstruction under Report 2.3. The next impermissible work is selecting a profitable model before these data contracts are implemented and verified.
