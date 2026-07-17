from __future__ import annotations

from pathlib import Path


def replace_once(path: Path, before: str, after: str, *, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(before) != 1:
        raise RuntimeError(f"Expected one {label} anchor, found {text.count(before)}")
    path.write_text(text.replace(before, after, 1), encoding="utf-8")


def patch_event_capture() -> None:
    path = Path("src/hybrid_trader/event_capture.py")
    replace_once(
        path,
        '''    feed_factory: FeedFactory = _default_feed_factory,
    extractor_factory: ExtractorFactory = _default_extractor_factory,
) -> EventCaptureManifest:
''',
        '''    feed_factory: FeedFactory = _default_feed_factory,
    extractor_factory: ExtractorFactory = _default_extractor_factory,
    maximum_new_semantic_records: int | None = None,
) -> EventCaptureManifest:
''',
        label="capture signature",
    )
    replace_once(
        path,
        '''    if captured_at is not None and captured_at.tzinfo is None:
        raise ValueError("captured_at must be timezone-aware")
    root = Path(output_dir)
''',
        '''    if captured_at is not None and captured_at.tzinfo is None:
        raise ValueError("captured_at must be timezone-aware")
    if maximum_new_semantic_records is not None and maximum_new_semantic_records < 1:
        raise ValueError("maximum_new_semantic_records must be positive")
    root = Path(output_dir)
''',
        label="capture budget validation",
    )
    replace_once(
        path,
        '''                if extraction_key in semantic_state.extraction_keys:
                    continue
                if envelope.document.document_id in existing_document_ids:
''',
        '''                if extraction_key in semantic_state.extraction_keys:
                    continue
                if (
                    maximum_new_semantic_records is not None
                    and len(records_to_append) >= maximum_new_semantic_records
                ):
                    break
                if envelope.document.document_id in existing_document_ids:
''',
        label="pre-call semantic budget",
    )


def patch_avalai_capture() -> None:
    path = Path("src/hybrid_trader/avalai_capture.py")
    replace_once(
        path,
        '''    transport: AvalAITransport | None = None,
    extractor_factory: Callable[[], AvalAIStructuredExtractor] | None = None,
) -> Phase3CAvalAIResult:
''',
        '''    transport: AvalAITransport | None = None,
    extractor_factory: Callable[[], AvalAIStructuredExtractor] | None = None,
    maximum_new_semantic_records: int | None = None,
) -> Phase3CAvalAIResult:
''',
        label="AvalAI capture signature",
    )
    replace_once(
        path,
        '''        capture_kwargs: dict[str, Any] = {"extractor_factory": lambda: extractor}
        if feed_factory is not None:
            capture_kwargs["feed_factory"] = feed_factory
''',
        '''        capture_kwargs: dict[str, Any] = {"extractor_factory": lambda: extractor}
        if feed_factory is not None:
            capture_kwargs["feed_factory"] = feed_factory
        if maximum_new_semantic_records is not None:
            capture_kwargs["maximum_new_semantic_records"] = maximum_new_semantic_records
''',
        label="AvalAI capture budget forwarding",
    )


def patch_cli() -> None:
    path = Path("scripts/capture_phase3c_avalai_events.py")
    replace_once(
        path,
        '''    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
''',
        '''    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--maximum-new-semantic-records", type=int)
    args = parser.parse_args()
''',
        label="capture CLI argument",
    )
    replace_once(
        path,
        '''        load_phase3c_avalai_config(args.config),
        args.output,
    )
''',
        '''        load_phase3c_avalai_config(args.config),
        args.output,
        maximum_new_semantic_records=args.maximum_new_semantic_records,
    )
''',
        label="capture CLI forwarding",
    )


if __name__ == "__main__":
    patch_event_capture()
    patch_avalai_capture()
    patch_cli()
