import pandas as pd

from hybrid_trader.config import AppConfig
from hybrid_trader.walkforward import expanding_folds, run_walk_forward


def test_expanding_folds_are_chronological() -> None:
    folds = expanding_folds(1000, initial_train=500, test_size=100, gap=2)
    assert len(folds) == 4
    for fold in folds:
        assert fold.train_end < fold.test_start
        assert fold.test_start < fold.test_end
    assert [fold.train_end for fold in folds] == sorted(fold.train_end for fold in folds)


def test_walk_forward_returns_fold_metrics(
    normalized_ohlcv: pd.DataFrame, config: AppConfig
) -> None:
    results = run_walk_forward(normalized_ohlcv, config, initial_train=350, test_size=100, gap=1)
    assert not results.empty
    assert {"fold", "total_return", "max_drawdown", "test_start", "test_end"}.issubset(
        results.columns
    )
