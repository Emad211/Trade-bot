from __future__ import annotations

import json
import os
import stat
import subprocess
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

import hybrid_trader.replication.okx_no_trade_execution_plan as execution_plan_module
from hybrid_trader.replication.okx_no_trade_execution_plan import (
    ClaimState,
    GitWorkspaceState,
    SealedExecutionPlanError,
    SealedPlanInputs,
    assert_private_file_mode,
    create_sealed_execution_plan,
    execute_sealed_real_no_trade_observation,
    load_execution_plan_claim,
    load_sealed_execution_plan,
    resolve_git_workspace,
    verify_sealed_execution_plan,
)
from hybrid_trader.replication.okx_no_trade_observation import (
    OWNER_CONFIRMATION_PHRASE,
    CredentialPermissionAttestation,
    NoTradeObservationConfig,
    NoTradeObservationResult,
    ObservationMode,
    OKXPrivateCredentials,
    default_no_trade_health_policy,
)
from hybrid_trader.replication.okx_owner_sampling_runner import OwnerRunnerAttestations

NOW = datetime(2026, 7, 22, 12, 0, tzinfo=UTC)
HEAD = "a" * 40
CREDENTIALS = OKXPrivateCredentials(
    api_key="synthetic-api-key-value",
    secret_key="synthetic-secret-key-value",
    passphrase="synthetic-passphrase-value",
)
OTHER_CREDENTIALS = OKXPrivateCredentials(
    api_key="other-api-key-value",
    secret_key="other-secret-key-value",
    passphrase="other-passphrase-value",
)


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
        owner_controlled_private_storage=True,
        owner_controlled_encryption_keys=True,
        real_execution_owner_confirmed=True,
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


def _config(tmp_path: Path, *, head: str = HEAD) -> NoTradeObservationConfig:
    repository_root = tmp_path / "repository"
    repository_root.mkdir(parents=True, exist_ok=True)
    private_root = tmp_path / "private-raw"
    safe_root = tmp_path / "owner-safe"
    return NoTradeObservationConfig(
        mode=ObservationMode.OWNER_REAL_NETWORK,
        private_root=private_root,
        repository_root=repository_root,
        private_fee_snapshot_output=private_root / "fee-snapshot.json",
        safe_batch_manifest_output=safe_root / "batch-manifest.json",
        safe_observation_receipt_output=safe_root / "observation-receipt.json",
        requested_retention_days=2,
        confirmation_phrase=OWNER_CONFIRMATION_PHRASE,
        enable_public_network_fetch=True,
        enable_private_network_fetch=True,
        owner_attestations=_owner_attestations(),
        credential_attestation=_credential_attestation(),
        health_policy=default_no_trade_health_policy(),
        api_domain="www.okx.com",
        code_head_sha=head,
    )


def _inputs(tmp_path: Path, *, config: NoTradeObservationConfig | None = None) -> SealedPlanInputs:
    observation_config = config or _config(tmp_path)
    safe_root = tmp_path / "owner-safe"
    return SealedPlanInputs(
        observation_config=observation_config,
        reviewed_head_sha=observation_config.code_head_sha,
        plan_output=safe_root / "sealed-plan.json",
        claim_output=safe_root / "plan-claim.json",
        safe_deletion_receipt_output=safe_root / "deletion-receipt.json",
        ttl_seconds=600,
    )


def _workspace(
    config: NoTradeObservationConfig, *, head: str = HEAD, clean: bool = True
) -> GitWorkspaceState:
    return GitWorkspaceState(
        repository_root=str(config.repository_root.resolve()),
        actual_head_sha=head,
        clean_worktree=clean,
    )


def _resolver(state: GitWorkspaceState):
    def resolve(_: Path) -> GitWorkspaceState:
        return state

    return resolve


def _create_plan(tmp_path: Path) -> tuple[SealedPlanInputs, object]:
    inputs = _inputs(tmp_path)
    plan = create_sealed_execution_plan(
        inputs,
        credentials=CREDENTIALS,
        now=NOW,
        git_resolver=_resolver(_workspace(inputs.observation_config)),
        nonce_factory=lambda: b"n" * 32,
    )
    return inputs, plan


