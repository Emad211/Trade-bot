from __future__ import annotations

from pathlib import Path

PATH = Path("tests/test_sharpe_robustness.py")


def main() -> None:
    text = PATH.read_text(encoding="utf-8")
    before = "    returns = rng.normal(0, 1, size=50_000)\n"
    after = "    returns = rng.normal(0, 0.01, size=50_000)\n"
    if text.count(before) != 1:
        raise RuntimeError("Expected exactly one normal-shape test scale anchor")
    PATH.write_text(text.replace(before, after, 1), encoding="utf-8")


if __name__ == "__main__":
    main()
