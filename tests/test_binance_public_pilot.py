from __future__ import annotations

import csv
import hashlib
import io
import zipfile
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from hybrid_trader.replication import binance_public_pilot as bp


def checksum(name: str, body: bytes) -> bytes:
    return f"{hashlib.sha256(body).hexdigest()}  {name}\n".encode()


def z(member: str, body: bytes) -> bytes:
    s = io.BytesIO()
    with zipfile.ZipFile(s, "w", zipfile.ZIP_DEFLATED) as a:
        a.writestr(member, body)
    return s.getvalue()


def kcsv(n: int = bp.HOURS) -> bytes:
    s = io.StringIO(newline="")
    w = csv.writer(s, lineterminator="\n")
    for i in range(n):
        t = bp.START + i * 3_600_000
        w.writerow(
            [
                t,
                "40000",
                "40100",
                "39900",
                "40050",
                "10",
                t + 3_599_999,
                "400500",
                "100",
                "5",
                "200250",
                "0",
            ]
        )
    return s.getvalue().encode()


def fcsv(n: int = 2) -> bytes:
    s = io.StringIO(newline="")
    w = csv.writer(s, lineterminator="\n")
    for i in range(n):
        w.writerow([bp.START + i * 28_800_000, 8, str(Decimal("0.0001"))])
    return s.getvalue().encode()


def spec(kind: str, n: int, name: str = "x") -> bp.Spec:
    return bp.Spec(
        name, "TEST", kind, "1h" if kind == "KLINE" else None, f"{name}.zip", n, kind
    )


def test_checksum_filename_binding() -> None:
    d = "a" * 64
    assert bp.parse_checksum(f"{d}  x.zip\n".encode(), "x.zip") == d
    with pytest.raises(bp.PilotError, match="filename mismatch"):
        bp.parse_checksum(f"{d}  y.zip\n".encode(), "x.zip")


def test_path_traversal() -> None:
    s = io.BytesIO()
    with zipfile.ZipFile(s, "w") as a:
        a.writestr("../x.csv", b"1\n")
    with pytest.raises(bp.PilotError, match="unsafe ZIP path"):
        bp.member_bytes(s.getvalue(), "x.csv")


def test_kline_checksum_and_schema() -> None:
    sp = spec("KLINE", bp.HOURS)
    raw = z("x.csv", kcsv())
    p, t = bp.validate(sp, raw, checksum(sp.filename, raw))
    assert (
        p.rows == bp.HOURS
        and len(t) == bp.HOURS
        and p.zip_sha256 == hashlib.sha256(raw).hexdigest()
    )


def test_funding_parser() -> None:
    sp = spec("FUNDING", 2)
    raw = z("x.csv", fcsv())
    p, t = bp.validate(sp, raw, checksum(sp.filename, raw))
    assert p.rows == 2 and t[1] - t[0] == 28_800_000


def test_checksum_mismatch() -> None:
    sp = spec("KLINE", bp.HOURS)
    raw = z("x.csv", kcsv())
    with pytest.raises(bp.PilotError, match="checksum mismatch"):
        bp.validate(sp, raw, f"{'0' * 64}  x.zip\n".encode())


def test_alignment_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    a, b = spec("KLINE", bp.HOURS, "a"), spec("KLINE", bp.HOURS, "b")
    monkeypatch.setattr(bp, "SPECS", (a, b))
    raw = z("a.csv", kcsv())
    p, t = bp.validate(a, raw, checksum(a.filename, raw))
    q = replace(p, source_id="b")
    with pytest.raises(bp.PilotError, match="not aligned"):
        bp.evidence(
            [(a, p, t), (b, q, tuple(x + 1 for x in t))],
            datetime(2026, 7, 20, tzinfo=UTC),
        )


def test_evidence_non_promotional(monkeypatch: pytest.MonkeyPatch) -> None:
    a = spec("KLINE", bp.HOURS)
    monkeypatch.setattr(bp, "SPECS", (a,))
    raw = z("x.csv", kcsv())
    p, t = bp.validate(a, raw, checksum(a.filename, raw))
    e = bp.evidence([(a, p, t)], datetime(2026, 7, 20, tzinfo=UTC))
    assert e["retention_state"]["raw_bytes_uploaded"] is False
    assert e["authorization"]["basis_computation"] is False
    assert e["economic_edge_verdict"] == "INCONCLUSIVE"


def test_premium_index_allows_negative_ohlc() -> None:
    sp = replace(spec("KLINE", bp.HOURS), data_type="premiumIndexKlines")
    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    for index in range(bp.HOURS):
        timestamp = bp.START + index * 3_600_000
        writer.writerow(
            [
                timestamp,
                "-0.0002",
                "0.0001",
                "-0.0003",
                "-0.0001",
                "0",
                timestamp + 3_599_999,
                "0",
                "0",
                "0",
                "0",
                "0",
            ]
        )
    raw = z("x.csv", stream.getvalue().encode())
    profile, _ = bp.validate(sp, raw, checksum(sp.filename, raw))
    assert profile.rows == bp.HOURS


def test_evidence_rejects_source_reordering(monkeypatch: pytest.MonkeyPatch) -> None:
    first = spec("KLINE", bp.HOURS, "a")
    second = spec("KLINE", bp.HOURS, "b")
    monkeypatch.setattr(bp, "SPECS", (first, second))
    raw_a = z("a.csv", kcsv())
    raw_b = z("b.csv", kcsv())
    profile_a, timestamps_a = bp.validate(first, raw_a, checksum(first.filename, raw_a))
    profile_b, timestamps_b = bp.validate(
        second, raw_b, checksum(second.filename, raw_b)
    )
    with pytest.raises(bp.PilotError, match="source identity/order mismatch"):
        bp.evidence(
            [(second, profile_b, timestamps_b), (first, profile_a, timestamps_a)],
            datetime(2026, 7, 20, tzinfo=UTC),
        )