def _synthetic_result(tmp_path: Path) -> NoTradeObservationResult:
    return NoTradeObservationResult(
        mode=ObservationMode.OWNER_REAL_NETWORK.value,
        real_public_requests_performed=True,
        real_private_fee_requests_performed=True,
        orders_sent=False,
        batch_id="sha256-" + "b" * 64,
        source_count=4,
        fee_bundle_sha256="c" * 64,
        safe_receipt_sha256="d" * 64,
        safe_receipt_output=str(tmp_path / "owner-safe" / "observation-receipt.json"),
        safe_manifest_output=str(tmp_path / "owner-safe" / "batch-manifest.json"),
        private_fee_snapshot_output=str(tmp_path / "private-raw" / "fee-snapshot.json"),
    )


def test_resolve_git_workspace_binds_top_level_head_and_cleanliness(tmp_path: Path) -> None:
    repository = tmp_path / "repo"
    repository.mkdir()
    subprocess.run(("git", "init"), cwd=repository, check=True, capture_output=True)
    subprocess.run(
        ("git", "config", "user.email", "gate63@example.invalid"), cwd=repository, check=True
    )
    subprocess.run(("git", "config", "user.name", "Gate 63"), cwd=repository, check=True)
    (repository / "tracked.txt").write_text("frozen\n", encoding="utf-8")
    subprocess.run(("git", "add", "tracked.txt"), cwd=repository, check=True)
    subprocess.run(
        ("git", "commit", "-m", "freeze"), cwd=repository, check=True, capture_output=True
    )

    state = resolve_git_workspace(repository)
    assert state.repository_root == str(repository.resolve())
    assert len(state.actual_head_sha) == 40
    assert state.clean_worktree is True

    (repository / "untracked.txt").write_text("dirty\n", encoding="utf-8")
    assert resolve_git_workspace(repository).clean_worktree is False
    with pytest.raises(SealedExecutionPlanError, match="Git workspace command failed"):
        resolve_git_workspace(repository / ".git")


def test_plan_is_private_content_addressed_and_contains_no_secrets_or_paths(tmp_path: Path) -> None:
    inputs, plan_object = _create_plan(tmp_path)
    plan = load_sealed_execution_plan(inputs.plan_output)
    assert plan == plan_object
    assert_private_file_mode(inputs.plan_output)
    assert plan.network_request_performed is False
    assert plan.orders_sent is False
    assert plan.report_2_4_authorized is False
    assert plan.clean_worktree is True
    assert plan.actual_git_head_sha == HEAD
    assert len(plan.plan_id) == 64
    assert len(plan.plan_authenticator_hmac_sha256) == 64
    assert len(plan.credential_binding_hmac_sha256) == 64

    text = inputs.plan_output.read_text(encoding="utf-8")
    for forbidden in (
        CREDENTIALS.api_key,
        CREDENTIALS.secret_key,
        CREDENTIALS.passphrase,
        str(inputs.observation_config.repository_root.resolve()),
        str(inputs.observation_config.private_root.resolve()),
        str(inputs.plan_output.resolve()),
        str(inputs.claim_output.resolve()),
    ):
        assert forbidden not in text


def test_actual_head_dirty_worktree_and_repository_root_mismatch_fail_closed(
    tmp_path: Path,
) -> None:
    inputs = _inputs(tmp_path)
    with pytest.raises(SealedExecutionPlanError, match="Actual Git head"):
        create_sealed_execution_plan(
            inputs,
            credentials=CREDENTIALS,
            now=NOW,
            git_resolver=_resolver(_workspace(inputs.observation_config, head="b" * 40)),
        )
    with pytest.raises(SealedExecutionPlanError, match="clean"):
        create_sealed_execution_plan(
            inputs,
            credentials=CREDENTIALS,
            now=NOW,
            git_resolver=_resolver(_workspace(inputs.observation_config, clean=False)),
        )
    wrong_root = GitWorkspaceState(
        repository_root=str((tmp_path / "other").resolve()),
        actual_head_sha=HEAD,
        clean_worktree=True,
    )
    with pytest.raises(SealedExecutionPlanError, match="top level"):
        create_sealed_execution_plan(
            inputs,
            credentials=CREDENTIALS,
            now=NOW,
            git_resolver=_resolver(wrong_root),
        )


