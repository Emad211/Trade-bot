from __future__ import annotations

from pathlib import Path


def replace_once(path: Path, before: str, after: str, *, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(before) != 1:
        raise RuntimeError(f"Expected one {label} anchor, found {text.count(before)}")
    path.write_text(text.replace(before, after, 1), encoding="utf-8")


def patch_source_admission() -> None:
    path = Path("src/hybrid_trader/source_admission.py")
    replace_once(
        path,
        '''    except Exception as exc:
        reasons.append("retrieval_or_parse_failed")
        error_type = type(exc).__name__
        error_message = str(exc)[:1000]
''',
        '''    except Exception as exc:
        reasons.append("retrieval_or_parse_failed")
        error_type = type(exc).__name__
        error_message = "Public feed retrieval or parsing failed"
''',
        label="public probe error redaction",
    )


def patch_test() -> None:
    path = Path("tests/test_phase3h_source_admission.py")
    replace_once(
        path,
        '''    assert result.error_type == "RuntimeError"
    assert result.error_message == f"offline {secret}"
    assert payload is None
    serialized = result.model_dump_json()
    assert "authorization" not in serialized.lower()
''',
        '''    assert result.error_type == "RuntimeError"
    assert result.error_message == "Public feed retrieval or parsing failed"
    assert payload is None
    serialized = result.model_dump_json()
    assert secret not in serialized
    assert "authorization" not in serialized.lower()
''',
        label="redacted error assertion",
    )


if __name__ == "__main__":
    patch_source_admission()
    patch_test()
