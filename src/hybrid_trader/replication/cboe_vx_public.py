"""Fail-closed parser for the public Cboe VX contract-history pilot."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

SOURCE_AUTHORITY = "Cboe Futures Exchange"
PILOT_VERSION = "CBOE_VX_PUBLIC_CONTRACT_LEVEL_PILOT_V1"
PILOT_START = date(2022, 9, 1)
PILOT_END = date(2022, 9, 30)
EXPECTED_HEADER = (
    "Trade Date",
    "Futures",
    "Open",
    "High",
    "Low",
    "Close",
    "Settle",
    "Change",
    "Total Volume",
    "EFP",
    "Open Interest",
)
SCHEMA_SHA256 = hashlib.sha256(",".join(EXPECTED_HEADER).encode()).hexdigest()
TERMS_URL = "https://www.cboe.com/terms"
USE_OF_CONTENT_URL = "https://www.cboe.com/en/use-of-content/"


@dataclass(frozen=True)
class ContractSpec:
    expiry: str
    expected_identity: str
    source_url: str
    expected_sha256: str
    expected_byte_count: int


CONTRACT_SPECS = (
    ContractSpec(
        expiry="2022-09-21",
        expected_identity="U (Sep 2022)",
        source_url=(
            "https://cdn.cboe.com/data/us/futures/market_statistics/"
            "historical_data/VX/VX_2022-09-21.csv"
        ),
        expected_sha256="a74598b17c5e92b068ee46ee38aefdfe8423d62153bee7d879ff4eddc2fbb626",
        expected_byte_count=15819,
    ),
    ContractSpec(
        expiry="2022-10-19",
        expected_identity="V (Oct 2022)",
        source_url=(
            "https://cdn.cboe.com/data/us/futures/market_statistics/"
            "historical_data/VX/VX_2022-10-19.csv"
        ),
        expected_sha256="270abe0333366e5395d88d6e56da51fa403962f03229d119a8208ece339c778d",
        expected_byte_count=15850,
    ),
)


@dataclass(frozen=True)
class ParsedContract:
    spec: ContractSpec
    raw_sha256: str
    raw_byte_count: int
    rows: tuple[dict[str, str], ...]
    first_trade_date: str
    last_trade_date: str
    settlement_close_difference_count: int


@dataclass(frozen=True)
class PilotProfile:
    pilot_version: str
    source_authority: str
    schema_sha256: str
    contract_count: int
    row_count: int
    first_trade_date: str
    last_trade_date: str
    settlement_close_difference_count: int
    continuous_series_used: bool
    back_adjustment_used: bool
    raw_redistribution_authorized: bool
    price_linkage_authorized: bool
    returns_authorized: bool


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _decimal(value: str, *, field: str, trade_date: str) -> Decimal:
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal {field} on {trade_date}: {value!r}") from exc


def _nonnegative_int(value: str, *, field: str, trade_date: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid integer {field} on {trade_date}: {value!r}") from exc
    if parsed < 0:
        raise ValueError(f"Negative {field} on {trade_date}: {parsed}")
    return parsed


def parse_contract_bytes(raw: bytes, spec: ContractSpec) -> ParsedContract:
    """Parse one exact Cboe contract file and reject silent provider changes."""

    if len(raw) != spec.expected_byte_count:
        raise ValueError(
            f"Cboe byte count changed for {spec.expiry}: {len(raw)} != {spec.expected_byte_count}"
        )
    digest = sha256_bytes(raw)
    if digest != spec.expected_sha256:
        raise ValueError(f"Cboe SHA-256 changed for {spec.expiry}: {digest}")
    if b"<html" in raw[:2000].lower() or b"<!doctype" in raw[:2000].lower():
        raise ValueError(f"Cboe returned HTML for {spec.expiry}")
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    header = tuple(reader.fieldnames or ())
    if header != EXPECTED_HEADER:
        raise ValueError(f"Unexpected Cboe schema for {spec.expiry}: {header}")
    rows = list(reader)
    if not rows:
        raise ValueError(f"Empty Cboe contract file for {spec.expiry}")

    parsed_dates: list[date] = []
    for row in rows:
        trade_date_text = row["Trade Date"].strip()
        try:
            trade_date = date.fromisoformat(trade_date_text)
        except ValueError as exc:
            raise ValueError(f"Invalid Cboe trade date: {trade_date_text!r}") from exc
        parsed_dates.append(trade_date)
        if row["Futures"].strip() != spec.expected_identity:
            raise ValueError(
                f"Unexpected Cboe futures identity on {trade_date_text}: {row['Futures']!r}"
            )

    if parsed_dates != sorted(parsed_dates):
        raise ValueError(f"Non-monotonic Cboe trade dates for {spec.expiry}")
    if len(parsed_dates) != len(set(parsed_dates)):
        raise ValueError(f"Duplicate Cboe trade dates for {spec.expiry}")
    if parsed_dates[-1].isoformat() != spec.expiry:
        raise ValueError(
            f"Last Cboe trade date {parsed_dates[-1]} does not match expiry {spec.expiry}"
        )

    previous_settle: Decimal | None = None
    settlement_close_differences = 0
    for row, trade_date in zip(rows, parsed_dates, strict=True):
        trade_date_text = trade_date.isoformat()
        settle = _decimal(row["Settle"].strip(), field="Settle", trade_date=trade_date_text)
        close = _decimal(row["Close"].strip(), field="Close", trade_date=trade_date_text)
        change = _decimal(row["Change"].strip(), field="Change", trade_date=trade_date_text)
        if settle <= 0:
            raise ValueError(f"Non-positive settlement on {trade_date_text}: {settle}")
        for field in ("Open", "High", "Low"):
            _decimal(row[field].strip(), field=field, trade_date=trade_date_text)
        for field in ("Total Volume", "EFP", "Open Interest"):
            _nonnegative_int(row[field].strip(), field=field, trade_date=trade_date_text)
        if previous_settle is not None and abs((settle - previous_settle) - change) > Decimal(
            "0.0001"
        ):
            raise ValueError(
                f"Settlement change mismatch on {trade_date_text}: "
                f"expected {settle - previous_settle}, found {change}"
            )
        previous_settle = settle
        if settle != close:
            settlement_close_differences += 1
    return ParsedContract(
        spec=spec,
        raw_sha256=digest,
        raw_byte_count=len(raw),
        rows=tuple(rows),
        first_trade_date=parsed_dates[0].isoformat(),
        last_trade_date=parsed_dates[-1].isoformat(),
        settlement_close_difference_count=settlement_close_differences,
    )


def load_contract_file(path: str | Path, spec: ContractSpec) -> ParsedContract:
    return parse_contract_bytes(Path(path).read_bytes(), spec)


def derive_pilot_rows(contracts: Sequence[ParsedContract]) -> list[dict[str, str]]:
    """Create a deterministic contract-level pilot without computing returns."""

    output: list[dict[str, str]] = []
    for contract in contracts:
        for row in contract.rows:
            trade_date = date.fromisoformat(row["Trade Date"])
            if not PILOT_START <= trade_date <= PILOT_END:
                continue
            output.append(
                {
                    "pilot_version": PILOT_VERSION,
                    "source_authority": SOURCE_AUTHORITY,
                    "source_url": contract.spec.source_url,
                    "raw_sha256": contract.raw_sha256,
                    "contract_expiry": contract.spec.expiry,
                    "contract_identity": contract.spec.expected_identity,
                    "trade_date": row["Trade Date"],
                    "open": row["Open"],
                    "high": row["High"],
                    "low": row["Low"],
                    "close": row["Close"],
                    "settle": row["Settle"],
                    "change": row["Change"],
                    "total_volume": row["Total Volume"],
                    "efp": row["EFP"],
                    "open_interest": row["Open Interest"],
                    "settlement_is_explicit_exchange_field": "true",
                    "continuous_series": "false",
                    "back_adjusted": "false",
                    "price_linkage_authorized": "false",
                    "returns_authorized": "false",
                }
            )
    output.sort(key=lambda item: (item["contract_expiry"], item["trade_date"]))
    if not output:
        raise ValueError("Cboe VX pilot contains no rows")
    keys = [(row["contract_expiry"], row["trade_date"]) for row in output]
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate contract/date key in Cboe VX pilot")
    return output


def render_pilot_csv(rows: Sequence[Mapping[str, str]]) -> bytes:
    if not rows:
        raise ValueError("Cannot render an empty Cboe VX pilot")
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode("utf-8")


def build_profile(contracts: Sequence[ParsedContract], rows: Sequence[Mapping[str, str]]) -> PilotProfile:
    dates = [row["trade_date"] for row in rows]
    return PilotProfile(
        pilot_version=PILOT_VERSION,
        source_authority=SOURCE_AUTHORITY,
        schema_sha256=SCHEMA_SHA256,
        contract_count=len(contracts),
        row_count=len(rows),
        first_trade_date=min(dates),
        last_trade_date=max(dates),
        settlement_close_difference_count=sum(
            contract.settlement_close_difference_count for contract in contracts
        ),
        continuous_series_used=False,
        back_adjustment_used=False,
        raw_redistribution_authorized=False,
        price_linkage_authorized=False,
        returns_authorized=False,
    )


def build_manifest(
    contracts: Sequence[ParsedContract], rows: Sequence[Mapping[str, str]], pilot_csv: bytes
) -> dict[str, Any]:
    profile = build_profile(contracts, rows)
    return {
        "schema_version": "1.0",
        "profile": asdict(profile),
        "pilot_csv": {"byte_count": len(pilot_csv), "sha256": sha256_bytes(pilot_csv)},
        "contracts": [
            {
                "expiry": contract.spec.expiry,
                "identity": contract.spec.expected_identity,
                "source_url": contract.spec.source_url,
                "raw_byte_count": contract.raw_byte_count,
                "raw_sha256": contract.raw_sha256,
                "first_trade_date": contract.first_trade_date,
                "last_trade_date": contract.last_trade_date,
                "row_count": len(contract.rows),
                "settlement_close_difference_count": (
                    contract.settlement_close_difference_count
                ),
            }
            for contract in contracts
        ],
        "license_state": {
            "website_terms_url": TERMS_URL,
            "use_of_content_url": USE_OF_CONTENT_URL,
            "raw_redistribution_authorized": False,
            "public_redisplay_authorized": False,
            "internal_research_status": "PENDING_FORMAL_LICENSE_INTERPRETATION",
        },
        "same_contract_return_formula_implemented_elsewhere": True,
        "returns_computed": False,
        "paper_replication_pass": False,
        "economic_edge_verdict": "INCONCLUSIVE",
    }


def write_pilot(
    output_dir: str | Path, september_path: str | Path, october_path: str | Path
) -> dict[str, Any]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    contracts = [
        load_contract_file(september_path, CONTRACT_SPECS[0]),
        load_contract_file(october_path, CONTRACT_SPECS[1]),
    ]
    rows = derive_pilot_rows(contracts)
    pilot_csv = render_pilot_csv(rows)
    manifest = build_manifest(contracts, rows, pilot_csv)
    (root / "cboe_vx_2022-09_public_contract_pilot.csv").write_bytes(pilot_csv)
    (root / "cboe_vx_public_contract_pilot_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--september", required=True)
    parser.add_argument("--october", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    manifest = write_pilot(args.output_dir, args.september, args.october)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0
