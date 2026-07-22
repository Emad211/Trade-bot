from __future__ import annotations

import hashlib
import io
import zipfile
from dataclasses import replace

import pytest

from hybrid_trader.replication.kenneth_french_daily import (
    DATA_STATE,
    RETURN_UNIT,
    SELECTED_FACTOR_SOURCE,
    SOURCE_CONTRACTS,
    build_selected_daily_panel,
    parse_daily_zip,
    trim_trailing_empty,
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
    row1 = "20000103," + ",".join(str(index + 1) for index in range(len(columns))) + suffix
    row2 = "20000104," + ",".join(str(index + 2) for index in range(len(columns))) + suffix
    return "preamble\n" + header + "\n" + row1 + "\n" + row2 + "\nfooter\n"


def synthetic_contract(key: str, *, trailing: bool = False):
    original = SOURCE_CONTRACTS[key]
    text = make_text(original.expected_columns, trailing=trailing)
    zip_bytes = make_zip(original.member_filename, text)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        crc32 = f"{archive.infolist()[0].CRC:08x}"
    return replace(
        original,
        zip_byte_count=len(zip_bytes),
        zip_sha256=hashlib.sha256(zip_bytes).hexdigest(),
        member_byte_count=len(text.encode()),
        member_sha256=hashlib.sha256(text.encode()).hexdigest(),
        member_crc32=crc32,
        expected_row_count=2,
        expected_first_date="2000-01-03",
        expected_last_date="2000-01-04",
        expected_header_index=1,
        expected_trailing_delimiter_rows=(2 if trailing else 0),
    ), zip_bytes


def test_trim_only_one_trailing_empty_cell() -> None:
    assert trim_trailing_empty(["", "Mom", ""]) == ["", "Mom"]
    assert trim_trailing_empty(["20000103", "", "1", ""]) == [
        "20000103",
        "",
        "1",
    ]


def test_valid_trailing_delimiter_is_normalized() -> None:
    contract, zip_bytes = synthetic_contract("mom", trailing=True)
    parsed = parse_daily_zip(zip_bytes, contract)
    assert len(parsed.frame) == 2
    assert parsed.trailing_delimiter_rows == 2
    assert parsed.frame.attrs["return_unit"] == RETURN_UNIT


def test_internal_blank_is_rejected() -> None:
    original = SOURCE_CONTRACTS["mom"]
    text = "preamble\n,Mom,\n20000103,,\nfooter\n"
    zip_bytes = make_zip(original.member_filename, text)
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        crc32 = f"{archive.infolist()[0].CRC:08x}"
    contract = replace(
        original,
        zip_byte_count=len(zip_bytes),
        zip_sha256=hashlib.sha256(zip_bytes).hexdigest(),
        member_byte_count=len(text.encode()),
        member_sha256=hashlib.sha256(text.encode()).hexdigest(),
        member_crc32=crc32,
        expected_row_count=1,
        expected_first_date="2000-01-03",
        expected_last_date="2000-01-03",
        expected_header_index=1,
        expected_trailing_delimiter_rows=1,
    )
    with pytest.raises(ValueError, match="Internal blank"):
        parse_daily_zip(zip_bytes, contract)


def test_zip_traversal_is_rejected() -> None:
    original = SOURCE_CONTRACTS["ff3"]
    zip_bytes = make_zip("../evil.csv", make_text(original.expected_columns))
    contract = replace(
        original,
        zip_byte_count=len(zip_bytes),
        zip_sha256=hashlib.sha256(zip_bytes).hexdigest(),
        member_filename="../evil.csv",
    )
    with pytest.raises(ValueError, match="Unsafe ZIP member path"):
        parse_daily_zip(zip_bytes, contract, require_exact_snapshot=False)


def test_multiple_members_are_rejected() -> None:
    original = SOURCE_CONTRACTS["ff3"]
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr(original.member_filename, make_text(original.expected_columns))
        archive.writestr("extra.csv", "x")
    with pytest.raises(ValueError, match="Expected one regular member"):
        parse_daily_zip(output.getvalue(), original, require_exact_snapshot=False)


def test_changed_exact_snapshot_is_rejected() -> None:
    contract, zip_bytes = synthetic_contract("ff3")
    with pytest.raises(ValueError, match=r"ZIP byte count changed|ZIP SHA-256 changed"):
        parse_daily_zip(zip_bytes + b"x", contract)


def test_header_mismatch_is_rejected() -> None:
    original = SOURCE_CONTRACTS["ff3"]
    text = make_text(("Mkt-RF", "SMB", "WRONG", "RF"))
    zip_bytes = make_zip(original.member_filename, text)
    with pytest.raises(ValueError, match="Expected header not found"):
        parse_daily_zip(zip_bytes, original, require_exact_snapshot=False)


def test_duplicate_dates_are_rejected() -> None:
    original = SOURCE_CONTRACTS["ff3"]
    header = "," + ",".join(original.expected_columns)
    values = ",".join("1" for _ in original.expected_columns)
    text = f"preamble\n{header}\n20000103,{values}\n20000103,{values}\n"
    zip_bytes = make_zip(original.member_filename, text)
    with pytest.raises(ValueError, match="Duplicate dates"):
        parse_daily_zip(zip_bytes, original, require_exact_snapshot=False)


def test_nonfinite_value_is_rejected() -> None:
    original = SOURCE_CONTRACTS["ff3"]
    header = "," + ",".join(original.expected_columns)
    text = f"preamble\n{header}\n20000103,nan,1,1,1\n"
    zip_bytes = make_zip(original.member_filename, text)
    with pytest.raises(ValueError, match="Non-finite"):
        parse_daily_zip(zip_bytes, original, require_exact_snapshot=False)


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


def test_predeclared_factor_source_mapping() -> None:
    assert SELECTED_FACTOR_SOURCE["SMB"] == ("ff3", "SMB")
    assert SELECTED_FACTOR_SOURCE["HML"] == ("ff3", "HML")
    assert SELECTED_FACTOR_SOURCE["RMW"] == ("ff5", "RMW")
    assert SELECTED_FACTOR_SOURCE["CMA"] == ("ff5", "CMA")


def test_selected_panel_refuses_incomplete_sources() -> None:
    contract, zip_bytes = synthetic_contract("ff3")
    parsed = parse_daily_zip(zip_bytes, contract)
    with pytest.raises(ValueError, match="Expected sources"):
        build_selected_daily_panel({"ff3": parsed})


def test_selected_panel_keeps_current_revision_label() -> None:
    parsed = {}
    for key in SOURCE_CONTRACTS:
        contract, zip_bytes = synthetic_contract(key, trailing=(key == "mom"))
        parsed[key] = parse_daily_zip(zip_bytes, contract)
    panel = build_selected_daily_panel(parsed)
    assert panel.attrs["data_state"] == DATA_STATE
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
