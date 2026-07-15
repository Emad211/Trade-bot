from pathlib import Path

path = Path("src/hybrid_trader/forecasting/chronos_adapter.py")
text = path.read_text("utf-8")
replacements = (
    (
        '            raise ValueError("quantile_levels must be unique, sorted and strictly inside (0, 1)")\n',
        '            raise ValueError(\n'
        '                "quantile_levels must be unique, sorted and strictly inside (0, 1)"\n'
        '            )\n',
    ),
    (
        """            raise RuntimeError("Install Chronos with: pip install -e '.[forecast]'") from exc
""",
        """            raise RuntimeError(
                "Install Chronos with: pip install -e '.[forecast]'"
            ) from exc
""",
    ),
    (
        '        self._pipeline = Chronos2Pipeline.from_pretrained(self.settings.model_id, **kwargs)\n',
        '        self._pipeline = Chronos2Pipeline.from_pretrained(\n'
        '            self.settings.model_id, **kwargs\n'
        '        )\n',
    ),
)
for before, after in replacements:
    if before not in text:
        raise RuntimeError(f"Formatting anchor not found: {before!r}")
    text = text.replace(before, after, 1)
path.write_text(text, encoding="utf-8")
