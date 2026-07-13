# Release gates

## Gate 1 — data

- point-in-time availability documented;
- immutable snapshot hash verified;
- missingness and outages reported;
- no revised macro data without vintage timestamps.

## Gate 2 — research

- sealed walk-forward complete;
- baseline comparisons complete;
- cost stress complete;
- ablations complete;
- no test-driven feature, parameter or prompt tuning.

## Gate 3 — prospective evidence

- hash-chained paper decisions recorded;
- enough independent decisions and regimes observed;
- calibration remains acceptable;
- drawdown and turnover remain inside pre-declared limits.

## Gate 4 — dry run

- venue eligibility independently verified;
- no-withdrawal API key;
- idempotent client order IDs;
- order, fill and balance reconciliation;
- stale-data and disconnect behavior tested;
- kill switch tested.

## Gate 5 — controlled capital

- explicit human approval;
- tiny capped allocation;
- no leverage;
- custody and withdrawal plan;
- monitoring and incident runbook;
- automatic halt on unexplained state divergence.
