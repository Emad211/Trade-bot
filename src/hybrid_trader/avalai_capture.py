"""Phase 3C orchestration for AvalAI semantic extraction over prospective feeds."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from hybrid_trader.avalai import (
    AvalAICallRecord,
    AvalAISettings,
    AvalAIStructuredExtractor,
    AvalAITransport,
    append_avalai_call_records,
    verify_avalai_call_ledger,
)
from hybrid_trader.event_capture import FeedFactory, capture_events
from hybrid_trader.event_capture_models import (
    EventCaptureFailure,
    EventCaptureManifest,
    EventCaptureSpec,
)
from hybrid_trader.event_capture_state import canonical_sha256
from hybrid_trader.semantic_extraction import verify_semantic_ledger

_SECRET_BYTES = re.compile(
    rb"(?i)(?:authorization\s*[:=]|bearer\s+|\b(?:aa|sk)-[A-Za-z0-9_-]{6,})"
)


class Phase3CAvalAIConfig(BaseModel):
    """Secret-free configuration committed to Git."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    capture: EventCaptureSpec
    avalai: AvalAISettings

    @model_validator(mode="after")
    def validate_provider_contract(self) -> Phase3CAvalAIConfig:
        if self.capture.extractor != "avalai_structured":
            raise ValueError("Phase 3C capture.extractor must be avalai_structured")
        return self


