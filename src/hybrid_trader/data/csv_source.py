"""CSV-backed OHLCV source."""

from pathlib import Path

import pandas as pd

from hybrid_trader.data.schema import normalize_ohlcv


def read_ohlcv_csv(path: str | Path) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Market data file not found: {csv_path}")
    return normalize_ohlcv(pd.read_csv(csv_path))


def write_ohlcv_csv(frame: pd.DataFrame, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    normalized = normalize_ohlcv(frame.reset_index() if "timestamp" not in frame.columns else frame)
    normalized.reset_index().to_csv(output_path, index=False)
    return output_path
