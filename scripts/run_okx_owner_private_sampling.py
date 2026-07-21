from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from hybrid_trader.replication.okx_owner_sampling_runner import (
    DELETE_CONFIRMATION_PHRASE,
    REAL_CONFIRMATION_PHRASE,
    OKXOwnerSamplingRunnerError,
    OwnerRunnerAttestations,
    OwnerRunnerMode,
    OwnerSamplingDeletionConfig,
    OwnerSamplingRunnerConfig,
    delete_owner_sampling_batch,
    execute_real_owner_sampling,
)


def _add_common_attestations(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--attest-terms-reviewed", action="store_true")
    parser.add_argument("--attest-personal-noncommercial-use", action="store_true")
    parser.add_argument("--attest-reasonable-rate-and-scale", action="store_true")
    parser.add_argument("--attest-redistribution-disabled", action="store_true")
    parser.add_argument("--attest-encryption-at-rest", action="store_true")
    parser.add_argument("--attest-owner-only-access", action="store_true")
    parser.add_argument("--attest-backup-and-sync-excluded", action="store_true")
    parser.add_argument("--attest-public-artifact-upload-disabled", action="store_true")
    parser.add_argument("--attest-owner-controlled-private-storage", action="store_true")
    parser.add_argument("--attest-owner-controlled-encryption-keys", action="store_true")
    parser.add_argument("--attest-real-execution-owner-confirmed", action="store_true")


def _attestations(args: argparse.Namespace) -> OwnerRunnerAttestations:
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
        owner_controlled_private_storage=bool(
            getattr(args, "attest_owner_controlled_private_storage", False)
        ),
        owner_controlled_encryption_keys=bool(
            getattr(args, "attest_owner_controlled_encryption_keys", False)
        ),
        real_execution_owner_confirmed=bool(
            getattr(args, "attest_real_execution_owner_confirmed", False)
        ),
    )


def _retain(args: argparse.Namespace) -> int:
    config = OwnerSamplingRunnerConfig(
        mode=OwnerRunnerMode.OWNER_REAL_NETWORK,
        private_root=args.private_root,
        repository_root=args.repository_root,
        safe_manifest_output=args.safe_manifest_output,
        requested_retention_days=args.retention_days,
        confirmation_phrase=args.confirm,
        enable_real_network_fetch=args.enable_real_network_fetch,
        attestations=_attestations(args),
        policy_id=args.policy_id,
        license_snapshot_id=args.license_snapshot_id,
    )
    result = execute_real_owner_sampling(config)
    print(json.dumps(asdict(result), indent=2, sort_keys=True))
    return 0


def _delete(args: argparse.Namespace) -> int:
    config = OwnerSamplingDeletionConfig(
        private_root=args.private_root,
        repository_root=args.repository_root,
        safe_manifest_path=args.safe_manifest,
        safe_deletion_receipt_output=args.safe_deletion_receipt_output,
        confirmation_phrase=args.confirm,
        reason=args.reason,
        attestations=_attestations(args),
    )
    receipt = delete_owner_sampling_batch(config)
    safe_summary = {
        "batch_id": receipt.batch_id,
        "source_count": receipt.source_count,
        "all_raw_deleted": receipt.all_raw_deleted,
        "all_leases_deleted": receipt.all_leases_deleted,
        "secure_erase_claimed": receipt.secure_erase_claimed,
        "safe_deletion_receipt_output": str(args.safe_deletion_receipt_output),
    }
    print(json.dumps(safe_summary, indent=2, sort_keys=True))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    retain = subparsers.add_parser(
        "retain",
        help=(
            "Perform one real public-data fetch and retain the four raw responses "
            "in owner-controlled private storage."
        ),
    )
    retain.add_argument("--private-root", required=True, type=Path)
    retain.add_argument("--repository-root", required=True, type=Path)
    retain.add_argument("--safe-manifest-output", required=True, type=Path)
    retain.add_argument("--retention-days", required=True, type=int)
    retain.add_argument("--confirm", required=True, help=f"Must equal: {REAL_CONFIRMATION_PHRASE}")
    retain.add_argument("--enable-real-network-fetch", action="store_true")
    retain.add_argument("--policy-id", default="OKX_LIVE_PRIVATE_SAMPLING_V1")
    retain.add_argument(
        "--license-snapshot-id",
        default="OKX_API_AGREEMENT_2026-03-26_REVIEWED_2026-07-21_V1",
    )
    _add_common_attestations(retain)
    retain.set_defaults(handler=_retain)

    delete = subparsers.add_parser(
        "delete", help="Delete one retained batch and write a safe deletion receipt."
    )
    delete.add_argument("--private-root", required=True, type=Path)
    delete.add_argument("--repository-root", required=True, type=Path)
    delete.add_argument("--safe-manifest", required=True, type=Path)
    delete.add_argument("--safe-deletion-receipt-output", required=True, type=Path)
    delete.add_argument("--reason", required=True)
    delete.add_argument(
        "--confirm", required=True, help=f"Must equal: {DELETE_CONFIRMATION_PHRASE}"
    )
    _add_common_attestations(delete)
    delete.set_defaults(handler=_delete)

    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except OKXOwnerSamplingRunnerError as exc:
        parser.error(str(exc))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
