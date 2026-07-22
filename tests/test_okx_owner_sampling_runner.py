from __future__ import annotations

import json
import stat
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from hybrid_trader.replication.okx_owner_sampling_runner import (
    DELETE_CONFIRMATION_PHRASE,
    REAL_CONFIRMATION_PHRASE,
    SYNTHETIC_CONFIRMATION_PHRASE,
    OKXOwnerSamplingRunnerError,
    OwnerRunnerAttestations,
    OwnerRunnerMode,
    OwnerSamplingDeletionConfig,
    OwnerSamplingRunnerConfig,
    delete_owner_sampling_batch,
    execute_real_owner_sampling,
    execute_synthetic_owner_sampling_for_validation,
    load_safe_sampling_manifest,
)
from hybrid_trader.replication.okx_price_linkage_probe import (
    SOURCE_CONTRACTS,
    HTTPResponse,
    TimedHTTPResponse,
    build_url,
    fetch_public_response,
)

NOW = datetime(2026, 7, 21, 14, 0, tzinfo=UTC)
FAKE_MARKET_VALUE = "123456.789123"


def _attestations(*, real: bool = False) -> OwnerRunnerAttestations:
    return OwnerRunnerAttestations(
        terms_reviewed=True,
        personal_noncommercial_use=True,
        reasonable_rate_and_scale=True,
        redistribution_disabled=True,
        encryption_at_rest=True,
        owner_only_access=True,
        backup_and_sync_excluded=True,
        public_artifact_upload_disabled=True,
        owner_controlled_private_storage=real,
        owner_controlled_encryption_keys=real,
        real_execution_owner_confirmed=real,
    )


def _config(
    tmp_path: Path,
    *,
    safe_output: Path | None = None,
    mode: OwnerRunnerMode = OwnerRunnerMode.SYNTHETIC_INJECTED,
    confirmation: str = SYNTHETIC_CONFIRMATION_PHRASE,
    enable_real_network_fetch: bool = False,
    attestations: OwnerRunnerAttestations | None = None,
) -> OwnerSamplingRunnerConfig:
    repository = tmp_path / "repo"
    repository.mkdir(parents=True, exist_ok=True)
    return OwnerSamplingRunnerConfig(
        mode=mode,
        private_root=tmp_path / "private",
        repository_root=repository,
        safe_manifest_output=safe_output or (tmp_path / "safe-manifest.json"),
        requested_retention_days=2,
        confirmation_phrase=confirmation,
        enable_real_network_fetch=enable_real_network_fetch,
        attestations=attestations or _attestations(),
    )


def _row(source_id: str, provider_timestamp_ms: int) -> dict[str, str]:
    ticker_values = {
        "last": FAKE_MARKET_VALUE,
        "lastSz": "1",
        "askPx": "123457.1",
        "askSz": "2",
        "bidPx": "123456.1",
        "bidSz": "3",
        "open24h": "120000",
        "high24h": "124000",
        "low24h": "119000",
        "volCcy24h": "1000000",
        "vol24h": "10",
        "sodUtc0": "121000",
        "sodUtc8": "122000",
        "ts": str(provider_timestamp_ms),
    }
    if source_id == "OKX_SPOT_BTC_USDT_TICKER":
        return {"instType": "SPOT", "instId": "BTC-USDT", **ticker_values}
    if source_id == "OKX_SWAP_BTC_USDT_SWAP_TICKER":
        return {"instType": "SWAP", "instId": "BTC-USDT-SWAP", **ticker_values}
    if source_id == "OKX_SWAP_BTC_USDT_SWAP_MARK_PRICE":
        return {
            "instType": "SWAP",
            "instId": "BTC-USDT-SWAP",
            "markPx": FAKE_MARKET_VALUE,
            "ts": str(provider_timestamp_ms),
        }
    if source_id == "OKX_BTC_USDT_INDEX_TICKER":
        return {
            "instId": "BTC-USDT",
            "idxPx": FAKE_MARKET_VALUE,
            "high24h": "124000",
            "open24h": "120000",
            "low24h": "119000",
            "sodUtc0": "121000",
            "sodUtc8": "122000",
            "ts": str(provider_timestamp_ms),
        }
    raise AssertionError(source_id)


