from __future__ import annotations

import base64
import hashlib
import hmac
import json
import stat
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from email.message import Message
from pathlib import Path
from urllib.request import Request

import pytest

from hybrid_trader.replication.okx_fee_accounting import FeeRateQuery, InstrumentType
from hybrid_trader.replication.okx_no_trade_observation import (
    ALLOWED_PRIVATE_ENDPOINTS,
    DELETE_CONFIRMATION_PHRASE,
    OWNER_CONFIRMATION_PHRASE,
    SYNTHETIC_CONFIRMATION_PHRASE,
    CredentialPermissionAttestation,
    NoTradeDeletionConfig,
    NoTradeObservationConfig,
    NoTradeObservationError,
    ObservationMode,
    OKXPrivateCredentials,
    PrivateTimedHTTPResponse,
    RejectPrivateRedirectHandler,
    build_fee_request_path,
    default_no_trade_health_policy,
    delete_no_trade_observation,
    execute_real_no_trade_observation,
    execute_synthetic_no_trade_observation_for_validation,
    fee_queries,
    load_credentials_from_environment,
    load_no_trade_health_policy,
    parse_fee_snapshot,
    require_admitted_public_batch,
    sign_private_get_request,
)
from hybrid_trader.replication.okx_owner_sampling_runner import OwnerRunnerAttestations
from hybrid_trader.replication.okx_price_linkage_probe import (
    SOURCE_CONTRACTS,
    HTTPResponse,
    TimedHTTPResponse,
    build_url,
)
from hybrid_trader.replication.okx_source_health import (
    RestHealthResult,
    SourceHealthState,
)

NOW = datetime(2026, 7, 21, 20, 0, tzinfo=UTC)
FAKE_MARKET_VALUE = "123456.789123"
FAKE_SPOT_MAKER = "-0.00123456"
FAKE_SPOT_TAKER = "-0.00234567"
FAKE_SWAP_MAKER = "-0.00345678"
FAKE_SWAP_TAKER = "-0.00456789"
SYNTHETIC_CREDENTIALS = OKXPrivateCredentials(
    api_key="synthetic-api-key",
    secret_key="synthetic-secret-key",
    passphrase="synthetic-passphrase",
)


def _owner_attestations(*, real: bool = False) -> OwnerRunnerAttestations:
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


def _credential_attestation(**overrides: bool) -> CredentialPermissionAttestation:
    values = {
        "read_permission_enabled": True,
        "trade_permission_disabled": True,
        "withdraw_permission_disabled": True,
        "ip_allowlist_enabled": True,
        "credentials_outside_repository": True,
        "credentials_outside_ci": True,
        "credentials_not_logged": True,
    }
    values.update(overrides)
    return CredentialPermissionAttestation(**values)


def _config(
    tmp_path: Path,
    *,
    mode: ObservationMode = ObservationMode.SYNTHETIC_INJECTED,
    confirmation: str = SYNTHETIC_CONFIRMATION_PHRASE,
    public_network: bool = False,
    private_network: bool = False,
    owner_attestations: OwnerRunnerAttestations | None = None,
    credential_attestation: CredentialPermissionAttestation | None = None,
    private_fee_output: Path | None = None,
    safe_manifest_output: Path | None = None,
    safe_receipt_output: Path | None = None,
) -> NoTradeObservationConfig:
    repository = tmp_path / "repo"
    repository.mkdir(parents=True, exist_ok=True)
    private_root = tmp_path / "private"
    return NoTradeObservationConfig(
        mode=mode,
        private_root=private_root,
        repository_root=repository,
        private_fee_snapshot_output=private_fee_output or (private_root / "fee-snapshot.json"),
        safe_batch_manifest_output=safe_manifest_output or (tmp_path / "safe-manifest.json"),
        safe_observation_receipt_output=safe_receipt_output or (tmp_path / "safe-observation.json"),
        requested_retention_days=2,
        confirmation_phrase=confirmation,
        enable_public_network_fetch=public_network,
        enable_private_network_fetch=private_network,
        owner_attestations=owner_attestations or _owner_attestations(),
        credential_attestation=credential_attestation or _credential_attestation(),
        health_policy=default_no_trade_health_policy(),
        api_domain="www.okx.com",
        code_head_sha="a" * 40,
    )


