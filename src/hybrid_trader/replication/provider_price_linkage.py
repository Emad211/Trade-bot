"""Fail-closed provider-candidate planning for point-in-time futures prices."""

from __future__ import annotations

import argparse
import base64
import csv
import gzip
import hashlib
import io
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

REGISTRY_VERSION = "CFTC_TFF_2022_09_13_INSTRUMENT_REGISTRY_V1"
EXPECTED_REGISTRY_SHA256 = "70a8e89db716cfc8b1285f3b627188294abaae920c2b99b193f4501a7e525c74"
EXPECTED_REGISTRY_ROWS = 54
PROVIDER_PLAN_VERSION = "CFTC_TFF_2022_09_13_DATABENTO_CANDIDATE_PLAN_V1"
PRIMARY_PROVIDER_CANDIDATE = "DATABENTO"
ORDINARY_CLASS = "HISTORICAL_SCREEN_TRADABLE_ROOT_VERIFIED"
AGGREGATE_CLASS = "NON_TRADABLE_CONSOLIDATED_AGGREGATE"
DATASET_BY_EXCHANGE = {
    "CME": "GLBX.MDP3",
    "CBOT": "GLBX.MDP3",
    "ICE Futures U.S.": "IFUS.IMPACT",
    "CFE": "XCBF.PITCH",
}
PILOT_ROOTS = ("ZN", "ES", "NIY", "DX", "VX")
REQUIRED_SCHEMAS = ("definition", "statistics")


@dataclass(frozen=True)
class ProviderPlanProfile:
    plan_version: str
    registry_sha256: str
    row_count: int
    ordinary_candidate_rows: int
    glbx_candidate_rows: int
    ifus_candidate_rows: int
    xcbf_candidate_rows: int
    aggregate_rows: int
    later_delisted_rows: int
    nonstandard_rows: int
    technical_symbol_pending_rows: int
    price_linkage_authorized_rows: int
    provider_contract_id_rows: int
    purchase_authorized: bool
    authenticated_probe_executed: bool


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_verified_registry_b64(path: str | Path) -> list[dict[str, str]]:
    """Decode the committed canonical registry and verify its exact identity."""

    encoded = Path(path).read_text(encoding="ascii").strip()
    try:
        raw = gzip.decompress(base64.b64decode(encoded, validate=True))
    except (ValueError, OSError) as exc:
        raise ValueError("Instrument registry is not valid gzip-compressed Base64") from exc
    digest = _sha256(raw)
    if digest != EXPECTED_REGISTRY_SHA256:
        raise ValueError(f"Instrument-registry SHA-256 changed: {digest}")
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8"), newline="")))
    if len(rows) != EXPECTED_REGISTRY_ROWS:
        raise ValueError(f"Expected {EXPECTED_REGISTRY_ROWS} registry rows, found {len(rows)}")
    if {row["registry_version"] for row in rows} != {REGISTRY_VERSION}:
        raise ValueError("Unexpected instrument-registry version")
    codes = [row["cftc_contract_market_code"] for row in rows]
    if len(codes) != len(set(codes)):
        raise ValueError("Duplicate CFTC codes in instrument registry")
    if codes != sorted(codes):
        raise ValueError("Instrument registry is not deterministically sorted")
    return rows


def _candidate_state(row: Mapping[str, str]) -> tuple[str, str, str, str]:
    mapping_class = row["mapping_class"]
    exchange = row["exchange_name"]
    root = row["exchange_product_code"]
    if mapping_class == AGGREGATE_CLASS:
        return (
            "",
            "",
            "NOT_APPLICABLE_NON_TRADABLE_AGGREGATE",
            "A consolidated reporting row must never receive a direct price series.",
        )
    dataset = DATASET_BY_EXCHANGE.get(exchange, "")
    parent = f"{root}.FUT" if root else ""
    if mapping_class == ORDINARY_CLASS:
        if not dataset or not parent:
            raise ValueError(f"Ordinary row lacks provider candidate identity: {row}")
        return (
            dataset,
            parent,
            "PENDING_AUTHENTICATED_METADATA_DEFINITION_AND_STATISTICS_PROBE",
            "Root identity is only a candidate until authenticated point-in-time evidence passes.",
        )
    if mapping_class == "HISTORICAL_LATER_DELISTED_ROOT_VERIFIED":
        return (
            dataset,
            parent,
            "PENDING_AUTHENTICATED_EXPIRED_HISTORY_AND_2022_VINTAGE_PROBE",
            "Current metadata cannot substitute for the 2022 expired-contract chain.",
        )
    if mapping_class == "NON_STANDARD_EXECUTION_PRODUCT":
        return (
            dataset,
            parent,
            "BLOCKED_EXCHANGE_NATIVE_NONSTANDARD_EXECUTION_CONTRACT_REQUIRED",
            "ClearPort/EFRP/BTIC semantics must be specified before provider price use.",
        )
    if mapping_class == "PRODUCT_IDENTITY_VERIFIED_TECHNICAL_SYMBOL_PENDING":
        return (
            dataset,
            parent,
            "PENDING_AUTHENTICATED_PARENT_AND_TECHNICAL_SYMBOL_RESOLUTION",
            "The product identity exists, but the provider technical symbol is unverified.",
        )
    raise ValueError(f"Unsupported mapping class: {mapping_class}")


