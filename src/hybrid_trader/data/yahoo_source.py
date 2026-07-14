"""Conservative public Yahoo chart reader for daily market-reference series."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

REVISION_POLICY = "market_price_latest_vintage"


@dataclass(frozen=True)
class YahooFetchResult:
    frame: pd.DataFrame
    url: str
    payload_sha256: str
    retrieved_at: datetime
    revision_policy: str


def _download(url: str, timeout_seconds: float) -> bytes:
    request = Request(
        url,
        headers={"User-Agent": "hybrid-trader/0.3 (+https://github.com/Emad211/Trade-bot)"},
    )
    with urlopen(request, timeout=timeout_seconds) as response:
        return bytes(response.read())


def _utc(value: pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    return timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")


@dataclass(frozen=True)
class YahooChartSource:
    """Fetch daily closes from Yahoo's public chart endpoint.

    A full-day release lag is applied by default. This intentionally avoids
    assuming that a timestamp inside Yahoo's response was usable at the start of
    that same UTC date.
    """

    symbol: str
    feature_name: str
    release_lag: timedelta = timedelta(days=1)
    source_latency: timedelta = timedelta(minutes=5)
    revision_policy: str = REVISION_POLICY
    timeout_seconds: float = 60.0

    def __post_init__(self) -> None:
        if not self.symbol or not self.feature_name:
            raise ValueError("symbol and feature_name are required")
        if self.release_lag < timedelta(0) or self.source_latency < timedelta(0):
            raise ValueError("Yahoo lag and latency cannot be negative")
        if self.revision_policy != REVISION_POLICY:
            raise ValueError("Yahoo chart is restricted to market/reference-price series")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    def url_for(self, start: pd.Timestamp, end: pd.Timestamp) -> str:
        start_utc, end_utc = _utc(start), _utc(end)
        query = urlencode(
            {
                "period1": int(start_utc.timestamp()),
                "period2": int((end_utc + pd.Timedelta(days=1)).timestamp()),
                "interval": "1d",
                "events": "history",
                "includeAdjustedClose": "true",
            }
        )
        encoded_symbol = quote(self.symbol, safe="")
        return f"https://query1.finance.yahoo.com/v8/finance/chart/{encoded_symbol}?{query}"

    def fetch(
        self,
        *,
        start: pd.Timestamp,
        end: pd.Timestamp,
        as_of: pd.Timestamp,
        downloader: Callable[[str], bytes] | None = None,
        retrieved_at: datetime | None = None,
    ) -> YahooFetchResult:
        start_utc, end_utc, as_of_utc = map(_utc, (start, end, as_of))
        if not start_utc <= end_utc <= as_of_utc:
            raise ValueError("Yahoo request requires start <= end <= as_of")
        url = self.url_for(start_utc, end_utc)
        payload = downloader(url) if downloader else _download(url, self.timeout_seconds)
        document = json.loads(payload)
        chart = document.get("chart")
        if not isinstance(chart, dict):
            raise ValueError("Yahoo payload is missing chart data")
        if chart.get("error") is not None:
            raise RuntimeError(f"Yahoo chart error: {chart['error']}")
        results = chart.get("result")
        if not isinstance(results, list) or not results:
            raise RuntimeError(f"Yahoo returned no chart result for {self.symbol}")
        result = results[0]
        timestamps = result.get("timestamp")
        indicators = result.get("indicators")
        if not isinstance(timestamps, list) or not isinstance(indicators, dict):
            raise ValueError("Yahoo chart result lacks timestamp/indicator arrays")
        quotes = indicators.get("quote")
        if not isinstance(quotes, list) or not quotes or not isinstance(quotes[0], dict):
            raise ValueError("Yahoo chart result lacks quote data")
        closes = quotes[0].get("close")
        if not isinstance(closes, list) or len(closes) != len(timestamps):
            raise ValueError("Yahoo timestamp and close arrays have different lengths")
        event = pd.to_datetime(np.asarray(timestamps, dtype=np.int64), unit="s", utc=True)
        values = pd.to_numeric(closes, errors="coerce")
        frame = pd.DataFrame({"event_time": event, self.feature_name: values}).dropna()
        frame = frame.loc[(frame.event_time >= start_utc) & (frame.event_time <= end_utc)].copy()
        frame["available_at"] = (
            frame.event_time + pd.Timedelta(self.release_lag) + pd.Timedelta(self.source_latency)
        )
        frame = frame.loc[frame.available_at <= as_of_utc].sort_values("event_time")
        frame = frame.drop_duplicates("event_time", keep="last")
        if frame.empty:
            raise RuntimeError(f"Yahoo returned no observable rows for {self.symbol}")
        values_array = frame[self.feature_name].to_numpy(dtype=float)
        if not np.isfinite(values_array).all() or (values_array <= 0).any():
            raise ValueError("Yahoo reference prices must be finite and positive")
        stamp = retrieved_at or datetime.now(UTC)
        stamp = stamp.replace(tzinfo=UTC) if stamp.tzinfo is None else stamp.astimezone(UTC)
        return YahooFetchResult(
            frame=frame.reset_index(drop=True),
            url=url,
            payload_sha256=hashlib.sha256(payload).hexdigest(),
            retrieved_at=stamp,
            revision_policy=self.revision_policy,
        )
