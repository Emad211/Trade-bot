.PHONY: install lint typecheck test check sample backtest

install:
	python -m pip install -e '.[dev]'

lint:
	ruff check .

typecheck:
	mypy src

test:
	pytest --cov=hybrid_trader --cov-report=term-missing

check: lint typecheck test

sample:
	hybrid-trader generate-sample --output data/sample_btc_4h.csv --bars 1200

backtest:
	hybrid-trader backtest --input data/sample_btc_4h.csv --config configs/btc_spot_4h.yaml --output artifacts/baseline.csv
