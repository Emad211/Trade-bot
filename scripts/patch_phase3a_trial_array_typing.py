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
        "from hybrid_trader.sharpe_robustness import sharpe_diagnostics\n",
        "from hybrid_trader.sharpe_robustness import FloatVector, sharpe_diagnostics\n",
        label="Sharpe import",
    )
    text = replace_once(
        text,
        "def aggregate_trial_sharpes(trial_metrics: pd.DataFrame) -> np.ndarray:\n",
        "def aggregate_trial_sharpes(trial_metrics: pd.DataFrame) -> FloatVector:\n",
        label="aggregate return type",
    )
    text = replace_once(
        text,
        '    values = trial_metrics.groupby(grouping, dropna=False)["sharpe"].mean().to_numpy(dtype=float)\n',
        '    values: FloatVector = np.asarray(\n'
        '        trial_metrics.groupby(grouping, dropna=False)["sharpe"]\n'
        '        .mean()\n'
        '        .to_numpy(dtype=float),\n'
        '        dtype=np.float64,\n'
        '    )\n',
        label="typed trial array",
    )
    PATH.write_text(text, encoding="utf-8")


if __name__ == "__main__":
    main()
