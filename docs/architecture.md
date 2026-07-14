# Reference architecture

Phase 2B implements the research path only. Live execution remains outside the
package until the release gates are satisfied.

```mermaid
flowchart LR
    A[Point-in-time market data] --> B[Validation + immutable snapshot]
    B --> C[Market feature pipeline]
    D[Funding / OI / basis / local premium] --> E[Availability-time as-of join]
    E --> C
    C --> F[Trend baseline]
    C --> G[Prior / Ridge / LightGBM / CatBoost]
    C --> H[TimesFM / Chronos feature cache]
    I[Timestamped news and on-chain events] --> J[LLM/RAG event encoder - future]
    F --> K[Sealed benchmark]
    G --> K
    H --> K
    J --> K
    K --> L[Probability calibration]
    L --> M[Validation-only threshold]
    M --> N[Deterministic risk sizing]
    N --> O[Prospective paper ledger]
    O --> P[Dry-run adapter - future]
    P --> Q[Production execution - future]
```

## Non-negotiable boundaries

1. Every source defines event time and availability time.
2. A label is used only after its outcome was observable.
3. Calibration and threshold selection have separate chronological partitions.
4. Final test cannot influence a feature, model, prompt, threshold, or cost assumption.
5. Foundation models are feature generators, never order generators.
6. LLM output is constrained event data and cannot override risk limits.
7. Exchange adapters are replaceable and do not leak into research logic.
8. Every test fold is liquidated and charged before the next fold starts.
9. A historical result cannot pass the prospective-evidence gate by itself.
