from __future__ import annotations

import json
import tempfile
from collections.abc import Sequence
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from hybrid_trader.replication.okx_owner_sampling_runner import (
    DELETE_CONFIRMATION_PHRASE,
    SYNTHETIC_CONFIRMATION_PHRASE,
    OwnerRunnerAttestations,
    OwnerRunnerMode,
    OwnerSamplingDeletionConfig,
    OwnerSamplingRunnerConfig,
    delete_owner_sampling_batch,
    execute_synthetic_owner_sampling_for_validation,
    load_safe_sampling_manifest,
)
from hybrid_trader.replication.okx_price_linkage_probe import (
    HTTPResponse,
    SOURCE_CONTRACTS,
    TimedHTTPResponse,
    build_url,
)

FAKE_VALUE = "987654.321987"


def _attestations() -> OwnerRunnerAttestations:
    return OwnerRunnerAttestations(
        terms_reviewed=True,
        personal_noncommercial_use=True,
        reasonable_rate_and_scale=True,
        redistribution_disabled=True,
        encryption_at_rest=True,
        owner_only_access=True,
        backup_and_sync_excluded=True,
        public_artifact_upload_disabled=True,
        owner_controlled_private_storage=False,
        owner_controlled_encryption_keys=False,
        real_execution_owner_confirmed=False,
    )


def _row(source_id: str, timestamp_ms: int) -> dict[str, str]:
    ticker = {
        "last": FAKE_VALUE,
        "lastSz": "1",
        "askPx": "987655",
        "askSz": "2",
        "bidPx": "987653",
        "bidSz": "3",
        "open24h": "980000",
        "high24h": "990000",
        "low24h": "970000",
        "volCcy24h": "1000000",
        "vol24h": "10",
        "sodUtc0": "981000",
        "sodUtc8": "982000",
        "ts": str(timestamp_ms),
    }
    if source_id == "OKX_SPOT_BTC_USDT_TICKER":
        return {"instType": "SPOT", "instId": "BTC-USDT", **ticker}
    if source_id == "OKX_SWAP_BTC_USDT_SWAP_TICKER":
        return {"instType": "SWAP", "instId": "BTC-USDT-SWAP", **ticker}
    if source_id == "OKX_SWAP_BTC_USDT_SWAP_MARK_PRICE":
        return {
            "instType": "SWAP",
            "instId": "BTC-USDT-SWAP",
            "markPx": FAKE_VALUE,
            "ts": str(timestamp_ms),
        }
    if source_id == "OKX_BTC_USDT_INDEX_TICKER":
        return {
            "instId": "BTC-USDT",
            "idxPx": FAKE_VALUE,
            "high24h": "990000",
            "open24h": "980000",
            "low24h": "970000",
            "sodUtc0": "981000",
            "sodUtc8": "982000",
            "ts": str(timestamp_ms),
        }
    raise AssertionError(source_id)


def main(argv: Sequence[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)

    base = datetime.now(UTC)
    urls = [build_url(contract) for contract in SOURCE_CONTRACTS]
    contracts_by_url = {build_url(contract): contract for contract in SOURCE_CONTRACTS}
    requested: list[str] = []

    def fake_fetcher(url: str) -> TimedHTTPResponse:
        requested.append(url)
        index = len(requested) - 1
        contract = contracts_by_url[url]
        request = base + timedelta(milliseconds=index * 100)
        response = request + timedelta(milliseconds=15)
        provider_timestamp_ms = int(response.timestamp() * 1000) - (400 + index * 100)
        body = json.dumps(
            {
                "code": "0",
                "msg": "",
                "data": [_row(contract.source_id, provider_timestamp_ms)],
            },
            sort_keys=True,
        ).encode()
        return TimedHTTPResponse(
            response=HTTPResponse(body, 200, "application/json", url),
            request_started_at=request,
            response_received_at=response,
        )

    with tempfile.TemporaryDirectory(prefix="okx-owner-runner-") as temporary:
        root = Path(temporary)
        repository = root / "repo"
        repository.mkdir()
        private_root = root / "owner-private"
        safe_manifest_path = root / "safe-manifest.json"
        safe_deletion_path = root / "safe-deletion.json"
        config = OwnerSamplingRunnerConfig(
            mode=OwnerRunnerMode.SYNTHETIC_INJECTED,
            private_root=private_root,
            repository_root=repository,
            safe_manifest_output=safe_manifest_path,
            requested_retention_days=2,
            confirmation_phrase=SYNTHETIC_CONFIRMATION_PHRASE,
            enable_real_network_fetch=False,
            attestations=_attestations(),
        )
        result = execute_synthetic_owner_sampling_for_validation(
            config, fetcher=fake_fetcher
        )
        manifest = load_safe_sampling_manifest(safe_manifest_path)
        raw_count_before_delete = len(list((private_root / "raw").glob("*.bin")))
        lease_count_before_delete = len(list((private_root / "leases").glob("*.json")))
        deletion = delete_owner_sampling_batch(
            OwnerSamplingDeletionConfig(
                private_root=private_root,
                repository_root=repository,
                safe_manifest_path=safe_manifest_path,
                safe_deletion_receipt_output=safe_deletion_path,
                confirmation_phrase=DELETE_CONFIRMATION_PHRASE,
                reason="SYNTHETIC_OWNER_RUNNER_VALIDATION_COMPLETE",
                attestations=_attestations(),
            )
        )
        raw_count_after_delete = len(list((private_root / "raw").glob("*.bin")))
        lease_count_after_delete = len(list((private_root / "leases").glob("*.json")))
        safe_manifest_text = safe_manifest_path.read_text(encoding="utf-8")
        safe_deletion_text = safe_deletion_path.read_text(encoding="utf-8")

        evidence = {
            "schema_version": "1.0",
            "validation_id": "OKX_OWNER_SIDE_ONE_BATCH_RUNNER_V1",
            "runner_outcome": "GO_OWNER_SIDE_OKX_ONE_BATCH_RUNNER_READY",
            "execution_mode": "SYNTHETIC_INJECTED",
            "official_network_fetcher_used": False,
            "real_okx_request_performed": False,
            "real_raw_sampling_executed": False,
            "real_execution_status": "NOT_EXECUTED_REQUIRES_OWNER_PRIVATE_STORAGE_AND_KEYS",
            "requested_urls": requested,
            "requested_urls_match_frozen_contract": requested == urls,
            "run_result": asdict(result),
            "safe_manifest": asdict(manifest),
            "raw_artifact_count_before_delete": raw_count_before_delete,
            "lease_count_before_delete": lease_count_before_delete,
            "deletion": asdict(deletion),
            "raw_artifact_count_after_delete": raw_count_after_delete,
            "lease_count_after_delete": lease_count_after_delete,
            "safe_manifest_contains_fake_market_value": FAKE_VALUE in safe_manifest_text,
            "safe_deletion_contains_fake_market_value": FAKE_VALUE in safe_deletion_text,
            "authorization": {
                "historical_backfill": False,
                "basis_computation": False,
                "funding_pnl_computation": False,
                "returns_computation": False,
                "transaction_cost_estimation": False,
                "empirical_fitting": False,
                "strategy_testing": False,
                "paper_or_live_trading": False,
                "capital_deployment": False,
                "report_2_4": False,
            },
        }

    serialized = json.dumps(evidence, indent=2, sort_keys=True) + "\n"
    forbidden = (FAKE_VALUE, "987655", "987653")
    if any(value in serialized for value in forbidden):
        raise SystemExit("Synthetic market values leaked into public evidence")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "okx-owner-sampling-runner-evidence.json"
    output.write_text(serialized, encoding="utf-8")
    print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
