from __future__ import annotations

from pathlib import Path

PATH = Path("src/hybrid_trader/candidate_robustness.py")


def replace_once(text: str, before: str, after: str, *, label: str) -> str:
    count = text.count(before)
    if count != 1:
        raise RuntimeError(f"Expected one {label} anchor, found {count}")
    return text.replace(before, after, 1)


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "        regimes = classify_market_regimes(\n",
        "        regime_labels = classify_market_regimes(\n",
        label="regime-label assignment",
    )
    text = replace_once(
        text,
        "            regimes,\n            periods_per_year=policy.periods_per_year,\n",
        "            regime_labels,\n            periods_per_year=policy.periods_per_year,\n",
        label="regime-label use",
    )
    text = replace_once(
        text,
        "    regimes = pd.concat(regime_frames, ignore_index=True)\n",
        "    regime_summary = pd.concat(regime_frames, ignore_index=True)\n",
        label="regime-summary assignment",
    )
    text = replace_once(
        text,
        '    regime_records = json.loads(regimes.to_json(orient="records"))\n',
        '    regime_records = json.loads(regime_summary.to_json(orient="records"))\n',
        label="regime-summary serialization",
    )
    text = replace_once(
        text,
        "    return summary.reset_index(drop=True), regimes, assessment\n",
        "    return summary.reset_index(drop=True), regime_summary, assessment\n",
        label="regime-summary return",
    )
    PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
