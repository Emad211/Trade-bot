from __future__ import annotations

from pathlib import Path

PATH = Path("src/hybrid_trader/phase3g_overlap.py")


def replace_once(text: str, before: str, after: str, *, label: str) -> str:
    if text.count(before) != 1:
        raise RuntimeError(f"Expected one {label} anchor, found {text.count(before)}")
    return text.replace(before, after, 1)


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    text = replace_once(
        text,
        '''    spot_factory: SpotFactory | None = None,
    recorded_at: datetime | None = None,
) -> Phase3GOverlapManifest:
''',
        '''    spot_factory: SpotFactory | None = None,
    trajectory_path: str | Path | None = None,
    recorded_at: datetime | None = None,
) -> Phase3GOverlapManifest:
''',
        label="overlap signature",
    )
    text = replace_once(
        text,
        '''    collector_kwargs: dict[str, object] = {
        "source_commit_sha": source_commit_sha,
        "retrieved_at": recorded_at,
    }
    if spot_factory is not None:
        collector_kwargs["spot_factory"] = spot_factory
    market_manifest = collect_phase3g_market(
        market_spec,
        market_root,
        **collector_kwargs,
    )
''',
        '''    if spot_factory is None:
        market_manifest = collect_phase3g_market(
            market_spec,
            market_root,
            source_commit_sha=source_commit_sha,
            retrieved_at=recorded_at,
        )
    else:
        market_manifest = collect_phase3g_market(
            market_spec,
            market_root,
            source_commit_sha=source_commit_sha,
            spot_factory=spot_factory,
            retrieved_at=recorded_at,
        )
''',
        label="typed collector call",
    )
    text = replace_once(
        text,
        '''    trajectory_path = root / "state" / "maturity_trajectory.jsonl"
    trajectory_before = verify_phase3g_trajectory(trajectory_path)
''',
        '''    trajectory_ledger = (
        Path(trajectory_path)
        if trajectory_path is not None
        else root / "state" / "maturity_trajectory.jsonl"
    )
    trajectory_before = verify_phase3g_trajectory(trajectory_ledger)
''',
        label="trajectory path resolution",
    )
    text = replace_once(
        text,
        "    trajectory_after = append_phase3g_trajectory(trajectory_path, entry)\n",
        "    trajectory_after = append_phase3g_trajectory(trajectory_ledger, entry)\n",
        label="trajectory append",
    )
    PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
