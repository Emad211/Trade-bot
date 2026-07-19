"""Build a fail-closed point-in-time CFTC-to-exchange product registry."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

REGISTRY_VERSION = "CFTC_TFF_2022_09_13_INSTRUMENT_REGISTRY_V1"
AS_OF_DATE = "2022-09-13"
EXPECTED_PILOT_SHA256 = "1be0028ba872ed56c970f6cd67b76c480b3653b170762c6e55f39dc10c3d268b"
EXPECTED_MAP_CONTRACT_SHA256 = "4dd92e493f9752371cdfaef5f6bc90edf72b235cd0f4d444aa96aa9e628251c2"
EXPECTED_SOURCE_REGISTRY_SHA256 = "bc861dbe5a7da1f27060d87cb588a51acdd6466dbb27c889cafc5c3680cd6fff"
EXPECTED_ROWS = 54

MAP_CONTRACT_COLUMNS = (
    "cftc_contract_market_code",
    "expected_name_contains",
    "exchange_name",
    "mapping_class",
    "tradability",
    "aggregate_components",
    "cftc_reporting_commodity_code",
    "exchange_product_code",
    "exchange_order_entry_symbol",
    "exchange_security_group",
    "price_quote_currency",
    "historical_status",
    "mapping_evidence_status",
    "price_linkage_status",
    "source_ids",
    "notes",
)

REGISTRY_COLUMNS = (
    "registry_version",
    "as_of_date",
    "source_pilot_sha256",
    "map_contract_sha256",
    "source_registry_sha256",
    "cftc_contract_market_code",
    "market_and_exchange_name",
    "cftc_dcm_code",
    "cftc_region_code",
    "cftc_commodity_group_code",
    "exchange_name",
    "contract_units_raw",
    "mapping_class",
    "tradability",
    "aggregate_components",
    "cftc_reporting_commodity_code",
    "exchange_product_code",
    "exchange_order_entry_symbol",
    "exchange_security_group",
    "price_quote_currency",
    "valid_on_as_of_date",
    "effective_from",
    "effective_to",
    "historical_status",
    "mapping_evidence_status",
    "price_linkage_status",
    "price_linkage_authorized",
    "provider_contract_id",
    "source_ids",
    "notes",
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _read_csv_with_hash(path: str | Path, *, expected_hash: str) -> list[dict[str, str]]:
    raw = Path(path).read_bytes()
    digest = _sha256(raw)
    if digest != expected_hash:
        raise ValueError(f"Artifact SHA-256 changed: {digest}")
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")))


def load_verified_pilot(path: str | Path) -> list[dict[str, str]]:
    rows = _read_csv_with_hash(path, expected_hash=EXPECTED_PILOT_SHA256)
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} pilot rows, found {len(rows)}")
    codes = [row["CFTC_Contract_Market_Code"].strip() for row in rows]
    if len(codes) != len(set(codes)):
        raise ValueError("Pilot contains duplicate CFTC contract-market codes")
    return rows


def load_mapping_contract(path: str | Path) -> dict[str, dict[str, str]]:
    rows = _read_csv_with_hash(path, expected_hash=EXPECTED_MAP_CONTRACT_SHA256)
    if len(rows) != EXPECTED_ROWS:
        raise ValueError(f"Expected {EXPECTED_ROWS} mapping rows, found {len(rows)}")
    if tuple(rows[0]) != MAP_CONTRACT_COLUMNS:
        raise ValueError(f"Mapping-contract columns changed: {tuple(rows[0])}")
    by_code: dict[str, dict[str, str]] = {}
    for row in rows:
        code = row["cftc_contract_market_code"].strip()
        if not code or code in by_code:
            raise ValueError(f"Missing or duplicate mapping code: {code!r}")
        by_code[code] = row
    return by_code


def load_source_registry(path: str | Path) -> dict[str, dict[str, str]]:
    raw = Path(path).read_bytes()
    digest = _sha256(raw)
    if digest != EXPECTED_SOURCE_REGISTRY_SHA256:
        raise ValueError(f"Source-registry SHA-256 changed: {digest}")
    decoded = json.loads(raw)
    if not isinstance(decoded, dict) or not decoded:
        raise ValueError("Source registry must be a non-empty JSON object")
    output: dict[str, dict[str, str]] = {}
    for source_id, value in decoded.items():
        if not isinstance(source_id, str) or not isinstance(value, dict):
            raise ValueError("Invalid source-registry entry")
        required = {"authority", "url", "role"}
        if required - set(value):
            raise ValueError(f"Source {source_id} lacks required fields")
        output[source_id] = {key: str(item) for key, item in value.items()}
    return output


def build_registry_rows(
    pilot_rows: Sequence[Mapping[str, str]],
    mapping_by_code: Mapping[str, Mapping[str, str]],
    source_registry: Mapping[str, Mapping[str, str]],
) -> list[dict[str, str]]:
    pilot_codes = {row["CFTC_Contract_Market_Code"].strip() for row in pilot_rows}
    mapping_codes = set(mapping_by_code)
    if pilot_codes != mapping_codes:
        raise ValueError(
            f"Mapping coverage mismatch: missing={sorted(pilot_codes - mapping_codes)}, "
            f"extra={sorted(mapping_codes - pilot_codes)}"
        )

    output: list[dict[str, str]] = []
    for pilot in sorted(pilot_rows, key=lambda row: row["CFTC_Contract_Market_Code"].strip()):
        code = pilot["CFTC_Contract_Market_Code"].strip()
        mapping = mapping_by_code[code]
        name = pilot["Market_and_Exchange_Names"].strip()
        expected_fragment = mapping["expected_name_contains"].strip()
        if expected_fragment.upper() not in name.upper():
            raise ValueError(
                f"Market name mismatch for {code}: expected {expected_fragment!r}, found {name!r}"
            )
        source_ids = [item for item in mapping["source_ids"].split("|") if item]
        missing_sources = sorted(set(source_ids) - set(source_registry))
        if missing_sources:
            raise ValueError(f"Mapping {code} references unknown sources: {missing_sources}")
        row = {
            "registry_version": REGISTRY_VERSION,
            "as_of_date": AS_OF_DATE,
            "source_pilot_sha256": EXPECTED_PILOT_SHA256,
            "map_contract_sha256": EXPECTED_MAP_CONTRACT_SHA256,
            "source_registry_sha256": EXPECTED_SOURCE_REGISTRY_SHA256,
            "cftc_contract_market_code": code,
            "market_and_exchange_name": name,
            "cftc_dcm_code": pilot["CFTC_Market_Code"].strip(),
            "cftc_region_code": pilot["CFTC_Region_Code"].strip(),
            "cftc_commodity_group_code": pilot["CFTC_Commodity_Code"].strip(),
            "exchange_name": mapping["exchange_name"].strip(),
            "contract_units_raw": pilot["Contract_Units"].strip(),
            "mapping_class": mapping["mapping_class"].strip(),
            "tradability": mapping["tradability"].strip(),
            "aggregate_components": mapping["aggregate_components"].strip(),
            "cftc_reporting_commodity_code": mapping[
                "cftc_reporting_commodity_code"
            ].strip(),
            "exchange_product_code": mapping["exchange_product_code"].strip(),
            "exchange_order_entry_symbol": mapping[
                "exchange_order_entry_symbol"
            ].strip(),
            "exchange_security_group": mapping["exchange_security_group"].strip(),
            "price_quote_currency": mapping["price_quote_currency"].strip(),
            "valid_on_as_of_date": "true",
            "effective_from": "",
            "effective_to": "",
            "historical_status": mapping["historical_status"].strip(),
            "mapping_evidence_status": mapping["mapping_evidence_status"].strip(),
            "price_linkage_status": mapping["price_linkage_status"].strip(),
            "price_linkage_authorized": "false",
            "provider_contract_id": "",
            "source_ids": "|".join(source_ids),
            "notes": mapping["notes"].strip(),
        }
        output.append(row)

    for row in output:
        aggregate = row["mapping_class"] == "NON_TRADABLE_CONSOLIDATED_AGGREGATE"
        if aggregate:
            if row["exchange_product_code"]:
                raise ValueError(f"Aggregate {row['cftc_contract_market_code']} received a root")
        elif not row["exchange_product_code"]:
            raise ValueError(f"Product {row['cftc_contract_market_code']} lacks a product code")
        if row["price_linkage_authorized"] != "false" or row["provider_contract_id"]:
            raise ValueError("Registry must not authorize provider price linkage")
    return output


def render_registry_csv(rows: Sequence[Mapping[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(REGISTRY_COLUMNS), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def write_registry_bundle(
    output_dir: str | Path,
    *,
    pilot_path: str | Path,
    mapping_contract_path: str | Path,
    source_registry_path: str | Path,
) -> dict[str, Any]:
    source_registry = load_source_registry(source_registry_path)
    rows = build_registry_rows(
        load_verified_pilot(pilot_path),
        load_mapping_contract(mapping_contract_path),
        source_registry,
    )
    registry_bytes = render_registry_csv(rows)
    output = Path(output_dir)
    csv_name = "cftc_tff_2022-09-13_instrument_registry.csv"
    _atomic_write(output / csv_name, registry_bytes)

    class_counts: dict[str, int] = {}
    linkage_counts: dict[str, int] = {}
    for row in rows:
        class_counts[row["mapping_class"]] = class_counts.get(row["mapping_class"], 0) + 1
        linkage_counts[row["price_linkage_status"]] = linkage_counts.get(
            row["price_linkage_status"], 0
        ) + 1
    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "registry_version": REGISTRY_VERSION,
        "as_of_date": AS_OF_DATE,
        "source_pilot_sha256": EXPECTED_PILOT_SHA256,
        "map_contract_sha256": EXPECTED_MAP_CONTRACT_SHA256,
        "source_registry_sha256": EXPECTED_SOURCE_REGISTRY_SHA256,
        "registry_filename": csv_name,
        "registry_byte_count": len(registry_bytes),
        "registry_sha256": _sha256(registry_bytes),
        "row_count": len(rows),
        "unique_contract_market_codes": len(
            {row["cftc_contract_market_code"] for row in rows}
        ),
        "mapping_class_counts": dict(sorted(class_counts.items())),
        "price_linkage_status_counts": dict(sorted(linkage_counts.items())),
        "source_registry": source_registry,
        "global_price_linkage_authorized": False,
        "returns_authorized": False,
        "empirical_fitting_authorized": False,
        "paper_replication_pass": False,
        "economic_edge_verdict": "INCONCLUSIVE",
        "next_gate": "PROVIDER_VINTAGE_CONTRACT_CHAIN_AND_POINT_IN_TIME_PRICE_SOURCE",
    }
    _atomic_write(
        output / "instrument-registry-manifest.json",
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", type=Path, required=True)
    parser.add_argument("--mapping-contract", type=Path, required=True)
    parser.add_argument("--source-registry", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    manifest = write_registry_bundle(
        args.output_dir,
        pilot_path=args.pilot,
        mapping_contract_path=args.mapping_contract,
        source_registry_path=args.source_registry,
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
