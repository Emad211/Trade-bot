from __future__ import annotations

import argparse
import json
import tempfile
from collections.abc import Sequence
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

from hybrid_trader.replication.okx_private_sampling import (
    ALLOWED_SOURCE_IDS,
    OwnerSamplingAuthorization,
    SamplingClock,
    SamplingExecutionMode,
    delete_sampling_batch,
    retain_sampling_batch,
)
from hybrid_trader.replication.revocable_retention import (
    ALLOWED_PURPOSE,
    PrivateRevocableArtifactStore,
    RetentionAttestation,
    RetentionPolicy,
)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)

    now = datetime.now(UTC)
    raw = {
        source_id: json.dumps(
            {
                "source": source_id,
                "synthetic_private_value": f"SYNTHETIC_DO_NOT_PUBLISH_{index}_99999.99",
            },
            sort_keys=True,
        ).encode()
        for index, source_id in enumerate(ALLOWED_SOURCE_IDS)
    }
    provider_values = [
        int(now.timestamp() * 1000) - 900,
        int(now.timestamp() * 1000) - 1200,
        int(now.timestamp() * 1000) - 300,
        int(now.timestamp() * 1000) - 700,
    ]
    clocks = {
        source_id: SamplingClock(
            request_started_at=now + timedelta(milliseconds=index * 20),
            response_received_at=now + timedelta(milliseconds=index * 20 + 10),
            provider_timestamp_ms=provider_values[index],
            research_available_at=now + timedelta(milliseconds=index * 20 + 15),
        )
        for index, source_id in enumerate(ALLOWED_SOURCE_IDS)
    }

    with tempfile.TemporaryDirectory(prefix="okx-private-sampling-") as temporary:
        temp_root = Path(temporary)
        repository = temp_root / "synthetic-repository"
        repository.mkdir()
        store = PrivateRevocableArtifactStore(
            temp_root / "owner-private-store",
            repository_root=repository,
            policy=RetentionPolicy(
                policy_id="OKX_LIVE_PRIVATE_SAMPLING_V1",
                license_snapshot_id=("OKX_API_AGREEMENT_2026-03-26_REVIEWED_2026-07-21_V1"),
                allowed_purpose=ALLOWED_PURPOSE,
                maximum_retention_days=7,
            ),
            attestation=RetentionAttestation(
                encryption_at_rest=True,
                owner_only_access=True,
                backup_and_sync_excluded=True,
                public_artifact_upload_disabled=True,
            ),
        )
        manifest = retain_sampling_batch(
            store=store,
            raw_by_source=raw,
            clocks_by_source=clocks,
            authorization=OwnerSamplingAuthorization(
                terms_reviewed=True,
                personal_noncommercial_use=True,
                reasonable_rate_and_scale=True,
                redistribution_disabled=True,
                owner_controlled_private_storage=False,
                owner_controlled_encryption_keys=False,
                real_execution_owner_confirmed=False,
            ),
            execution_mode=SamplingExecutionMode.SYNTHETIC_VALIDATION,
            requested_retention_days=2,
            now=now + timedelta(seconds=1),
        )
        active = store.assert_compliant(now=now + timedelta(hours=1))
        deletion = delete_sampling_batch(
            store=store,
            manifest=manifest,
            reason="SYNTHETIC_VALIDATION_COMPLETE",
            now=now + timedelta(hours=1),
        )
        post_delete = store.assert_compliant(now=now + timedelta(hours=2))

        evidence = {
            "schema_version": "1.0",
            "validation_id": "OKX_PRIVATE_SYNCHRONIZED_SAMPLING_CONTRACT_V1",
            "execution_mode": "SYNTHETIC_VALIDATION",
            "real_okx_request_performed": False,
            "real_raw_sampling_executed": False,
            "private_owner_storage_available_in_actions": False,
            "manifest": asdict(manifest),
            "active_compliance": {
                "compliant": active.compliant,
                "active_artifact_count": active.active_artifact_count,
            },
            "deletion": asdict(deletion),
            "post_delete_compliance": {
                "compliant": post_delete.compliant,
                "active_artifact_count": post_delete.active_artifact_count,
            },
            "synthetic_raw_values_published": False,
            "contract_outcome": "GO_OWNER_CONTROLLED_PRIVATE_OKX_SAMPLING_CONTRACT",
            "real_execution_status": "NOT_EXECUTED_REQUIRES_OWNER_PRIVATE_STORAGE_AND_KEYS",
            "authorization": {
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
    if "SYNTHETIC_DO_NOT_PUBLISH" in serialized or "synthetic_private_value" in serialized:
        raise SystemExit("Synthetic raw values leaked into safe evidence")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / "okx-private-sampling-contract-evidence.json"
    output.write_text(serialized, encoding="utf-8")
    print(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
