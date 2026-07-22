from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from hybrid_trader.replication.okx_fee_accounting import FeeRateQuery, InstrumentType
from hybrid_trader.replication.okx_no_trade_observation import (
    DELETE_CONFIRMATION_PHRASE,
    GATE_ID,
    SYNTHETIC_CONFIRMATION_PHRASE,
    CredentialPermissionAttestation,
    NoTradeDeletionConfig,
    NoTradeObservationConfig,
    ObservationMode,
    OKXPrivateCredentials,
    PrivateTimedHTTPResponse,
    build_fee_request_path,
    delete_no_trade_observation,
    execute_synthetic_no_trade_observation_for_validation,
    load_no_trade_health_policy,
    sign_private_get_request,
)
from hybrid_trader.replication.okx_owner_sampling_runner import OwnerRunnerAttestations
from hybrid_trader.replication.okx_price_linkage_probe import (
    SOURCE_CONTRACTS,
    HTTPResponse,
    TimedHTTPResponse,
    build_url,
)

NOW = datetime(2026, 7, 21, 20, 0, tzinfo=UTC)
SYNTHETIC_MARKET_SENTINEL = "987654.321987"
SYNTHETIC_FEE_SENTINELS = (
    "-0.00112233",
    "-0.00223344",
    "-0.00334455",
    "-0.00445566",
)
SYNTHETIC_CREDENTIAL_SENTINELS = (
    "synthetic-gate61-api-key",
    "synthetic-gate61-secret",
    "synthetic-gate61-passphrase",
)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _owner_attestations() -> OwnerRunnerAttestations:
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


def _credential_attestation() -> CredentialPermissionAttestation:
    return CredentialPermissionAttestation(
        read_permission_enabled=True,
        trade_permission_disabled=True,
        withdraw_permission_disabled=True,
        ip_allowlist_enabled=True,
        credentials_outside_repository=True,
        credentials_outside_ci=True,
        credentials_not_logged=True,
    )


def _public_row(source_id: str, timestamp_ms: int) -> dict[str, str]:
    ticker = {
        "last": SYNTHETIC_MARKET_SENTINEL,
        "lastSz": "1",
        "askPx": "987655.0",
        "askSz": "2",
        "bidPx": "987654.0",
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
            "markPx": SYNTHETIC_MARKET_SENTINEL,
            "ts": str(timestamp_ms),
        }
    if source_id == "OKX_BTC_USDT_INDEX_TICKER":
        return {
            "instId": "BTC-USDT",
            "idxPx": SYNTHETIC_MARKET_SENTINEL,
            "high24h": "990000",
            "open24h": "980000",
            "low24h": "970000",
            "sodUtc0": "981000",
            "sodUtc8": "982000",
            "ts": str(timestamp_ms),
        }
    raise ValueError(f"Unknown synthetic source: {source_id}")


def _public_fetcher(calls: list[str]) -> Callable[[str], TimedHTTPResponse]:
    contracts = {build_url(contract): contract for contract in SOURCE_CONTRACTS}

    def fetch(url: str) -> TimedHTTPResponse:
        contract = contracts[url]
        index = len(calls)
        calls.append(url)
        request_started_at = NOW + timedelta(milliseconds=index * 100)
        response_received_at = request_started_at + timedelta(milliseconds=10)
        provider_timestamp_ms = int(response_received_at.timestamp() * 1000) - 500 - index * 50
        body = json.dumps(
            {
                "code": "0",
                "msg": "",
                "data": [_public_row(contract.source_id, provider_timestamp_ms)],
            },
            sort_keys=True,
        ).encode("utf-8")
        return TimedHTTPResponse(
            response=HTTPResponse(body, 200, "application/json", url),
            request_started_at=request_started_at,
            response_received_at=response_received_at,
        )

    return fetch


def _fee_row(query: FeeRateQuery) -> dict[str, str]:
    common = {
        "instType": query.instrument_type.value,
        "level": "Lv1",
        "ruleType": "normal",
        "ts": str(int(NOW.timestamp() * 1000)),
        "makerUSDC": "",
        "takerUSDC": "",
    }
    if query.instrument_type is InstrumentType.SPOT:
        return {
            **common,
            "maker": SYNTHETIC_FEE_SENTINELS[0],
            "taker": SYNTHETIC_FEE_SENTINELS[1],
            "makerU": "",
            "takerU": "",
        }
    return {
        **common,
        "maker": "-0.0005",
        "taker": "-0.0007",
        "makerU": SYNTHETIC_FEE_SENTINELS[2],
        "takerU": SYNTHETIC_FEE_SENTINELS[3],
    }


