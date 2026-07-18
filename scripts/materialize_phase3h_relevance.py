from __future__ import annotations

from pathlib import Path

CAPTURE = Path("src/hybrid_trader/event_capture.py")
VERIFY = Path("scripts/verify_phase3b_events.py")


def replace_once(text: str, before: str, after: str, *, label: str) -> str:
    if text.count(before) != 1:
        raise RuntimeError(f"Expected one {label} anchor, found {text.count(before)}")
    return text.replace(before, after, 1)


def patch_capture() -> None:
    text = CAPTURE.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '''from hybrid_trader.event_ledger import append_documents, verify_document_ledger
from hybrid_trader.feed_source import FeedFetchResult, PublicFeedSource
''',
        '''from hybrid_trader.event_ledger import append_documents, verify_document_ledger
from hybrid_trader.event_relevance import (
    RelevanceDecision,
    evaluate_relevance,
    relevance_decisions_sha256,
)
from hybrid_trader.feed_source import FeedFetchResult, PublicFeedSource
''',
        label="capture relevance imports",
    )
    text = replace_once(
        text,
        '''        attempts: list[SourceCaptureAttempt] = []
        envelopes: list[DocumentEnvelope] = []
        raw_records_staging: list[tuple[str, Path, str, int]] = []
''',
        '''        attempts: list[SourceCaptureAttempt] = []
        envelopes: list[DocumentEnvelope] = []
        relevance_decisions: list[RelevanceDecision] = []
        raw_records_staging: list[tuple[str, Path, str, int]] = []
''',
        label="capture relevance state",
    )
    text = replace_once(
        text,
        '''                attempts.append(
                    SourceCaptureAttempt(
                        source_id=source_spec.source_id,
                        feed_url=source_spec.feed_url,
                        required=source_spec.required,
                        status="success",
                        retrieved_at=result.retrieved_at,
                        payload_sha256=result.payload_sha256,
                        payload_bytes=len(result.payload),
                        parsed_documents=len(result.parse_result.documents),
                        duplicate_documents=result.parse_result.duplicate_count,
                        skipped_documents=result.parse_result.skipped_count,
                        truncated_documents=result.parse_result.truncated_count,
                        warnings=result.parse_result.warnings,
                    )
                )
                envelopes.extend(result.parse_result.documents)
''',
        '''                source_relevance = tuple(
                    evaluate_relevance(envelope, source_spec.relevance)
                    for envelope in result.parse_result.documents
                )
                accepted_documents = [
                    envelope
                    for envelope, decision in zip(
                        result.parse_result.documents,
                        source_relevance,
                        strict=True,
                    )
                    if decision.accepted
                ]
                relevance_decisions.extend(source_relevance)
                attempts.append(
                    SourceCaptureAttempt(
                        source_id=source_spec.source_id,
                        feed_url=source_spec.feed_url,
                        required=source_spec.required,
                        status="success",
                        retrieved_at=result.retrieved_at,
                        payload_sha256=result.payload_sha256,
                        payload_bytes=len(result.payload),
                        parsed_documents=len(result.parse_result.documents),
                        duplicate_documents=result.parse_result.duplicate_count,
                        skipped_documents=result.parse_result.skipped_count,
                        truncated_documents=result.parse_result.truncated_count,
                        relevance_accepted_documents=len(accepted_documents),
                        relevance_rejected_documents=(
                            len(result.parse_result.documents) - len(accepted_documents)
                        ),
                        warnings=result.parse_result.warnings,
                    )
                )
                envelopes.extend(accepted_documents)
''',
        label="source relevance evaluation",
    )
    text = replace_once(
        text,
        '''        extractor = extractor_factory()
        config_sha = canonical_sha256(spec.model_dump(mode="json"))
''',
        '''        ordered_relevance_decisions = tuple(
            sorted(
                relevance_decisions,
                key=lambda item: (item.source_id, item.document_id, item.decision_id),
            )
        )
        relevance_sha = relevance_decisions_sha256(ordered_relevance_decisions)
        relevance_accepted_count = sum(
            decision.accepted for decision in ordered_relevance_decisions
        )
        relevance_rejected_count = (
            len(ordered_relevance_decisions) - relevance_accepted_count
        )
        extractor = extractor_factory()
        config_sha = canonical_sha256(spec.model_dump(mode="json"))
''',
        label="ordered relevance decisions",
    )
    text = replace_once(
        text,
        '''        identity = {
            "schema_version": "1.1",
            "status": status,
''',
        '''        identity = {
            "schema_version": "1.2",
            "status": status,
''',
        label="capture identity schema",
    )
    text = replace_once(
        text,
        '''            "semantic_ledger_head_sha256": semantic_state.head_sha256,
            "failure_type": type(failure).__name__ if failure is not None else None,
''',
        '''            "semantic_ledger_head_sha256": semantic_state.head_sha256,
            "relevance_decision_count": len(ordered_relevance_decisions),
            "relevance_accepted_document_count": relevance_accepted_count,
            "relevance_rejected_document_count": relevance_rejected_count,
            "relevance_decisions_sha256": relevance_sha,
            "failure_type": type(failure).__name__ if failure is not None else None,
''',
        label="capture identity relevance",
    )
    text = replace_once(
        text,
        '''            cross_source_duplicate_content_count=duplicate_content_count(envelopes),
            extractor_model_id=extractor.model_id,
''',
        '''            cross_source_duplicate_content_count=duplicate_content_count(envelopes),
            relevance_decision_count=len(ordered_relevance_decisions),
            relevance_accepted_document_count=relevance_accepted_count,
            relevance_rejected_document_count=relevance_rejected_count,
            relevance_decisions_sha256=relevance_sha,
            extractor_model_id=extractor.model_id,
''',
        label="capture manifest relevance",
    )
    text = replace_once(
        text,
        '''            raw_staging=raw_staging,
            manifest=manifest,
        )
''',
        '''            raw_staging=raw_staging,
            manifest=manifest,
            relevance_decisions=ordered_relevance_decisions,
        )
''',
        label="capture relevance persistence",
    )
    CAPTURE.write_text(text, encoding="utf-8")