def _public_row(source_id: str, timestamp_ms: int, *, extra_field: bool = False) -> dict[str, str]:
    ticker = {
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
        "ts": str(timestamp_ms),
    }
    if source_id == "OKX_SPOT_BTC_USDT_TICKER":
        row = {"instType": "SPOT", "instId": "BTC-USDT", **ticker}
    elif source_id == "OKX_SWAP_BTC_USDT_SWAP_TICKER":
        row = {"instType": "SWAP", "instId": "BTC-USDT-SWAP", **ticker}
    elif source_id == "OKX_SWAP_BTC_USDT_SWAP_MARK_PRICE":
        row = {
            "instType": "SWAP",
            "instId": "BTC-USDT-SWAP",
            "markPx": FAKE_MARKET_VALUE,
            "ts": str(timestamp_ms),
        }
    elif source_id == "OKX_BTC_USDT_INDEX_TICKER":
        row = {
            "instId": "BTC-USDT",
            "idxPx": FAKE_MARKET_VALUE,
            "high24h": "124000",
            "open24h": "120000",
            "low24h": "119000",
            "sodUtc0": "121000",
            "sodUtc8": "122000",
            "ts": str(timestamp_ms),
        }
    else:
        raise AssertionError(source_id)
    if extra_field:
        row["unexpected"] = "1"
    return row


def _public_fetcher(
    calls: list[str],
    *,
    provider_age_ms: int = 500,
    provider_ages_ms: tuple[int, ...] | None = None,
    fail_on_index: int | None = None,
    schema_drift_on_index: int | None = None,
) -> Callable[[str], TimedHTTPResponse]:
    by_url = {build_url(contract): contract for contract in SOURCE_CONTRACTS}

    def fetch(url: str) -> TimedHTTPResponse:
        calls.append(url)
        index = len(calls) - 1
        if fail_on_index is not None and index == fail_on_index:
            raise RuntimeError("synthetic public fetch failure")
        contract = by_url[url]
        request = NOW + timedelta(milliseconds=index * 100)
        response = request + timedelta(milliseconds=10)
        age_ms = (
            provider_ages_ms[index]
            if provider_ages_ms is not None
            else provider_age_ms + index * 50
        )
        provider_ms = int(response.timestamp() * 1000) - age_ms
        row = _public_row(
            contract.source_id,
            provider_ms,
            extra_field=(schema_drift_on_index == index),
        )
        body = json.dumps({"code": "0", "msg": "", "data": [row]}, sort_keys=True).encode()
        return TimedHTTPResponse(
            response=HTTPResponse(body, 200, "application/json", url),
            request_started_at=request,
            response_received_at=response,
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
            "maker": FAKE_SPOT_MAKER,
            "taker": FAKE_SPOT_TAKER,
            "makerU": "",
            "takerU": "",
        }
    return {
        **common,
        "maker": "-0.0005",
        "taker": "-0.0007",
        "makerU": FAKE_SWAP_MAKER,
        "takerU": FAKE_SWAP_TAKER,
    }


def _private_fetcher(
    calls: list[str], *, fail_on_index: int | None = None
) -> Callable[[FeeRateQuery], PrivateTimedHTTPResponse]:
    def fetch(query: FeeRateQuery) -> PrivateTimedHTTPResponse:
        index = len(calls)
        path = build_fee_request_path(query)
        calls.append(path)
        if fail_on_index is not None and index == fail_on_index:
            raise RuntimeError("synthetic fee fetch failure")
        body = json.dumps(
            {"code": "0", "msg": "", "data": [_fee_row(query)]}, sort_keys=True
        ).encode()
        return PrivateTimedHTTPResponse(
            body=body,
            status_code=200,
            content_type="application/json",
            final_url=f"https://www.okx.com{path}",
            request_started_at=NOW,
            response_received_at=NOW + timedelta(milliseconds=10),
        )

    return fetch


def _healthy_result(source_id: str, provider_at: datetime) -> RestHealthResult:
    policy = default_no_trade_health_policy()
    return RestHealthResult(
        source_id=source_id,
        state=SourceHealthState.HEALTHY,
        admitted=True,
        quarantine_required=False,
        provider_timestamp=provider_at,
        research_available_at=NOW + timedelta(seconds=1),
        provider_age_ms=500,
        future_skew_ms=0,
        research_delay_ms=100,
        policy_id=policy.policy_id,
        policy_fingerprint_sha256=policy.policy_fingerprint_sha256,
        response_sha256="1" * 64,
        schema_sha256=policy.expected_schema_sha256[source_id],
        identity_sha256=policy.expected_identity_sha256[source_id],
    )


