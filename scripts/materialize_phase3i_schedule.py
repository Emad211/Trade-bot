from __future__ import annotations

from pathlib import Path


def replace_once(path: Path, before: str, after: str, *, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if after in text:
        return
    if text.count(before) != 1:
        raise RuntimeError(f"Expected one {label} anchor, found {text.count(before)}")
    path.write_text(text.replace(before, after, 1), encoding="utf-8")


def patch_schedule() -> None:
    replace_once(
        Path(".github/workflows/phase3g-prospective-overlap.yml"),
        '''name: phase3g-prospective-overlap

on:
  workflow_dispatch:
  schedule:
    - cron: "47 7 * * 1"
  push:
''',
        '''name: phase3g-prospective-overlap

# Manual historical reproduction only; scheduled overlap moved to Phase 3I.
on:
  workflow_dispatch:
  push:
''',
        label="Phase 3G schedule transition",
    )


def patch_health_typing() -> None:
    path = Path("src/hybrid_trader/phase3i_health.py")
    replace_once(
        path,
        '''from hybrid_trader.event_capture_state import canonical_sha256
from hybrid_trader.event_ledger import load_document_index, verify_document_ledger
''',
        '''from hybrid_trader.event_capture_state import canonical_sha256
from hybrid_trader.event_documents import ProspectiveDocument
from hybrid_trader.event_ledger import load_document_index, verify_document_ledger
''',
        label="Phase 3I document type import",
    )
    replace_once(
        path,
        '''    for record in semantic_records:
        if record.document_id in semantic_by_document:
            raise ValueError("More than one semantic record exists for a document")
        if record.extraction_key in semantic_by_extraction:
            raise ValueError("Semantic state contains duplicate extraction keys")
        document = documents.get(record.document_id)
        if document is None:
            raise ValueError("Semantic record references a missing document")
        if document.source_id != record.source_id:
            raise ValueError("Semantic record source disagrees with its document")
        if document.source_quality != record.document_source_quality:
            raise ValueError("Semantic record source quality disagrees with its document")
        if document.asset_tags != record.document_asset_tags:
            raise ValueError("Semantic record asset tags disagree with its document")
        semantic_by_document[record.document_id] = record
        semantic_by_extraction[record.extraction_key] = record
''',
        '''    for semantic_record in semantic_records:
        if semantic_record.document_id in semantic_by_document:
            raise ValueError("More than one semantic record exists for a document")
        if semantic_record.extraction_key in semantic_by_extraction:
            raise ValueError("Semantic state contains duplicate extraction keys")
        document = documents.get(semantic_record.document_id)
        if document is None:
            raise ValueError("Semantic record references a missing document")
        if document.source_id != semantic_record.source_id:
            raise ValueError("Semantic record source disagrees with its document")
        if document.source_quality != semantic_record.document_source_quality:
            raise ValueError("Semantic record source quality disagrees with its document")
        if document.asset_tags != semantic_record.document_asset_tags:
            raise ValueError("Semantic record asset tags disagree with its document")
        semantic_by_document[semantic_record.document_id] = semantic_record
        semantic_by_extraction[semantic_record.extraction_key] = semantic_record
''',
        label="Phase 3I semantic record loop",
    )
    replace_once(
        path,
        '''    for record in call_records:
        destination = successful_calls if record.status == "success" else failed_calls
        if record.extraction_key in destination:
            raise ValueError("Provider ledger contains duplicate call status for an extraction")
        destination[record.extraction_key] = record
''',
        '''    for call_record in call_records:
        destination = (
            successful_calls if call_record.status == "success" else failed_calls
        )
        if call_record.extraction_key in destination:
            raise ValueError("Provider ledger contains duplicate call status for an extraction")
        destination[call_record.extraction_key] = call_record
''',
        label="Phase 3I provider call loop",
    )
    replace_once(
        path,
        '''    call_by_id = {record.call_id: record for record in call_records}
''',
        '''    call_by_id = {call_record.call_id: call_record for call_record in call_records}
''',
        label="Phase 3I call index",
    )
    replace_once(
        path,
        '''    documents_by_source: dict[str, list[object]] = defaultdict(list)
''',
        '''    documents_by_source: dict[str, list[ProspectiveDocument]] = defaultdict(list)
''',
        label="Phase 3I source document type",
    )
    replace_once(
        path,
        '''    for record in semantic_records:
        semantics_by_source[record.source_id].append(record)
''',
        '''    for semantic_record in semantic_records:
        semantics_by_source[semantic_record.source_id].append(semantic_record)
''',
        label="Phase 3I semantic source index",
    )


if __name__ == "__main__":
    patch_schedule()
    patch_health_typing()
