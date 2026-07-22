"""Owner-controlled OKX no-trade observation package.

The package binds two read-only account fee snapshots to one four-source public
market observation. It is disabled by default, performs no order action, and
retains raw/fee values only in owner-controlled private storage.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path
from typing import Any, cast
from urllib.parse import parse_qsl, urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, OpenerDirector, Request, build_opener

import yaml

from hybrid_trader.replication.okx_fee_accounting import (
    ACCOUNT_FEE_ENDPOINT,
    SPOT_INSTRUMENT_ID,
    SWAP_INSTRUMENT_FAMILY,
    AccountFeeRateSnapshot,
    FeeRateQuery,
    InstrumentType,
)
from hybrid_trader.replication.okx_owner_sampling_runner import (
    OwnerRunnerAttestations,
    OwnerSamplingRunnerConfig,
    load_safe_sampling_manifest,
)
from hybrid_trader.replication.okx_price_linkage_probe import (
    SOURCE_CONTRACTS,
    TimedHTTPResponse,
    build_url,
    fetch_public_response,
    validate_source_response,
)
from hybrid_trader.replication.okx_private_sampling import (
    OwnerSamplingAuthorization,
    SafeSamplingBatchDeletionReceipt,
    SafeSamplingBatchManifest,
    SamplingClock,
    SamplingExecutionMode,
    delete_sampling_batch,
    retain_sampling_batch,
    safe_manifest_json,
)
from hybrid_trader.replication.okx_source_health import (
    BatchAdmissionResult,
    BatchDecision,
    RestHealthResult,
    RestObservation,
    SourceHealthPolicy,
    admit_sampling_batch,
    evaluate_rest_observation,
)
from hybrid_trader.replication.revocable_retention import (
    ALLOWED_PURPOSE,
    PrivateRevocableArtifactStore,
    RetentionAttestation,
    RetentionPolicy,
)

OWNER_CONFIRMATION_PHRASE = "I_CONFIRM_OWNER_CONTROLLED_OKX_NO_TRADE_OBSERVATION"
SYNTHETIC_CONFIRMATION_PHRASE = "I_CONFIRM_SYNTHETIC_OKX_NO_TRADE_OBSERVATION_ONLY"
DELETE_CONFIRMATION_PHRASE = "I_CONFIRM_DELETE_OWNER_CONTROLLED_OKX_NO_TRADE_OBSERVATION"
GATE_ID = "OKX_OWNER_CONTROLLED_NO_TRADE_OBSERVATION_V1"
DEFAULT_POLICY_ID = "OKX_OWNER_NO_TRADE_HEALTH_POLICY_V1"
DEFAULT_BACKOFF_POLICY_ID = "EXPONENTIAL_1_2_4_MAX3_NO_JITTER_V1"
DEFAULT_LICENSE_SNAPSHOT_ID = "OKX_API_AGREEMENT_2026-03-26_REVIEWED_2026-07-21_V1"
MAX_PRIVATE_RESPONSE_BYTES = 200_000
ALLOWED_API_DOMAINS = frozenset({"www.okx.com", "us.okx.com", "eea.okx.com"})
ALLOWED_PRIVATE_METHODS = frozenset({"GET"})
ALLOWED_PRIVATE_ENDPOINTS = frozenset({ACCOUNT_FEE_ENDPOINT})
FORBIDDEN_PRIVATE_ENDPOINT_FRAGMENTS = (
    "/trade/order",
    "/trade/cancel",
    "/trade/amend",
    "/asset/withdrawal",
    "/asset/transfer",
    "/account/set-",
)

EXPECTED_SCHEMA_SHA256 = {
    "OKX_SPOT_BTC_USDT_TICKER": (
        "a0efda49b5a0800771ceb73e426c7ea32649d12ec43296cc9a08f4864dbd2c78"
    ),
    "OKX_SWAP_BTC_USDT_SWAP_TICKER": (
        "a0efda49b5a0800771ceb73e426c7ea32649d12ec43296cc9a08f4864dbd2c78"
    ),
    "OKX_SWAP_BTC_USDT_SWAP_MARK_PRICE": (
        "6bf8819de4ac4a636c639c06322c30591d1834517402895b9b830916d0bbbe3f"
    ),
    "OKX_BTC_USDT_INDEX_TICKER": (
        "9aa78fdea927d6e3737b088b7a504f68be1b444aec4fe63acee5222d3ee7ef12"
    ),
}
EXPECTED_IDENTITY_SHA256 = {
    "OKX_SPOT_BTC_USDT_TICKER": (
        "2187ca4d4d68c0915be1c43b994ac50711e8a79cca0a3ca3aa0d4adf5bf8f05e"
    ),
    "OKX_SWAP_BTC_USDT_SWAP_TICKER": (
        "b91ac7bef32cc5dfc21bbe2bef5e690cb7ece317a6a0e29b5e919747a8bd4e1f"
    ),
    "OKX_SWAP_BTC_USDT_SWAP_MARK_PRICE": (
        "b91ac7bef32cc5dfc21bbe2bef5e690cb7ece317a6a0e29b5e919747a8bd4e1f"
    ),
    "OKX_BTC_USDT_INDEX_TICKER": (
        "fe56f11ebf091923b2e6f2ab8d5caffa8ed6ed4ef43015b17491f067121f169a"
    ),
}


class NoTradeObservationError(RuntimeError):
    """Raised when the no-trade observation package fails closed."""


class RejectPrivateRedirectHandler(HTTPRedirectHandler):
    """Reject every redirect before private authentication headers can be replayed."""

    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> Request | None:
        del req, fp, code, msg, headers, newurl
        raise NoTradeObservationError(
            "Private authenticated fee requests must not follow redirects"
        )


def _private_fee_opener() -> OpenerDirector:
    return build_opener(RejectPrivateRedirectHandler())


class ObservationMode(StrEnum):
    SYNTHETIC_INJECTED = "SYNTHETIC_INJECTED"
    OWNER_REAL_NETWORK = "OWNER_REAL_NETWORK"


@dataclass(frozen=True)
class CredentialPermissionAttestation:
    read_permission_enabled: bool
    trade_permission_disabled: bool
    withdraw_permission_disabled: bool
    ip_allowlist_enabled: bool
    credentials_outside_repository: bool
    credentials_outside_ci: bool
    credentials_not_logged: bool

    def validate(self) -> None:
        required = asdict(self)
        missing = [name for name, value in required.items() if value is not True]
        if missing:
            raise NoTradeObservationError(
                "Read-only credential attestations are incomplete: " + ", ".join(missing)
            )


@dataclass(frozen=True, repr=False)
class OKXPrivateCredentials:
    api_key: str = field(repr=False)
    secret_key: str = field(repr=False)
    passphrase: str = field(repr=False)

    def validate(self) -> None:
        for field_name, value in (
            ("api_key", self.api_key),
            ("secret_key", self.secret_key),
            ("passphrase", self.passphrase),
        ):
            if not value or value != value.strip():
                raise NoTradeObservationError(f"{field_name} is missing or has outer whitespace")
            if any(character in value for character in ("\n", "\r", "\x00")):
                raise NoTradeObservationError(
                    f"{field_name} contains a forbidden control character"
                )

    def __repr__(self) -> str:
        return "OKXPrivateCredentials(api_key=<redacted>, secret_key=<redacted>, passphrase=<redacted>)"


@dataclass(frozen=True)
class PrivateTimedHTTPResponse:
    body: bytes
    status_code: int
    content_type: str
    final_url: str
    request_started_at: datetime
    response_received_at: datetime


@dataclass(frozen=True)
class FeeSnapshotSafeIdentity:
    query_id: str
    response_sha256: str
    response_timestamp_ms: int
    level_present: bool
    rule_type_normal: bool
    spot_maker_taker_present: bool
    swap_maker_u_taker_u_present: bool


@dataclass(frozen=True)
class PrivateFeeSnapshotBundle:
    schema_version: str
    contract_id: str
    captured_at_utc: str
    api_domain: str
    snapshots: tuple[AccountFeeRateSnapshot, ...]
    response_sha256_by_query: Mapping[str, str]

    @property
    def canonical_bytes(self) -> bytes:
        payload = {
            "schema_version": self.schema_version,
            "contract_id": self.contract_id,
            "captured_at_utc": self.captured_at_utc,
            "api_domain": self.api_domain,
            "snapshots": [_private_snapshot_payload(snapshot) for snapshot in self.snapshots],
            "response_sha256_by_query": dict(sorted(self.response_sha256_by_query.items())),
        }
        return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")

    @property
    def bundle_sha256(self) -> str:
        return _sha256(self.canonical_bytes)

    @property
    def safe_identities(self) -> tuple[FeeSnapshotSafeIdentity, ...]:
        identities: list[FeeSnapshotSafeIdentity] = []
        for snapshot in self.snapshots:
            query_id = _fee_query_id(snapshot.query)
            identities.append(
                FeeSnapshotSafeIdentity(
                    query_id=query_id,
                    response_sha256=self.response_sha256_by_query[query_id],
                    response_timestamp_ms=snapshot.response_timestamp_ms,
                    level_present=bool(snapshot.level),
                    rule_type_normal=(snapshot.rule_type == "normal"),
                    spot_maker_taker_present=(
                        snapshot.query.instrument_type is InstrumentType.SPOT
                        and snapshot.maker is not None
                        and snapshot.taker is not None
                    ),
                    swap_maker_u_taker_u_present=(
                        snapshot.query.instrument_type is InstrumentType.SWAP
                        and snapshot.maker_u is not None
                        and snapshot.taker_u is not None
                    ),
                )
            )
        return tuple(identities)


@dataclass(frozen=True)
class SafeNoTradeObservationReceipt:
    schema_version: str
    gate_id: str
    receipt_id: str
    code_head_sha: str
    mode: str
    synthetic_validation_only: bool
    real_public_requests_performed: bool
    real_private_fee_requests_performed: bool
    orders_sent: bool
    trade_permission_used: bool
    withdraw_permission_used: bool
    private_endpoint_paths: tuple[str, ...]
    fee_query_ids: tuple[str, ...]
    fee_bundle_sha256: str
    fee_snapshots: tuple[FeeSnapshotSafeIdentity, ...]
    health_policy_id: str
    health_policy_fingerprint_sha256: str
    health_state_by_source: Mapping[str, str]
    public_response_sha256_by_source: Mapping[str, str]
    public_schema_sha256_by_source: Mapping[str, str]
    public_identity_sha256_by_source: Mapping[str, str]
    batch_decision: str
    batch_state: str
    cross_source_provider_time_skew_ms: int
    provider_timestamps_monotonic_in_request_order: bool
    private_batch_id: str
    private_batch_manifest_sha256: str
    private_source_count: int
    requested_retention_days: int
    credentials_present_in_receipt: bool
    fee_values_present_in_receipt: bool
    market_values_present_in_receipt: bool
    basis_computation_authorized: bool
    funding_pnl_computation_authorized: bool
    returns_computation_authorized: bool
    transaction_cost_estimation_authorized: bool
    strategy_testing_authorized: bool
    paper_or_live_trading_authorized: bool
    report_2_4_authorized: bool
    economic_edge_verdict: str


@dataclass(frozen=True)
class NoTradeObservationResult:
    mode: str
    real_public_requests_performed: bool
    real_private_fee_requests_performed: bool
    orders_sent: bool
    batch_id: str
    source_count: int
    fee_bundle_sha256: str
    safe_receipt_sha256: str
    safe_receipt_output: str
    safe_manifest_output: str
    private_fee_snapshot_output: str


@dataclass(frozen=True)
class NoTradeObservationConfig:
    mode: ObservationMode
    private_root: Path
    repository_root: Path
    private_fee_snapshot_output: Path
    safe_batch_manifest_output: Path
    safe_observation_receipt_output: Path
    requested_retention_days: int
    confirmation_phrase: str
    enable_public_network_fetch: bool
    enable_private_network_fetch: bool
    owner_attestations: OwnerRunnerAttestations
    credential_attestation: CredentialPermissionAttestation
    health_policy: SourceHealthPolicy
    api_domain: str
    code_head_sha: str
    policy_id: str = DEFAULT_POLICY_ID
    license_snapshot_id: str = DEFAULT_LICENSE_SNAPSHOT_ID

    def validate(self) -> None:
        if self.api_domain not in ALLOWED_API_DOMAINS:
            raise NoTradeObservationError("API domain is outside the frozen regional allowlist")
        if not _is_git_sha(self.code_head_sha):
            raise NoTradeObservationError("code_head_sha must be a 40-character lowercase Git SHA")
        if not 1 <= self.requested_retention_days <= 7:
            raise NoTradeObservationError("requested_retention_days must be between 1 and 7")
        if self.health_policy.policy_id != self.policy_id:
            raise NoTradeObservationError("health policy ID and retention policy ID must match")
        _validate_health_policy_contract(self.health_policy)
        self.credential_attestation.validate()

        private_root = self.private_root.expanduser().resolve(strict=False)
        repository_root = self.repository_root.expanduser().resolve(strict=False)
        private_fee = self.private_fee_snapshot_output.expanduser().resolve(strict=False)
        safe_manifest = self.safe_batch_manifest_output.expanduser().resolve(strict=False)
        safe_receipt = self.safe_observation_receipt_output.expanduser().resolve(strict=False)
        if private_root == repository_root or private_root.is_relative_to(repository_root):
            raise NoTradeObservationError("Private storage must be outside the repository")
        if not private_fee.is_relative_to(private_root):
            raise NoTradeObservationError("Private fee snapshot must be inside private_root")
        for path in (safe_manifest, safe_receipt):
            if path == private_root or path.is_relative_to(private_root):
                raise NoTradeObservationError("Safe outputs must be outside private raw storage")
            if path == repository_root or path.is_relative_to(repository_root):
                raise NoTradeObservationError(
                    "Owner-run safe outputs must be outside the repository"
                )
        for path in (private_fee, safe_manifest, safe_receipt):
            if _safe_path_exists(path):
                raise NoTradeObservationError(f"Output already exists: {path.name}")
            if path.suffix.casefold() != ".json":
                raise NoTradeObservationError("All observation outputs must be JSON files")

        runner_config = self.owner_runner_config
        runner_config.validate()
        if self.mode is ObservationMode.OWNER_REAL_NETWORK:
            if self.confirmation_phrase != OWNER_CONFIRMATION_PHRASE:
                raise NoTradeObservationError("Exact owner no-trade confirmation is required")
            if not self.enable_public_network_fetch or not self.enable_private_network_fetch:
                raise NoTradeObservationError(
                    "Both public and private network fetches must be explicit"
                )
        else:
            if self.confirmation_phrase != SYNTHETIC_CONFIRMATION_PHRASE:
                raise NoTradeObservationError("Exact synthetic no-trade confirmation is required")
            if self.enable_public_network_fetch or self.enable_private_network_fetch:
                raise NoTradeObservationError("Synthetic mode cannot enable network access")

    @property
    def owner_runner_config(self) -> OwnerSamplingRunnerConfig:
        from hybrid_trader.replication.okx_owner_sampling_runner import OwnerRunnerMode

        mode = (
            OwnerRunnerMode.OWNER_REAL_NETWORK
            if self.mode is ObservationMode.OWNER_REAL_NETWORK
            else OwnerRunnerMode.SYNTHETIC_INJECTED
        )
        confirmation = (
            "I_CONFIRM_OWNER_CONTROLLED_PRIVATE_OKX_RAW_SAMPLING"
            if self.mode is ObservationMode.OWNER_REAL_NETWORK
            else "I_CONFIRM_SYNTHETIC_INJECTED_RESPONSES_ONLY"
        )
        return OwnerSamplingRunnerConfig(
            mode=mode,
            private_root=self.private_root,
            repository_root=self.repository_root,
            safe_manifest_output=self.safe_batch_manifest_output,
            requested_retention_days=self.requested_retention_days,
            confirmation_phrase=confirmation,
            enable_real_network_fetch=(self.mode is ObservationMode.OWNER_REAL_NETWORK),
            attestations=self.owner_attestations,
            policy_id=self.policy_id,
            license_snapshot_id=self.license_snapshot_id,
        )


@dataclass(frozen=True)
class NoTradeDeletionConfig:
    private_root: Path
    repository_root: Path
    private_fee_snapshot_path: Path
    safe_batch_manifest_path: Path
    safe_observation_receipt_path: Path
    safe_deletion_receipt_output: Path
    confirmation_phrase: str
    reason: str
    owner_attestations: OwnerRunnerAttestations

    def validate(self) -> None:
        if self.confirmation_phrase != DELETE_CONFIRMATION_PHRASE:
            raise NoTradeObservationError("Exact no-trade deletion confirmation is required")
        if not self.reason.strip():
            raise NoTradeObservationError("Deletion reason cannot be empty")
        for path in (
            self.private_fee_snapshot_path,
            self.safe_batch_manifest_path,
            self.safe_observation_receipt_path,
        ):
            if not path.is_file():
                raise NoTradeObservationError(f"Required observation file is missing: {path.name}")
        if _safe_path_exists(self.safe_deletion_receipt_output):
            raise NoTradeObservationError("Deletion receipt output already exists")
        if self.safe_deletion_receipt_output.suffix.casefold() != ".json":
            raise NoTradeObservationError("Deletion receipt output must be JSON")
        required = {
            "owner_only_access": self.owner_attestations.owner_only_access,
            "public_artifact_upload_disabled": (
                self.owner_attestations.public_artifact_upload_disabled
            ),
        }
        missing = [name for name, value in required.items() if value is not True]
        if missing:
            raise NoTradeObservationError(
                "Deletion attestations are incomplete: " + ", ".join(missing)
            )


def default_no_trade_health_policy() -> SourceHealthPolicy:
    """Return the explicit, versioned engineering guard for one owner observation."""

    required = tuple(sorted(EXPECTED_SCHEMA_SHA256))
    return SourceHealthPolicy(
        policy_id=DEFAULT_POLICY_ID,
        maximum_provider_age_ms=15_000,
        maximum_future_clock_skew_ms=2_000,
        maximum_response_to_research_delay_ms=2_000,
        maximum_websocket_silence_seconds=20.0,
        maximum_cross_source_provider_time_skew_ms=15_000,
        required_source_ids=required,
        expected_schema_sha256=dict(EXPECTED_SCHEMA_SHA256),
        expected_identity_sha256=dict(EXPECTED_IDENTITY_SHA256),
        checksum_deprecation_effective_at=datetime(2026, 6, 23, tzinfo=UTC),
        sequence_validation_mode="SEQ_ID_PREV_SEQ_ID",
        rate_limit_backoff_policy_id=DEFAULT_BACKOFF_POLICY_ID,
    )


def load_no_trade_health_policy(path: Path) -> SourceHealthPolicy:
    try:
        decoded: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise NoTradeObservationError("Cannot read no-trade health policy YAML") from exc
    if not isinstance(decoded, dict):
        raise NoTradeObservationError("No-trade health policy must be a mapping")
    payload = cast(Mapping[str, Any], decoded)
    required_keys = {
        "policy_id",
        "maximum_provider_age_ms",
        "maximum_future_clock_skew_ms",
        "maximum_response_to_research_delay_ms",
        "maximum_websocket_silence_seconds",
        "maximum_cross_source_provider_time_skew_ms",
        "required_source_ids",
        "expected_schema_sha256",
        "expected_identity_sha256",
        "checksum_deprecation_effective_at",
        "sequence_validation_mode",
        "rate_limit_backoff_policy_id",
    }
    if set(payload) != required_keys:
        raise NoTradeObservationError("No-trade health policy keys differ from the frozen schema")
    try:
        policy = SourceHealthPolicy(
            policy_id=str(payload["policy_id"]),
            maximum_provider_age_ms=int(payload["maximum_provider_age_ms"]),
            maximum_future_clock_skew_ms=int(payload["maximum_future_clock_skew_ms"]),
            maximum_response_to_research_delay_ms=int(
                payload["maximum_response_to_research_delay_ms"]
            ),
            maximum_websocket_silence_seconds=float(payload["maximum_websocket_silence_seconds"]),
            maximum_cross_source_provider_time_skew_ms=int(
                payload["maximum_cross_source_provider_time_skew_ms"]
            ),
            required_source_ids=tuple(str(item) for item in payload["required_source_ids"]),
            expected_schema_sha256={
                str(key): str(value)
                for key, value in cast(Mapping[Any, Any], payload["expected_schema_sha256"]).items()
            },
            expected_identity_sha256={
                str(key): str(value)
                for key, value in cast(
                    Mapping[Any, Any], payload["expected_identity_sha256"]
                ).items()
            },
            checksum_deprecation_effective_at=_parse_iso_utc(
                str(payload["checksum_deprecation_effective_at"])
            ),
            sequence_validation_mode=str(payload["sequence_validation_mode"]),
            rate_limit_backoff_policy_id=str(payload["rate_limit_backoff_policy_id"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise NoTradeObservationError("No-trade health policy values are invalid") from exc
    _validate_health_policy_contract(policy)
    return policy


def load_credentials_from_environment(
    environment: Mapping[str, str] | None = None,
) -> OKXPrivateCredentials:
    env = os.environ if environment is None else environment
    required = ("OKX_API_KEY", "OKX_SECRET_KEY", "OKX_PASSPHRASE")
    missing = [name for name in required if not env.get(name)]
    if missing:
        raise NoTradeObservationError(
            "Missing owner-local credential environment variables: " + ", ".join(missing)
        )
    credentials = OKXPrivateCredentials(
        api_key=env["OKX_API_KEY"],
        secret_key=env["OKX_SECRET_KEY"],
        passphrase=env["OKX_PASSPHRASE"],
    )
    credentials.validate()
    return credentials


def fee_queries() -> tuple[FeeRateQuery, ...]:
    queries = (
        FeeRateQuery(instrument_type=InstrumentType.SPOT, instrument_id=SPOT_INSTRUMENT_ID),
        FeeRateQuery(
            instrument_type=InstrumentType.SWAP,
            instrument_family=SWAP_INSTRUMENT_FAMILY,
        ),
    )
    for query in queries:
        query.validate()
    return queries


def build_fee_request_path(query: FeeRateQuery) -> str:
    query.validate()
    if query.instrument_type is InstrumentType.SPOT:
        parameters = (("instType", "SPOT"), ("instId", SPOT_INSTRUMENT_ID))
    else:
        parameters = (("instType", "SWAP"), ("instFamily", SWAP_INSTRUMENT_FAMILY))
    return f"{ACCOUNT_FEE_ENDPOINT}?{urlencode(parameters)}"


def sign_private_get_request(
    *,
    credentials: OKXPrivateCredentials,
    timestamp: datetime,
    request_path: str,
) -> Mapping[str, str]:
    credentials.validate()
    timestamp_utc = _aware_utc(timestamp, field="private request timestamp")
    if not request_path.startswith(f"{ACCOUNT_FEE_ENDPOINT}?"):
        raise NoTradeObservationError("Private request path is outside the fee endpoint contract")
    if any(fragment in request_path for fragment in FORBIDDEN_PRIVATE_ENDPOINT_FRAGMENTS):
        raise NoTradeObservationError("Order-capable or account-mutating endpoint is forbidden")
    timestamp_text = timestamp_utc.isoformat(timespec="milliseconds").replace("+00:00", "Z")
    prehash = f"{timestamp_text}GET{request_path}".encode()
    digest = hmac.new(credentials.secret_key.encode("utf-8"), prehash, hashlib.sha256).digest()
    signature = base64.b64encode(digest).decode("ascii")
    return {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "OK-ACCESS-KEY": credentials.api_key,
        "OK-ACCESS-SIGN": signature,
        "OK-ACCESS-TIMESTAMP": timestamp_text,
        "OK-ACCESS-PASSPHRASE": credentials.passphrase,
        "User-Agent": "Emad211-Trade-bot-no-trade-observation/1.0",
    }


def fetch_private_fee_response(
    *,
    api_domain: str,
    query: FeeRateQuery,
    credentials: OKXPrivateCredentials,
    timeout_seconds: float = 30.0,
) -> PrivateTimedHTTPResponse:
    if api_domain not in ALLOWED_API_DOMAINS:
        raise NoTradeObservationError("API domain is outside the frozen allowlist")
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    request_path = build_fee_request_path(query)
    request_started_at = datetime.now(UTC)
    headers = sign_private_get_request(
        credentials=credentials,
        timestamp=request_started_at,
        request_path=request_path,
    )
    request = Request(f"https://{api_domain}{request_path}", headers=dict(headers), method="GET")
    opener = _private_fee_opener()
    with opener.open(request, timeout=timeout_seconds) as response:
        body = response.read(MAX_PRIVATE_RESPONSE_BYTES + 1)
        status_code = int(response.status)
        content_type = response.headers.get("Content-Type", "")
        final_url = response.geturl()
    response_received_at = datetime.now(UTC)
    if len(body) > MAX_PRIVATE_RESPONSE_BYTES:
        raise NoTradeObservationError("Private fee response exceeded the byte guard")
    parsed = urlsplit(final_url)
    if parsed.scheme != "https" or parsed.hostname != api_domain:
        raise NoTradeObservationError("Private response redirected outside the frozen API domain")
    if parsed.path not in ALLOWED_PRIVATE_ENDPOINTS:
        raise NoTradeObservationError("Private response path is outside the fee endpoint allowlist")
    return PrivateTimedHTTPResponse(
        body=body,
        status_code=status_code,
        content_type=content_type,
        final_url=final_url,
        request_started_at=request_started_at,
        response_received_at=response_received_at,
    )


def parse_fee_snapshot(
    *, query: FeeRateQuery, response: PrivateTimedHTTPResponse
) -> AccountFeeRateSnapshot:
    query.validate()
    parsed_url = urlsplit(response.final_url)
    expected_path = build_fee_request_path(query)
    expected_query = tuple(parse_qsl(urlsplit(expected_path).query, keep_blank_values=True))
    observed_query = tuple(parse_qsl(parsed_url.query, keep_blank_values=True))
    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname not in ALLOWED_API_DOMAINS
        or parsed_url.path != ACCOUNT_FEE_ENDPOINT
        or observed_query != expected_query
    ):
        raise NoTradeObservationError("Fee response URL differs from the frozen request contract")
    request_time = _aware_utc(response.request_started_at, field="fee request start")
    response_time = _aware_utc(response.response_received_at, field="fee response time")
    if response_time < request_time:
        raise NoTradeObservationError("Fee request clocks are invalid")
    if response.status_code != 200:
        raise NoTradeObservationError(f"Fee endpoint returned HTTP {response.status_code}")
    if not response.body or len(response.body) > MAX_PRIVATE_RESPONSE_BYTES:
        raise NoTradeObservationError("Fee endpoint response is empty or oversized")
    if "json" not in response.content_type.casefold():
        raise NoTradeObservationError("Fee endpoint content type is not JSON")
    try:
        decoded: Any = json.loads(response.body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NoTradeObservationError("Fee endpoint response is not valid UTF-8 JSON") from exc
    if not isinstance(decoded, dict):
        raise NoTradeObservationError("Fee response must be a JSON object")
    payload = cast(Mapping[str, Any], decoded)
    if str(payload.get("code")) != "0" or str(payload.get("msg")) != "":
        raise NoTradeObservationError("OKX returned an unsuccessful fee response")
    data = payload.get("data")
    if not isinstance(data, list) or len(data) != 1 or not isinstance(data[0], dict):
        raise NoTradeObservationError("Fee response must contain exactly one row")
    row = cast(Mapping[str, Any], data[0])
    if str(row.get("instType")) != query.instrument_type.value:
        raise NoTradeObservationError("Fee response instrument type differs from the query")
    snapshot = AccountFeeRateSnapshot(
        query=query,
        level=str(row.get("level", "")),
        rule_type=str(row.get("ruleType", "")),
        response_timestamp_ms=_parse_timestamp_ms(row.get("ts")),
        maker=_optional_decimal(row.get("maker")),
        taker=_optional_decimal(row.get("taker")),
        maker_u=_optional_decimal(row.get("makerU")),
        taker_u=_optional_decimal(row.get("takerU")),
        maker_usdc=_optional_decimal(row.get("makerUSDC")),
        taker_usdc=_optional_decimal(row.get("takerUSDC")),
        open_api_reflects_zero_fee_exceptions=False,
    )
    snapshot.validate()
    return snapshot


def require_admitted_public_batch(
    health_results: Sequence[RestHealthResult],
    *,
    policy: SourceHealthPolicy,
) -> BatchAdmissionResult:
    admission = admit_sampling_batch(health_results, policy=policy)
    if admission.decision is not BatchDecision.ADMIT_PRIVATE_BATCH:
        raise NoTradeObservationError(
            f"Public batch failed health admission: {admission.decision.value}/{admission.state.value}"
        )
    if admission.cross_source_provider_time_skew_ms is None:
        raise NoTradeObservationError("Admitted batch lacks cross-source skew evidence")
    return admission


def execute_real_no_trade_observation(
    config: NoTradeObservationConfig,
    *,
    credentials: OKXPrivateCredentials,
) -> NoTradeObservationResult:
    if config.mode is not ObservationMode.OWNER_REAL_NETWORK:
        raise NoTradeObservationError("Real executor requires OWNER_REAL_NETWORK mode")
    return _execute_observation(
        config,
        credentials=credentials,
        private_fetcher=lambda query: fetch_private_fee_response(
            api_domain=config.api_domain,
            query=query,
            credentials=credentials,
        ),
        public_fetcher=fetch_public_response,
        now_provider=lambda: datetime.now(UTC),
    )


def execute_synthetic_no_trade_observation_for_validation(
    config: NoTradeObservationConfig,
    *,
    credentials: OKXPrivateCredentials,
    private_fetcher: Callable[[FeeRateQuery], PrivateTimedHTTPResponse],
    public_fetcher: Callable[[str], TimedHTTPResponse],
    now_provider: Callable[[], datetime],
) -> NoTradeObservationResult:
    if config.mode is not ObservationMode.SYNTHETIC_INJECTED:
        raise NoTradeObservationError("Synthetic executor requires SYNTHETIC_INJECTED mode")
    if public_fetcher is fetch_public_response:
        raise NoTradeObservationError("Synthetic validation cannot use the real public fetcher")
    return _execute_observation(
        config,
        credentials=credentials,
        private_fetcher=private_fetcher,
        public_fetcher=public_fetcher,
        now_provider=now_provider,
    )


def _execute_observation(
    config: NoTradeObservationConfig,
    *,
    credentials: OKXPrivateCredentials,
    private_fetcher: Callable[[FeeRateQuery], PrivateTimedHTTPResponse],
    public_fetcher: Callable[[str], TimedHTTPResponse],
    now_provider: Callable[[], datetime],
) -> NoTradeObservationResult:
    config.validate()
    credentials.validate()
    fee_bundle = _collect_fee_bundle(
        config=config,
        private_fetcher=private_fetcher,
        now_provider=now_provider,
    )
    raw_by_source, clocks_by_source, health_results = _collect_public_batch(
        config=config,
        public_fetcher=public_fetcher,
        now_provider=now_provider,
    )
    admission = require_admitted_public_batch(health_results, policy=config.health_policy)
    admission_skew_ms = admission.cross_source_provider_time_skew_ms
    if admission_skew_ms is None:
        raise NoTradeObservationError("Admitted public batch is missing cross-source skew evidence")

    runner_config = config.owner_runner_config
    store = _store_from_runner_config(runner_config)
    execution_mode = (
        SamplingExecutionMode.OWNER_CONTROLLED_REAL
        if config.mode is ObservationMode.OWNER_REAL_NETWORK
        else SamplingExecutionMode.SYNTHETIC_VALIDATION
    )
    committed_at = max(
        _aware_utc(now_provider(), field="commit time"),
        *(clock.research_available_at for clock in clocks_by_source.values()),
    )
    manifest = retain_sampling_batch(
        store=store,
        raw_by_source=raw_by_source,
        clocks_by_source=clocks_by_source,
        authorization=_authorization_from_runner_config(runner_config),
        execution_mode=execution_mode,
        requested_retention_days=config.requested_retention_days,
        now=committed_at,
    )

    fee_written = False
    manifest_written = False
    try:
        _atomic_write(config.private_fee_snapshot_output, fee_bundle.canonical_bytes, mode=0o600)
        fee_written = True
        manifest_bytes = safe_manifest_json(manifest).encode("utf-8")
        _atomic_write(config.safe_batch_manifest_output, manifest_bytes, mode=0o600)
        manifest_written = True
        receipt = _build_safe_receipt(
            config=config,
            fee_bundle=fee_bundle,
            health_results=health_results,
            admission_skew_ms=admission_skew_ms,
            provider_timestamps_monotonic=bool(
                admission.provider_timestamps_monotonic_in_input_order
            ),
            manifest=manifest,
            manifest_bytes=manifest_bytes,
        )
        receipt_bytes = (json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
        _assert_safe_receipt_bytes(receipt_bytes)
        _atomic_write(config.safe_observation_receipt_output, receipt_bytes, mode=0o600)
    except BaseException as exc:
        if fee_written:
            _best_effort_unlink(config.private_fee_snapshot_output)
        if manifest_written:
            _best_effort_unlink(config.safe_batch_manifest_output)
        _best_effort_unlink(config.safe_observation_receipt_output)
        try:
            delete_sampling_batch(
                store=store,
                manifest=manifest,
                reason="NO_TRADE_OBSERVATION_ROLLBACK",
                now=_aware_utc(now_provider(), field="rollback time"),
            )
        except BaseException as rollback_exc:
            raise NoTradeObservationError(
                "Observation commit failed and private rollback was incomplete"
            ) from rollback_exc
        raise NoTradeObservationError(
            "Observation commit failed; private batch and fee snapshot were rolled back"
        ) from exc

    receipt_bytes = config.safe_observation_receipt_output.read_bytes()
    return NoTradeObservationResult(
        mode=config.mode.value,
        real_public_requests_performed=(config.mode is ObservationMode.OWNER_REAL_NETWORK),
        real_private_fee_requests_performed=(config.mode is ObservationMode.OWNER_REAL_NETWORK),
        orders_sent=False,
        batch_id=manifest.batch_id,
        source_count=manifest.source_count,
        fee_bundle_sha256=fee_bundle.bundle_sha256,
        safe_receipt_sha256=_sha256(receipt_bytes),
        safe_receipt_output=str(config.safe_observation_receipt_output),
        safe_manifest_output=str(config.safe_batch_manifest_output),
        private_fee_snapshot_output=str(config.private_fee_snapshot_output),
    )


def delete_no_trade_observation(
    config: NoTradeDeletionConfig,
) -> Mapping[str, Any]:
    config.validate()
    manifest = load_safe_sampling_manifest(config.safe_batch_manifest_path)
    receipt_payload = _load_json_object(config.safe_observation_receipt_path)
    expected_fee_hash = str(receipt_payload.get("fee_bundle_sha256", ""))
    observed_fee_hash = _sha256(config.private_fee_snapshot_path.read_bytes())
    if expected_fee_hash != observed_fee_hash:
        raise NoTradeObservationError("Private fee snapshot hash differs from the safe receipt")

    store = PrivateRevocableArtifactStore(
        config.private_root,
        repository_root=config.repository_root,
        policy=RetentionPolicy(
            policy_id=manifest.policy_id,
            license_snapshot_id=manifest.license_snapshot_id,
            allowed_purpose=ALLOWED_PURPOSE,
            maximum_retention_days=7,
        ),
        attestation=RetentionAttestation(
            encryption_at_rest=config.owner_attestations.encryption_at_rest,
            owner_only_access=config.owner_attestations.owner_only_access,
            backup_and_sync_excluded=config.owner_attestations.backup_and_sync_excluded,
            public_artifact_upload_disabled=(
                config.owner_attestations.public_artifact_upload_disabled
            ),
        ),
    )
    batch_receipt: SafeSamplingBatchDeletionReceipt = delete_sampling_batch(
        store=store,
        manifest=manifest,
        reason=config.reason,
        now=datetime.now(UTC),
    )
    config.private_fee_snapshot_path.unlink()
    fee_exists_after_delete = config.private_fee_snapshot_path.exists()
    safe = {
        "schema_version": "1.0",
        "gate_id": GATE_ID,
        "batch_id": manifest.batch_id,
        "delete_reason": config.reason.strip(),
        "source_count": batch_receipt.source_count,
        "all_public_raw_deleted": batch_receipt.all_raw_deleted,
        "all_public_leases_deleted": batch_receipt.all_leases_deleted,
        "private_fee_snapshot_integrity_matched": True,
        "private_fee_snapshot_exists_after_delete": fee_exists_after_delete,
        "secure_erase_claimed": False,
        "market_values_present": False,
        "fee_values_present": False,
    }
    if fee_exists_after_delete:
        raise NoTradeObservationError("Private fee snapshot deletion did not complete")
    _atomic_write(
        config.safe_deletion_receipt_output,
        (json.dumps(safe, indent=2, sort_keys=True) + "\n").encode("utf-8"),
        mode=0o600,
    )
    return safe


def _collect_fee_bundle(
    *,
    config: NoTradeObservationConfig,
    private_fetcher: Callable[[FeeRateQuery], PrivateTimedHTTPResponse],
    now_provider: Callable[[], datetime],
) -> PrivateFeeSnapshotBundle:
    snapshots: list[AccountFeeRateSnapshot] = []
    hashes: dict[str, str] = {}
    for query in fee_queries():
        response = private_fetcher(query)
        snapshot = parse_fee_snapshot(query=query, response=response)
        query_id = _fee_query_id(query)
        snapshots.append(snapshot)
        hashes[query_id] = _sha256(response.body)
    return PrivateFeeSnapshotBundle(
        schema_version="1.0",
        contract_id="OKX_ACCOUNT_FEE_SNAPSHOT_PRIVATE_V1",
        captured_at_utc=_aware_utc(now_provider(), field="fee capture time").isoformat(),
        api_domain=config.api_domain,
        snapshots=tuple(snapshots),
        response_sha256_by_query=hashes,
    )


def _collect_public_batch(
    *,
    config: NoTradeObservationConfig,
    public_fetcher: Callable[[str], TimedHTTPResponse],
    now_provider: Callable[[], datetime],
) -> tuple[dict[str, bytes], dict[str, SamplingClock], tuple[RestHealthResult, ...]]:
    raw_by_source: dict[str, bytes] = {}
    clocks_by_source: dict[str, SamplingClock] = {}
    health_results: list[RestHealthResult] = []
    for contract in SOURCE_CONTRACTS:
        url = build_url(contract)
        timed = public_fetcher(url)
        available = max(
            _aware_utc(now_provider(), field="research available time"),
            _aware_utc(timed.response_received_at, field="response_received_at"),
        )
        source = validate_source_response(
            contract=contract,
            response=timed.response,
            request_url=url,
            request_started_at=timed.request_started_at,
            response_received_at=timed.response_received_at,
            research_available_at=available,
        )
        identity_sha = _canonical_sha256(source.identity_fields)
        rest = RestObservation(
            source_id=source.source_id,
            request_started_at=_parse_iso_utc(source.request_started_at),
            response_received_at=_parse_iso_utc(source.response_received_at),
            provider_timestamp=_parse_iso_utc(source.provider_timestamp_utc),
            research_available_at=_parse_iso_utc(source.research_available_at),
            http_status=source.http_status,
            provider_code=source.application_code,
            row_count=source.row_count,
            response_sha256=source.response_sha256,
            schema_sha256=source.schema_sha256,
            identity_sha256=identity_sha,
        )
        health = evaluate_rest_observation(rest, policy=config.health_policy)
        health_results.append(health)
        raw_by_source[source.source_id] = timed.response.body
        clocks_by_source[source.source_id] = SamplingClock(
            request_started_at=rest.request_started_at,
            response_received_at=rest.response_received_at,
            provider_timestamp_ms=source.provider_timestamp_ms,
            research_available_at=rest.research_available_at,
        )
    return raw_by_source, clocks_by_source, tuple(health_results)


def _build_safe_receipt(
    *,
    config: NoTradeObservationConfig,
    fee_bundle: PrivateFeeSnapshotBundle,
    health_results: Sequence[RestHealthResult],
    admission_skew_ms: int,
    provider_timestamps_monotonic: bool,
    manifest: SafeSamplingBatchManifest,
    manifest_bytes: bytes,
) -> SafeNoTradeObservationReceipt:
    base = {
        "code_head_sha": config.code_head_sha,
        "mode": config.mode.value,
        "fee_bundle_sha256": fee_bundle.bundle_sha256,
        "health_policy_fingerprint_sha256": (config.health_policy.policy_fingerprint_sha256),
        "private_batch_id": manifest.batch_id,
        "private_batch_manifest_sha256": _sha256(manifest_bytes),
    }
    receipt_id = _canonical_sha256(base)
    return SafeNoTradeObservationReceipt(
        schema_version="1.0",
        gate_id=GATE_ID,
        receipt_id=receipt_id,
        code_head_sha=config.code_head_sha,
        mode=config.mode.value,
        synthetic_validation_only=(config.mode is ObservationMode.SYNTHETIC_INJECTED),
        real_public_requests_performed=(config.mode is ObservationMode.OWNER_REAL_NETWORK),
        real_private_fee_requests_performed=(config.mode is ObservationMode.OWNER_REAL_NETWORK),
        orders_sent=False,
        trade_permission_used=False,
        withdraw_permission_used=False,
        private_endpoint_paths=(ACCOUNT_FEE_ENDPOINT,),
        fee_query_ids=tuple(_fee_query_id(query) for query in fee_queries()),
        fee_bundle_sha256=fee_bundle.bundle_sha256,
        fee_snapshots=fee_bundle.safe_identities,
        health_policy_id=config.health_policy.policy_id,
        health_policy_fingerprint_sha256=(config.health_policy.policy_fingerprint_sha256),
        health_state_by_source={result.source_id: result.state.value for result in health_results},
        public_response_sha256_by_source={
            result.source_id: result.response_sha256 for result in health_results
        },
        public_schema_sha256_by_source={
            result.source_id: result.schema_sha256 for result in health_results
        },
        public_identity_sha256_by_source={
            result.source_id: result.identity_sha256 for result in health_results
        },
        batch_decision=BatchDecision.ADMIT_PRIVATE_BATCH.value,
        batch_state="HEALTHY",
        cross_source_provider_time_skew_ms=admission_skew_ms,
        provider_timestamps_monotonic_in_request_order=provider_timestamps_monotonic,
        private_batch_id=manifest.batch_id,
        private_batch_manifest_sha256=_sha256(manifest_bytes),
        private_source_count=manifest.source_count,
        requested_retention_days=config.requested_retention_days,
        credentials_present_in_receipt=False,
        fee_values_present_in_receipt=False,
        market_values_present_in_receipt=False,
        basis_computation_authorized=False,
        funding_pnl_computation_authorized=False,
        returns_computation_authorized=False,
        transaction_cost_estimation_authorized=False,
        strategy_testing_authorized=False,
        paper_or_live_trading_authorized=False,
        report_2_4_authorized=False,
        economic_edge_verdict="INCONCLUSIVE",
    )


def _store_from_runner_config(
    config: OwnerSamplingRunnerConfig,
) -> PrivateRevocableArtifactStore:
    return PrivateRevocableArtifactStore(
        config.private_root,
        repository_root=config.repository_root,
        policy=RetentionPolicy(
            policy_id=config.policy_id,
            license_snapshot_id=config.license_snapshot_id,
            allowed_purpose=ALLOWED_PURPOSE,
            maximum_retention_days=7,
        ),
        attestation=RetentionAttestation(
            encryption_at_rest=config.attestations.encryption_at_rest,
            owner_only_access=config.attestations.owner_only_access,
            backup_and_sync_excluded=config.attestations.backup_and_sync_excluded,
            public_artifact_upload_disabled=(config.attestations.public_artifact_upload_disabled),
        ),
    )


def _authorization_from_runner_config(
    config: OwnerSamplingRunnerConfig,
) -> OwnerSamplingAuthorization:
    real = config.mode.value == "OWNER_REAL_NETWORK"
    return OwnerSamplingAuthorization(
        terms_reviewed=config.attestations.terms_reviewed,
        personal_noncommercial_use=config.attestations.personal_noncommercial_use,
        reasonable_rate_and_scale=config.attestations.reasonable_rate_and_scale,
        redistribution_disabled=config.attestations.redistribution_disabled,
        owner_controlled_private_storage=(
            config.attestations.owner_controlled_private_storage if real else False
        ),
        owner_controlled_encryption_keys=(
            config.attestations.owner_controlled_encryption_keys if real else False
        ),
        real_execution_owner_confirmed=(
            config.attestations.real_execution_owner_confirmed if real else False
        ),
    )


def _validate_health_policy_contract(policy: SourceHealthPolicy) -> None:
    policy.validate()
    if set(policy.required_source_ids) != set(EXPECTED_SCHEMA_SHA256):
        raise NoTradeObservationError(
            "Health policy source set differs from the four-source contract"
        )
    if dict(policy.expected_schema_sha256) != EXPECTED_SCHEMA_SHA256:
        raise NoTradeObservationError(
            "Health policy schema fingerprints differ from the frozen contract"
        )
    if dict(policy.expected_identity_sha256) != EXPECTED_IDENTITY_SHA256:
        raise NoTradeObservationError(
            "Health policy identity fingerprints differ from the frozen contract"
        )


def _fee_query_id(query: FeeRateQuery) -> str:
    query.validate()
    return (
        "SPOT_BTC_USDT" if query.instrument_type is InstrumentType.SPOT else "SWAP_BTC_USDT_FAMILY"
    )


def _private_snapshot_payload(snapshot: AccountFeeRateSnapshot) -> Mapping[str, Any]:
    snapshot.validate()
    return {
        "query_id": _fee_query_id(snapshot.query),
        "instrument_type": snapshot.query.instrument_type.value,
        "instrument_id": snapshot.query.instrument_id,
        "instrument_family": snapshot.query.instrument_family,
        "level": snapshot.level,
        "rule_type": snapshot.rule_type,
        "response_timestamp_ms": snapshot.response_timestamp_ms,
        "maker": _decimal_text(snapshot.maker),
        "taker": _decimal_text(snapshot.taker),
        "maker_u": _decimal_text(snapshot.maker_u),
        "taker_u": _decimal_text(snapshot.taker_u),
        "maker_usdc": _decimal_text(snapshot.maker_usdc),
        "taker_usdc": _decimal_text(snapshot.taker_usdc),
        "open_api_reflects_zero_fee_exceptions": (snapshot.open_api_reflects_zero_fee_exceptions),
    }


def _decimal_text(value: Decimal | None) -> str | None:
    return None if value is None else format(value, "f")


def _optional_decimal(value: object) -> Decimal | None:
    if value is None or str(value) == "":
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise NoTradeObservationError("Invalid decimal in fee response") from exc
    if not result.is_finite():
        raise NoTradeObservationError("Non-finite decimal in fee response")
    return result


def _parse_timestamp_ms(value: object) -> int:
    try:
        result = int(str(value))
    except ValueError as exc:
        raise NoTradeObservationError("Invalid fee response timestamp") from exc
    if result < 10**12 or result >= 10**14:
        raise NoTradeObservationError("Fee response timestamp is not Unix milliseconds")
    return result


def _aware_utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise NoTradeObservationError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)


def _parse_iso_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return _aware_utc(parsed, field="ISO timestamp")


def _is_git_sha(value: str) -> bool:
    return len(value) == 40 and all(character in "0123456789abcdef" for character in value)


def _canonical_sha256(value: Any) -> str:
    return _sha256(json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _atomic_write(path: Path, data: bytes, *, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, mode)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _load_json_object(path: Path) -> Mapping[str, Any]:
    try:
        decoded: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NoTradeObservationError(f"Cannot read JSON object: {path.name}") from exc
    if not isinstance(decoded, dict):
        raise NoTradeObservationError(f"JSON file is not an object: {path.name}")
    return cast(Mapping[str, Any], decoded)


def _best_effort_unlink(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        return


def _safe_path_exists(path: Path) -> bool:
    try:
        return path.exists()
    except OSError:
        return False


def _assert_safe_receipt_bytes(payload: bytes) -> None:
    lower = payload.lower()
    forbidden_tokens = (
        b'"ok-access-key":',
        b'"ok-access-sign":',
        b'"ok-access-passphrase":',
        b'"api_key":',
        b'"secret_key":',
        b'"passphrase":',
        b'"maker":',
        b'"taker":',
        b'"maker_u":',
        b'"taker_u":',
        b'"askpx":',
        b'"bidpx":',
        b'"markpx":',
        b'"idxpx":',
        b'"price":',
        b'"balance":',
        b'"pnl":',
    )
    leaked = [token.decode("ascii") for token in forbidden_tokens if token in lower]
    if leaked:
        raise NoTradeObservationError(
            "Safe receipt contains forbidden value-bearing keys: " + ", ".join(leaked)
        )
