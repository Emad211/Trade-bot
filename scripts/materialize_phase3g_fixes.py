from __future__ import annotations

from pathlib import Path


def replace_once(path: Path, before: str, after: str, *, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(before) != 1:
        raise RuntimeError(f"Expected one {label} anchor, found {text.count(before)}")
    path.write_text(text.replace(before, after, 1), encoding="utf-8")


def patch_registry_validation() -> None:
    path = Path("src/hybrid_trader/semantic_monitor.py")
    replace_once(
        path,
        '''        if self.maturity.paper_or_live_trading_allowed:
            raise ValueError("Embedded maturity assessment permits trading")
        expected_id = maturity_observation_id(
''',
        '''        if self.maturity.paper_or_live_trading_allowed:
            raise ValueError("Embedded maturity assessment permits trading")
        expected_deficits = maturity_deficits(self.maturity)
        if self.deficits != expected_deficits:
            raise ValueError("Maturity deficits do not match the frozen policy")
        expected_id = maturity_observation_id(
''',
        label="deficit validation",
    )


if __name__ == "__main__":
    patch_registry_validation()
