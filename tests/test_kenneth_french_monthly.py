from __future__ import annotations

import hashlib
import io
import zipfile
from dataclasses import replace

import pytest

from hybrid_trader.replication.kenneth_french_monthly import (
    DATA_STATE,
    RETURN_UNIT,
    SELECTED_FACTOR_SOURCE,
    SOURCE_CONTRACTS,
    build_selected_monthly_panel,
    parse_monthly_zip,
    trim_one_trailing_empty,
    validate_data_library_page,
)


def make_zip(member_name: str, text: str) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member_name, text)
    return output.getvalue()


def make_text(columns: tuple[str, ...], *, trailing: bool = False) -> str:
    suffix = "," if trailing else ""
    header = "," + ",".join(columns) + suffix
    monthly_1 = "200001," + ",".join(str(index + 1) for index in range(len(columns))) + suffix
    monthly_2 = "200002," + ",".join(str(index + 2) for index in range(len(columns))) + suffix
    annual = "2000," + ",".join(str(index + 3) for index in range(len(columns))) + suffix
    return (
        "preamble\n"
        + header
        + "\n"
        + monthly_1
        + "\n"
        + monthly_2
        + "\n\nAnnual Factors: January-December\n"
        + annual
        + "\nfooter\n"
    )


def synthetic_contract(key: str, *, trailing: bool = False):
    original = SOURCE_CONTRACTS[key]
    text = make_text(original.expected_columns, trailing=trailing)
    zip_bytes = make_zip(original.member_filename, text)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        crc32 = f"{archive.infolist()[0].CRC:08x}"
    preamble_sha = hashlib.sha256(b"preamble\n").hexdigest()
    non_data = "Annual Factors: January-December\nfooter\n"
    return replace(
        original,
        zip_byte_count=len(zip_bytes),
        zip_sha256=hashlib.sha256(zip_bytes).hexdigest(),
        member_byte_count=len(text.encode()),
        member_sha256=hashlib.sha256(text.encode()).hexdigest(),
        member_crc32=crc32,
        expected_monthly_row_count=2,
        expected_first_month="2000-01",
        expected_last_month="2000-02",
        expected_annual_row_count=1,
        expected_first_annual_year=2000,
        expected_last_annual_year=2000,
        expected_header_index=1,
        expected_trailing_delimiter_lines=(4 if trailing else 0),
        expected_preamble_sha256=preamble_sha,
        expected_non_data_line_count=2,
        expected_non_data_lines_sha256=hashlib.sha256(non_data.encode()).hexdigest(),
    ), zip_bytes


def test_trim_only_one_trailing_empty_cell() -> None:
    assert trim_one_trailing_empty(["", "Mom", ""]) == ["", "Mom"]
    assert trim_one_trailing_empty(["200001", "", "1", ""]) == [
        "200001",
        "",
        "1",
    ]


def test_valid_monthly_and_annual_blocks_are_separate() -> None:
    contract, zip_bytes = synthetic_contract("ff3_monthly")
    parsed = parse_monthly_zip(zip_bytes, contract)
    assert len(parsed.monthly_frame) == 2
    assert len(parsed.annual_frame) == 1
    assert parsed.monthly_frame.attrs["return_unit"] == RETURN_UNIT
    assert parsed.monthly_frame.attrs["daily_compounding_used_as_monthly_substitute"] is False


def test_monthly_row_after_annual_block_is_rejected() -> None:
    original = SOURCE_CONTRACTS["momentum_monthly"]
    text = "preamble\n,Mom\n200001,1\n2000,2\n200002,3\n"
    zip_bytes = make_zip(original.member_filename, text)
    with pytest.raises(ValueError, match="Monthly row after annual block"):
        parse_monthly_zip(zip_bytes, original, require_exact_snapshot=False)


def test_internal_blank_monthly_value_is_rejected() -> None:
    original = SOURCE_CONTRACTS["momentum_monthly"]
    text = "preamble\n,Mom,\n200001,,\n2000,1,\n"
    zip_bytes = make_zip(original.member_filename, text)
    with pytest.raises(ValueError, match="Internal blank monthly field"):
        parse_monthly_zip(zip_bytes, original, require_exact_snapshot=False)


def test_duplicate_month_is_rejected() -> None:
    original = SOURCE_CONTRACTS["momentum_monthly"]
    text = "preamble\n,Mom\n200001,1\n200001,2\n2000,3\n"
    zip_bytes = make_zip(original.member_filename, text)
    with pytest.raises(ValueError, match="Duplicate months"):
        parse_monthly_zip(zip_bytes, original, require_exact_snapshot=False)


