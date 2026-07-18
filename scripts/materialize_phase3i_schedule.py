from __future__ import annotations

from pathlib import Path


path = Path(".github/workflows/phase3g-prospective-overlap.yml")
text = path.read_text(encoding="utf-8")
before = '''name: phase3g-prospective-overlap

on:
  workflow_dispatch:
  schedule:
    - cron: "47 7 * * 1"
  push:
'''
after = '''name: phase3g-prospective-overlap

# Manual historical reproduction only; scheduled overlap moved to Phase 3I.
on:
  workflow_dispatch:
  push:
'''
if text.count(before) != 1:
    raise RuntimeError("Phase 3G schedule transition anchor is not unique")
path.write_text(text.replace(before, after, 1), encoding="utf-8")
