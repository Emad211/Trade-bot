from __future__ import annotations

import pandas as pd
import pytest

from hybrid_trader.replication.moreira_muir_reconciliation import (
    RECONCILIATION_FACTORS,
    reconcile_unmanaged_factors,
)


def frames(*, mismatch_factor: str | None = None):
    dates = pd.date_range("2000-01-01", periods=4, freq="MS")
    author_data = {"Date": dates}
    current_data = {}
    for index, factor in enumerate(RECONCILIATION_FACTORS, start=1):
        values = [float(index + offset) for offset in range(4)]
        author_data[factor] = values.copy()
        current_data[factor] = values.copy()
    if mismatch_factor is not None:
        current_data[mismatch_factor][2] += 0.01
    return pd.DataFrame(author_data), pd.DataFrame(current_data, index=dates)


def test_exact_sources_match_all_factors() -> None:
    author, current = frames()
    results = reconcile_unmanaged_factors(author, current)
    assert len(results) == 7
    assert all(item.exact_current_source_match for item in results)
    assert all(item.exact_mismatch_count == 0 for item in results)


def test_source_mismatch_is_retained_not_hidden() -> None:
    author, current = frames(mismatch_factor="SMB")
    results = {item.factor: item for item in reconcile_unmanaged_factors(author, current)}
    assert results["SMB"].exact_current_source_match is False
    assert results["SMB"].exact_mismatch_count == 1
    assert results["SMB"].maximum_absolute_difference_percent == 0.01
    assert results["SMB"].first_exact_mismatch_month == "2000-03"
    assert results["SMB"].last_exact_mismatch_month == "2000-03"
    assert results["Mkt-RF"].exact_current_source_match is True


def test_small_numerical_difference_is_exact_mismatch_but_within_tolerance() -> None:
    author, current = frames()
    current.loc[pd.Timestamp("2000-02-01"), "HML"] += 1e-13
    result = {
        item.factor: item for item in reconcile_unmanaged_factors(author, current)
    }["HML"]
    assert result.exact_mismatch_count == 1
    assert result.numerical_tolerance_mismatch_count == 0
    assert result.maximum_absolute_difference_percent == 0.0
    assert result.exact_current_source_match is False


def test_missing_pair_values_use_common_nonmissing_interval() -> None:
    author, current = frames()
    author.loc[0, "RMW"] = float("nan")
    current.loc[pd.Timestamp("2000-04-01"), "RMW"] = float("nan")
    result = {
        item.factor: item for item in reconcile_unmanaged_factors(author, current)
    }["RMW"]
    assert result.overlap_count == 2
    assert result.first_overlap_month == "2000-02"
    assert result.last_overlap_month == "2000-03"


def test_no_overlap_is_rejected() -> None:
    author, current = frames()
    author["CMA"] = float("nan")
    with pytest.raises(ValueError, match="No overlapping observations"):
        reconcile_unmanaged_factors(author, current)


def test_missing_factor_is_rejected() -> None:
    author, current = frames()
    with pytest.raises(ValueError, match="Author frame lacks Mom"):
        reconcile_unmanaged_factors(author.drop(columns=["Mom"]), current)
    with pytest.raises(ValueError, match="Monthly panel lacks Mom"):
        reconcile_unmanaged_factors(author, current.drop(columns=["Mom"]))


def test_non_datetime_monthly_index_is_rejected() -> None:
    author, current = frames()
    current.index = [1, 2, 3, 4]
    with pytest.raises(ValueError, match="DatetimeIndex"):
        reconcile_unmanaged_factors(author, current)


def test_difference_hash_is_deterministic() -> None:
    author, current = frames(mismatch_factor="Mom")
    first = reconcile_unmanaged_factors(author, current)
    second = reconcile_unmanaged_factors(author, current)
    assert [item.difference_vector_sha256 for item in first] == [
        item.difference_vector_sha256 for item in second
    ]
