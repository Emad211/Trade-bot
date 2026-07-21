from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from hybrid_trader.replication.okx_no_trade_observation import (
    DELETE_CONFIRMATION_PHRASE,
    OWNER_CONFIRMATION_PHRASE,
    CredentialPermissionAttestation,
    NoTradeDeletionConfig,
    NoTradeObservationConfig,
    NoTradeObservationError,
    ObservationMode,
    delete_no_trade_observation,
    execute_real_no_trade_observation,
    load_credentials_from_environment,
    load_no_trade_health_policy,
)
from hybrid_trader.replication.okx_owner_sampling_runner import OwnerRunnerAttestations


def _add_storage_attestations(parser: argparse.ArgumentParser, *, real: bool) -> None:
    parser.add_argument("--attest-terms-reviewed", action="store_true")
    parser.add_argument("--attest-personal-noncommercial-use", action="store_true")
    parser.add_argument("--attest-reasonable-rate-and-scale", action="store_true")
    parser.add_argument("--attest-redistribution-disabled", action="store_true")
    parser.add_argument("--attest-encryption-at-rest", action="store_true")
    parser.add_argument("--attest-owner-only-access", action="store_true")
    parser.add_argument("--attest-backup-and-sync-excluded", action="store_true")
    parser.add_argument("--attest-public-artifact-upload-disabled", action="store_true")
    if real:
        parser.add_argument("--attest-owner-controlled-private-storage", action="store_true")
        parser.add_argument("--attest-owner-controlled-encryption-keys", action="store_true")
        parser.add_argument("--attest-real-execution-owner-confirmed", action="store_true")