def _execute(
    config: NoTradeObservationConfig,
    *,
    public_fetcher: Callable[[str], TimedHTTPResponse] | None = None,
    private_fetcher: Callable[[FeeRateQuery], PrivateTimedHTTPResponse] | None = None,
):
    return execute_synthetic_no_trade_observation_for_validation(
        config,
        credentials=SYNTHETIC_CREDENTIALS,
        private_fetcher=private_fetcher or _private_fetcher([]),
        public_fetcher=public_fetcher or _public_fetcher([]),
        now_provider=lambda: NOW + timedelta(seconds=1),
    )


def test_read_only_permission_contract_fails_closed(tmp_path: Path) -> None:
    for field in (
        "read_permission_enabled",
        "trade_permission_disabled",
        "withdraw_permission_disabled",
        "ip_allowlist_enabled",
        "credentials_outside_repository",
        "credentials_outside_ci",
        "credentials_not_logged",
    ):
        config = _config(
            tmp_path / field,
            credential_attestation=_credential_attestation(**{field: False}),
        )
        with pytest.raises(NoTradeObservationError, match="Read-only credential"):
            config.validate()


def test_real_mode_requires_exact_confirmation_network_and_owner_attestations(
    tmp_path: Path,
) -> None:
    config = _config(
        tmp_path / "confirm",
        mode=ObservationMode.OWNER_REAL_NETWORK,
        confirmation="wrong",
        public_network=True,
        private_network=True,
        owner_attestations=_owner_attestations(real=True),
    )
    with pytest.raises(NoTradeObservationError, match="Exact owner"):
        config.validate()

    config = _config(
        tmp_path / "network",
        mode=ObservationMode.OWNER_REAL_NETWORK,
        confirmation=OWNER_CONFIRMATION_PHRASE,
        public_network=False,
        private_network=True,
        owner_attestations=_owner_attestations(real=True),
    )
    with pytest.raises(NoTradeObservationError, match="Both public and private"):
        config.validate()


def test_private_endpoint_and_fee_queries_are_exact() -> None:
    queries = fee_queries()
    assert {"/api/v5/account/trade-fee"} == ALLOWED_PRIVATE_ENDPOINTS
    assert [build_fee_request_path(query) for query in queries] == [
        "/api/v5/account/trade-fee?instType=SPOT&instId=BTC-USDT",
        "/api/v5/account/trade-fee?instType=SWAP&instFamily=BTC-USDT",
    ]
    assert all("order" not in build_fee_request_path(query) for query in queries)


def test_hmac_signature_is_deterministic_and_repr_is_redacted() -> None:
    query_path = build_fee_request_path(fee_queries()[0])
    headers = sign_private_get_request(
        credentials=SYNTHETIC_CREDENTIALS,
        timestamp=NOW,
        request_path=query_path,
    )
    timestamp = "2026-07-21T20:00:00.000Z"
    expected = base64.b64encode(
        hmac.new(
            b"synthetic-secret-key",
            f"{timestamp}GET{query_path}".encode(),
            hashlib.sha256,
        ).digest()
    ).decode()
    assert headers["OK-ACCESS-SIGN"] == expected
    assert headers["OK-ACCESS-TIMESTAMP"] == timestamp
    assert "synthetic-secret-key" not in repr(SYNTHETIC_CREDENTIALS)
    assert "synthetic-api-key" not in repr(SYNTHETIC_CREDENTIALS)


def test_private_authenticated_redirect_is_rejected_before_replay() -> None:
    handler = RejectPrivateRedirectHandler()
    request = Request(
        "https://www.okx.com/api/v5/account/trade-fee?instType=SPOT&instId=BTC-USDT",
        headers={"OK-ACCESS-KEY": "synthetic-api-key"},
        method="GET",
    )
    with pytest.raises(NoTradeObservationError, match="must not follow redirects"):
        handler.redirect_request(
            request,
            None,
            302,
            "Found",
            Message(),
            "https://attacker.invalid/collect",
        )


def test_fee_responses_parse_into_issue_56_model() -> None:
    fetch = _private_fetcher([])
    spot_query, swap_query = fee_queries()
    spot = parse_fee_snapshot(query=spot_query, response=fetch(spot_query))
    swap = parse_fee_snapshot(query=swap_query, response=fetch(swap_query))
    assert str(spot.maker) == FAKE_SPOT_MAKER
    assert str(spot.taker) == FAKE_SPOT_TAKER
    assert str(swap.maker_u) == FAKE_SWAP_MAKER
    assert str(swap.taker_u) == FAKE_SWAP_TAKER