def patch_verifier() -> None:
    text = VERIFY.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '''from hybrid_trader.event_ledger import verify_document_ledger
from hybrid_trader.semantic_extraction import verify_semantic_ledger
''',
        '''from hybrid_trader.event_ledger import verify_document_ledger
from hybrid_trader.event_relevance import (
    RelevanceDecision,
    relevance_decisions_sha256,
)
from hybrid_trader.semantic_extraction import verify_semantic_ledger
''',
        label="verifier relevance imports",
    )
    text = replace_once(
        text,
        '''def _capture_id(manifest: EventCaptureManifest) -> str:
    return canonical_sha256(
        {
            "schema_version": manifest.schema_version,
            "status": manifest.status,
            "config_sha256": manifest.config_sha256,
            "capture_started_at": manifest.capture_started_at.isoformat(),
            "capture_completed_at": manifest.capture_completed_at.isoformat(),
            "source_attempts": [
                attempt.model_dump(mode="json") for attempt in manifest.source_attempts
            ],
            "document_ledger_head_sha256": manifest.document_ledger_head_sha256,
            "semantic_ledger_head_sha256": manifest.semantic_ledger_head_sha256,
            "failure_type": manifest.failure_type,
            "failure_message": manifest.failure_message,
        }
    )
''',
        '''def _capture_id(manifest: EventCaptureManifest) -> str:
    payload: dict[str, object] = {
        "schema_version": manifest.schema_version,
        "status": manifest.status,
        "config_sha256": manifest.config_sha256,
        "capture_started_at": manifest.capture_started_at.isoformat(),
        "capture_completed_at": manifest.capture_completed_at.isoformat(),
        "source_attempts": [
            attempt.model_dump(mode="json") for attempt in manifest.source_attempts
        ],
        "document_ledger_head_sha256": manifest.document_ledger_head_sha256,
        "semantic_ledger_head_sha256": manifest.semantic_ledger_head_sha256,
        "failure_type": manifest.failure_type,
        "failure_message": manifest.failure_message,
    }
    if manifest.schema_version != "1.1":
        payload.update(
            {
                "relevance_decision_count": manifest.relevance_decision_count,
                "relevance_accepted_document_count": (
                    manifest.relevance_accepted_document_count
                ),
                "relevance_rejected_document_count": (
                    manifest.relevance_rejected_document_count
                ),
                "relevance_decisions_sha256": manifest.relevance_decisions_sha256,
            }
        )
    return canonical_sha256(payload)
''',
        label="schema-aware capture identity",
    )
    text = replace_once(
        text,
        '''        expected = {"capture_manifest.json", "raw_payloads.json", "source_attempts.json"}
        if set(inventory) != expected:
            raise RuntimeError("Unexpected compact capture checksum inventory")
''',
        '''        expected = {
            "capture_manifest.json",
            "raw_payloads.json",
            "source_attempts.json",
        }
        if manifest.schema_version != "1.1":
            expected.add("relevance_decisions.json")
        if set(inventory) != expected:
            raise RuntimeError("Unexpected compact capture checksum inventory")
''',
        label="schema-aware capture inventory",
    )
    text = replace_once(
        text,
        '''        successful_sources = {
            attempt.source_id for attempt in manifest.source_attempts if attempt.status == "success"
        }
''',
        '''        if manifest.schema_version != "1.1":
            decisions = tuple(
                RelevanceDecision.model_validate(item)
                for item in json.loads(
                    (capture_dir / "relevance_decisions.json").read_text(
                        encoding="utf-8"
                    )
                )
            )
            if len(decisions) != manifest.relevance_decision_count:
                raise RuntimeError("Capture relevance decision count does not match")
            accepted = sum(decision.accepted for decision in decisions)
            if accepted != manifest.relevance_accepted_document_count:
                raise RuntimeError("Capture accepted relevance count does not match")
            if len(decisions) - accepted != manifest.relevance_rejected_document_count:
                raise RuntimeError("Capture rejected relevance count does not match")
            if relevance_decisions_sha256(decisions) != manifest.relevance_decisions_sha256:
                raise RuntimeError("Capture relevance decision hash does not match")

        successful_sources = {
            attempt.source_id for attempt in manifest.source_attempts if attempt.status == "success"
        }
''',
        label="relevance verifier",
    )
    VERIFY.write_text(text, encoding="utf-8")


def main() -> None:
    patch_capture()
    patch_verifier()


if __name__ == "__main__":
    main()