def _fake_fetcher(
    calls: list[str], *, fail_on_index: int | None = None
) -> Callable[[str], TimedHTTPResponse]:
    by_url = {build_url(contract): contract for contract in SOURCE_CONTRACTS}

    def fetch(url: str) -> TimedHTTPResponse:
        calls.append(url)
        index = len(calls) - 1
        if fail_on_index is not None and index == fail_on_index:
            raise RuntimeError("synthetic fetch failure")
        contract = by_url[url]
        request = NOW + timedelta(milliseconds=index * 100)
        response = request + timedelta(milliseconds=10)
        provider_timestamp_ms = int(response.timestamp() * 1000) - (500 + index * 100)
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

    return fetch


def test_runner_is_disabled_without_exact_confirmation(tmp_path: Path) -> None:
    config = _config(tmp_path, confirmation="wrong")
    with pytest.raises(OKXOwnerSamplingRunnerError, match="Exact synthetic"):
        config.validate()


def test_real_mode_requires_network_and_owner_controlled_attestations(
    tmp_path: Path,
) -> None:
    config = _config(
        tmp_path,
        mode=OwnerRunnerMode.OWNER_REAL_NETWORK,
        confirmation=REAL_CONFIRMATION_PHRASE,
        enable_real_network_fetch=False,
        attestations=_attestations(),
    )
    with pytest.raises(OKXOwnerSamplingRunnerError, match="network fetch is disabled"):
        config.validate()

    config = _config(
        tmp_path,
        mode=OwnerRunnerMode.OWNER_REAL_NETWORK,
        confirmation=REAL_CONFIRMATION_PHRASE,
        enable_real_network_fetch=True,
        attestations=_attestations(),
    )
    with pytest.raises(OKXOwnerSamplingRunnerError, match="owner-side execution"):
        config.validate()


def test_synthetic_mode_refuses_official_network_fetcher(tmp_path: Path) -> None:
    with pytest.raises(OKXOwnerSamplingRunnerError, match="official network fetcher"):
        execute_synthetic_owner_sampling_for_validation(
            _config(tmp_path), fetcher=fetch_public_response
        )


def test_successful_synthetic_runner_requests_exact_sources_and_retains_privately(
    tmp_path: Path,
) -> None:
    calls: list[str] = []
    config = _config(tmp_path)
    result = execute_synthetic_owner_sampling_for_validation(config, fetcher=_fake_fetcher(calls))

    assert calls == [build_url(contract) for contract in SOURCE_CONTRACTS]
    assert result.mode == "SYNTHETIC_INJECTED"
    assert result.real_okx_request_performed is False
    assert result.real_raw_sampling_executed is False
    assert result.source_count == 4
    assert result.private_artifact_count == 4
    assert config.safe_manifest_output.is_file()
    assert stat.S_IMODE(config.safe_manifest_output.stat().st_mode) == 0o600
    text = config.safe_manifest_output.read_text(encoding="utf-8")
    assert FAKE_MARKET_VALUE not in text
    assert "markPx" not in text
    assert "idxPx" not in text
    manifest = load_safe_sampling_manifest(config.safe_manifest_output)
    assert manifest.synthetic_validation_only is True
    assert len(list((config.private_root / "raw").glob("*.bin"))) == 4
    assert len(list((config.private_root / "leases").glob("*.json"))) == 4


