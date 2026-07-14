import pandas as pd
import pytest

from hybrid_trader.splits import SplitSpec, purge_unknown_labels, sealed_folds


def test_sealed_folds_are_expanding_and_embargoed() -> None:
    spec = SplitSpec(100, 20, 20, 20, 20, embargo=2)
    folds = sealed_folds(220, spec)
    assert len(folds) >= 2
    assert folds[0].train == slice(0, 100)
    assert folds[0].calibration.start == 102
    assert folds[0].test.start == 144
    assert folds[1].train.stop == 120


def test_no_complete_fold_returns_empty() -> None:
    spec = SplitSpec(100, 20, 20, 20, 20, embargo=2)
    assert sealed_folds(150, spec) == []


def test_purge_removes_labels_unknown_at_boundary() -> None:
    times = pd.date_range("2024-01-01", periods=5, freq="h", tz="UTC")
    frame = pd.DataFrame(
        {
            "target_positive": [1.0] * 5,
            "label_available_at": times + pd.Timedelta(hours=2),
        },
        index=times,
    )
    result = purge_unknown_labels(frame, slice(0, 5), known_by=times[3])
    assert len(result) == 2


def test_split_spec_rejects_negative_embargo() -> None:
    with pytest.raises(ValueError):
        SplitSpec(100, 20, 20, 20, 20, embargo=-1)
