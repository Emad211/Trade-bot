# Report 2.3B — Static Analysis, Test, and Coverage Verification

**Program:** Edge Discovery Research Program  
**Section:** 2 — Research Replication  
**Parent:** [Report 2.3](02-03-controlled-empirical-and-code-replication.md)  
**Independent verification:** [Report 2.3A](02-03-independent-reality-verification-log.md)  
**Verification date:** 2026-07-18  
**Status:** Complete for the local checks explicitly recorded here

---

# 1. Purpose

This report records the static and dynamic verification actually executed against the hardened Report 2.3 replication package.

It distinguishes:

- a local tool pass;
- a GitHub-hosted CI pass;
- implementation correctness on deterministic fixtures;
- empirical paper replication.

Only the first and third were established in this run. A GitHub-hosted workflow was committed, but no workflow run or status check was observed. No empirical paper result was reproduced.

---

# 2. Files in verification scope

```text
src/hybrid_trader/replication/
├── __init__.py
├── artifacts.py
├── cftc.py
├── crypto.py
├── factor_audit.py
├── futures.py
├── provenance.py
├── runner.py
└── verdicts.py

tests/
├── test_replication_cftc.py
├── test_replication_crypto.py
├── test_replication_factor_audit.py
├── test_replication_futures.py
└── test_replication_provenance.py
```

The source was reconstructed from authenticated GitHub commit content and then hardened. The final content was the content committed to `agent/edge-research-reports`.

---

# 3. Tool versions

```text
Python: 3.13.5 in the independent temporary container
Ruff: 0.15.22
Mypy: 2.3.0
Pytest: 9.0.2
Coverage.py / pytest-cov: available in the verification environment
Pandas: 2.2.3
NumPy: 2.3.5
Pydantic: 2.13.4
```

The repository CI workflow separately pins Python 3.11 because the project declares Python 3.11 or newer. That workflow has been committed but has not produced a confirmed GitHub run in this verification.

---

# 4. Ruff

The final check used the repository lint selection rather than Ruff defaults:

```bash
python -m ruff check \
  --select E,F,I,UP,B,SIM,RUF \
  --ignore E501 \
  src/hybrid_trader/replication \
  tests/test_replication_*.py
```

Result:

```text
All checks passed!
```

Before the pass, Ruff identified real issues including import ordering, quoted return annotations, unnecessary nested conditions, and a redundant integer conversion. Those issues were corrected rather than ignored.

Verdict:

```text
LOCAL_RUFF: PASS
GITHUB_CI_RUFF: NOT_YET_OBSERVED
```

---

# 5. Mypy

The final strict check was:

```bash
python -m mypy \
  --strict \
  --ignore-missing-imports \
  src/hybrid_trader/replication
```

Result:

```text
Success: no issues found in 9 source files
```

The initial check failed with seven real typing errors involving:

- pandas scalar conversion;
- `Hashable` column labels treated as strings;
- ambiguous return typing in monthly date parsing.

The code was changed until the strict check passed. No `# type: ignore` escape was added for these defects.

Verdict:

```text
LOCAL_MYPY_STRICT: PASS
GITHUB_CI_MYPY: NOT_YET_OBSERVED
```

---

# 6. Pytest

Command:

```bash
PYTHONPATH=/tmp/replication-audit/src \
python -m pytest -q /tmp/replication-audit/tests
```

Final result:

```text
...............                                                          [100%]
15 passed
```

The 15 tests include:

- three factor and volatility tests;
- two futures contract/roll tests;
- three CFTC timing tests;
- three cryptocurrency semantics/accounting tests;
- four immutable provenance and verdict-gating tests.

The test inputs are deterministic synthetic fixtures. They prove the tested implementation invariants, not the claims of any paper.

Verdict:

```text
LOCAL_PYTEST: PASS_15
PAPER_REPLICATION: NOT_INFERRED
```

---

# 7. Coverage

Command:

```bash
python -m pytest -q tests/test_replication_*.py \
  --cov=hybrid_trader.replication \
  --cov-report=term-missing \
  --cov-fail-under=80
```

Result:

```text
15 tests passed
Total replication-package coverage: 85.44%
Required threshold: 80%
Coverage gate: PASS
```

This is statement coverage for the replication package under synthetic tests. It is not market-history coverage, paper-table coverage, venue coverage, or economic regime coverage.

Verdict:

```text
LOCAL_COVERAGE: PASS_85.44_PERCENT
EMPIRICAL_COVERAGE: NOT_ESTABLISHED
```

---

# 8. Compilation

Command:

```bash
python -m compileall -q src tests
```

Result:

```text
PASS
```

---

# 9. GitHub Actions workflow

Committed workflow:

```text
.github/workflows/replication-integrity.yml
```

The workflow is configured to run:

1. Python 3.11 setup;
2. installation of `.[dev,replication]`;
3. Ruff using the repository configuration;
4. strict mypy configuration from the repository;
5. replication tests;
6. replication-package coverage with an 80% minimum.

At the time of this report:

```text
WORKFLOW_FILE: COMMITTED
WORKFLOW_RUN: NOT_OBSERVED
COMBINED_STATUS: EMPTY
CI_VERDICT: UNVERIFIED
```

The absence of a run is not converted into a pass or a fail. The local verification remains the only executed static-analysis evidence recorded here.

---

# 10. Current code-verification verdict

```text
EXACT COMMITTED SOURCE RECONSTRUCTION: CONFIRMED
RUFF LOCAL: PASS
MYPY STRICT LOCAL: PASS
PYTEST LOCAL: 15 PASS
COVERAGE LOCAL: 85.44% PASS
COMPILEALL LOCAL: PASS
GITHUB-HOSTED CI: NOT YET CONFIRMED
OFFICIAL DATA INGESTION: INCOMPLETE
PAPER-LEVEL NUMERICAL REPLICATION: NOT COMPLETE
ECONOMIC EDGE: NOT ESTABLISHED
```

---

# 11. Authorization consequence

The successful code checks authorize continued implementation and official artifact acquisition only.

They do not authorize:

- parameter search;
- strategy selection;
- a sensitivity tournament over unreplicated results;
- paper trading;
- live trading;
- leverage;
- capital deployment.

Report 2.4 remains blocked until the official artifact gates in Report 2.3 pass.