def test_fetch_failure_retains_nothing(tmp_path: Path) -> None:
    calls: list[str] = []
    config = _config(tmp_path)
    with pytest.raises(RuntimeError, match="synthetic fetch failure"):
        execute_synthetic_owner_sampling_for_validation(
            config, fetcher=_fake_fetcher(calls, fail_on_index=2)
        )
    assert calls == [build_url(contract) for contract in SOURCE_CONTRACTS[:3]]
    assert not config.safe_manifest_output.exists()
    assert not (config.private_root / "raw").exists()


def test_safe_manifest_write_failure_rolls_back_private_batch(tmp_path: Path) -> None:
    blocked_parent = tmp_path / "blocked-parent"
    blocked_parent.write_text("not a directory", encoding="utf-8")
    config = _config(tmp_path, safe_output=blocked_parent / "manifest.json")
    with pytest.raises(OKXOwnerSamplingRunnerError, match="rolled back"):
        execute_synthetic_owner_sampling_for_validation(config, fetcher=_fake_fetcher([]))
    assert not list((config.private_root / "raw").glob("*.bin"))
    assert not list((config.private_root / "leases").glob("*.json"))
    assert len(list((config.private_root / "tombstones").glob("*.json"))) == 4


def test_manifest_inside_private_tree_and_existing_output_are_rejected(
    tmp_path: Path,
) -> None:
    config = _config(tmp_path, safe_output=tmp_path / "private" / "manifest.json")
    with pytest.raises(OKXOwnerSamplingRunnerError, match="outside the private"):
        config.validate()

    existing = tmp_path / "existing.json"
    existing.write_text("{}", encoding="utf-8")
    config = _config(tmp_path, safe_output=existing)
    with pytest.raises(OKXOwnerSamplingRunnerError, match="already exists"):
        config.validate()


def test_owner_delete_command_removes_batch_and_writes_safe_receipt(tmp_path: Path) -> None:
    config = _config(tmp_path)
    execute_synthetic_owner_sampling_for_validation(config, fetcher=_fake_fetcher([]))
    receipt_output = tmp_path / "safe-deletion.json"
    deletion = OwnerSamplingDeletionConfig(
        private_root=config.private_root,
        repository_root=config.repository_root,
        safe_manifest_path=config.safe_manifest_output,
        safe_deletion_receipt_output=receipt_output,
        confirmation_phrase=DELETE_CONFIRMATION_PHRASE,
        reason="OWNER_TEST_DELETE",
        attestations=_attestations(),
    )
    receipt = delete_owner_sampling_batch(deletion)
    assert receipt.all_raw_deleted is True
    assert receipt.all_leases_deleted is True
    assert receipt.source_count == 4
    assert receipt_output.is_file()
    text = receipt_output.read_text(encoding="utf-8")
    assert FAKE_MARKET_VALUE not in text
    assert not list((config.private_root / "raw").glob("*.bin"))
    assert not list((config.private_root / "leases").glob("*.json"))


def test_delete_requires_confirmation_and_valid_manifest(tmp_path: Path) -> None:
    config = _config(tmp_path)
    execute_synthetic_owner_sampling_for_validation(config, fetcher=_fake_fetcher([]))
    deletion = OwnerSamplingDeletionConfig(
        private_root=config.private_root,
        repository_root=config.repository_root,
        safe_manifest_path=config.safe_manifest_output,
        safe_deletion_receipt_output=tmp_path / "receipt.json",
        confirmation_phrase="wrong",
        reason="DELETE",
        attestations=_attestations(),
    )
    with pytest.raises(OKXOwnerSamplingRunnerError, match="deletion confirmation"):
        deletion.validate()

    invalid = tmp_path / "invalid.json"
    invalid.write_text("[]", encoding="utf-8")
    with pytest.raises(OKXOwnerSamplingRunnerError, match="not an object"):
        load_safe_sampling_manifest(invalid)


def test_real_executor_rejects_synthetic_configuration(tmp_path: Path) -> None:
    with pytest.raises(OKXOwnerSamplingRunnerError, match="OWNER_REAL_NETWORK"):
        execute_real_owner_sampling(_config(tmp_path))