def test_monthly_calendar_gap_is_rejected() -> None:
    original = SOURCE_CONTRACTS["momentum_monthly"]
    text = "preamble\n,Mom\n200001,1\n200003,2\n2000,3\n"
    zip_bytes = make_zip(original.member_filename, text)
    with pytest.raises(ValueError, match="Monthly calendar gap"):
        parse_monthly_zip(zip_bytes, original, require_exact_snapshot=False)


def test_duplicate_annual_year_is_rejected() -> None:
    original = SOURCE_CONTRACTS["momentum_monthly"]
    text = "preamble\n,Mom\n200001,1\n2000,2\n2000,3\n"
    zip_bytes = make_zip(original.member_filename, text)
    with pytest.raises(ValueError, match="Duplicate annual years"):
        parse_monthly_zip(zip_bytes, original, require_exact_snapshot=False)


def test_zip_traversal_is_rejected() -> None:
    original = SOURCE_CONTRACTS["ff3_monthly"]
    zip_bytes = make_zip("../evil.csv", make_text(original.expected_columns))
    contract = replace(original, member_filename="../evil.csv")
    with pytest.raises(ValueError, match="Unsafe ZIP member path"):
        parse_monthly_zip(zip_bytes, contract, require_exact_snapshot=False)


def test_multiple_members_are_rejected() -> None:
    original = SOURCE_CONTRACTS["ff3_monthly"]
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(original.member_filename, make_text(original.expected_columns))
        archive.writestr("extra.csv", "x")
    with pytest.raises(ValueError, match="Expected one regular member"):
        parse_monthly_zip(output.getvalue(), original, require_exact_snapshot=False)


def test_changed_exact_snapshot_is_rejected() -> None:
    contract, zip_bytes = synthetic_contract("ff3_monthly")
    with pytest.raises(ValueError, match=r"ZIP byte count changed|ZIP SHA-256 changed"):
        parse_monthly_zip(zip_bytes + b"x", contract)


def test_nonfinite_value_is_rejected() -> None:
    original = SOURCE_CONTRACTS["momentum_monthly"]
    text = "preamble\n,Mom\n200001,nan\n2000,1\n"
    zip_bytes = make_zip(original.member_filename, text)
    with pytest.raises(ValueError, match="Non-finite"):
        parse_monthly_zip(zip_bytes, original, require_exact_snapshot=False)


def test_data_library_warning_contract() -> None:
    page = " ".join(
        (
            "Legacy Format (FIZ)",
            "Flat File Format 2.0 (CIZ)",
            "reconstruct the full history of returns each month",
            "Historical returns can change",
        )
    ).encode()
    identity = validate_data_library_page(page, require_exact_snapshot=False)
    assert identity["byte_count"] == len(page)
    with pytest.raises(ValueError, match="revision warning changed"):
        validate_data_library_page(b"Legacy Format (FIZ)", require_exact_snapshot=False)


def test_predeclared_monthly_factor_source_mapping() -> None:
    assert SELECTED_FACTOR_SOURCE["SMB"] == ("ff3_monthly", "SMB")
    assert SELECTED_FACTOR_SOURCE["HML"] == ("ff3_monthly", "HML")
    assert SELECTED_FACTOR_SOURCE["RMW"] == ("ff5_monthly", "RMW")
    assert SELECTED_FACTOR_SOURCE["CMA"] == ("ff5_monthly", "CMA")
    assert SELECTED_FACTOR_SOURCE["Mom"] == ("momentum_monthly", "Mom")


def test_selected_panel_refuses_incomplete_sources() -> None:
    contract, zip_bytes = synthetic_contract("ff3_monthly")
    parsed = parse_monthly_zip(zip_bytes, contract)
    with pytest.raises(ValueError, match="Expected sources"):
        build_selected_monthly_panel({"ff3_monthly": parsed})


def test_selected_panel_keeps_revision_and_no_compounding_labels() -> None:
    parsed = {}
    for key in SOURCE_CONTRACTS:
        contract, zip_bytes = synthetic_contract(key)
        parsed[key] = parse_monthly_zip(zip_bytes, contract)
    panel = build_selected_monthly_panel(parsed)
    assert panel.attrs["data_state"] == DATA_STATE
    assert panel.attrs["daily_compounding_used_as_monthly_substitute"] is False
    assert panel.attrs["performance_calculation_authorized"] is False
    assert list(panel.columns) == [
        "Mkt-RF",
        "SMB",
        "HML",
        "RMW",
        "CMA",
        "Mom",
        "RF",
    ]