class AvalAIProviderRunManifest(BaseModel):
    """Compact, secret-free evidence for one AvalAI-backed capture."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: str = "1.0"
    provider_run_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    capture_id: str = Field(pattern=r"^[0-9a-f]{64}$")
    capture_status: Literal["success", "failed"]
    capture_manifest_relative_path: str
    config_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    settings_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    endpoint: str
    route: str
    model: str
    model_revision: str
    extractor_model_id: str
    prompt_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    call_ledger_relative_path: str
    call_ledger_head_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    call_count_before: int = Field(ge=0)
    call_count_after: int = Field(ge=0)
    new_call_count: int = Field(ge=0)
    successful_call_count: int = Field(ge=0)
    failed_call_count: int = Field(ge=0)
    new_call_ids: tuple[str, ...]
    prospective_decisions_created: bool = False
    secret_material_persisted: bool = False
    raw_provider_responses_persisted: bool = False

    @model_validator(mode="after")
    def validate_provider_run(self) -> AvalAIProviderRunManifest:
        if self.call_count_after < self.call_count_before:
            raise ValueError("AvalAI call count cannot move backward")
        if self.new_call_count != self.call_count_after - self.call_count_before:
            raise ValueError("AvalAI new_call_count does not match the ledger delta")
        if self.new_call_count != len(self.new_call_ids):
            raise ValueError("AvalAI new_call_ids does not match new_call_count")
        if self.successful_call_count + self.failed_call_count != self.new_call_count:
            raise ValueError("AvalAI call status counts do not match new_call_count")
        if len(set(self.new_call_ids)) != len(self.new_call_ids):
            raise ValueError("AvalAI new_call_ids cannot contain duplicates")
        if self.prospective_decisions_created:
            raise ValueError("AvalAI capture cannot create prospective decisions")
        if self.secret_material_persisted:
            raise ValueError("AvalAI capture cannot persist secret material")
        if self.raw_provider_responses_persisted:
            raise ValueError("AvalAI capture cannot persist raw provider responses")
        return self


class Phase3CAvalAIResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    capture: EventCaptureManifest
    provider: AvalAIProviderRunManifest


def load_phase3c_avalai_config(path: str | Path) -> Phase3CAvalAIConfig:
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"AvalAI capture config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as handle:
        payload: Any = yaml.safe_load(handle) or {}
    return Phase3CAvalAIConfig.model_validate(payload)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _call_records(path: Path) -> tuple[AvalAICallRecord, ...]:
    if not path.exists():
        return ()
    return tuple(
        AvalAICallRecord.model_validate_json(line)
        for line in path.read_bytes().splitlines()
        if line
    )


def _write_provider_manifest(root: Path, manifest: AvalAIProviderRunManifest) -> Path:
    run_root = root / "state" / "avalai_runs" / manifest.capture_id
    if run_root.exists():
        raise FileExistsError(f"AvalAI provider run is immutable: {run_root}")
    run_root.mkdir(parents=True)
    manifest_path = run_root / "provider_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (run_root / "SHA256SUMS").write_text(
        f"{_sha256(manifest_path)}  provider_manifest.json\n",
        encoding="utf-8",
    )
    return manifest_path


def capture_avalai_events(
    config: Phase3CAvalAIConfig,
    output_dir: str | Path,
    *,
    api_key: str | None = None,
    feed_factory: FeedFactory | None = None,
    transport: AvalAITransport | None = None,
    extractor_factory: Callable[[], AvalAIStructuredExtractor] | None = None,
) -> Phase3CAvalAIResult:
    """Run a real-time AvalAI capture and persist only secret-free provider metadata."""

    root = Path(output_dir)
    state_root = root / "state"
    state_root.mkdir(parents=True, exist_ok=True)
    call_ledger = state_root / "avalai_calls.jsonl"
    before = verify_avalai_call_ledger(call_ledger)

    if extractor_factory is not None:
        extractor = extractor_factory()
    else:
        extractor_kwargs: dict[str, Any] = {"api_key": api_key}
        if transport is not None:
            extractor_kwargs["transport"] = transport
        extractor = AvalAIStructuredExtractor(config.avalai, **extractor_kwargs)

    capture_manifest: EventCaptureManifest | None = None
    capture_failure: EventCaptureFailure | None = None
    try:
        capture_kwargs: dict[str, Any] = {"extractor_factory": lambda: extractor}
        if feed_factory is not None:
            capture_kwargs["feed_factory"] = feed_factory
        capture_manifest = capture_events(config.capture, root, **capture_kwargs)
    except EventCaptureFailure as exc:
        capture_failure = exc
        capture_manifest = EventCaptureManifest.model_validate_json(
            exc.manifest_path.read_text(encoding="utf-8")
        )
    finally:
        append_avalai_call_records(call_ledger, extractor.call_records)

    if capture_manifest is None:  # pragma: no cover - defensive invariant
        raise RuntimeError("AvalAI capture did not produce a capture manifest")

    after = verify_avalai_call_ledger(call_ledger)
    existing_ids = before.call_ids
    new_records = tuple(
        record for record in _call_records(call_ledger) if record.call_id not in existing_ids
    )
    settings_payload = config.avalai.model_dump(mode="json")
    config_sha = canonical_sha256(config.model_dump(mode="json"))
    settings_sha = canonical_sha256(settings_payload)
    identity = {
        "capture_id": capture_manifest.capture_id,
        "config_sha256": config_sha,
        "settings_sha256": settings_sha,
        "call_ledger_head_sha256": after.head_sha256,
        "new_call_ids": [record.call_id for record in new_records],
    }
    provider = AvalAIProviderRunManifest(
        provider_run_id=canonical_sha256(identity),
        capture_id=capture_manifest.capture_id,
        capture_status=capture_manifest.status,
        capture_manifest_relative_path=(
            f"state/captures/{capture_manifest.capture_id}/capture_manifest.json"
        ),
        config_sha256=config_sha,
        settings_sha256=settings_sha,
        endpoint=config.avalai.endpoint,
        route=config.avalai.route,
        model=config.avalai.model,
        model_revision=config.avalai.model_revision,
        extractor_model_id=extractor.model_id,
        prompt_sha256=extractor.prompt_sha256,
        call_ledger_relative_path="state/avalai_calls.jsonl",
        call_ledger_head_sha256=after.head_sha256,
        call_count_before=before.count,
        call_count_after=after.count,
        new_call_count=len(new_records),
        successful_call_count=sum(record.status == "success" for record in new_records),
        failed_call_count=sum(record.status == "failed" for record in new_records),
        new_call_ids=tuple(record.call_id for record in new_records),
    )
    _write_provider_manifest(root, provider)
    result = Phase3CAvalAIResult(capture=capture_manifest, provider=provider)
    if capture_failure is not None:
        raise capture_failure
    return result


def verify_phase3c_avalai_root(root: str | Path) -> dict[str, object]:
    """Verify provider provenance, capture linkage and the non-activation boundary."""

    capture_root = Path(root)
    state_root = capture_root / "state"
    decisions = state_root / "prospective_decisions.jsonl"
    if not decisions.is_file() or decisions.read_text(encoding="utf-8").strip():
        raise RuntimeError("Prospective decision ledger must exist and remain empty")

    call_ledger = state_root / "avalai_calls.jsonl"
    call_state = verify_avalai_call_ledger(call_ledger)
    calls = _call_records(call_ledger)
    calls_by_id = {record.call_id: record for record in calls}
    semantic_state = verify_semantic_ledger(state_root / "semantic_events.jsonl")
    for record in calls:
        if record.status == "success" and record.extraction_key not in semantic_state.extraction_keys:
            raise RuntimeError("Successful AvalAI call has no matching semantic record")

    run_manifests: list[AvalAIProviderRunManifest] = []
    runs_root = state_root / "avalai_runs"
    if not runs_root.is_dir():
        raise RuntimeError("No AvalAI provider-run manifests were found")
    for run_root in sorted(path for path in runs_root.iterdir() if path.is_dir()):
        manifest_path = run_root / "provider_manifest.json"
        manifest = AvalAIProviderRunManifest.model_validate_json(
            manifest_path.read_text(encoding="utf-8")
        )
        if manifest.capture_id != run_root.name:
            raise RuntimeError("AvalAI provider run directory disagrees with its manifest")
        expected_inventory = f"{_sha256(manifest_path)}  provider_manifest.json"
        if (run_root / "SHA256SUMS").read_text(encoding="utf-8").strip() != expected_inventory:
            raise RuntimeError("AvalAI provider-run checksum inventory is invalid")
        capture_manifest = capture_root / manifest.capture_manifest_relative_path
        if not capture_manifest.is_file():
            raise FileNotFoundError("Referenced event capture manifest is missing")
        parsed_capture = EventCaptureManifest.model_validate_json(
            capture_manifest.read_text(encoding="utf-8")
        )
        if parsed_capture.capture_id != manifest.capture_id:
            raise RuntimeError("AvalAI provider manifest references a different capture")
        if parsed_capture.extractor_model_id != manifest.extractor_model_id:
            raise RuntimeError("AvalAI extractor identity disagrees with event capture")
        if parsed_capture.extractor_model_revision != manifest.model_revision:
            raise RuntimeError("AvalAI model revision disagrees with event capture")
        if parsed_capture.extractor_prompt_sha256 != manifest.prompt_sha256:
            raise RuntimeError("AvalAI prompt hash disagrees with event capture")
        if any(call_id not in calls_by_id for call_id in manifest.new_call_ids):
            raise RuntimeError("AvalAI provider manifest references an unknown call")
        run_manifests.append(manifest)

    if not run_manifests:
        raise RuntimeError("No valid AvalAI provider-run manifests were found")
    latest = max(run_manifests, key=lambda item: (item.call_count_after, item.capture_id))
    if latest.call_count_after != call_state.count:
        raise RuntimeError("Latest AvalAI provider manifest does not match call-ledger count")
    if latest.call_ledger_head_sha256 != call_state.head_sha256:
        raise RuntimeError("Latest AvalAI provider manifest does not match call-ledger head")

    for path in state_root.rglob("*"):
        if path.is_file() and _SECRET_BYTES.search(path.read_bytes()):
            raise RuntimeError(f"Possible secret material found in AvalAI state: {path}")

    return {
        "provider_run_count": len(run_manifests),
        "call_count": call_state.count,
        "successful_call_count": sum(record.status == "success" for record in calls),
        "failed_call_count": sum(record.status == "failed" for record in calls),
        "semantic_record_count": semantic_state.count,
        "call_ledger_head_sha256": call_state.head_sha256,
        "prospective_decision_count": 0,
        "secret_material_persisted": False,
    }