def test_policy_file_is_exact_and_versioned() -> None:
    root = Path(__file__).resolve().parents[1]
    policy = load_no_trade_health_policy(
        root / "configs" / "okx_no_trade_observation_policy_v1.yaml"
    )
    assert policy.policy_id == "OKX_OWNER_NO_TRADE_HEALTH_POLICY_V1"
    assert policy.maximum_provider_age_ms == 15_000
    assert policy.maximum_cross_source_provider_time_skew_ms == 15_000
    assert (
        policy.policy_fingerprint_sha256
        == default_no_trade_health_policy().policy_fingerprint_sha256
    )


def test_duplicate_partial_and_cross_skew_fail_admission() -> None:
    policy = default_no_trade_health_policy()
    source_ids = policy.required_source_ids
    healthy = tuple(_healthy_result(source_id, NOW) for source_id in source_ids)

    with pytest.raises(NoTradeObservationError, match="DUPLICATE_SOURCE"):
        require_admitted_public_batch((*healthy, healthy[0]), policy=policy)
    with pytest.raises(NoTradeObservationError, match="PARTIAL_SOURCE_SET"):
        require_admitted_public_batch(healthy[:-1], policy=policy)

    skewed = tuple(
        _healthy_result(
            source_id,
            NOW + timedelta(milliseconds=index * 6_000),
        )
        for index, source_id in enumerate(source_ids)
    )
    with pytest.raises(NoTradeObservationError, match="CROSS_SOURCE_SKEW_EXCEEDED"):
        require_admitted_public_batch(skewed, policy=policy)


def test_cross_source_skew_is_rejected_before_retention(tmp_path: Path) -> None:
    config = _config(tmp_path)
    ages = (-1_500, 4_000, 10_000, 15_000)
    with pytest.raises(NoTradeObservationError, match="CROSS_SOURCE_SKEW_EXCEEDED"):
        _execute(config, public_fetcher=_public_fetcher([], provider_ages_ms=ages))
    assert not (config.private_root / "raw").exists()
    assert not config.private_fee_snapshot_output.exists()


def test_successful_synthetic_observation_is_private_and_no_trade(tmp_path: Path) -> None:
    public_calls: list[str] = []
    private_calls: list[str] = []
    config = _config(tmp_path)
    result = _execute(
        config,
        public_fetcher=_public_fetcher(public_calls),
        private_fetcher=_private_fetcher(private_calls),
    )

    assert public_calls == [build_url(contract) for contract in SOURCE_CONTRACTS]
    assert private_calls == [build_fee_request_path(query) for query in fee_queries()]
    assert result.real_public_requests_performed is False
    assert result.real_private_fee_requests_performed is False
    assert result.orders_sent is False
    assert result.source_count == 4
    assert config.private_fee_snapshot_output.is_file()
    assert config.safe_batch_manifest_output.is_file()
    assert config.safe_observation_receipt_output.is_file()
    assert stat.S_IMODE(config.private_fee_snapshot_output.stat().st_mode) == 0o600
    assert stat.S_IMODE(config.safe_observation_receipt_output.stat().st_mode) == 0o600

    private_text = config.private_fee_snapshot_output.read_text(encoding="utf-8")
    safe_text = config.safe_observation_receipt_output.read_text(encoding="utf-8")
    assert FAKE_SPOT_MAKER in private_text
    assert FAKE_SWAP_TAKER in private_text
    for secret_or_value in (
        FAKE_SPOT_MAKER,
        FAKE_SPOT_TAKER,
        FAKE_SWAP_MAKER,
        FAKE_SWAP_TAKER,
        FAKE_MARKET_VALUE,
        "synthetic-api-key",
        "synthetic-secret-key",
        "synthetic-passphrase",
        "OK-ACCESS-SIGN",
    ):
        assert secret_or_value not in safe_text
    safe = json.loads(safe_text)
    assert safe["orders_sent"] is False
    assert safe["trade_permission_used"] is False
    assert safe["withdraw_permission_used"] is False
    assert safe["batch_decision"] == "ADMIT_PRIVATE_BATCH"
    assert set(safe["health_state_by_source"].values()) == {"HEALTHY"}
    assert safe["report_2_4_authorized"] is False
    assert safe["economic_edge_verdict"] == "INCONCLUSIVE"
    assert len(list((config.private_root / "raw").glob("*.bin"))) == 4