def test_plan_paths_must_be_outside_repository_and_private_raw_tree(tmp_path: Path) -> None:
    config = _config(tmp_path)
    inside_repo = replace(
        _inputs(tmp_path, config=config),
        plan_output=config.repository_root / "plan.json",
    )
    with pytest.raises(SealedExecutionPlanError, match="outside the repository"):
        create_sealed_execution_plan(
            inside_repo,
            credentials=CREDENTIALS,
            now=NOW,
            git_resolver=_resolver(_workspace(config)),
        )
    inside_private = replace(
        _inputs(tmp_path, config=config),
        claim_output=config.private_root / "claim.json",
    )
    with pytest.raises(SealedExecutionPlanError, match="outside private raw"):
        create_sealed_execution_plan(
            inside_private,
            credentials=CREDENTIALS,
            now=NOW,
            git_resolver=_resolver(_workspace(config)),
        )


def test_same_credentials_verify_and_different_credentials_fail(tmp_path: Path) -> None:
    inputs, _ = _create_plan(tmp_path)
    state = _workspace(inputs.observation_config)
    verified = verify_sealed_execution_plan(
        inputs,
        plan_path=inputs.plan_output,
        credentials=CREDENTIALS,
        now=NOW + timedelta(seconds=1),
        git_resolver=_resolver(state),
    )
    assert verified.actual_git_head_sha == HEAD
    with pytest.raises(SealedExecutionPlanError, match="Credential binding"):
        verify_sealed_execution_plan(
            inputs,
            plan_path=inputs.plan_output,
            credentials=OTHER_CREDENTIALS,
            now=NOW + timedelta(seconds=1),
            git_resolver=_resolver(state),
        )


def test_any_bound_configuration_change_is_rejected(tmp_path: Path) -> None:
    inputs, _ = _create_plan(tmp_path)
    changed_config = replace(inputs.observation_config, requested_retention_days=3)
    changed_inputs = replace(inputs, observation_config=changed_config)
    with pytest.raises(SealedExecutionPlanError, match="configuration differs"):
        verify_sealed_execution_plan(
            changed_inputs,
            plan_path=inputs.plan_output,
            credentials=CREDENTIALS,
            now=NOW + timedelta(seconds=1),
            git_resolver=_resolver(_workspace(changed_config)),
        )


def test_tampered_plan_is_rejected(tmp_path: Path) -> None:
    inputs, _ = _create_plan(tmp_path)
    payload = json.loads(inputs.plan_output.read_text(encoding="utf-8"))
    payload["policy_id"] = "TAMPERED"
    inputs.plan_output.write_text(json.dumps(payload), encoding="utf-8")
    inputs.plan_output.chmod(0o600)
    with pytest.raises(SealedExecutionPlanError):
        verify_sealed_execution_plan(
            inputs,
            plan_path=inputs.plan_output,
            credentials=CREDENTIALS,
            now=NOW + timedelta(seconds=1),
            git_resolver=_resolver(_workspace(inputs.observation_config)),
        )


def test_expired_future_dated_and_excessive_ttl_plans_fail(tmp_path: Path) -> None:
    expired_inputs, _ = _create_plan(tmp_path / "expired")
    with pytest.raises(SealedExecutionPlanError, match="expired"):
        verify_sealed_execution_plan(
            expired_inputs,
            plan_path=expired_inputs.plan_output,
            credentials=CREDENTIALS,
            now=NOW + timedelta(seconds=601),
            git_resolver=_resolver(_workspace(expired_inputs.observation_config)),
        )

    future_inputs = _inputs(tmp_path / "future")
    create_sealed_execution_plan(
        future_inputs,
        credentials=CREDENTIALS,
        now=NOW + timedelta(seconds=10),
        git_resolver=_resolver(_workspace(future_inputs.observation_config)),
        nonce_factory=lambda: b"f" * 32,
    )
    with pytest.raises(SealedExecutionPlanError, match="future"):
        verify_sealed_execution_plan(
            future_inputs,
            plan_path=future_inputs.plan_output,
            credentials=CREDENTIALS,
            now=NOW,
            git_resolver=_resolver(_workspace(future_inputs.observation_config)),
        )

    excessive = replace(_inputs(tmp_path / "ttl"), ttl_seconds=1801)
    with pytest.raises(SealedExecutionPlanError, match="ttl_seconds"):
        create_sealed_execution_plan(
            excessive,
            credentials=CREDENTIALS,
            now=NOW,
            git_resolver=_resolver(_workspace(excessive.observation_config)),
        )