def _private_fetcher(calls: list[str]) -> Callable[[FeeRateQuery], PrivateTimedHTTPResponse]:
    def fetch(query: FeeRateQuery) -> PrivateTimedHTTPResponse:
        path = build_fee_request_path(query)
        calls.append(path)
        body = json.dumps(
            {"code": "0", "msg": "", "data": [_fee_row(query)]},
            sort_keys=True,
        ).encode("utf-8")
        return PrivateTimedHTTPResponse(
            body=body,
            status_code=200,
            content_type="application/json",
            final_url=f"https://www.okx.com{path}",
            request_started_at=NOW,
            response_received_at=NOW + timedelta(milliseconds=10),
        )

    return fetch


def _scan_forbidden(payload: bytes) -> None:
    text = payload.decode("utf-8")
    forbidden = (
        SYNTHETIC_MARKET_SENTINEL,
        *SYNTHETIC_FEE_SENTINELS,
        *SYNTHETIC_CREDENTIAL_SENTINELS,
        "OK-ACCESS-SIGN",
        "OK-ACCESS-PASSPHRASE",
        '"maker":',
        '"taker":',
        '"makerU":',
        '"takerU":',
        '"price":',
        '"size":',
        '"balance":',
        '"pnl":',
        '"return":',
    )
    leaked = [token for token in forbidden if token in text]
    if leaked:
        raise RuntimeError(f"Safe Gate 61 evidence leaked forbidden tokens: {leaked}")


