"""Public derivatives feature collection through CCXT unified methods."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, cast

import numpy as np
import pandas as pd

from hybrid_trader.data.schema import MarketDataError
from hybrid_trader.data.timeframe import timeframe_to_timedelta


class UnsupportedPublicEndpoint(RuntimeError):
    """Raised when a venue lacks a requested unified public endpoint."""


def _timestamped_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("timestamp") is not None]


def _validate_source_latency(source_latency: timedelta) -> None:
    if source_latency < timedelta(0):
        raise ValueError("source_latency cannot be negative")


@dataclass
class CCXTDerivativesSource:
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

    @staticmethod
    def _require(exchange: Any, capability: str, method_name: str) -> Callable[..., Any]:
        if not bool(getattr(exchange, "has", {}).get(capability)):
            raise UnsupportedPublicEndpoint(
                f"{getattr(exchange, 'id', 'exchange')} does not advertise {capability}"
            )
        method = getattr(exchange, method_name, None)
        if method is None:
            raise UnsupportedPublicEndpoint(f"CCXT method {method_name} is unavailable")
        return cast(Callable[..., Any], method)

    @staticmethod
    def _paginate(
        method: Callable[..., Any],
        *,
        symbol: str,
        since_ms: int | None,
        until_ms: int | None,
        limit: int,
        max_pages: int,
        extra_args: tuple[Any, ...] = (),
        params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        cursor = since_ms
        for _ in range(max_pages):
            batch = method(symbol, *extra_args, cursor, limit, params or {})
            if not batch:
                break
            rows.extend(batch)
            timestamps = [
                int(item["timestamp"]) for item in batch if item.get("timestamp") is not None
            ]
            if not timestamps:
                break
            newest = max(timestamps)
            if until_ms is not None and newest >= until_ms:
                break
            next_cursor = newest + 1
            if cursor is not None and next_cursor <= cursor:
                break
            cursor = next_cursor
            if len(batch) < limit:
                break
        return rows

    def fetch_funding_history(
        self,
        symbol: str,
        *,
        since_ms: int | None = None,
        until_ms: int | None = None,
        limit: int = 200,
        max_pages: int = 100,
        source_latency: timedelta = timedelta(minutes=1),
        params: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        _validate_source_latency(source_latency)
        exchange = self._build_exchange()
        method = self._require(exchange, "fetchFundingRateHistory", "fetch_funding_rate_history")
        rows = self._paginate(
            method,
            symbol=symbol,
            since_ms=since_ms,
            until_ms=until_ms,
            limit=limit,
            max_pages=max_pages,
            params=params,
        )
        rows = _timestamped_rows(rows)
        if not rows:
            raise RuntimeError("Exchange returned no funding history")
        frame = pd.DataFrame(
            {
                "event_time": pd.to_datetime(
                    np.asarray([int(row["timestamp"]) for row in rows], dtype=np.int64),
                    unit="ms",
                    utc=True,
                ),
                "funding_rate": pd.to_numeric(
                    [row.get("fundingRate") for row in rows], errors="coerce"
                ),
            }
        ).dropna()
        if until_ms is not None:
            frame = frame.loc[frame["event_time"] <= pd.to_datetime(until_ms, unit="ms", utc=True)]
        frame = frame.sort_values("event_time").drop_duplicates("event_time", keep="last")
        if frame.empty:
            raise RuntimeError("No funding rows remain in the requested interval")
        if not np.isfinite(frame["funding_rate"].to_numpy(dtype=float)).all():
            raise MarketDataError("Funding history contains non-finite values")
        frame["available_at"] = frame["event_time"] + pd.Timedelta(source_latency)
        return frame.reset_index(drop=True)

    def fetch_open_interest_history(
        self,
        symbol: str,
        timeframe: str,
        *,
        since_ms: int | None = None,
        until_ms: int | None = None,
        limit: int = 200,
        max_pages: int = 100,
        source_latency: timedelta = timedelta(minutes=1),
        params: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        _validate_source_latency(source_latency)
        exchange = self._build_exchange()
        method = self._require(exchange, "fetchOpenInterestHistory", "fetch_open_interest_history")
        rows = self._paginate(
            method,
            symbol=symbol,
            since_ms=since_ms,
            until_ms=until_ms,
            limit=limit,
            max_pages=max_pages,
            extra_args=(timeframe,),
            params=params,
        )
        rows = _timestamped_rows(rows)
        if not rows:
            raise RuntimeError("Exchange returned no open-interest history")
        values: list[float | None] = []
        for row in rows:
            value = row.get("openInterestValue")
            if value is None:
                value = row.get("openInterestAmount")
            values.append(value)
        frame = pd.DataFrame(
            {
                "event_time": pd.to_datetime(
                    np.asarray([int(row["timestamp"]) for row in rows], dtype=np.int64),
                    unit="ms",
                    utc=True,
                ),
                "open_interest": pd.to_numeric(values, errors="coerce"),
            }
        ).dropna()
        if until_ms is not None:
            frame = frame.loc[frame["event_time"] <= pd.to_datetime(until_ms, unit="ms", utc=True)]
        frame = frame.sort_values("event_time").drop_duplicates("event_time", keep="last")
        if frame.empty:
            raise RuntimeError("No open-interest rows remain in the requested interval")
        open_interest = frame["open_interest"].to_numpy(dtype=float)
        if not np.isfinite(open_interest).all() or (open_interest < 0).any():
            raise MarketDataError("Open-interest history must be finite and non-negative")
        interval = pd.Timedelta(timeframe_to_timedelta(timeframe))
        frame["available_at"] = frame["event_time"] + interval + pd.Timedelta(source_latency)
        return frame.reset_index(drop=True)

    def fetch_basis_history(
        self,
        symbol: str,
        timeframe: str,
        *,
        since_ms: int | None = None,
        until_ms: int | None = None,
        limit: int = 1000,
        max_pages: int = 100,
        source_latency: timedelta = timedelta(minutes=1),
    ) -> pd.DataFrame:
        """Compute mark-minus-index basis from public OHLCV endpoints."""

        _validate_source_latency(source_latency)
        exchange = self._build_exchange()
        mark_method = getattr(exchange, "fetch_mark_ohlcv", None)
        index_method = getattr(exchange, "fetch_index_ohlcv", None)
        if (mark_method is None or index_method is None) and (
            not bool(getattr(exchange, "has", {}).get("fetchMarkOHLCV"))
            or not bool(getattr(exchange, "has", {}).get("fetchIndexOHLCV"))
        ):
            raise UnsupportedPublicEndpoint("Venue lacks mark/index OHLCV history")

        def fetch(method: Callable[..., Any] | None, price: str) -> pd.DataFrame:
            rows: list[list[float]] = []
            cursor = since_ms
            for _ in range(max_pages):
                if method is not None:
                    batch = method(symbol, timeframe, cursor, limit, {})
                else:  # pragma: no cover - compatibility path
                    batch = exchange.fetch_ohlcv(symbol, timeframe, cursor, limit, {"price": price})
                if not batch:
                    break
                rows.extend(batch)
                newest = int(batch[-1][0])
                if until_ms is not None and newest >= until_ms:
                    break
                cursor = newest + 1
                if len(batch) < limit:
                    break
            data = pd.DataFrame(
                rows, columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            if data.empty:
                return pd.DataFrame(columns=["event_time", "close"])
            data["event_time"] = pd.to_datetime(data["timestamp"], unit="ms", utc=True)
            return data[["event_time", "close"]].drop_duplicates("event_time", keep="last")

        mark = fetch(mark_method, "mark").rename(columns={"close": "mark_price"})
        index = fetch(index_method, "index").rename(columns={"close": "index_price"})
        merged = mark.merge(index, on="event_time", how="inner").sort_values("event_time")
        if merged.empty:
            raise RuntimeError("No overlapping mark and index history")
        if until_ms is not None:
            merged = merged.loc[
                merged["event_time"] <= pd.to_datetime(until_ms, unit="ms", utc=True)
            ]
        if merged.empty:
            raise RuntimeError("No basis rows remain in the requested interval")
        prices = merged[["mark_price", "index_price"]].to_numpy(dtype=float)
        if not np.isfinite(prices).all() or (prices <= 0).any():
            raise MarketDataError("Basis prices must be finite and positive")
        merged["basis"] = merged["mark_price"] / merged["index_price"] - 1.0
        if not np.isfinite(merged["basis"].to_numpy(dtype=float)).all():
            raise MarketDataError("Basis history contains non-finite values")
        interval = pd.Timedelta(timeframe_to_timedelta(timeframe))
        merged["available_at"] = merged["event_time"] + interval + pd.Timedelta(source_latency)
        return merged.reset_index(drop=True)