def build_provider_candidate_rows(
    registry_rows: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    """Build a provider-candidate plan without granting price or return authorization."""

    output: list[dict[str, str]] = []
    for row in registry_rows:
        dataset, parent, status, reason = _candidate_state(row)
        candidate = PRIMARY_PROVIDER_CANDIDATE if dataset else ""
        output.append(
            {
                "plan_version": PROVIDER_PLAN_VERSION,
                "as_of_date": row["as_of_date"],
                "cftc_contract_market_code": row["cftc_contract_market_code"],
                "market_and_exchange_name": row["market_and_exchange_name"],
                "exchange_name": row["exchange_name"],
                "mapping_class": row["mapping_class"],
                "exchange_product_code": row["exchange_product_code"],
                "provider_candidate": candidate,
                "dataset_id_candidate": dataset,
                "parent_symbol_candidate": parent,
                "required_schemas": ";".join(REQUIRED_SCHEMAS) if dataset else "",
                "required_settlement_stat_type": "3" if dataset else "",
                "dataset_range_status": "NOT_CHECKED_AUTHENTICATION_REQUIRED"
                if dataset
                else "NOT_APPLICABLE",
                "dataset_condition_status": "NOT_CHECKED_AUTHENTICATION_REQUIRED"
                if dataset
                else "NOT_APPLICABLE",
                "parent_resolution_status": "NOT_CHECKED_AUTHENTICATION_REQUIRED"
                if dataset
                else "NOT_APPLICABLE",
                "definition_evidence_status": "NOT_ACQUIRED" if dataset else "NOT_APPLICABLE",
                "settlement_statistics_status": "NOT_ACQUIRED"
                if dataset
                else "NOT_APPLICABLE",
                "cost_quote_status": "NOT_REQUESTED" if dataset else "NOT_APPLICABLE",
                "license_snapshot_status": "NOT_CAPTURED" if dataset else "NOT_APPLICABLE",
                "provider_contract_id": "",
                "price_linkage_authorized": "false",
                "returns_authorized": "false",
                "candidate_status": status,
                "reason": reason,
            }
        )
    output.sort(key=lambda row: row["cftc_contract_market_code"])
    return output


def provider_plan_profile(rows: Sequence[Mapping[str, str]]) -> ProviderPlanProfile:
    classes = Counter(row["mapping_class"] for row in rows)
    datasets = Counter(
        row["dataset_id_candidate"]
        for row in rows
        if row["mapping_class"] == ORDINARY_CLASS
    )
    return ProviderPlanProfile(
        plan_version=PROVIDER_PLAN_VERSION,
        registry_sha256=EXPECTED_REGISTRY_SHA256,
        row_count=len(rows),
        ordinary_candidate_rows=classes[ORDINARY_CLASS],
        glbx_candidate_rows=datasets["GLBX.MDP3"],
        ifus_candidate_rows=datasets["IFUS.IMPACT"],
        xcbf_candidate_rows=datasets["XCBF.PITCH"],
        aggregate_rows=classes[AGGREGATE_CLASS],
        later_delisted_rows=classes["HISTORICAL_LATER_DELISTED_ROOT_VERIFIED"],
        nonstandard_rows=classes["NON_STANDARD_EXECUTION_PRODUCT"],
        technical_symbol_pending_rows=classes[
            "PRODUCT_IDENTITY_VERIFIED_TECHNICAL_SYMBOL_PENDING"
        ],
        price_linkage_authorized_rows=sum(
            row["price_linkage_authorized"] == "true" for row in rows
        ),
        provider_contract_id_rows=sum(bool(row["provider_contract_id"]) for row in rows),
        purchase_authorized=False,
        authenticated_probe_executed=False,
    )


def render_candidate_csv(rows: Sequence[Mapping[str, str]]) -> bytes:
    if not rows:
        raise ValueError("Provider candidate plan is empty")
    output = io.StringIO(newline="")
    fieldnames = list(rows[0].keys())
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue().encode("utf-8")


def authenticated_probe_request(rows: Sequence[Mapping[str, str]]) -> dict[str, Any]:
    by_root = {row["exchange_product_code"]: row for row in rows}
    missing = [root for root in PILOT_ROOTS if root not in by_root]
    if missing:
        raise ValueError(f"Probe roots missing from provider plan: {missing}")
    probes = []
    for root in PILOT_ROOTS:
        row = by_root[root]
        probes.append(
            {
                "cftc_contract_market_code": row["cftc_contract_market_code"],
                "root": root,
                "dataset": row["dataset_id_candidate"],
                "parent_symbol": row["parent_symbol_candidate"],
                "as_of_date": "2022-09-13",
                "definition_window_start": "2022-09-01T00:00:00Z",
                "definition_window_end": "2022-10-01T00:00:00Z",
                "settlement_session_date": "2022-09-16",
            }
        )
    return {
        "schema_version": "1.0",
        "probe_id": "DATABENTO_CFTC_TFF_2022_09_13_PROVIDER_PROBE_V1",
        "provider": PRIMARY_PROVIDER_CANDIDATE,
        "authentication_secret_name": "DATABENTO_API_KEY",
        "purchase_authorized": False,
        "max_cost_usd": 0.0,
        "execution_status": "BLOCKED_MISSING_AUTHENTICATED_ACCOUNT_AND_EXPLICIT_COST_APPROVAL",
        "required_metadata_methods": [
            "list_datasets",
            "list_schemas",
            "get_dataset_range",
            "get_dataset_condition",
            "get_cost",
            "symbology.resolve",
        ],
        "required_time_series_schemas": list(REQUIRED_SCHEMAS),
        "settlement_contract": {
            "schema": "statistics",
            "stat_type": 3,
            "require_final_flag": True,
            "require_actual_flag": True,
            "allow_ohlcv_as_settlement_substitute": False,
        },
        "definition_contract": {
            "require_outright_future": True,
            "exclude_spreads": True,
            "require_raw_symbol": True,
            "require_instrument_id": True,
            "require_activation_or_listing_time": True,
            "require_expiration_or_last_trade_time": True,
            "require_min_price_increment": True,
            "require_multiplier_or_unit_quantity": True,
            "require_quote_currency": True,
        },
        "evidence_requirements": [
            "provider request hash",
            "provider response hash",
            "dataset range and condition for 2022 dates",
            "point-in-time parent-to-child resolution",
            "definition records for every accepted child contract",
            "final actual settlement statistics",
            "cost quote before download",
            "license and redistribution snapshot",
            "immutable storage identity before artifact audit pass",
        ],
        "probes": probes,
        "price_linkage_authorized": False,
        "returns_authorized": False,
        "economic_edge_verdict": "INCONCLUSIVE",
    }


def build_manifest(rows: Sequence[Mapping[str, str]], candidate_csv: bytes) -> dict[str, Any]:
    profile = provider_plan_profile(rows)
    probe = authenticated_probe_request(rows)
    return {
        "schema_version": "1.0",
        "plan_profile": asdict(profile),
        "candidate_csv_sha256": _sha256(candidate_csv),
        "candidate_csv_byte_count": len(candidate_csv),
        "provider_decision": {
            "primary_integration_candidate": PRIMARY_PROVIDER_CANDIDATE,
            "accepted_provider": None,
            "reason": (
                "Unified candidate coverage with point-in-time definitions and venue "
                "statistics; authenticated evidence remains mandatory."
            ),
        },
        "exchange_native_audit_sources": {
            "CME_CBOT": "CME DataMine and CME Reference Data",
            "CFE": "Cboe historical data and DataShop",
            "ICE_FUTURES_US": "ICE Report Center and ICE Data Services",
        },
        "authenticated_probe": probe,
        "global_price_linkage_authorized": False,
        "global_returns_authorized": False,
        "paper_replication_pass": False,
        "economic_edge_verdict": "INCONCLUSIVE",
    }


def write_plan(output_dir: str | Path, registry_b64_path: str | Path) -> dict[str, Any]:
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    registry = load_verified_registry_b64(registry_b64_path)
    rows = build_provider_candidate_rows(registry)
    candidate_csv = render_candidate_csv(rows)
    manifest = build_manifest(rows, candidate_csv)
    (root / "databento-provider-candidate-plan.csv").write_bytes(candidate_csv)
    (root / "authenticated-probe-request.json").write_text(
        json.dumps(manifest["authenticated_probe"], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (root / "provider-candidate-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry-b64", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    manifest = write_plan(args.output_dir, args.registry_b64)
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
