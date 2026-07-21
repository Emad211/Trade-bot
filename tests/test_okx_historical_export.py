from __future__ import annotations

import io
import json
import zipfile

import pytest

from hybrid_trader.replication.okx_historical_export import (
    OKXHistoricalExportError,
    inspect_funding_archive_bytes,
)


def _archive(
    csv_text: str,
    *,
    filename: str = "BTC-USDT-SWAP-fundingrates-2022-03.csv",
    extra_member: bool = False,
) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(filename, csv_text)
        if extra_member:
            archive.writestr("extra.csv", csv_text)
    return output.getvalue()


def test_profiles_archive_without_retaining_rate_values() -> None:
    raw = _archive(
        "fundingTime,fundingRate,realizedRate\n"
        "1646092800000,0.000123,0.000122\n"
        "1646121600000,-0.000456,-0.000455\n"
        "1646150400000,0.000789,0.000788\n"
    )

    profile = inspect_funding_archive_bytes(raw)
    safe_json = json.dumps(profile.to_safe_dict(), sort_keys=True)

    assert profile.member.row_count == 3
    assert profile.member.timestamp_field == "fundingTime"
    assert profile.member.timestamp_order == "ascending"
    assert profile.member.unique_timestamp_count == 3
    assert profile.member.duplicate_timestamp_count == 0
    assert profile.member.minimum_timestamp_utc == "2022-03-01T00:00:00Z"
    assert profile.member.maximum_timestamp_utc == "2022-03-01T16:00:00Z"
    assert profile.raw_rows_retained is False
    assert profile.ordered_timestamp_series_retained is False
    assert profile.funding_rate_values_retained is False
    assert "0.000123" not in safe_json
    assert "-0.000456" not in safe_json
    assert "0.000789" not in safe_json


def test_records_descending_and_duplicate_timestamps() -> None:
    raw = _archive(
        "fundingTime,fundingRate\n1646150400000,0.1\n1646121600000,0.2\n1646121600000,0.3\n"
    )

    profile = inspect_funding_archive_bytes(raw)

    assert profile.member.timestamp_order == "descending"
    assert profile.member.unique_timestamp_count == 2
    assert profile.member.duplicate_timestamp_count == 1


def test_accepts_iso_timestamp_field_case_insensitively() -> None:
    raw = _archive(
        "Timestamp,Funding Rate\n2022-03-01T00:00:00Z,0.1\n2022-03-01T08:00:00+00:00,0.2\n"
    )

    profile = inspect_funding_archive_bytes(raw)

    assert profile.member.timestamp_field == "Timestamp"
    assert profile.member.first_timestamp_utc == "2022-03-01T00:00:00Z"
    assert profile.member.last_timestamp_utc == "2022-03-01T08:00:00Z"


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        (b"not-a-zip", "valid ZIP"),
        (_archive("fundingTime,fundingRate\n", extra_member=True), "exactly one"),
        (_archive("fundingTime,fundingRate\n1646092800000,0.1\n", filename="../x.csv"), "Unsafe"),
        (_archive("value,fundingRate\n1,0.1\n"), "timestamp field"),
        (_archive("fundingTime,fundingRate\n,0.1\n"), "cannot be empty"),
    ],
)
def test_rejects_malformed_or_unsafe_archives(raw: bytes, message: str) -> None:
    with pytest.raises(OKXHistoricalExportError, match=message):
        inspect_funding_archive_bytes(raw)