def _add_credential_attestations(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--attest-read-permission-enabled", action="store_true")
    parser.add_argument("--attest-trade-permission-disabled", action="store_true")
    parser.add_argument("--attest-withdraw-permission-disabled", action="store_true")
    parser.add_argument("--attest-ip-allowlist-enabled", action="store_true")
    parser.add_argument("--attest-credentials-outside-repository", action="store_true")
    parser.add_argument("--attest-credentials-outside-ci", action="store_true")
    parser.add_argument("--attest-credentials-not-logged", action="store_true")


def _owner_attestations(args: argparse.Namespace, *, real: bool) -> OwnerRunnerAttestations:
    return OwnerRunnerAttestations(
        terms_reviewed=bool(getattr(args, "attest_terms_reviewed", False)),
        personal_noncommercial_use=bool(getattr(args, "attest_personal_noncommercial_use", False)),
        reasonable_rate_and_scale=bool(getattr(args, "attest_reasonable_rate_and_scale", False)),
        redistribution_disabled=bool(getattr(args, "attest_redistribution_disabled", False)),
        encryption_at_rest=bool(getattr(args, "attest_encryption_at_rest", False)),
        owner_only_access=bool(getattr(args, "attest_owner_only_access", False)),
        backup_and_sync_excluded=bool(getattr(args, "attest_backup_and_sync_excluded", False)),
        public_artifact_upload_disabled=bool(
            getattr(args, "attest_public_artifact_upload_disabled", False)
        ),
        owner_controlled_private_storage=(
            bool(getattr(args, "attest_owner_controlled_private_storage", False)) if real else False
        ),
        owner_controlled_encryption_keys=(
            bool(getattr(args, "attest_owner_controlled_encryption_keys", False)) if real else False
        ),
        real_execution_owner_confirmed=(
            bool(getattr(args, "attest_real_execution_owner_confirmed", False)) if real else False
        ),
    )


def _credential_attestation(args: argparse.Namespace) -> CredentialPermissionAttestation:
    return CredentialPermissionAttestation(
        read_permission_enabled=bool(args.attest_read_permission_enabled),
        trade_permission_disabled=bool(args.attest_trade_permission_disabled),
        withdraw_permission_disabled=bool(args.attest_withdraw_permission_disabled),
        ip_allowlist_enabled=bool(args.attest_ip_allowlist_enabled),
        credentials_outside_repository=bool(args.attest_credentials_outside_repository),
        credentials_outside_ci=bool(args.attest_credentials_outside_ci),
        credentials_not_logged=bool(args.attest_credentials_not_logged),
    )


def _config(args: argparse.Namespace) -> NoTradeObservationConfig:
    policy = load_no_trade_health_policy(args.policy)
    return NoTradeObservationConfig(
        mode=ObservationMode.OWNER_REAL_NETWORK,
        private_root=args.private_root,
        repository_root=args.repository_root,
        private_fee_snapshot_output=args.private_fee_snapshot_output,
        safe_batch_manifest_output=args.safe_batch_manifest_output,
        safe_observation_receipt_output=args.safe_observation_receipt_output,
        requested_retention_days=args.retention_days,
        confirmation_phrase=args.confirm,
        enable_public_network_fetch=bool(args.enable_public_network_fetch),
        enable_private_network_fetch=bool(args.enable_private_network_fetch),
        owner_attestations=_owner_attestations(args, real=True),
        credential_attestation=_credential_attestation(args),
        health_policy=policy,
        api_domain=args.api_domain,
        code_head_sha=args.code_head_sha,
    )


def _preflight(args: argparse.Namespace) -> int:
    config = _config(args)
    config.validate()
    credentials = load_credentials_from_environment()
    credentials.validate()
    safe = {
        "preflight": "PASS",
        "mode": config.mode.value,
        "api_domain": config.api_domain,
        "policy_id": config.health_policy.policy_id,
        "policy_fingerprint_sha256": config.health_policy.policy_fingerprint_sha256,
        "required_public_source_count": len(config.health_policy.required_source_ids),
        "fee_query_count": 2,
        "credential_environment_fields_present": True,
        "credential_values_printed": False,
        "network_request_performed": False,
        "orders_sent": False,
        "trade_permission_used": False,
        "withdraw_permission_used": False,
        "report_2_4_authorized": False,
    }
    print(json.dumps(safe, indent=2, sort_keys=True))
    return 0


def _observe(args: argparse.Namespace) -> int:
    config = _config(args)
    credentials = load_credentials_from_environment()
    result = execute_real_no_trade_observation(config, credentials=credentials)
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0


def _delete(args: argparse.Namespace) -> int:
    config = NoTradeDeletionConfig(
        private_root=args.private_root,
        repository_root=args.repository_root,
        private_fee_snapshot_path=args.private_fee_snapshot,
        safe_batch_manifest_path=args.safe_batch_manifest,
        safe_observation_receipt_path=args.safe_observation_receipt,
        safe_deletion_receipt_output=args.safe_deletion_receipt_output,
        confirmation_phrase=args.confirm,
        reason=args.reason,
        owner_attestations=_owner_attestations(args, real=False),
    )
    result = delete_no_trade_observation(config)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


def _add_observation_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--private-root", required=True, type=Path)
    parser.add_argument("--repository-root", required=True, type=Path)
    parser.add_argument("--private-fee-snapshot-output", required=True, type=Path)
    parser.add_argument("--safe-batch-manifest-output", required=True, type=Path)
    parser.add_argument("--safe-observation-receipt-output", required=True, type=Path)
    parser.add_argument("--policy", required=True, type=Path)
    parser.add_argument("--code-head-sha", required=True)
    parser.add_argument(
        "--api-domain", required=True, choices=("www.okx.com", "us.okx.com", "eea.okx.com")
    )
    parser.add_argument("--retention-days", required=True, type=int)
    parser.add_argument("--confirm", required=True, help=f"Must equal: {OWNER_CONFIRMATION_PHRASE}")
    parser.add_argument("--enable-public-network-fetch", action="store_true")
    parser.add_argument("--enable-private-network-fetch", action="store_true")
    _add_storage_attestations(parser, real=True)
    _add_credential_attestations(parser)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Owner-local, disabled-by-default OKX no-trade observation package."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight = subparsers.add_parser(
        "preflight", help="Validate local policy, paths, attestations and credential presence only."
    )
    _add_observation_arguments(preflight)
    preflight.set_defaults(handler=_preflight)

    observe = subparsers.add_parser(
        "observe", help="Perform one owner-confirmed fee snapshot plus four-source public batch."
    )
    _add_observation_arguments(observe)
    observe.set_defaults(handler=_observe)

    delete = subparsers.add_parser(
        "delete", help="Delete one retained no-trade observation and write a safe receipt."
    )
    delete.add_argument("--private-root", required=True, type=Path)
    delete.add_argument("--repository-root", required=True, type=Path)
    delete.add_argument("--private-fee-snapshot", required=True, type=Path)
    delete.add_argument("--safe-batch-manifest", required=True, type=Path)
    delete.add_argument("--safe-observation-receipt", required=True, type=Path)
    delete.add_argument("--safe-deletion-receipt-output", required=True, type=Path)
    delete.add_argument("--reason", required=True)
    delete.add_argument(
        "--confirm", required=True, help=f"Must equal: {DELETE_CONFIRMATION_PHRASE}"
    )
    _add_storage_attestations(delete, real=False)
    delete.set_defaults(handler=_delete)

    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except NoTradeObservationError as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
