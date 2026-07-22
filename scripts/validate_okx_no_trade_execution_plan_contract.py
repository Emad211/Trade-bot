from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import tempfile
from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from hybrid_trader.replication.okx_no_trade_execution_plan import (
    ClaimState,
    GitWorkspaceState,
    SealedExecutionPlanError,
    SealedPlanInputs,
    assert_private_file_mode,
    create_sealed_execution_plan,
    execute_sealed_real_no_trade_observation,
    load_execution_plan_claim,
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

NOW = datetime(2026, 7, 22, 12, 30, tzinfo=UTC)
SYNTHETIC_CREDENTIALS = OKXPrivateCredentials(
    api_key="gate63-synthetic-api-key",
    secret_key="gate63-synthetic-secret-key",
    passphrase="gate63-synthetic-passphrase",
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


def _config(root: Path, *, head: str) -> NoTradeObservationConfig:
    repository = root / "repository"
    repository.mkdir(parents=True, exist_ok=True)
    private_root = root / "private-raw"
    safe_root = root / "owner-safe"
    return NoTradeObservationConfig(
        mode=ObservationMode.OWNER_REAL_NETWORK,
        private_root=private_root,
        repository_root=repository,
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


def _inputs(root: Path, *, head: str) -> SealedPlanInputs:
    config = _config(root, head=head)
    safe_root = root / "owner-safe"
    return SealedPlanInputs(
        observation_config=config,
        reviewed_head_sha=head,
        plan_output=safe_root / "sealed-plan.json",
        claim_output=safe_root / "execution-claim.json",
        safe_deletion_receipt_output=safe_root / "deletion-receipt.json",
        ttl_seconds=600,
    )


def _resolver(
    inputs: SealedPlanInputs, *, clean: bool = True, head: str | None = None
) -> Callable[[Path], GitWorkspaceState]:
    state = GitWorkspaceState(
        repository_root=str(inputs.observation_config.repository_root.resolve()),
        actual_head_sha=head or inputs.reviewed_head_sha,
        clean_worktree=clean,
    )

    def resolve(_: Path) -> GitWorkspaceState:
        return state

    return resolve


def _result(root: Path) -> NoTradeObservationResult:
    return NoTradeObservationResult(
        mode=ObservationMode.OWNER_REAL_NETWORK.value,
        real_public_requests_performed=True,
        real_private_fee_requests_performed=True,
        orders_sent=False,
        batch_id="sha256-" + "b" * 64,
        source_count=4,
        fee_bundle_sha256="c" * 64,
        safe_receipt_sha256="d" * 64,
        safe_receipt_output=str(root / "owner-safe" / "observation-receipt.json"),
        safe_manifest_output=str(root / "owner-safe" / "batch-manifest.json"),
        private_fee_snapshot_output=str(root / "private-raw" / "fee-snapshot.json"),
    )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _expected_failure(operation: Callable[[], object], *, contains: str) -> bool:
    try:
        operation()
    except SealedExecutionPlanError as exc:
        return contains.casefold() in str(exc).casefold()
    return False


def build_safe_evidence(*, code_head_sha: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="gate63-sealed-plan-") as temporary:
        root = Path(temporary)
        durability_inputs = _inputs(root / "durability", head=code_head_sha)
        sync_targets: list[str] = []
        real_fsync = os.fsync

        def recording_fsync(descriptor: int) -> None:
            mode = os.fstat(descriptor).st_mode
            sync_targets.append("directory" if stat.S_ISDIR(mode) else "file")
            real_fsync(descriptor)

        with patch.object(os, "fsync", recording_fsync):
            create_sealed_execution_plan(
                durability_inputs,
                credentials=SYNTHETIC_CREDENTIALS,
                now=NOW,
                git_resolver=_resolver(durability_inputs),
                nonce_factory=lambda: b"y" * 32,
            )
        durable_file_and_parent_directory_fsync_verified = (
            "file" in sync_targets and "directory" in sync_targets
        )

        success_inputs = _inputs(root / "success", head=code_head_sha)
        plan = create_sealed_execution_plan(
            success_inputs,
            credentials=SYNTHETIC_CREDENTIALS,
            now=NOW,
            git_resolver=_resolver(success_inputs),
            nonce_factory=lambda: b"s" * 32,
        )
        assert_private_file_mode(success_inputs.plan_output)
        verified = verify_sealed_execution_plan(
            success_inputs,
            plan_path=success_inputs.plan_output,
            credentials=SYNTHETIC_CREDENTIALS,
            now=NOW + timedelta(seconds=1),
            git_resolver=_resolver(success_inputs),
        )
        claim_seen_before_executor = False

        def successful_executor(
            config: NoTradeObservationConfig,
            *,
            credentials: OKXPrivateCredentials,
        ) -> NoTradeObservationResult:
            nonlocal claim_seen_before_executor
            if config != success_inputs.observation_config or credentials != SYNTHETIC_CREDENTIALS:
                raise AssertionError("Synthetic executor received changed inputs")
            claim = load_execution_plan_claim(success_inputs.claim_output)
            claim_seen_before_executor = (
                claim.state == ClaimState.CLAIMED.value
                and claim.network_may_have_started is True
                and claim.replay_allowed is False
            )
            return _result(root / "success")

        result = execute_sealed_real_no_trade_observation(
            success_inputs,
            plan_path=success_inputs.plan_output,
            credentials=SYNTHETIC_CREDENTIALS,
            executor=successful_executor,
            now=NOW + timedelta(seconds=2),
            git_resolver=_resolver(success_inputs),
        )
        completed_claim = load_execution_plan_claim(success_inputs.claim_output)
        replay_rejected = _expected_failure(
            lambda: execute_sealed_real_no_trade_observation(
                success_inputs,
                plan_path=success_inputs.plan_output,
                credentials=SYNTHETIC_CREDENTIALS,
                executor=successful_executor,
                now=NOW + timedelta(seconds=3),
                git_resolver=_resolver(success_inputs),
            ),
            contains="already claimed",
        )

        failed_inputs = _inputs(root / "failed", head=code_head_sha)
        create_sealed_execution_plan(
            failed_inputs,
            credentials=SYNTHETIC_CREDENTIALS,
            now=NOW,
            git_resolver=_resolver(failed_inputs),
            nonce_factory=lambda: b"f" * 32,
        )

        def failing_executor(
            config: NoTradeObservationConfig,
            *,
            credentials: OKXPrivateCredentials,
        ) -> NoTradeObservationResult:
            if config != failed_inputs.observation_config or credentials != SYNTHETIC_CREDENTIALS:
                raise AssertionError("Synthetic failing executor received changed inputs")
            if not failed_inputs.claim_output.is_file():
                raise AssertionError("Claim was not created before injected execution")
            raise RuntimeError("injected failure after one-time claim")

        failure_raised = False
        try:
            execute_sealed_real_no_trade_observation(
                failed_inputs,
                plan_path=failed_inputs.plan_output,
                credentials=SYNTHETIC_CREDENTIALS,
                executor=failing_executor,
                now=NOW + timedelta(seconds=2),
                git_resolver=_resolver(failed_inputs),
            )
        except RuntimeError:
            failure_raised = True
        failed_claim = load_execution_plan_claim(failed_inputs.claim_output)
        failed_replay_rejected = _expected_failure(
            lambda: execute_sealed_real_no_trade_observation(
                failed_inputs,
                plan_path=failed_inputs.plan_output,
                credentials=SYNTHETIC_CREDENTIALS,
                executor=failing_executor,
                now=NOW + timedelta(seconds=3),
                git_resolver=_resolver(failed_inputs),
            ),
            contains="already claimed",
        )

        invalid_receipt_inputs = _inputs(root / "invalid-receipt", head=code_head_sha)
        create_sealed_execution_plan(
            invalid_receipt_inputs,
            credentials=SYNTHETIC_CREDENTIALS,
            now=NOW,
            git_resolver=_resolver(invalid_receipt_inputs),
            nonce_factory=lambda: b"i" * 32,
        )

        def invalid_receipt_executor(
            config: NoTradeObservationConfig,
            *,
            credentials: OKXPrivateCredentials,
        ) -> NoTradeObservationResult:
            if (
                config != invalid_receipt_inputs.observation_config
                or credentials != SYNTHETIC_CREDENTIALS
            ):
                raise AssertionError("Invalid-receipt executor received changed inputs")
            return replace(_result(root / "invalid-receipt"), safe_receipt_sha256="invalid")

        invalid_receipt_sha_rejected = _expected_failure(
            lambda: execute_sealed_real_no_trade_observation(
                invalid_receipt_inputs,
                plan_path=invalid_receipt_inputs.plan_output,
                credentials=SYNTHETIC_CREDENTIALS,
                executor=invalid_receipt_executor,
                now=NOW + timedelta(seconds=2),
                git_resolver=_resolver(invalid_receipt_inputs),
            ),
            contains="receipt SHA-256",
        )
        invalid_receipt_claim = load_execution_plan_claim(invalid_receipt_inputs.claim_output)
        invalid_receipt_plan_consumed = (
            invalid_receipt_claim.state == ClaimState.FAILED.value
            and invalid_receipt_claim.safe_observation_receipt_sha256 is None
            and invalid_receipt_claim.failure_type_fingerprint_sha256 is not None
        )

        tampered_claim_path = root / "tampered-claim.json"
        tampered_claim_payload = json.loads(success_inputs.claim_output.read_text(encoding="utf-8"))
        tampered_claim_payload["replay_allowed"] = True
        tampered_claim_path.write_text(json.dumps(tampered_claim_payload), encoding="utf-8")
        tampered_claim_path.chmod(0o600)
        tampered_claim_rejected = _expected_failure(
            lambda: load_execution_plan_claim(tampered_claim_path),
            contains="cannot allow replay",
        )

        changed_inputs = replace(
            success_inputs,
            observation_config=replace(
                success_inputs.observation_config,
                requested_retention_days=3,
            ),
            claim_output=root / "changed" / "claim.json",
        )
        configuration_change_rejected = _expected_failure(
            lambda: verify_sealed_execution_plan(
                changed_inputs,
                plan_path=success_inputs.plan_output,
                credentials=SYNTHETIC_CREDENTIALS,
                now=NOW + timedelta(seconds=1),
                git_resolver=_resolver(changed_inputs),
            ),
            contains="differs",
        )
        credential_change_rejected = _expected_failure(
            lambda: verify_sealed_execution_plan(
                replace(success_inputs, claim_output=root / "other-credential-claim.json"),
                plan_path=success_inputs.plan_output,
                credentials=OKXPrivateCredentials(
                    api_key="other-api-key",
                    secret_key="other-secret-key",
                    passphrase="other-passphrase",
                ),
                now=NOW + timedelta(seconds=1),
                git_resolver=_resolver(success_inputs),
            ),
            contains="credential binding",
        )
        expired_rejected = _expected_failure(
            lambda: verify_sealed_execution_plan(
                replace(success_inputs, claim_output=root / "expired-claim.json"),
                plan_path=success_inputs.plan_output,
                credentials=SYNTHETIC_CREDENTIALS,
                now=NOW + timedelta(seconds=601),
                git_resolver=_resolver(success_inputs),
            ),
            contains="expired",
        )
        dirty_rejected = _expected_failure(
            lambda: verify_sealed_execution_plan(
                replace(success_inputs, claim_output=root / "dirty-claim.json"),
                plan_path=success_inputs.plan_output,
                credentials=SYNTHETIC_CREDENTIALS,
                now=NOW + timedelta(seconds=1),
                git_resolver=_resolver(success_inputs, clean=False),
            ),
            contains="clean",
        )
        head_mismatch_rejected = _expected_failure(
            lambda: verify_sealed_execution_plan(
                replace(success_inputs, claim_output=root / "head-claim.json"),
                plan_path=success_inputs.plan_output,
                credentials=SYNTHETIC_CREDENTIALS,
                now=NOW + timedelta(seconds=1),
                git_resolver=_resolver(success_inputs, head="e" * 40),
            ),
            contains="actual git head",
        )

        plan_text = success_inputs.plan_output.read_text(encoding="utf-8")
        claim_text = success_inputs.claim_output.read_text(encoding="utf-8")
        forbidden_values = (
            SYNTHETIC_CREDENTIALS.api_key,
            SYNTHETIC_CREDENTIALS.secret_key,
            SYNTHETIC_CREDENTIALS.passphrase,
            str(success_inputs.observation_config.repository_root.resolve()),
            str(success_inputs.observation_config.private_root.resolve()),
            str(success_inputs.plan_output.resolve()),
            str(success_inputs.claim_output.resolve()),
        )
        safe_local_files = all(
            forbidden not in plan_text and forbidden not in claim_text
            for forbidden in forbidden_values
        )

        evidence: dict[str, object] = {
            "schema_version": "1.0",
            "gate_id": "OKX_OWNER_LOCAL_SEALED_EXECUTION_PLAN_V1",
            "issue_number": 63,
            "validation_mode": "SYNTHETIC_INJECTED_EXECUTOR_ONLY",
            "code_head_sha": code_head_sha,
            "predecessor_gate_id": "OKX_OWNER_CONTROLLED_NO_TRADE_OBSERVATION_V1",
            "plan_id": plan.plan_id,
            "plan_sha256": _sha256(success_inputs.plan_output),
            "claim_sha256": _sha256(success_inputs.claim_output),
            "policy_id": plan.policy_id,
            "policy_fingerprint_sha256": plan.policy_fingerprint_sha256,
            "configuration_fingerprint_sha256": plan.configuration_fingerprint_sha256,
            "plan_ttl_seconds": success_inputs.ttl_seconds,
            "actual_head_bound": verified.actual_git_head_sha == code_head_sha,
            "clean_worktree_required": verified.clean_worktree,
            "plan_mode_0600": success_inputs.plan_output.stat().st_mode & 0o777 == 0o600,
            "claim_mode_0600": success_inputs.claim_output.stat().st_mode & 0o777 == 0o600,
            "credential_binding_hmac_present": len(plan.credential_binding_hmac_sha256) == 64,
            "plan_authenticator_hmac_present": len(plan.plan_authenticator_hmac_sha256) == 64,
            "claim_created_before_executor": claim_seen_before_executor,
            "successful_claim_finalized": (
                completed_claim.state == ClaimState.COMPLETED.value
                and completed_claim.safe_observation_receipt_sha256 == result.safe_receipt_sha256
            ),
            "replay_rejected": replay_rejected,
            "failure_raised_after_claim": failure_raised,
            "failed_plan_consumed": (
                failed_claim.state == ClaimState.FAILED.value
                and failed_claim.failure_type_fingerprint_sha256 is not None
            ),
            "failed_plan_replay_rejected": failed_replay_rejected,
            "configuration_change_rejected": configuration_change_rejected,
            "credential_change_rejected": credential_change_rejected,
            "expired_plan_rejected": expired_rejected,
            "dirty_worktree_rejected": dirty_rejected,
            "head_mismatch_rejected": head_mismatch_rejected,
            "durable_file_and_parent_directory_fsync_verified": (
                durable_file_and_parent_directory_fsync_verified
            ),
            "invalid_receipt_sha_rejected": invalid_receipt_sha_rejected,
            "invalid_receipt_plan_consumed": invalid_receipt_plan_consumed,
            "tampered_claim_rejected": tampered_claim_rejected,
            "credentials_present_in_safe_evidence": False,
            "owner_path_values_present_in_safe_evidence": False,
            "safe_local_plan_and_claim_exclude_values": safe_local_files,
            "real_public_request_performed": False,
            "real_private_fee_request_performed": False,
            "credentials_supplied_to_ci": False,
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
        required_true = (
            "actual_head_bound",
            "clean_worktree_required",
            "plan_mode_0600",
            "claim_mode_0600",
            "credential_binding_hmac_present",
            "plan_authenticator_hmac_present",
            "claim_created_before_executor",
            "successful_claim_finalized",
            "replay_rejected",
            "failure_raised_after_claim",
            "failed_plan_consumed",
            "failed_plan_replay_rejected",
            "configuration_change_rejected",
            "credential_change_rejected",
            "expired_plan_rejected",
            "dirty_worktree_rejected",
            "head_mismatch_rejected",
            "durable_file_and_parent_directory_fsync_verified",
            "invalid_receipt_sha_rejected",
            "invalid_receipt_plan_consumed",
            "tampered_claim_rejected",
            "safe_local_plan_and_claim_exclude_values",
        )
        if any(evidence[name] is not True for name in required_true):
            raise SystemExit(f"Synthetic sealed-plan check failed: {evidence}")
        return evidence


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--code-head-sha", required=True)
    args = parser.parse_args(argv)
    if len(args.code_head_sha) != 40:
        parser.error("--code-head-sha must be a 40-character SHA")
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        parser.error("--output-dir must not contain existing files")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    evidence = build_safe_evidence(code_head_sha=args.code_head_sha)
    output = args.output_dir / "okx-sealed-execution-plan-safe-evidence.json"
    output.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"safe_evidence_sha256": _sha256(output)}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
