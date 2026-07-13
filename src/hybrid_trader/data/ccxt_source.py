"""Optional public OHLCV downloader backed by CCXT."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd

from hybrid_trader.data.point_in_time import (
    add_bar_availability,
    closed_bars_as_of,
    validate_point_in_time_bars,
)
from hybrid_trader.data.schema import normalize_ohlcv
from hybrid_trader.data.timeframe import timeframe_to_timedelta


@dataclass
class CCXTOHLCVSource:
    """Download public, completed candles without requiring exchange credentials."""

    exchange_id: str
    enable_rate_limit: bool = True
    exchange_options: dict[str, Any] = field(default_factory=dict)

    def _build_exchange(self) -> Any:
        try:
            import ccxt
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "Install exchange support with: pip install -e '.[exchange]'"
            ) from exc
        if not hasattr(ccxt, self.exchange_id):
            raise ValueError(f"Unknown CCXT exchange: {self.exchange_id}")
        exchange_class = getattr(ccxt, self.exchange_id)
        return exchange_class({"enableRateLimit": self.enable_rate_limit, **self.exchange_options})

    def fetch(
        self,
        symbol: str,
        timeframe: str,
        *,
        since_ms: int | None = None,
        until_ms: int | None = None,
        page_limit: int = 1000,
        max_pages: int = 100,
        drop_incomplete: bool = True,
        now: datetime | None = None,
    ) -> pd.DataFrame:
        exchange = self._build_exchange()
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
        normalized = normalize_ohlcv(frame.drop_duplicates(subset="timestamp", keep="last"))
        if drop_incomplete:
            observed_now = now or datetime.now(UTC)
            close_cutoff = pd.Timestamp(observed_now) - pd.Timedelta(
                timeframe_to_timedelta(timeframe)
            )
            normalized = normalized.loc[normalized.index <= close_cutoff]
            if normalized.empty:
                raise RuntimeError("No completed OHLCV bars remain after filtering")
        return normalized

    def fetch_point_in_time(
        self,
        symbol: str,
        timeframe: str,
        *,
        source_latency: timedelta = timedelta(seconds=30),
        since_ms: int | None = None,
        until_ms: int | None = None,
        page_limit: int = 1000,
        max_pages: int = 100,
        now: datetime | None = None,
    ) -> pd.DataFrame:
        raw = self.fetch(
            symbol,
            timeframe,
            since_ms=since_ms,
            until_ms=until_ms,
            page_limit=page_limit,
            max_pages=max_pages,
            drop_incomplete=True,
            now=now,
        )
        pit = add_bar_availability(
            raw.reset_index(), timeframe=timeframe, source_latency=source_latency
        )
        observed_now = now or datetime.now(UTC)
        observable = closed_bars_as_of(pit, pd.Timestamp(observed_now))
        if observable.empty:
            raise RuntimeError("No point-in-time bars are observable after source latency")
        return validate_point_in_time_bars(observable, timeframe=timeframe)
