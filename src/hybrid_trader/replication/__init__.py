"""Auditable empirical-replication primitives.

The package is deliberately fail-closed. It provides deterministic data audits,
formula reproductions, and accounting checks; it does not authorize strategy
selection or live trading.
"""

from hybrid_trader.replication.factor_audit import (
    annualized_metrics,
    compare_factor_vintages,
    volatility_managed_returns,
)
from hybrid_trader.replication.futures import build_roll_ledger, same_contract_returns
from hybrid_trader.replication.verdicts import ReplicationStatus, ReplicationVerdict

__all__ = [
    "ReplicationStatus",
    "ReplicationVerdict",
    "annualized_metrics",
    "build_roll_ledger",
    "compare_factor_vintages",
    "same_contract_returns",
    "volatility_managed_returns",
]
