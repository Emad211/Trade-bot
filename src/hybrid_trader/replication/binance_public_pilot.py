"""Ephemeral, checksum-bound validation of a bounded Binance public-data pilot."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import urllib.error
import urllib.request
import zipfile
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from itertools import pairwise
from pathlib import Path, PurePosixPath
from typing import Any
from urllib.parse import urlparse

BASE = "https://data.binance.vision/"
VERSION = "BINANCE_BTCUSDT_PUBLIC_EPHEMERAL_PILOT_V1"
START, END = 1704067200000, 1706745600000
HOURS, FUNDINGS = 744, 93
README_BLOB_SHA = "311354cd82a76bcaaec588e6818e6c12644abef0"
KLINE = (
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_volume",
    "count",
    "taker_buy_volume",
    "taker_buy_quote_volume",
    "ignore",
)
FUNDING = ("calc_time", "funding_interval_hours", "last_funding_rate")


class PilotError(RuntimeError):
    pass


@dataclass(frozen=True)
class Spec:
    source_id: str
    market: str
    data_type: str
    interval: str | None
    path: str
    rows: int
    kind: str

    @property
    def filename(self) -> str:
        return PurePosixPath(self.path).name

    @property
    def url(self) -> str:
        return BASE + self.path

    @property
    def checksum_url(self) -> str:
        return self.url + ".CHECKSUM"


SPECS = (
    Spec(
        "SPOT_KLINES",
        "SPOT",
        "klines",
        "1h",
        "data/spot/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-2024-01.zip",
        HOURS,
        "KLINE",
    ),
    Spec(
        "UM_KLINES",
        "USD_M_FUTURES",
        "klines",
        "1h",
        "data/futures/um/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-2024-01.zip",
        HOURS,
        "KLINE",
    ),
    Spec(
        "UM_MARK",
        "USD_M_FUTURES",
        "markPriceKlines",
        "1h",
        "data/futures/um/monthly/markPriceKlines/BTCUSDT/1h/BTCUSDT-1h-2024-01.zip",
        HOURS,
        "KLINE",
    ),
    Spec(
        "UM_INDEX",
        "USD_M_FUTURES",
        "indexPriceKlines",
        "1h",
        "data/futures/um/monthly/indexPriceKlines/BTCUSDT/1h/BTCUSDT-1h-2024-01.zip",
        HOURS,
        "KLINE",
    ),
    Spec(
        "UM_PREMIUM",
        "USD_M_FUTURES",
        "premiumIndexKlines",
        "1h",
        "data/futures/um/monthly/premiumIndexKlines/BTCUSDT/1h/BTCUSDT-1h-2024-01.zip",
        HOURS,
        "KLINE",
    ),
    Spec(
        "UM_FUNDING",
        "USD_M_FUTURES",
        "fundingRate",
        None,
        "data/futures/um/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-2024-01.zip",
        FUNDINGS,
        "FUNDING",
    ),
)


@dataclass(frozen=True)
class Profile:
    source_id: str
    data_type: str
    zip_sha256: str
    zip_bytes: int
    provider_sha256: str
    member: str
    member_sha256: str
    member_bytes: int
    schema_fields: int
    schema_sha256: str
    header: bool
    rows: int
    first_ms: int
    last_ms: int
    cadence_ms: int
    cadence_breaks: int


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def schema_hash(xs: Sequence[str]) -> str:
    return sha256("\0".join(xs).encode())


def fetch(url: str, timeout: float = 60) -> bytes:
    u = urlparse(url)
    if (u.scheme, u.hostname) != ("https", "data.binance.vision"):
        raise PilotError(f"disallowed URL {url}")
    req = urllib.request.Request(
        url, headers={"User-Agent": "Emad211-Trade-bot-replication/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = bytes(response.read())
            status = int(response.status)
            final_url = response.geturl()
            final = urlparse(final_url)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
        raise PilotError(f"download failed {url}: {e}") from e
    if status != 200 or not body:
        raise PilotError(f"bad HTTP result {status}/{len(body)}")
    if (final.scheme, final.hostname) != ("https", "data.binance.vision"):
        raise PilotError(f"redirect left allowlist: {final_url}")
    return body


CHECK = re.compile(r"^([0-9a-fA-F]{64})\s+[* ]?([^\r\n]+)$")


def parse_checksum(raw: bytes, filename: str) -> str:
    try:
        text = raw.decode("ascii").strip()
    except UnicodeDecodeError as e:
        raise PilotError("checksum is not ASCII") from e
    m = CHECK.fullmatch(text)
    if not m:
        raise PilotError("malformed checksum")
    digest, named = m.groups()
    if PurePosixPath(named).name != filename:
        raise PilotError("checksum filename mismatch")
    return digest.lower()


def member_bytes(raw: bytes, expected: str) -> bytes:
    try:
        z = zipfile.ZipFile(io.BytesIO(raw))
    except zipfile.BadZipFile as e:
        raise PilotError("invalid ZIP") from e
    with z:
        if (bad := z.testzip()) is not None:
            raise PilotError(f"CRC failure {bad}")
        infos = [x for x in z.infolist() if not x.is_dir()]
        if len(infos) != 1:
            raise PilotError("ZIP must contain one file")
        x, p = infos[0], PurePosixPath(infos[0].filename)
        if p.is_absolute() or ".." in p.parts or len(p.parts) != 1:
            raise PilotError("unsafe ZIP path")
        if x.flag_bits & 1 or x.file_size <= 0 or x.file_size > 50_000_000:
            raise PilotError("unsafe ZIP member")
        if x.compress_size <= 0 or x.file_size / x.compress_size > 100:
            raise PilotError("unsafe ZIP ratio")
        if x.filename != expected:
            raise PilotError(f"unexpected member {x.filename}")
        return z.read(x)


def rows(raw: bytes) -> tuple[tuple[str, ...] | None, list[list[str]]]:
    try:
        parsed = list(csv.reader(io.StringIO(raw.decode("utf-8-sig"), newline="")))
    except UnicodeDecodeError as e:
        raise PilotError("CSV is not UTF-8") from e
    if not parsed:
        raise PilotError("empty CSV")
    has_header = not parsed[0] or not parsed[0][0].strip().lstrip("-").isdigit()
    header = tuple(x.strip() for x in parsed[0]) if has_header else None
    data = parsed[1:] if has_header else parsed
    if not data:
        raise PilotError("no data rows")
    return header, data


def integer(x: str, field: str, n: int) -> int:
    try:
        return int(x)
    except ValueError as e:
        raise PilotError(f"row {n}: invalid {field}") from e


def decimal(x: str, field: str, n: int) -> Decimal:
    try:
        d = Decimal(x)
    except InvalidOperation as e:
        raise PilotError(f"row {n}: invalid {field}") from e
    if not d.is_finite():
        raise PilotError(f"row {n}: nonfinite {field}")
    return d


def validate_kline(
    data: Sequence[Sequence[str]], expected: int, *, require_positive_prices: bool
) -> tuple[tuple[str, ...], tuple[int, ...]]:
    ts: list[int] = []
    for n, r in enumerate(data, 2):
        if len(r) != 12:
            raise PilotError(f"row {n}: kline columns {len(r)}")
        t, close_t = integer(r[0], "open_time", n), integer(r[6], "close_time", n)
        if not START <= t < END or close_t != t + 3_599_999:
            raise PilotError(f"row {n}: bad time")
        open_price, high, low, close = (decimal(r[i], KLINE[i], n) for i in range(1, 5))
        activity = [decimal(r[i], KLINE[i], n) for i in (5, 7, 9, 10)]
        trades = integer(r[8], "trades", n)
        if require_positive_prices and min(open_price, high, low, close) <= 0:
            raise PilotError(f"row {n}: non-positive price")
        if high < max(open_price, close) or low > min(open_price, close) or high < low:
            raise PilotError(f"row {n}: bad OHLC envelope")
        if min(activity) < 0 or trades < 0:
            raise PilotError(f"row {n}: negative activity")
        ts.append(t)
    if len(data) != expected or ts != sorted(set(ts)):
        raise PilotError("kline count/order/uniqueness failure")
    if ts[0] != START or ts[-1] != START + (expected - 1) * 3_600_000:
        raise PilotError("kline span failure")
    if any(b - a != 3_600_000 for a, b in pairwise(ts)):
        raise PilotError("kline cadence failure")
    return KLINE, tuple(ts)


def validate_funding(
    data: Sequence[Sequence[str]], expected: int
) -> tuple[tuple[str, ...], tuple[int, ...]]:
    ts: list[int] = []
    intervals: list[int] = []
    for n, r in enumerate(data, 2):
        if len(r) != 3:
            raise PilotError(f"row {n}: funding columns {len(r)}")
        t, interval = integer(r[0], "calc_time", n), integer(r[1], "interval", n)
        decimal(r[2], "funding_rate", n)
        if not START <= t < END or not 0 < interval <= 24:
            raise PilotError(f"row {n}: bad funding time/interval")
        ts.append(t)
        intervals.append(interval)
    if len(data) != expected or ts != sorted(set(ts)):
        raise PilotError("funding count/order/uniqueness failure")
    if any(hours != 8 for hours in intervals):
        raise PilotError("unexpected funding interval")
    if expected == FUNDINGS and (ts[0] != START or ts[-1] != END - 28_800_000):
        raise PilotError("funding span failure")
    if any(
        b - a != h * 3_600_000
        for a, b, h in zip(ts, ts[1:], intervals[1:], strict=False)
    ):
        raise PilotError("funding cadence failure")
    return FUNDING, tuple(ts)


def validate(
    spec: Spec, zip_raw: bytes, checksum_raw: bytes
) -> tuple[Profile, tuple[int, ...]]:
    if len(zip_raw) > 20_000_000:
        raise PilotError("ZIP exceeds pilot size limit")
    provider = parse_checksum(checksum_raw, spec.filename)
    observed = sha256(zip_raw)
    if observed != provider:
        raise PilotError("provider checksum mismatch")
    member_name = spec.filename.removesuffix(".zip") + ".csv"
    member = member_bytes(zip_raw, member_name)
    header, data = rows(member)
    expected_schema: tuple[str, ...]
    if spec.kind == "KLINE":
        expected_schema, ts = validate_kline(
            data,
            spec.rows,
            require_positive_prices=spec.data_type != "premiumIndexKlines",
        )
        cadence = 3_600_000
    elif spec.kind == "FUNDING":
        expected_schema, ts = validate_funding(data, spec.rows)
        cadence = 28_800_000
    else:
        raise PilotError("unknown parser kind")
    schema = header or expected_schema
    if header and tuple(x.lower() for x in header) != tuple(
        x.lower() for x in expected_schema
    ):
        raise PilotError(f"unexpected header {header}")
    return Profile(
        spec.source_id,
        spec.data_type,
        observed,
        len(zip_raw),
        provider,
        member_name,
        sha256(member),
        len(member),
        len(schema),
        schema_hash(schema),
        header is not None,
        len(data),
        ts[0],
        ts[-1],
        cadence,
        0,
    ), ts


def evidence(
    items: Sequence[tuple[Spec, Profile, tuple[int, ...]]], when: datetime
) -> dict[str, Any]:
    if when.tzinfo is None:
        raise ValueError("retrieval time must be aware")
    if len(items) != len(SPECS):
        raise PilotError("missing required source")
    observed_ids = tuple(spec.source_id for spec, _, _ in items)
    expected_ids = tuple(spec.source_id for spec in SPECS)
    if observed_ids != expected_ids:
        raise PilotError("source identity/order mismatch")
    grids = [t for s, _, t in items if s.kind == "KLINE"]
    aligned = bool(grids) and all(x == grids[0] for x in grids[1:])
    if not aligned:
        raise PilotError("hourly grids not aligned")
    sources = []
    for s, p, _ in items:
        x = asdict(p)
        x.update(
            {
                "market": s.market,
                "symbol": "BTCUSDT",
                "interval": s.interval,
                "source_url": s.url,
                "checksum_url": s.checksum_url,
            }
        )
        sources.append(x)
    return {
        "schema_version": "1.0",
        "pilot_version": VERSION,
        "pilot_month": "2024-01",
        "retrieved_at": when.astimezone(UTC).isoformat(),
        "official_repository": "binance/binance-public-data",
        "official_readme_blob_sha": README_BLOB_SHA,
        "official_readme_license_statement": "MIT",
        "source_count": len(items),
        "sources": sources,
        "cross_source_checks": {
            "hourly_timestamp_grids_exactly_aligned": aligned,
            "hourly_row_count": HOURS,
            "funding_row_count": FUNDINGS,
            "timestamp_unit": "MILLISECONDS",
            "spot_microsecond_transition_not_applicable": True,
        },
        "retention_state": {
            "raw_bytes_written_to_disk": False,
            "raw_bytes_uploaded": False,
            "derived_price_rows_uploaded": False,
            "safe_hash_profile_only": True,
            "raw_retention_authorized": False,
            "raw_redistribution_authorized": False,
            "formal_data_terms_review": "PENDING",
        },
        "authorization": {
            "ephemeral_validation": True,
            "point_in_time_instrument_metadata_complete": False,
            "historical_available_at_complete": False,
            "basis_computation": False,
            "funding_pnl_computation": False,
            "return_computation": False,
            "empirical_fitting": False,
            "parameter_tuning": False,
            "paper_trading": False,
            "live_trading": False,
            "capital_deployment": False,
            "report_2_4_full_authorization": False,
        },
        "paper_replication_pass": False,
        "economic_edge_verdict": "INCONCLUSIVE",
    }


def run(output: Path) -> dict[str, Any]:
    parsed = []
    now = datetime.now(UTC)
    for spec in SPECS:
        try:
            p, t = validate(spec, fetch(spec.url), fetch(spec.checksum_url))
        except PilotError as exc:
            raise PilotError(f"{spec.source_id}: {exc}") from exc
        parsed.append((spec, p, t))
    result = evidence(parsed, now)
    output.mkdir(parents=True, exist_ok=True)
    (output / "binance-btcusdt-public-ephemeral-pilot-evidence.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output-dir", type=Path, required=True)
    print(json.dumps(run(ap.parse_args(argv).output_dir), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
