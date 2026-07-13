"""Execution-aligned labels with explicit information availability."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class LabelSpec:
    execution_delay_bars: int = 1
    holding_period_bars: int = 1
    positive_threshold_bps: float = 0.0

    def __post_init__(self) -> None:
        if self.execution_delay_bars < 0:
            raise ValueError("execution_delay_bars cannot be negative")
        if self.holding_period_bars <= 0:
            raise ValueError("holding_period_bars must be positive")

    @property
    def entry_offset(self) -> int:
        # A decision made after bar t closes cannot transact at Open[t+1].
        # Delay zero therefore means the first subsequent open, Open[t+1].
        return 1 + self.execution_delay_bars

    @property
    def exit_offset(self) -> int:
        return self.entry_offset + self.holding_period_bars


def add_execution_labels(frame: pd.DataFrame, spec: LabelSpec) -> pd.DataFrame:
    """Add Open-to-Open target returns and the time each label became observable."""

    required = {"open", "open_available_at", "available_at"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Label frame missing columns: {sorted(missing)}")
    result = frame.copy()
    result["decision_time"] = pd.to_datetime(result["available_at"], utc=True)
    entry_price = result["open"].shift(-spec.entry_offset)
    exit_price = result["open"].shift(-spec.exit_offset)
    result["entry_time"] = pd.Series(result.index, index=result.index).shift(-spec.entry_offset)
    result["exit_time"] = pd.Series(result.index, index=result.index).shift(-spec.exit_offset)
    result["entry_available_at"] = result["open_available_at"].shift(-spec.entry_offset)
    result["label_available_at"] = result["open_available_at"].shift(-spec.exit_offset)
    result["target_return"] = exit_price / entry_price - 1.0
    threshold = spec.positive_threshold_bps / 10_000.0
    result["target_positive"] = np.where(
        result["target_return"].notna(),
        (result["target_return"] > threshold).astype(float),
        np.nan,
    )

    valid_times = result["entry_available_at"].notna() & result["label_available_at"].notna()
    if (
        result.loc[valid_times, "entry_available_at"] < result.loc[valid_times, "decision_time"]
    ).any():
        raise ValueError("Execution contract permits entry before the decision is available")
    if (
        result.loc[valid_times, "label_available_at"]
        <= result.loc[valid_times, "entry_available_at"]
    ).any():
        raise ValueError("Label must become available after entry")
    return result
