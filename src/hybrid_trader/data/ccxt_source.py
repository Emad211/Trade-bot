"""Optional public OHLCV downloader backed by CCXT."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from hybrid_trader.data.schema import normalize_ohlcv


@dataclass(frozen=True)
class CCXTOHLCVSource:
    """Download public candles without requiring exchange credentials."""

    exchange_id: str
    enable_rate_limit: bool = True
    exchange_options: dict[str, Any] = field(default_factory=dict)

    def fetch(
        self,
        symbol: str,
        timeframe: str,
        *,
        since_ms: int | None = None,
        until_ms: int | None = None,
        page_limit: int = 1000,
        max_pages: int = 100,
    ) -> pd.DataFrame:
        try:
            import ccxt
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("Install exchange support with: pip install -e '.[exchange]'") from exc

        if not hasattr(ccxt, self.exchange_id):
            raise ValueError(f"Unknown CCXT exchange: {self.exchange_id}")

        exchange_class = getattr(ccxt, self.exchange_id)
        exchange = exchange_class(
            {"enableRateLimit": self.enable_rate_limit, **self.exchange_options}
        )
        rows: list[list[float]] = []
        cursor = since_ms

        for _ in range(max_pages):
            batch = exchange.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                since=cursor,
                limit=page_limit,
            )
            if not batch:
                break
            rows.extend(batch)
            newest = int(batch[-1][0])
            if until_ms is not None and newest >= until_ms:
                break
            next_cursor = newest + 1
            if cursor is not None and next_cursor <= cursor:
                break
            cursor = next_cursor
            if len(batch) < page_limit:
                break

        columns = ["timestamp", "open", "high", "low", "close", "volume"]
        frame = pd.DataFrame(rows, columns=columns)
        if frame.empty:
            raise RuntimeError("Exchange returned no OHLCV rows")
        if until_ms is not None:
            frame = frame.loc[frame["timestamp"] <= until_ms]
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], unit="ms", utc=True)
        return normalize_ohlcv(frame.drop_duplicates(subset="timestamp", keep="last"))
