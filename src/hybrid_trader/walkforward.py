"""Chronological walk-forward evaluation utilities."""

from dataclasses import dataclass

import pandas as pd

from hybrid_trader.backtest import calculate_metrics, run_backtest
from hybrid_trader.config import AppConfig
from hybrid_trader.strategies import generate_trend_exposure


@dataclass(frozen=True)
class Fold:
    train_start: int
    train_end: int
    test_start: int
    test_end: int


def expanding_folds(
    n_samples: int,
    *,
    initial_train: int,
    test_size: int,
    step_size: int | None = None,
    gap: int = 1,
) -> list[Fold]:
    """Create expanding chronological folds with an embargo gap."""

    if min(n_samples, initial_train, test_size) <= 0:
        raise ValueError("n_samples, initial_train and test_size must be positive")
    if gap < 0:
        raise ValueError("gap cannot be negative")
    step = step_size or test_size
    folds: list[Fold] = []
    train_end = initial_train
    while True:
        test_start = train_end + gap
        test_end = test_start + test_size
        if test_end > n_samples:
            break
        folds.append(Fold(0, train_end, test_start, test_end))
        train_end += step
    return folds


def run_walk_forward(
    data: pd.DataFrame,
    config: AppConfig,
    *,
    initial_train: int,
    test_size: int,
    gap: int = 1,
) -> pd.DataFrame:
    """Evaluate the fixed baseline across consecutive out-of-sample windows."""

    folds = expanding_folds(
        len(data),
        initial_train=initial_train,
        test_size=test_size,
        gap=gap,
    )
    if not folds:
        raise ValueError("No complete walk-forward fold can be constructed")

    signal_frame = generate_trend_exposure(data, config)
    full = run_backtest(signal_frame, config).frame
    rows: list[dict[str, float | int | str]] = []
    for fold_number, fold in enumerate(folds, start=1):
        window = full.iloc[fold.test_start : fold.test_end]
        metrics = calculate_metrics(
            window["net_strategy_return"],
            window["executed_exposure"],
            window["turnover"],
            window["close"],
            config.market.periods_per_year,
        )
        rows.append(
            {
                "fold": fold_number,
                "train_bars": fold.train_end - fold.train_start,
                "test_bars": fold.test_end - fold.test_start,
                "test_start": str(window.index[0]),
                "test_end": str(window.index[-1]),
                **metrics,
            }
        )
    return pd.DataFrame(rows)