def test_claim_exists_before_executor_and_success_finalizes_it(tmp_path: Path) -> None:
    inputs, _ = _create_plan(tmp_path)
    calls = 0

    def executor(
        config: NoTradeObservationConfig,
        *,
        credentials: OKXPrivateCredentials,
    ) -> NoTradeObservationResult:
        nonlocal calls
        calls += 1
        assert config == inputs.observation_config
        assert credentials == CREDENTIALS
        claim = load_execution_plan_claim(inputs.claim_output)
        assert claim.state == ClaimState.CLAIMED.value
        assert claim.network_may_have_started is True
        assert claim.replay_allowed is False
        assert_private_file_mode(inputs.claim_output)
        return _synthetic_result(tmp_path)

    result = execute_sealed_real_no_trade_observation(
        inputs,
        plan_path=inputs.plan_output,
        credentials=CREDENTIALS,
        executor=executor,
        now=NOW + timedelta(seconds=1),
        git_resolver=_resolver(_workspace(inputs.observation_config)),
    )
    assert result.safe_receipt_sha256 == "d" * 64
    assert calls == 1
    claim = load_execution_plan_claim(inputs.claim_output)
    assert claim.state == ClaimState.COMPLETED.value
    assert claim.safe_observation_receipt_sha256 == "d" * 64
    assert claim.failure_type_fingerprint_sha256 is None
    assert claim.credentials_present_in_claim is False
    assert claim.owner_path_values_present_in_claim is False
    assert claim.orders_sent is False
    assert claim.report_2_4_authorized is False

    with pytest.raises(SealedExecutionPlanError, match="already claimed"):
        execute_sealed_real_no_trade_observation(
            inputs,
            plan_path=inputs.plan_output,
            credentials=CREDENTIALS,
            executor=executor,
            now=NOW + timedelta(seconds=2),
            git_resolver=_resolver(_workspace(inputs.observation_config)),
        )
    assert calls == 1


def test_failed_execution_consumes_plan_and_cannot_be_replayed(tmp_path: Path) -> None:
    inputs, _ = _create_plan(tmp_path)
    calls = 0

    def failing_executor(
        config: NoTradeObservationConfig,
        *,
        credentials: OKXPrivateCredentials,
    ) -> NoTradeObservationResult:
        nonlocal calls
        calls += 1
        assert config == inputs.observation_config
        assert credentials == CREDENTIALS
        assert load_execution_plan_claim(inputs.claim_output).network_may_have_started is True
        raise RuntimeError("synthetic execution failure")

    with pytest.raises(RuntimeError, match="synthetic execution failure"):
        execute_sealed_real_no_trade_observation(
            inputs,
            plan_path=inputs.plan_output,
            credentials=CREDENTIALS,
            executor=failing_executor,
            now=NOW + timedelta(seconds=1),
            git_resolver=_resolver(_workspace(inputs.observation_config)),
        )
    claim = load_execution_plan_claim(inputs.claim_output)
    assert claim.state == ClaimState.FAILED.value
    assert claim.failure_type_fingerprint_sha256 is not None
    assert claim.safe_observation_receipt_sha256 is None
    assert calls == 1

    with pytest.raises(SealedExecutionPlanError, match="already claimed"):
        execute_sealed_real_no_trade_observation(
            inputs,
            plan_path=inputs.plan_output,
            credentials=CREDENTIALS,
            executor=failing_executor,
            now=NOW + timedelta(seconds=2),
            git_resolver=_resolver(_workspace(inputs.observation_config)),
        )
    assert calls == 1