def validate_contract(*, output_dir: Path, policy_path: Path, code_head_sha: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = output_dir / "okx-no-trade-observation-contract-safe-evidence.json"
    if evidence_path.exists():
        raise RuntimeError("Safe evidence output already exists")

    policy = load_no_trade_health_policy(policy_path)
    credentials = OKXPrivateCredentials(
        api_key=SYNTHETIC_CREDENTIAL_SENTINELS[0],
        secret_key=SYNTHETIC_CREDENTIAL_SENTINELS[1],
        passphrase=SYNTHETIC_CREDENTIAL_SENTINELS[2],
    )
    headers = sign_private_get_request(
        credentials=credentials,
        timestamp=NOW,
        request_path=build_fee_request_path(
            FeeRateQuery(instrument_type=InstrumentType.SPOT, instrument_id="BTC-USDT")
        ),
    )
    signature_fingerprint = _sha256(headers["OK-ACCESS-SIGN"].encode("utf-8"))

    with tempfile.TemporaryDirectory(prefix="gate61-") as temporary_name:
        temporary = Path(temporary_name)
        repository_root = temporary / "repository"
        repository_root.mkdir()
        private_root = temporary / "private"
        safe_manifest = temporary / "safe-batch-manifest.json"
        safe_receipt = temporary / "safe-observation-receipt.json"
        deletion_receipt = temporary / "safe-deletion-receipt.json"
        private_fee = private_root / "fee-snapshot.json"
        public_calls: list[str] = []
        private_calls: list[str] = []

        config = NoTradeObservationConfig(
            mode=ObservationMode.SYNTHETIC_INJECTED,
            private_root=private_root,
            repository_root=repository_root,
            private_fee_snapshot_output=private_fee,
            safe_batch_manifest_output=safe_manifest,
            safe_observation_receipt_output=safe_receipt,
            requested_retention_days=2,
            confirmation_phrase=SYNTHETIC_CONFIRMATION_PHRASE,
            enable_public_network_fetch=False,
            enable_private_network_fetch=False,
            owner_attestations=_owner_attestations(),
            credential_attestation=_credential_attestation(),
            health_policy=policy,
            api_domain="www.okx.com",
            code_head_sha=code_head_sha,
        )
        result = execute_synthetic_no_trade_observation_for_validation(
            config,
            credentials=credentials,
            private_fetcher=_private_fetcher(private_calls),
            public_fetcher=_public_fetcher(public_calls),
            now_provider=lambda: NOW + timedelta(seconds=1),
        )
        safe_receipt_payload: dict[str, Any] = json.loads(safe_receipt.read_text(encoding="utf-8"))
        if safe_receipt_payload["batch_decision"] != "ADMIT_PRIVATE_BATCH":
            raise RuntimeError("Synthetic healthy batch was not admitted")
        if safe_receipt_payload["orders_sent"] is not False:
            raise RuntimeError("No-trade receipt claimed an order")
        if safe_receipt_payload["credentials_present_in_receipt"] is not False:
            raise RuntimeError("Safe receipt claimed credentials")
        if safe_receipt_payload["fee_values_present_in_receipt"] is not False:
            raise RuntimeError("Safe receipt claimed fee values")
        if safe_receipt_payload["market_values_present_in_receipt"] is not False:
            raise RuntimeError("Safe receipt claimed market values")
        _scan_forbidden(safe_receipt.read_bytes())
        _scan_forbidden(safe_manifest.read_bytes())

        deletion = delete_no_trade_observation(
            NoTradeDeletionConfig(
                private_root=private_root,
                repository_root=repository_root,
                private_fee_snapshot_path=private_fee,
                safe_batch_manifest_path=safe_manifest,
                safe_observation_receipt_path=safe_receipt,
                safe_deletion_receipt_output=deletion_receipt,
                confirmation_phrase=DELETE_CONFIRMATION_PHRASE,
                reason="SYNTHETIC_GATE_61_VALIDATION_COMPLETE",
                owner_attestations=_owner_attestations(),
            )
        )
        if deletion["all_public_raw_deleted"] is not True:
            raise RuntimeError("Synthetic public raw batch was not deleted")
        if deletion["private_fee_snapshot_exists_after_delete"] is not False:
            raise RuntimeError("Synthetic private fee snapshot was not deleted")
        _scan_forbidden(deletion_receipt.read_bytes())

        evidence = {
            "schema_version": "1.0",
            "gate_id": GATE_ID,
            "issue_number": 61,
            "validation_mode": "SYNTHETIC_INJECTED_RESPONSES_ONLY",
            "code_head_sha": code_head_sha,
            "policy_id": policy.policy_id,
            "policy_fingerprint_sha256": policy.policy_fingerprint_sha256,
            "required_public_sources": list(policy.required_source_ids),
            "public_source_count": len(public_calls),
            "private_fee_query_paths": private_calls,
            "private_fee_query_count": len(private_calls),
            "private_endpoint_allowlist": ["/api/v5/account/trade-fee"],
            "private_method_allowlist": ["GET"],
            "private_redirect_following_allowed": False,
            "synthetic_signature_fingerprint_sha256": signature_fingerprint,
            "safe_observation_receipt_sha256": result.safe_receipt_sha256,
            "safe_batch_manifest_sha256": _sha256(safe_manifest.read_bytes()),
            "safe_deletion_receipt_sha256": _sha256(deletion_receipt.read_bytes()),
            "batch_id": result.batch_id,
            "batch_admitted": True,
            "batch_deleted": True,
            "private_fee_snapshot_deleted": True,
            "real_public_request_performed": False,
            "real_private_fee_request_performed": False,
            "credentials_supplied_to_ci": False,
            "credentials_present_in_safe_evidence": False,
            "fee_values_present_in_safe_evidence": False,
            "market_values_present_in_safe_evidence": False,
            "orders_sent": False,
            "trade_permission_used": False,
            "withdraw_permission_used": False,
            "basis_computation_authorized": False,
            "funding_pnl_computation_authorized": False,
            "returns_computation_authorized": False,
            "transaction_cost_estimation_authorized": False,
            "strategy_testing_authorized": False,
            "paper_or_live_trading_authorized": False,
            "report_2_4_authorized": False,
            "economic_edge_verdict": "INCONCLUSIVE",
        }

    raw = (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _scan_forbidden(raw)
    evidence_path.write_bytes(raw)
    return evidence_path


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--code-head-sha", required=True)
    args = parser.parse_args(argv)
    evidence_path = validate_contract(
        output_dir=args.output_dir,
        policy_path=args.policy,
        code_head_sha=args.code_head_sha,
    )
    print(
        json.dumps(
            {
                "safe_evidence": str(evidence_path),
                "byte_count": evidence_path.stat().st_size,
                "sha256": _sha256(evidence_path.read_bytes()),
                "real_requests_performed": False,
                "orders_sent": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
