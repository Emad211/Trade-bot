# Prospective forward-test ledger

Historical tests cannot fully eliminate foundation-model contamination. The forward
ledger records decisions after the experiment is frozen and before outcomes occur.

Each decision stores:

- recording and decision timestamps;
- symbol;
- immutable dataset SHA;
- experiment ID;
- calibrated probability and threshold;
- desired Long/Flat exposure;
- reason codes;
- SHA-256 of the previous canonical record.

`forward-verify` validates parsing, the complete hash chain, strictly increasing
decision times, non-decreasing recording times, and the final head hash. Editing,
deleting or reordering an earlier record breaks the chain.

Before a prospective period, freeze:

- code commit;
- dataset and feature-cache SHAs;
- model ID and revision;
- feature list;
- calibration and threshold procedure;
- cost assumptions;
- exposure and stop conditions.

The ledger is a single-writer research artifact, not a distributed transaction log,
and no ledger record is an exchange order.
