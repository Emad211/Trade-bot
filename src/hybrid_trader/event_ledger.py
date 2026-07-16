"""Tamper-evident prospective ledgers for raw event metadata."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from hybrid_trader.event_documents import ProspectiveDocument


def _canonical_line(document: ProspectiveDocument) -> bytes:
    payload = json.dumps(
        document.model_dump(mode="json"),
        sort_keys=True,
        separators=(",", ":"),
    )
    return (payload + "\n").encode("utf-8")


def document_record_sha256(document: ProspectiveDocument) -> str:
    return hashlib.sha256(_canonical_line(document)).hexdigest()


def verify_document_ledger(
    path: str | Path,
) -> tuple[str | None, ProspectiveDocument | None, int, frozenset[str]]:
    ledger = Path(path)
    if not ledger.exists():
        return None, None, 0, frozenset()
    previous_sha: str | None = None
    previous_document: ProspectiveDocument | None = None
    document_ids: set[str] = set()
    count = 0
    with ledger.open("rb") as handle:
        for line_number, raw in enumerate(handle, start=1):
            if not raw.endswith(b"\n"):
                raise ValueError(f"Event ledger line {line_number} is not newline-terminated")
            try:
                document = ProspectiveDocument.model_validate_json(raw)
            except Exception as exc:
                raise ValueError(f"Invalid event ledger line {line_number}") from exc
            if document.previous_record_sha256 != previous_sha:
                raise ValueError(f"Event ledger hash chain breaks at line {line_number}")
            if document.document_id in document_ids:
                raise ValueError(f"Duplicate document ID at line {line_number}")
            if previous_document is not None:
                if document.retrieved_at < previous_document.retrieved_at:
                    raise ValueError("Event retrieval times cannot move backward")
                if document.retrieved_at == previous_document.retrieved_at and (
                    document.source_id,
                    document.document_id,
                ) <= (previous_document.source_id, previous_document.document_id):
                    raise ValueError("Equal-time event records must use canonical source/ID order")
            previous_sha = document_record_sha256(document)
            previous_document = document
            document_ids.add(document.document_id)
            count += 1
    return previous_sha, previous_document, count, frozenset(document_ids)


def load_document_index(path: str | Path) -> dict[str, ProspectiveDocument]:
    ledger = Path(path)
    verify_document_ledger(ledger)
    if not ledger.exists():
        return {}
    index: dict[str, ProspectiveDocument] = {}
    with ledger.open("rb") as handle:
        for raw in handle:
            document = ProspectiveDocument.model_validate_json(raw)
            index[document.document_id] = document
    return index


def append_documents(
    path: str | Path,
    documents: tuple[ProspectiveDocument, ...] | list[ProspectiveDocument],
) -> tuple[int, str | None]:
    """Append unseen documents in deterministic order and fsync once."""

    ledger = Path(path)
    ledger.parent.mkdir(parents=True, exist_ok=True)
    head, previous, _, existing_ids = verify_document_ledger(ledger)
    existing = load_document_index(ledger)
    for document in documents:
        stored = existing.get(document.document_id)
        if stored is None:
            continue
        if (
            stored.source_quality != document.source_quality
            or stored.asset_tags != document.asset_tags
            or stored.source_id != document.source_id
        ):
            raise ValueError(
                "Existing document identity was observed under conflicting source metadata"
            )
    pending = [document for document in documents if document.document_id not in existing_ids]
    pending.sort(key=lambda item: (item.retrieved_at, item.source_id, item.document_id))
    if not pending:
        return 0, head
    if previous is not None and pending[0].retrieved_at < previous.retrieved_at:
        raise ValueError("New event retrieval time predates the current ledger head")

    payloads: list[bytes] = []
    next_head = head
    last_sort_key = (
        (previous.retrieved_at, previous.source_id, previous.document_id)
        if previous is not None
        else None
    )
    for item in pending:
        sort_key = (item.retrieved_at, item.source_id, item.document_id)
        if last_sort_key is not None and sort_key <= last_sort_key:
            raise ValueError("New event records are not strictly ordered")
        chained = item.model_copy(update={"previous_record_sha256": next_head})
        payload = _canonical_line(chained)
        payloads.append(payload)
        next_head = hashlib.sha256(payload).hexdigest()
        last_sort_key = sort_key

    descriptor = os.open(ledger, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        for payload in payloads:
            os.write(descriptor, payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    return len(payloads), next_head
