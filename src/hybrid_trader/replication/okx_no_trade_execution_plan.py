"""Sealed one-time execution plans for owner-local OKX no-trade observations."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import stat
import subprocess
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass, fields, replace
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol, cast

from hybrid_trader.replication.okx_no_trade_observation import (
    GATE_ID as NO_TRADE_GATE_ID,
)
from hybrid_trader.replication.okx_no_trade_observation import (
    NoTradeObservationConfig,
    NoTradeObservationResult,
    OKXPrivateCredentials,
    execute_real_no_trade_observation,
    fee_queries,
)
from hybrid_trader.replication.okx_price_linkage_probe import SOURCE_CONTRACTS

SEALED_PLAN_GATE_ID = "OKX_OWNER_LOCAL_SEALED_EXECUTION_PLAN_V1"
DEFAULT_PLAN_TTL_SECONDS = 600
MAX_PLAN_TTL_SECONDS = 1800
PLAN_SCHEMA_VERSION = "1.0"
CLAIM_SCHEMA_VERSION = "1.0"


class SealedExecutionPlanError(RuntimeError):
    """Raised when a sealed preflight plan or one-time claim fails closed."""


class ClaimState(StrEnum):
    CLAIMED = "CLAIMED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class GitWorkspaceState:
    repository_root: str
    actual_head_sha: str
    clean_worktree: bool


@dataclass(frozen=True)
class SealedExecutionPlan:
    schema_version: str
    gate_id: str
    predecessor_gate_id: str
    plan_id: str
    nonce_hex: str
    created_at_utc: str
    expires_at_utc: str
    actual_git_head_sha: str
    reviewed_git_head_sha: str
    clean_worktree: bool
    policy_id: str
    policy_fingerprint_sha256: str
    configuration_fingerprint_sha256: str
    owner_path_fingerprints: Mapping[str, str]
    credential_binding_hmac_sha256: str
    plan_authenticator_hmac_sha256: str
    fee_query_paths: tuple[str, ...]
    required_public_source_ids: tuple[str, ...]
    network_request_performed: bool
    credentials_present_in_plan: bool
    owner_path_values_present_in_plan: bool
    orders_sent: bool
    trade_permission_used: bool
    withdraw_permission_used: bool
    basis_computation_authorized: bool
    funding_pnl_computation_authorized: bool
    returns_computation_authorized: bool
    transaction_cost_estimation_authorized: bool
    strategy_testing_authorized: bool
    report_2_4_authorized: bool


@dataclass(frozen=True)
class ExecutionPlanClaim:
    schema_version: str
    gate_id: str
    plan_id: str
    state: str
    claimed_at_utc: str
    finalized_at_utc: str | None
    actual_git_head_sha: str
    configuration_fingerprint_sha256: str
    safe_observation_receipt_sha256: str | None
    failure_type_fingerprint_sha256: str | None
    network_may_have_started: bool
    replay_allowed: bool
    credentials_present_in_claim: bool
    owner_path_values_present_in_claim: bool
    orders_sent: bool
    report_2_4_authorized: bool


@dataclass(frozen=True)
class SealedPlanInputs:
    observation_config: NoTradeObservationConfig
    reviewed_head_sha: str
    plan_output: Path
    claim_output: Path
    safe_deletion_receipt_output: Path
    ttl_seconds: int = DEFAULT_PLAN_TTL_SECONDS

    def validate_paths(self) -> None:
        config = self.observation_config
        config.validate()
        if self.reviewed_head_sha != config.code_head_sha:
            raise SealedExecutionPlanError(
                "reviewed_head_sha must equal the observation config code_head_sha"
            )
        if not 1 <= self.ttl_seconds <= MAX_PLAN_TTL_SECONDS:
            raise SealedExecutionPlanError(
                f"ttl_seconds must be between 1 and {MAX_PLAN_TTL_SECONDS}"
            )
        repository_root = config.repository_root.expanduser().resolve(strict=False)
        private_root = config.private_root.expanduser().resolve(strict=False)
        for field_name, path in (
            ("plan_output", self.plan_output),
            ("claim_output", self.claim_output),
            ("safe_deletion_receipt_output", self.safe_deletion_receipt_output),
        ):
            resolved = path.expanduser().resolve(strict=False)
            if resolved.suffix.casefold() != ".json":
                raise SealedExecutionPlanError(f"{field_name} must be a JSON file")
            if resolved == repository_root or resolved.is_relative_to(repository_root):
                raise SealedExecutionPlanError(f"{field_name} must be outside the repository")
            if resolved == private_root or resolved.is_relative_to(private_root):
                raise SealedExecutionPlanError(f"{field_name} must be outside private raw storage")
        if _path_exists(self.plan_output):
            raise SealedExecutionPlanError("plan_output already exists")
        if _path_exists(self.claim_output):
            raise SealedExecutionPlanError("claim_output already exists")
        if _path_exists(self.safe_deletion_receipt_output):
            raise SealedExecutionPlanError("safe_deletion_receipt_output already exists")


class ObservationExecutor(Protocol):
    def __call__(
        self,
        config: NoTradeObservationConfig,
        *,
        credentials: OKXPrivateCredentials,
    ) -> NoTradeObservationResult: ...


GitResolver = Callable[[Path], GitWorkspaceState]
NonceFactory = Callable[[], bytes]


def resolve_git_workspace(repository_root: Path) -> GitWorkspaceState:
    """Resolve the exact Git top level, head, and clean-worktree state."""

    requested = repository_root.expanduser().resolve(strict=True)
    top_level = _run_git(requested, ("rev-parse", "--show-toplevel"))
    resolved_top = Path(top_level).expanduser().resolve(strict=True)
    if resolved_top != requested:
        raise SealedExecutionPlanError(
            "repository_root does not equal the resolved Git top-level directory"
        )
    head = _run_git(requested, ("rev-parse", "HEAD"))
    if not _is_git_sha(head):
        raise SealedExecutionPlanError("Git returned an invalid HEAD SHA")
    status_output = _run_git(
        requested,
        ("status", "--porcelain=v1", "--untracked-files=normal"),
        allow_empty=True,
    )
    return GitWorkspaceState(
        repository_root=str(resolved_top),
        actual_head_sha=head,
        clean_worktree=(status_output == ""),
    )


def create_sealed_execution_plan(
    inputs: SealedPlanInputs,
    *,
    credentials: OKXPrivateCredentials,
    now: datetime | None = None,
    git_resolver: GitResolver = resolve_git_workspace,
    nonce_factory: NonceFactory = lambda: secrets.token_bytes(32),
) -> SealedExecutionPlan:
    """Create one short-lived owner-local plan without network access."""

    inputs.validate_paths()
    credentials.validate()
    observed_at = _aware_utc(now or datetime.now(UTC), field="plan creation time")
    workspace = git_resolver(inputs.observation_config.repository_root)
    _require_workspace_binding(
        workspace,
        expected_repository_root=inputs.observation_config.repository_root,
        reviewed_head_sha=inputs.reviewed_head_sha,
        config_head_sha=inputs.observation_config.code_head_sha,
    )
    nonce = nonce_factory()
    if len(nonce) < 32:
        raise SealedExecutionPlanError("Plan nonce must contain at least 32 bytes")
    nonce_hex = nonce.hex()
    expires_at = observed_at + timedelta(seconds=inputs.ttl_seconds)
    path_fingerprints = _owner_path_fingerprints(inputs, credentials, nonce_hex)
    config_fingerprint = _configuration_fingerprint(
        inputs,
        workspace=workspace,
        path_fingerprints=path_fingerprints,
    )
    safe_core = _safe_plan_core(
        inputs,
        workspace=workspace,
        nonce_hex=nonce_hex,
        created_at=observed_at,
        expires_at=expires_at,
        path_fingerprints=path_fingerprints,
        configuration_fingerprint=config_fingerprint,
    )
    plan_id = _canonical_sha256(safe_core)
    credential_binding = _credential_binding(
        credentials,
        plan_id=plan_id,
        nonce_hex=nonce_hex,
    )
    authenticated_core = {
        **safe_core,
        "plan_id": plan_id,
        "credential_binding_hmac_sha256": credential_binding,
    }
    authenticator = _hmac_sha256(credentials.secret_key, authenticated_core)
    plan = SealedExecutionPlan(
        **authenticated_core,
        plan_authenticator_hmac_sha256=authenticator,
    )
    _atomic_create_json(inputs.plan_output, asdict(plan), mode=0o600)
    return plan


def verify_sealed_execution_plan(
    inputs: SealedPlanInputs,
    *,
    plan_path: Path,
    credentials: OKXPrivateCredentials,
    now: datetime | None = None,
    git_resolver: GitResolver = resolve_git_workspace,
) -> SealedExecutionPlan:
    """Verify plan authenticity, expiry, workspace, and exact configuration binding."""

    credentials.validate()
    plan = load_sealed_execution_plan(plan_path)
    assert_private_file_mode(plan_path)
    inputs_for_observe = replace(inputs, plan_output=plan_path)
    _validate_observe_paths(inputs_for_observe)
    observed_at = _aware_utc(now or datetime.now(UTC), field="plan verification time")
    workspace = git_resolver(inputs.observation_config.repository_root)
    _require_workspace_binding(
        workspace,
        expected_repository_root=inputs.observation_config.repository_root,
        reviewed_head_sha=inputs.reviewed_head_sha,
        config_head_sha=inputs.observation_config.code_head_sha,
    )
    if plan.actual_git_head_sha != workspace.actual_head_sha:
        raise SealedExecutionPlanError("Plan actual Git head differs from the current head")
    if plan.reviewed_git_head_sha != inputs.reviewed_head_sha:
        raise SealedExecutionPlanError("Plan reviewed Git head differs from the requested head")
    created_at = _parse_iso_utc(plan.created_at_utc, field="plan created_at")
    expires_at = _parse_iso_utc(plan.expires_at_utc, field="plan expires_at")
    if expires_at <= created_at:
        raise SealedExecutionPlanError("Plan expiry must be after creation")
    if created_at > observed_at + timedelta(seconds=5):
        raise SealedExecutionPlanError("Plan creation time is unexpectedly in the future")
    if observed_at > expires_at:
        raise SealedExecutionPlanError("Sealed execution plan has expired")
    if expires_at - created_at > timedelta(seconds=MAX_PLAN_TTL_SECONDS):
        raise SealedExecutionPlanError("Sealed execution plan exceeds the maximum TTL")

    expected_binding = _credential_binding(
        credentials,
        plan_id=plan.plan_id,
        nonce_hex=plan.nonce_hex,
    )
    if not hmac.compare_digest(plan.credential_binding_hmac_sha256, expected_binding):
        raise SealedExecutionPlanError("Credential binding differs from sealed preflight")
    expected_path_fingerprints = _owner_path_fingerprints(
        inputs,
        credentials,
        plan.nonce_hex,
    )
    if dict(plan.owner_path_fingerprints) != expected_path_fingerprints:
        raise SealedExecutionPlanError("Owner path binding differs from sealed preflight")
    expected_config = _configuration_fingerprint(
        inputs,
        workspace=workspace,
        path_fingerprints=expected_path_fingerprints,
    )
    if plan.configuration_fingerprint_sha256 != expected_config:
        raise SealedExecutionPlanError("Observation configuration differs from sealed preflight")
    core = _plan_authenticated_core(plan)
    expected_authenticator = _hmac_sha256(credentials.secret_key, core)
    if not hmac.compare_digest(plan.plan_authenticator_hmac_sha256, expected_authenticator):
        raise SealedExecutionPlanError("Sealed execution plan authentication failed")
    expected_plan_id = _canonical_sha256(_plan_safe_core_from_plan(plan))
    if plan.plan_id != expected_plan_id:
        raise SealedExecutionPlanError("Sealed execution plan ID is inconsistent")
    _assert_plan_closed_fields(plan)
    return plan


def execute_sealed_real_no_trade_observation(
    inputs: SealedPlanInputs,
    *,
    plan_path: Path,
    credentials: OKXPrivateCredentials,
    executor: ObservationExecutor = execute_real_no_trade_observation,
    now: datetime | None = None,
    git_resolver: GitResolver = resolve_git_workspace,
) -> NoTradeObservationResult:
    """Consume a plan before network access and finalize its claim after execution."""

    observed_at = _aware_utc(now or datetime.now(UTC), field="claim time")
    plan = verify_sealed_execution_plan(
        inputs,
        plan_path=plan_path,
        credentials=credentials,
        now=observed_at,
        git_resolver=git_resolver,
    )
    claim = ExecutionPlanClaim(
        schema_version=CLAIM_SCHEMA_VERSION,
        gate_id=SEALED_PLAN_GATE_ID,
        plan_id=plan.plan_id,
        state=ClaimState.CLAIMED.value,
        claimed_at_utc=observed_at.isoformat(),
        finalized_at_utc=None,
        actual_git_head_sha=plan.actual_git_head_sha,
        configuration_fingerprint_sha256=plan.configuration_fingerprint_sha256,
        safe_observation_receipt_sha256=None,
        failure_type_fingerprint_sha256=None,
        network_may_have_started=False,
        replay_allowed=False,
        credentials_present_in_claim=False,
        owner_path_values_present_in_claim=False,
        orders_sent=False,
        report_2_4_authorized=False,
    )
    _atomic_create_json(inputs.claim_output, asdict(claim), mode=0o600)
    network_claim = replace(claim, network_may_have_started=True)
    _atomic_replace_json(inputs.claim_output, asdict(network_claim), mode=0o600)
    try:
        result = executor(inputs.observation_config, credentials=credentials)
        _require_sha256(
            result.safe_receipt_sha256,
            field="safe observation receipt SHA-256",
        )
    except BaseException as exc:
        failed = replace(
            network_claim,
            state=ClaimState.FAILED.value,
            finalized_at_utc=datetime.now(UTC).isoformat(),
            failure_type_fingerprint_sha256=_sha256(type(exc).__name__.encode("utf-8")),
        )
        _atomic_replace_json(inputs.claim_output, asdict(failed), mode=0o600)
        raise
    completed = replace(
        network_claim,
        state=ClaimState.COMPLETED.value,
        finalized_at_utc=datetime.now(UTC).isoformat(),
        safe_observation_receipt_sha256=result.safe_receipt_sha256,
    )
    _atomic_replace_json(inputs.claim_output, asdict(completed), mode=0o600)
    return result


def load_sealed_execution_plan(path: Path) -> SealedExecutionPlan:
    value = _load_json_object(path, label="sealed execution plan")
    expected_fields = {item.name for item in fields(SealedExecutionPlan)}
    if set(value) != expected_fields:
        raise SealedExecutionPlanError("Sealed execution plan contains unexpected fields")
    try:
        normalized = {
            **value,
            "owner_path_fingerprints": dict(value["owner_path_fingerprints"]),
            "fee_query_paths": tuple(value["fee_query_paths"]),
            "required_public_source_ids": tuple(value["required_public_source_ids"]),
        }
        plan = SealedExecutionPlan(**normalized)
    except (TypeError, ValueError) as exc:
        raise SealedExecutionPlanError("Sealed execution plan schema is invalid") from exc
    if len(plan.nonce_hex) != 64 or any(
        character not in "0123456789abcdef" for character in plan.nonce_hex
    ):
        raise SealedExecutionPlanError("Sealed execution plan nonce is invalid")
    return plan


def load_execution_plan_claim(path: Path) -> ExecutionPlanClaim:
    assert_private_file_mode(path)
    value = _load_json_object(path, label="execution plan claim")
    expected_fields = {item.name for item in fields(ExecutionPlanClaim)}
    if set(value) != expected_fields:
        raise SealedExecutionPlanError("Execution plan claim contains unexpected fields")
    try:
        claim = ExecutionPlanClaim(**value)
    except TypeError as exc:
        raise SealedExecutionPlanError("Execution plan claim schema is invalid") from exc
    if claim.schema_version != CLAIM_SCHEMA_VERSION:
        raise SealedExecutionPlanError("Execution plan claim schema version is invalid")
    if claim.gate_id != SEALED_PLAN_GATE_ID:
        raise SealedExecutionPlanError("Execution plan claim gate identity is invalid")
    try:
        ClaimState(claim.state)
    except ValueError as exc:
        raise SealedExecutionPlanError("Execution plan claim state is invalid") from exc
    _require_sha256(claim.plan_id, field="execution plan claim plan ID")
    _require_sha256(
        claim.configuration_fingerprint_sha256,
        field="execution plan claim configuration fingerprint",
    )
    if claim.safe_observation_receipt_sha256 is not None:
        _require_sha256(
            claim.safe_observation_receipt_sha256,
            field="execution plan claim receipt SHA-256",
        )
    if claim.failure_type_fingerprint_sha256 is not None:
        _require_sha256(
            claim.failure_type_fingerprint_sha256,
            field="execution plan claim failure fingerprint",
        )
    if claim.replay_allowed:
        raise SealedExecutionPlanError("Execution plan claim cannot allow replay")
    if claim.credentials_present_in_claim or claim.owner_path_values_present_in_claim:
        raise SealedExecutionPlanError("Execution plan claim violates the safe-evidence boundary")
    if claim.orders_sent or claim.report_2_4_authorized:
        raise SealedExecutionPlanError("Execution plan claim opened a prohibited action")
    return claim


def _safe_plan_core(
    inputs: SealedPlanInputs,
    *,
    workspace: GitWorkspaceState,
    nonce_hex: str,
    created_at: datetime,
    expires_at: datetime,
    path_fingerprints: Mapping[str, str],
    configuration_fingerprint: str,
) -> dict[str, Any]:
    config = inputs.observation_config
    return {
        "schema_version": PLAN_SCHEMA_VERSION,
        "gate_id": SEALED_PLAN_GATE_ID,
        "predecessor_gate_id": NO_TRADE_GATE_ID,
        "nonce_hex": nonce_hex,
        "created_at_utc": created_at.isoformat(),
        "expires_at_utc": expires_at.isoformat(),
        "actual_git_head_sha": workspace.actual_head_sha,
        "reviewed_git_head_sha": inputs.reviewed_head_sha,
        "clean_worktree": workspace.clean_worktree,
        "policy_id": config.health_policy.policy_id,
        "policy_fingerprint_sha256": config.health_policy.policy_fingerprint_sha256,
        "configuration_fingerprint_sha256": configuration_fingerprint,
        "owner_path_fingerprints": dict(sorted(path_fingerprints.items())),
        "fee_query_paths": tuple(_fee_query_paths()),
        "required_public_source_ids": tuple(sorted(c.source_id for c in SOURCE_CONTRACTS)),
        "network_request_performed": False,
        "credentials_present_in_plan": False,
        "owner_path_values_present_in_plan": False,
        "orders_sent": False,
        "trade_permission_used": False,
        "withdraw_permission_used": False,
        "basis_computation_authorized": False,
        "funding_pnl_computation_authorized": False,
        "returns_computation_authorized": False,
        "transaction_cost_estimation_authorized": False,
        "strategy_testing_authorized": False,
        "report_2_4_authorized": False,
    }


def _configuration_fingerprint(
    inputs: SealedPlanInputs,
    *,
    workspace: GitWorkspaceState,
    path_fingerprints: Mapping[str, str],
) -> str:
    config = inputs.observation_config
    payload = {
        "actual_git_head_sha": workspace.actual_head_sha,
        "reviewed_git_head_sha": inputs.reviewed_head_sha,
        "clean_worktree": workspace.clean_worktree,
        "api_domain": config.api_domain,
        "policy_id": config.health_policy.policy_id,
        "policy_fingerprint_sha256": config.health_policy.policy_fingerprint_sha256,
        "requested_retention_days": config.requested_retention_days,
        "plan_ttl_seconds": inputs.ttl_seconds,
        "confirmation_phrase_sha256": _sha256(config.confirmation_phrase.encode("utf-8")),
        "enable_public_network_fetch": config.enable_public_network_fetch,
        "enable_private_network_fetch": config.enable_private_network_fetch,
        "owner_attestations": asdict(config.owner_attestations),
        "credential_attestation": asdict(config.credential_attestation),
        "owner_path_fingerprints": dict(sorted(path_fingerprints.items())),
        "fee_query_paths": _fee_query_paths(),
        "required_public_source_ids": sorted(c.source_id for c in SOURCE_CONTRACTS),
    }
    return _canonical_sha256(payload)


def _owner_path_fingerprints(
    inputs: SealedPlanInputs,
    credentials: OKXPrivateCredentials,
    nonce_hex: str,
) -> dict[str, str]:
    config = inputs.observation_config
    paths = {
        "repository_root": config.repository_root,
        "private_root": config.private_root,
        "private_fee_snapshot_output": config.private_fee_snapshot_output,
        "safe_batch_manifest_output": config.safe_batch_manifest_output,
        "safe_observation_receipt_output": config.safe_observation_receipt_output,
        "safe_deletion_receipt_output": inputs.safe_deletion_receipt_output,
        "plan_output": inputs.plan_output,
        "claim_output": inputs.claim_output,
    }
    return {
        name: _hmac_text(
            credentials.secret_key,
            f"owner-path|{nonce_hex}|{path.expanduser().resolve(strict=False)}",
        )
        for name, path in paths.items()
    }


def _credential_binding(
    credentials: OKXPrivateCredentials,
    *,
    plan_id: str,
    nonce_hex: str,
) -> str:
    message = {
        "plan_id": plan_id,
        "nonce_hex": nonce_hex,
        "api_key": credentials.api_key,
        "passphrase": credentials.passphrase,
    }
    return _hmac_sha256(credentials.secret_key, message)


def _plan_safe_core_from_plan(plan: SealedExecutionPlan) -> dict[str, Any]:
    payload = asdict(plan)
    for field_name in (
        "plan_id",
        "credential_binding_hmac_sha256",
        "plan_authenticator_hmac_sha256",
    ):
        payload.pop(field_name)
    return payload


def _plan_authenticated_core(plan: SealedExecutionPlan) -> dict[str, Any]:
    payload = asdict(plan)
    payload.pop("plan_authenticator_hmac_sha256")
    return payload


def _assert_plan_closed_fields(plan: SealedExecutionPlan) -> None:
    forbidden_true = {
        "network_request_performed": plan.network_request_performed,
        "credentials_present_in_plan": plan.credentials_present_in_plan,
        "owner_path_values_present_in_plan": plan.owner_path_values_present_in_plan,
        "orders_sent": plan.orders_sent,
        "trade_permission_used": plan.trade_permission_used,
        "withdraw_permission_used": plan.withdraw_permission_used,
        "basis_computation_authorized": plan.basis_computation_authorized,
        "funding_pnl_computation_authorized": plan.funding_pnl_computation_authorized,
        "returns_computation_authorized": plan.returns_computation_authorized,
        "transaction_cost_estimation_authorized": plan.transaction_cost_estimation_authorized,
        "strategy_testing_authorized": plan.strategy_testing_authorized,
        "report_2_4_authorized": plan.report_2_4_authorized,
    }
    if any(forbidden_true.values()):
        raise SealedExecutionPlanError(f"Sealed plan violated closed fields: {forbidden_true}")
    if not plan.clean_worktree:
        raise SealedExecutionPlanError("Sealed plan does not attest a clean worktree")
    if plan.gate_id != SEALED_PLAN_GATE_ID or plan.predecessor_gate_id != NO_TRADE_GATE_ID:
        raise SealedExecutionPlanError("Sealed plan gate identity is invalid")


def _require_workspace_binding(
    workspace: GitWorkspaceState,
    *,
    expected_repository_root: Path,
    reviewed_head_sha: str,
    config_head_sha: str,
) -> None:
    expected_root = expected_repository_root.expanduser().resolve(strict=False)
    observed_root = Path(workspace.repository_root).expanduser().resolve(strict=False)
    if observed_root != expected_root:
        raise SealedExecutionPlanError("Resolved Git top level differs from repository_root")
    if not workspace.clean_worktree:
        raise SealedExecutionPlanError("Git worktree must be clean")
    if workspace.actual_head_sha != reviewed_head_sha:
        raise SealedExecutionPlanError("Actual Git head differs from reviewed head")
    if workspace.actual_head_sha != config_head_sha:
        raise SealedExecutionPlanError("Actual Git head differs from observation config head")


def _validate_observe_paths(inputs: SealedPlanInputs) -> None:
    config = inputs.observation_config
    config.validate()
    repository_root = config.repository_root.expanduser().resolve(strict=False)
    private_root = config.private_root.expanduser().resolve(strict=False)
    for field_name, path in (
        ("plan_path", inputs.plan_output),
        ("claim_output", inputs.claim_output),
        ("safe_deletion_receipt_output", inputs.safe_deletion_receipt_output),
    ):
        resolved = path.expanduser().resolve(strict=False)
        if resolved == repository_root or resolved.is_relative_to(repository_root):
            raise SealedExecutionPlanError(f"{field_name} must be outside the repository")
        if resolved == private_root or resolved.is_relative_to(private_root):
            raise SealedExecutionPlanError(f"{field_name} must be outside private raw storage")
    if not inputs.plan_output.is_file():
        raise SealedExecutionPlanError("Sealed execution plan does not exist")
    if _path_exists(inputs.claim_output):
        raise SealedExecutionPlanError("Execution plan was already claimed")


def _fee_query_paths() -> list[str]:
    from hybrid_trader.replication.okx_no_trade_observation import build_fee_request_path

    return [build_fee_request_path(query) for query in fee_queries()]


def _run_git(
    repository_root: Path,
    arguments: Sequence[str],
    *,
    allow_empty: bool = False,
) -> str:
    command = ("git", "-C", str(repository_root), *arguments)
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise SealedExecutionPlanError(
            f"Git workspace command failed: {' '.join(arguments)}"
        ) from exc
    output = result.stdout.strip()
    if not allow_empty and not output:
        raise SealedExecutionPlanError(
            f"Git workspace command returned empty output: {' '.join(arguments)}"
        )
    return output


def _atomic_create_json(path: Path, payload: Mapping[str, Any], *, mode: int) -> None:
    data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    except FileExistsError as exc:
        raise SealedExecutionPlanError(f"Refusing to overwrite one-time file: {path.name}") from exc
    try:
        os.fchmod(descriptor, mode)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(path, mode)
        _fsync_file(path)
        _fsync_directory(path.parent)
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _atomic_replace_json(path: Path, payload: Mapping[str, Any], *, mode: int) -> None:
    data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
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
        _fsync_file(path)
        _fsync_directory(path.parent)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _fsync_file(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise SealedExecutionPlanError(
            "Durable one-time claim publication requires directory fsync support"
        ) from exc
    try:
        os.fsync(descriptor)
    except OSError as exc:
        raise SealedExecutionPlanError(
            "Durable one-time claim publication could not fsync its parent directory"
        ) from exc
    finally:
        os.close(descriptor)


def _load_json_object(path: Path, *, label: str) -> dict[str, Any]:
    try:
        value: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SealedExecutionPlanError(f"Cannot read {label}") from exc
    if not isinstance(value, dict):
        raise SealedExecutionPlanError(f"{label} must be a JSON object")
    return cast(dict[str, Any], value)


def _require_sha256(value: str, *, field: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise SealedExecutionPlanError(f"{field} must be a lowercase SHA-256 digest")


def _canonical_sha256(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return _sha256(raw)


def _hmac_sha256(secret_key: str, payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(secret_key.encode("utf-8"), raw, hashlib.sha256).hexdigest()


def _hmac_text(secret_key: str, value: str) -> str:
    return hmac.new(secret_key.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _parse_iso_utc(value: str, *, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SealedExecutionPlanError(f"{field} is not a valid ISO timestamp") from exc
    return _aware_utc(parsed, field=field)


def _aware_utc(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise SealedExecutionPlanError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)


def _path_exists(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return True


def _is_git_sha(value: str) -> bool:
    return (
        len(value) == 40 and value == value.lower() and all(c in "0123456789abcdef" for c in value)
    )


def assert_private_file_mode(path: Path) -> None:
    """Verify an owner-local plan/claim file uses mode 0600."""

    mode = stat.S_IMODE(path.stat().st_mode)
    if mode != 0o600:
        raise SealedExecutionPlanError(f"Owner-local file mode must be 0600, got {mode:o}")
