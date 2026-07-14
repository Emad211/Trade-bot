"""Chronological sealed walk-forward split construction and label purging."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime

import pandas as pd


@dataclass(frozen=True)
class SplitSpec:
    initial_train: int
    calibration_size: int
    validation_size: int
    test_size: int
    step_size: int
    embargo: int = 1

    def __post_init__(self) -> None:
        if self.initial_train <= 0:
            raise ValueError("initial_train must be positive")
        for name in ("calibration_size", "validation_size", "test_size", "step_size"):
            if getattr(self, name) <= 0:
                raise ValueError(f"{name} must be positive")
        if self.embargo < 0:
            raise ValueError("embargo cannot be negative")

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


@dataclass(frozen=True)
class SealedFold:
    fold: int
    train: slice
    calibration: slice
    validation: slice
    test: slice

    def __post_init__(self) -> None:
        slices = (self.train, self.calibration, self.validation, self.test)
        for item in slices:
            if item.start is None or item.stop is None:
                raise ValueError("Sealed fold slices require explicit start and stop")
            if item.start < 0 or item.stop <= item.start:
                raise ValueError("Sealed fold slices must be non-empty and non-negative")
        if not (
            self.train.stop <= self.calibration.start
            and self.calibration.stop <= self.validation.start
            and self.validation.stop <= self.test.start
        ):
            raise ValueError("Sealed fold partitions must be chronological and non-overlapping")


def sealed_folds(length: int, spec: SplitSpec) -> list[SealedFold]:
    """Build expanding-train folds with separate calibration, validation and test."""

    if length <= 0:
        raise ValueError("length must be positive")
    folds: list[SealedFold] = []
    fold_number = 0
    train_end = spec.initial_train
    while True:
        calibration_start = train_end + spec.embargo
        calibration_end = calibration_start + spec.calibration_size
        validation_start = calibration_end
        validation_end = validation_start + spec.validation_size
        test_start = validation_end + spec.embargo
        test_end = test_start + spec.test_size
        if test_end > length:
            break
        folds.append(
            SealedFold(
                fold=fold_number,
                train=slice(0, train_end),
                calibration=slice(calibration_start, calibration_end),
                validation=slice(validation_start, validation_end),
                test=slice(test_start, test_end),
            )
        )
        fold_number += 1
        train_end += spec.step_size
    return folds


def purge_unknown_labels(
    frame: pd.DataFrame,
    partition: slice,
    *,
    known_by: pd.Timestamp | datetime | date | str,
) -> pd.DataFrame:
    """Keep rows whose outcomes were observable by the next partition boundary."""

    required = {"target_positive", "label_available_at"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Cannot purge labels; missing columns: {sorted(missing)}")
    result = frame.iloc[partition].copy()
    boundary = pd.Timestamp(known_by)
    boundary = (
        boundary.tz_localize("UTC") if boundary.tzinfo is None else boundary.tz_convert("UTC")
    )
    labels_available = pd.to_datetime(result["label_available_at"], utc=True, errors="coerce")
    mask = (
        result["target_positive"].notna()
        & labels_available.notna()
        & (labels_available <= boundary)
    )
    return result.loc[mask].copy()
