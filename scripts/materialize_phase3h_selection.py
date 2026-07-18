from __future__ import annotations

from pathlib import Path


def replace_once(path: Path, before: str, after: str, *, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(before) != 1:
        raise RuntimeError(f"Expected one {label} anchor, found {text.count(before)}")
    path.write_text(text.replace(before, after, 1), encoding="utf-8")


def patch_capture() -> None:
    path = Path("src/hybrid_trader/event_capture.py")
    replace_once(
        path,
        '''from hybrid_trader.event_relevance import (
    RelevanceDecision,
    evaluate_relevance,
    relevance_decisions_sha256,
)
from hybrid_trader.feed_source import FeedFetchResult, PublicFeedSource
''',
        '''from hybrid_trader.event_relevance import (
    RelevanceDecision,
    evaluate_relevance,
    relevance_decisions_sha256,
)
from hybrid_trader.event_selection import select_semantic_envelopes
from hybrid_trader.feed_source import FeedFetchResult, PublicFeedSource
''',
        label="event selection import",
    )
    replace_once(
        path,
        '''            semantic_state = verify_semantic_ledger(semantic_ledger)
            records_to_append: list[SemanticEventRecord] = []
            for envelope in ordered_envelopes:
                extraction_key = extractor.extraction_key(envelope)
                if extraction_key in semantic_state.extraction_keys:
                    continue
                if (
                    maximum_new_semantic_records is not None
                    and len(records_to_append) >= maximum_new_semantic_records
                ):
                    break
                if envelope.document.document_id in existing_document_ids:
                    recovered_semantic_count += 1
                records_to_append.append(
                    extractor.extract(
                        envelope,
                        inference_started_at=fixed_time,
                        inference_completed_at=fixed_time,
                    )
                )
''',
        '''            semantic_state = verify_semantic_ledger(semantic_ledger)
            selected_envelopes = select_semantic_envelopes(
                ordered_envelopes,
                extraction_key=extractor.extraction_key,
                existing_extraction_keys=semantic_state.extraction_keys,
                strategy=spec.semantic_selection_strategy,
                source_order=tuple(source.source_id for source in spec.sources),
                maximum_records=maximum_new_semantic_records,
            )
            records_to_append: list[SemanticEventRecord] = []
            for envelope in selected_envelopes:
                if envelope.document.document_id in existing_document_ids:
                    recovered_semantic_count += 1
                records_to_append.append(
                    extractor.extract(
                        envelope,
                        inference_started_at=fixed_time,
                        inference_completed_at=fixed_time,
                    )
                )
''',
        label="semantic selection block",
    )


def patch_config() -> None:
    path = Path("configs/phase3c_avalai_event_sources.yaml")
    replace_once(
        path,
        '''capture:
  schema_version: "1.3"
  extractor: avalai_structured
  timeout_seconds: 30
  minimum_successful_sources: 2
''',
        '''capture:
  schema_version: "1.4"
  extractor: avalai_structured
  timeout_seconds: 30
  minimum_successful_sources: 2
  semantic_selection_strategy: source_round_robin
''',
        label="Phase 3H capture policy",
    )


if __name__ == "__main__":
    patch_capture()
    patch_config()