def test_stale_batch_is_rejected_before_private_write(tmp_path: Path) -> None:
    config = _config(tmp_path)
    with pytest.raises(NoTradeObservationError, match="failed health admission"):
        _execute(config, public_fetcher=_public_fetcher([], provider_age_ms=60_000))
    assert not config.private_fee_snapshot_output.exists()
    assert not config.safe_batch_manifest_output.exists()
    assert not config.safe_observation_receipt_output.exists()
    assert not (config.private_root / "raw").exists()


def test_schema_drift_is_quarantined_before_retention(tmp_path: Path) -> None:
    config = _config(tmp_path)
    with pytest.raises(NoTradeObservationError, match="failed health admission"):
        _execute(config, public_fetcher=_public_fetcher([], schema_drift_on_index=2))
    assert not (config.private_root / "raw").exists()


def test_public_or_private_fetch_failure_retains_nothing(tmp_path: Path) -> None:
    config = _config(tmp_path / "public")
    with pytest.raises(RuntimeError, match="public fetch failure"):
        _execute(config, public_fetcher=_public_fetcher([], fail_on_index=2))
    assert not (config.private_root / "raw").exists()

    config = _config(tmp_path / "private")
    with pytest.raises(RuntimeError, match="fee fetch failure"):
        _execute(config, private_fetcher=_private_fetcher([], fail_on_index=1))
    assert not (config.private_root / "raw").exists()


def test_private_fee_write_failure_rolls_back_public_batch(tmp_path: Path) -> None:
    config = _config(tmp_path)
    config.private_root.mkdir(parents=True)
    blocked = config.private_root / "blocked"
    blocked.write_text("not a directory", encoding="utf-8")
    config = _config(tmp_path, private_fee_output=blocked / "fee.json")
    with pytest.raises(NoTradeObservationError, match="rolled back"):
        _execute(config)
    assert not list((config.private_root / "raw").glob("*.bin"))
    assert not list((config.private_root / "leases").glob("*.json"))


def test_safe_receipt_failure_rolls_back_fee_and_public_batch(tmp_path: Path) -> None:
    blocked = tmp_path / "blocked"
    blocked.write_text("not a directory", encoding="utf-8")
    config = _config(tmp_path, safe_receipt_output=blocked / "receipt.json")
    with pytest.raises(NoTradeObservationError, match="rolled back"):
        _execute(config)
    assert not config.private_fee_snapshot_output.exists()
    assert not config.safe_batch_manifest_output.exists()
    assert not list((config.private_root / "raw").glob("*.bin"))
    assert not list((config.private_root / "leases").glob("*.json"))


def test_delete_removes_private_fee_and_public_batch(tmp_path: Path) -> None:
    config = _config(tmp_path)
    _execute(config)
    deletion_output = tmp_path / "safe-deletion.json"
    deletion = NoTradeDeletionConfig(
        private_root=config.private_root,
        repository_root=config.repository_root,
        private_fee_snapshot_path=config.private_fee_snapshot_output,
        safe_batch_manifest_path=config.safe_batch_manifest_output,
        safe_observation_receipt_path=config.safe_observation_receipt_output,
        safe_deletion_receipt_output=deletion_output,
        confirmation_phrase=DELETE_CONFIRMATION_PHRASE,
        reason="OWNER_TEST_DELETE",
        owner_attestations=_owner_attestations(),
    )
    safe = delete_no_trade_observation(deletion)
    assert safe["all_public_raw_deleted"] is True
    assert safe["all_public_leases_deleted"] is True
    assert safe["private_fee_snapshot_exists_after_delete"] is False
    assert safe["secure_erase_claimed"] is False
    assert deletion_output.is_file()
    assert not config.private_fee_snapshot_output.exists()
    assert not list((config.private_root / "raw").glob("*.bin"))


def test_environment_loader_and_real_executor_fail_closed(tmp_path: Path) -> None:
    with pytest.raises(NoTradeObservationError, match="Missing owner-local"):
        load_credentials_from_environment({})
    loaded = load_credentials_from_environment(
        {
            "OKX_API_KEY": "key",
            "OKX_SECRET_KEY": "secret",
            "OKX_PASSPHRASE": "pass",
        }
    )
    rendered = repr(loaded)
    assert "api_key='key'" not in rendered
    assert "secret_key='secret'" not in rendered
    assert "passphrase='pass'" not in rendered
    with pytest.raises(NoTradeObservationError, match="OWNER_REAL_NETWORK"):
        execute_real_no_trade_observation(_config(tmp_path), credentials=loaded)
