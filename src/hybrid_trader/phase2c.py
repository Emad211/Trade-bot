"""Public Phase 2C API.

Implementation is split into focused modules so source contracts, collection,
reporting and orchestration can be reviewed and type-checked independently.
"""

from hybrid_trader.phase2c_contracts import (
    DerivativeVenueSpec,
    FredSeriesSpec,
    Phase2CRegistry,
    Phase2CResult,
    Phase2CSpec,
    SourceAttempt,
    SpotVenueSpec,
    StooqSeriesSpec,
    load_phase2c_spec,
)
from hybrid_trader.phase2c_runner import main, run_phase2c

__all__ = [
    "DerivativeVenueSpec",
    "FredSeriesSpec",
    "Phase2CRegistry",
    "Phase2CResult",
    "Phase2CSpec",
    "SourceAttempt",
    "SpotVenueSpec",
    "StooqSeriesSpec",
    "load_phase2c_spec",
    "main",
    "run_phase2c",
]

if __name__ == "__main__":
    main()
