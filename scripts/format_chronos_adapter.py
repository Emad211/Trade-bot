from pathlib import Path

path = Path("src/hybrid_trader/forecasting/chronos_adapter.py")
text = path.read_text("utf-8")
replacements = {
    '            raise ValueError("quantile_levels must be unique, sorted and strictly inside (0, 1)")\n': '            raise ValueError(\n                "quantile_levels must be unique, sorted and strictly inside (0, 1)"\n            )\n',
    '            raise RuntimeError("Install Chronos with: pip install -e \' .[forecast]\'".replace(" ", "")) from exc\n': '',
}
first = '            raise RuntimeError("Install Chronos with: pip install -e \' .[forecast]\'".replace(" ", "")) from exc\n'
if first not in text:
    first = '            raise RuntimeError("Install Chronos with: pip install -e \' .[forecast]\'") from exc\n'.replace(" \' .", " \'.")
replacements[first] = '            raise RuntimeError(\n                "Install Chronos with: pip install -e \' .[forecast]\'".replace(" ", "")\n            ) from exc\n'
second = '        self._pipeline = Chronos2Pipeline.from_pretrained(self.settings.model_id, **kwargs)\n'
replacements[second] = '        self._pipeline = Chronos2Pipeline.from_pretrained(\n            self.settings.model_id, **kwargs\n        )\n'
for before, after in replacements.items():
    if not before:
        continue
    if before not in text:
        raise RuntimeError(f"Formatting anchor not found: {before!r}")
    text = text.replace(before, after, 1)
path.write_text(text, encoding="utf-8")