def test_plan_file_mode_is_enforced_during_verification(tmp_path: Path) -> None:
    inputs, _ = _create_plan(tmp_path)
    inputs.plan_output.chmod(0o644)
    with pytest.raises(SealedExecutionPlanError, match="0600"):
        verify_sealed_execution_plan(
            inputs,
            plan_path=inputs.plan_output,
            credentials=CREDENTIALS,
            now=NOW + timedelta(seconds=1),
            git_resolver=_resolver(_workspace(inputs.observation_config)),
        )


def test_atomic_publication_fsyncs_file_and_parent_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    synced_kinds: list[str] = []
    real_fsync = os.fsync

    def recording_fsync(descriptor: int) -> None:
        mode = os.fstat(descriptor).st_mode
        synced_kinds.append("directory" if stat.S_ISDIR(mode) else "file")
        real_fsync(descriptor)

    monkeypatch.setattr(execution_plan_module.os, "fsync", recording_fsync)
    _create_plan(tmp_path)

    assert "file" in synced_kinds
    assert "directory" in synced_kinds


def test_invalid_receipt_sha_fails_and_consumes_plan(tmp_path: Path) -> None:
    inputs, _ = _create_plan(tmp_path)

    def malformed_executor(
        config: NoTradeObservationConfig,
        *,
        credentials: OKXPrivateCredentials,
    ) -> NoTradeObservationResult:
        assert config == inputs.observation_config
        assert credentials == CREDENTIALS
        return replace(_synthetic_result(tmp_path), safe_receipt_sha256="not-a-sha")

    with pytest.raises(SealedExecutionPlanError, match="receipt SHA-256"):
        execute_sealed_real_no_trade_observation(
            inputs,
            plan_path=inputs.plan_output,
            credentials=CREDENTIALS,
            executor=malformed_executor,
            now=NOW + timedelta(seconds=1),
            git_resolver=_resolver(_workspace(inputs.observation_config)),
        )

    claim = load_execution_plan_claim(inputs.claim_output)
    assert claim.state == ClaimState.FAILED.value
    assert claim.safe_observation_receipt_sha256 is None
    assert claim.failure_type_fingerprint_sha256 is not None
    with pytest.raises(SealedExecutionPlanError, match="already claimed"):
        execute_sealed_real_no_trade_observation(
            inputs,
            plan_path=inputs.plan_output,
            credentials=CREDENTIALS,
            executor=malformed_executor,
            now=NOW + timedelta(seconds=2),
            git_resolver=_resolver(_workspace(inputs.observation_config)),
        )


def test_claim_loader_rejects_replay_and_invalid_digest_tampering(tmp_path: Path) -> None:
    inputs, _ = _create_plan(tmp_path)

    def executor(
        config: NoTradeObservationConfig,
        *,
        credentials: OKXPrivateCredentials,
    ) -> NoTradeObservationResult:
        assert config == inputs.observation_config
        assert credentials == CREDENTIALS
        return _synthetic_result(tmp_path)

    execute_sealed_real_no_trade_observation(
        inputs,
        plan_path=inputs.plan_output,
        credentials=CREDENTIALS,
        executor=executor,
        now=NOW + timedelta(seconds=1),
        git_resolver=_resolver(_workspace(inputs.observation_config)),
    )
    payload = json.loads(inputs.claim_output.read_text(encoding="utf-8"))
    payload["replay_allowed"] = True
    inputs.claim_output.write_text(json.dumps(payload), encoding="utf-8")
    inputs.claim_output.chmod(0o600)
    with pytest.raises(SealedExecutionPlanError, match="cannot allow replay"):
        load_execution_plan_claim(inputs.claim_output)

    payload["replay_allowed"] = False
    payload["safe_observation_receipt_sha256"] = "invalid"
    inputs.claim_output.write_text(json.dumps(payload), encoding="utf-8")
    inputs.claim_output.chmod(0o600)
    with pytest.raises(SealedExecutionPlanError, match="receipt SHA-256"):
        load_execution_plan_claim(inputs.claim_output)
