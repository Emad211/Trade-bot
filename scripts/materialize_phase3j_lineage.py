from __future__ import annotations

from pathlib import Path


def replace_once(path: Path, before: str, after: str, *, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if after in text:
        return
    if text.count(before) != 1:
        raise RuntimeError(f"Expected one {label} anchor, found {text.count(before)}")
    path.write_text(text.replace(before, after, 1), encoding="utf-8")


def patch_lineage() -> None:
    path = Path("src/hybrid_trader/phase3i_lineage.py")
    replace_once(
        path,
        '''SemanticWorkflowName = Literal[
    "phase3e-longitudinal-events",
    "phase3h-avalai-pilot",
]

_WORKFLOW_PRIORITY: dict[str, int] = {
    "phase3e-longitudinal-events": 1,
    "phase3h-avalai-pilot": 2,
}
''',
        '''SemanticWorkflowName = Literal[
    "phase3e-longitudinal-events",
    "phase3h-avalai-pilot",
    "phase3j-diversified-longitudinal",
]

_WORKFLOW_PRIORITY: dict[str, int] = {
    "phase3e-longitudinal-events": 1,
    "phase3h-avalai-pilot": 2,
    "phase3j-diversified-longitudinal": 3,
}
''',
        label="Phase 3I semantic workflow registry",
    )


def patch_lineage_test() -> None:
    path = Path("tests/test_phase3i_lineage.py")
    text = path.read_text(encoding="utf-8")
    marker = "def test_phase3j_wins_when_its_artifact_is_newest() -> None:"
    if marker in text:
        return
    text += '''


def test_phase3j_wins_when_its_artifact_is_newest() -> None:
    observed = datetime(2026, 7, 18, 8, tzinfo=UTC)
    phase3e = _candidate("phase3e-longitudinal-events", 50, created_at=observed)
    phase3h = _candidate(
        "phase3h-avalai-pilot",
        51,
        created_at=observed + timedelta(hours=1),
    )
    phase3j = _candidate(
        "phase3j-diversified-longitudinal",
        52,
        created_at=observed + timedelta(hours=2),
    )
    selection = select_semantic_state(
        [phase3e, phase3h, phase3j],
        selected_at=observed + timedelta(hours=3),
    )
    assert selection.selected_candidate == phase3j
    assert set(selection.rejected_candidate_ids) == {
        phase3e.candidate_id,
        phase3h.candidate_id,
    }
'''
    path.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    patch_lineage()
    patch_lineage_test()
