"""Canonical URL and public-feed host validation for prospective event sources."""

from __future__ import annotations

import ipaddress
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

_TRACKING_QUERY_KEYS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "ref",
    "source",
}


def canonical_hostname(value: str) -> str:
    hostname = value.lower().strip(".")
    if not hostname:
        raise ValueError("URL host cannot be empty")
    try:
        return hostname.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise ValueError("URL host is not valid IDNA") from exc


def validate_public_hostname(hostname: str) -> None:
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise ValueError("Feed URLs cannot target localhost")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return
    if not address.is_global:
        raise ValueError("Feed URLs must target a globally routable address")


def canonicalize_url(value: str) -> str:
    """Normalize an HTTP(S) URL and remove common tracking parameters."""

    parts = urlsplit(value.strip())
    scheme = parts.scheme.lower()
    if parts.username is not None or parts.password is not None:
        raise ValueError("User information is not allowed in event URLs")
    hostname = canonical_hostname(parts.hostname or "")
    if scheme not in {"http", "https"}:
        raise ValueError("URL must be absolute HTTP(S)")
    try:
        port = parts.port
    except ValueError as exc:
        raise ValueError("URL port is invalid") from exc
    default_port = (scheme == "https" and port == 443) or (scheme == "http" and port == 80)
    netloc = hostname if port is None or default_port else f"{hostname}:{port}"
    path = parts.path or "/"
    if not path.startswith("/"):
        path = f"/{path}"
    if path != "/":
        path = path.rstrip("/")
    query_pairs = [
        (key, item)
        for key, item in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith("utm_") and key.lower() not in _TRACKING_QUERY_KEYS
    ]
    query = urlencode(sorted(query_pairs))
    return urlunsplit((scheme, netloc, path, query, ""))


def url_is_allowed(url: str, allowed_domains: tuple[str, ...]) -> bool:
    hostname = canonical_hostname(urlsplit(url).hostname or "")
    return any(hostname == domain or hostname.endswith(f".{domain}") for domain in allowed_domains)
