from __future__ import annotations

import csv
import io
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

from hybrid_trader.replication.moreira_muir import (
    EXPECTED_HEADER,
    SAFE_METRIC_DECIMAL_PLACES,
    VOLATILITY_MATCH_RELATIVE_TOLERANCE,
    factor_pair_audits,
    parse_official_factor_bytes,
    validate_author_page,
    write_safe_evidence,
)

RowMutator = Callable[[int, list[str]], None]


def make_csv(*, months: int = 8, mutate: RowMutator | None = None) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(EXPECTED_HEADER)
    dates = pd.date_range("2000-01-01", periods=months, freq="MS")
    for index, date in enumerate(dates):
        base = float(index + 1)
        row: list[str] = [date.strftime("%Y-%m")]
        row.extend(
            [
                str(base),
                str(base + 0.1),
                str(base + 0.2),
                str(base + 0.3),
                str(base + 0.4),
                str(base + 0.5),
                str(base),
                str(base + 0.1),
                str(base + 0.2),
                str(base + 0.3),
                str(base + 0.4),
                str(base + 0.5),
                "0.1",
            ]
        )
        if mutate is not None:
            mutate(index, row)
        writer.writerow(row)
    return output.getvalue().encode()


def test_parse_preserves_percent_unit_and_factor_pairs() -> None:
    frame = parse_official_factor_bytes(make_csv(), require_exact_snapshot=False)
    assert frame.attrs["return_unit"] == "PERCENT"
    assert len(frame) == 8
    assert len(factor_pair_audits(frame)) == 6


def test_exact_snapshot_rejects_synthetic_hash() -> None:
    with pytest.raises(ValueError, match="byte count changed"):
        parse_official_factor_bytes(make_csv())


def test_html_is_rejected() -> None:
    with pytest.raises(ValueError, match="returned HTML"):
        parse_official_factor_bytes(b"<!doctype html>", require_exact_snapshot=False)


def test_duplicate_month_is_rejected() -> None:
    def mutate(index: int, row: list[str]) -> None:
        if index == 2:
            row[0] = "2000-02"

    with pytest.raises(ValueError, match="duplicate months"):
        parse_official_factor_bytes(make_csv(mutate=mutate), require_exact_snapshot=False)


def test_monthly_gap_is_rejected() -> None:
    def mutate(index: int, row: list[str]) -> None:
        if index == 3:
            row[0] = "2000-05"

    with pytest.raises(ValueError, match=r"duplicate months|monthly date gap"):
        parse_official_factor_bytes(make_csv(mutate=mutate), require_exact_snapshot=False)


def test_pair_missingness_mismatch_is_rejected() -> None:
    def mutate(index: int, row: list[str]) -> None:
        if index == 0:
            row[5] = ""

    with pytest.raises(ValueError, match="missingness mismatch"):
        parse_official_factor_bytes(make_csv(mutate=mutate), require_exact_snapshot=False)


def test_non_leading_late_factor_missingness_is_rejected() -> None:
    def mutate(index: int, row: list[str]) -> None:
        if index == 3:
            row[5] = ""
            row[11] = ""

    with pytest.raises(ValueError, match="Non-leading missing"):
        parse_official_factor_bytes(make_csv(mutate=mutate), require_exact_snapshot=False)


def test_nonfinite_value_is_rejected() -> None:
    def mutate(index: int, row: list[str]) -> None:
        if index == 2:
            row[1] = "nan"

    with pytest.raises(ValueError, match="Non-finite"):
        parse_official_factor_bytes(make_csv(mutate=mutate), require_exact_snapshot=False)


def test_volatility_match_failure_is_reported_not_hidden() -> None:
    def mutate(index: int, row: list[str]) -> None:
        row[1] = str((index + 1) * 2.0)

    frame = parse_official_factor_bytes(make_csv(mutate=mutate), require_exact_snapshot=False)
    audit = factor_pair_audits(frame)[0]
    assert audit.relative_standard_deviation_error > VOLATILITY_MATCH_RELATIVE_TOLERANCE
    assert audit.volatility_match_within_tolerance is False


def test_safe_metrics_are_canonicalized() -> None:
    frame = parse_official_factor_bytes(make_csv(), require_exact_snapshot=False)
    for audit in factor_pair_audits(frame):
        assert audit.managed_standard_deviation_percent == round(
            audit.managed_standard_deviation_percent, SAFE_METRIC_DECIMAL_PLACES
        )
        assert audit.unmanaged_standard_deviation_percent == round(
            audit.unmanaged_standard_deviation_percent, SAFE_METRIC_DECIMAL_PLACES
        )
        assert audit.standard_deviation_ratio == round(
            audit.standard_deviation_ratio, SAFE_METRIC_DECIMAL_PLACES
        )
        assert audit.relative_standard_deviation_error == round(
            audit.relative_standard_deviation_error, SAFE_METRIC_DECIMAL_PLACES
        )
        assert audit.correlation == round(audit.correlation, SAFE_METRIC_DECIMAL_PLACES)


def test_author_page_requires_unit_and_scaling_description() -> None:
    page = b"Volatility-Managed Factor Returns Returns are in percent inverse of the prior month"
    identity = validate_author_page(page)
    assert identity["byte_count"] == len(page)
    with pytest.raises(ValueError, match="description changed"):
        validate_author_page(b"Volatility-Managed Factor Returns")


def test_safe_evidence_requires_the_frozen_official_snapshot(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    page_path = tmp_path / "data.html"
    output = tmp_path / "safe"
    csv_path.write_bytes(make_csv())
    page_path.write_bytes(
        b"Volatility-Managed Factor Returns Returns are in percent inverse of the prior month"
    )
    with pytest.raises(ValueError, match="byte count changed"):
        write_safe_evidence(csv_path=csv_path, author_page_path=page_path, output_dir=output)
