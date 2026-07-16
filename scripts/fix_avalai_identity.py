from __future__ import annotations

from pathlib import Path

PROVIDER = Path("src/hybrid_trader/avalai.py")
TESTS = Path("tests/test_avalai_provider.py")


def replace_once(text: str, before: str, after: str, label: str) -> str:
    if text.count(before) != 1:
        raise RuntimeError(f"Expected one {label} anchor, found {text.count(before)}")
    return text.replace(before, after, 1)


def main() -> None:
    text = PROVIDER.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "from collections.abc import Callable, Mapping\n",
        "from collections.abc import Callable, Mapping\nfrom contextlib import suppress\n",
        "contextlib import",
    )
    text = replace_once(
        text,
        '''def _call_id(payload: Mapping[str, Any]) -> str:
    identity = {
        key: value
        for key, value in payload.items()
        if key not in {"call_id", "previous_record_sha256"}
    }
    return hashlib.sha256(_canonical_json_bytes(identity)).hexdigest()
''',
        '''def _identity_value(value: Any) -> Any:
    if isinstance(value, datetime):
        normalized = value.astimezone(UTC).isoformat()
        return normalized.replace("+00:00", "Z")
    if isinstance(value, Mapping):
        return {str(key): _identity_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_identity_value(item) for item in value]
    return value


def _call_id(payload: Mapping[str, Any]) -> str:
    identity = {
        key: _identity_value(value)
        for key, value in payload.items()
        if key not in {"call_id", "previous_record_sha256"}
    }
    return hashlib.sha256(_canonical_json_bytes(identity)).hexdigest()
''',
        "call identity",
    )
    text = replace_once(
        text,
        '''            if retry_after is not None:
                try:
                    base_delay = max(base_delay, float(retry_after))
                except ValueError:
                    pass
''',
        '''            if retry_after is not None:
                with suppress(ValueError):
                    base_delay = max(base_delay, float(retry_after))
''',
        "retry-after parsing",
    )
    PROVIDER.write_text(text, encoding="utf-8")

    tests = TESTS.read_text(encoding="utf-8")
    tests = replace_once(
        tests,
        '''    with pytest.raises(ValueError, match="not allowed"):
        extractor.extract(_envelope(asset_tags=("BTC",)))
''',
        '''    with pytest.raises(AvalAIRequestError) as caught:
        extractor.extract(_envelope(asset_tags=("BTC",)))
    assert caught.value.call_record.error_code == "semantic_contract_violation"
    assert "not allowed" in str(caught.value)
''',
        "semantic contract test",
    )
    tests = tests.replace(
        'match="Invalid AvalAI|hash chain|call_id"',
        'match=r"Invalid AvalAI|hash chain|call_id"',
    )
    TESTS.write_text(tests, encoding="utf-8")


if __name__ == "__main__":
    main()
