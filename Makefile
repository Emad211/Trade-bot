.PHONY: install install-ml format lint typecheck test test-core test-ml check check-all sample snapshot features benchmark smoke phase2c-plan

install:
	python -m pip install -e '.[dev]'

install-ml:
	python -m pip install -e '.[dev,ml]'

format:
	ruff format .

lint:
	ruff format --check .
	ruff check .

typecheck:
	mypy --python-version 3.11 src
	mypy --python-version 3.12 src

test: test-core

test-core:
	pytest -m "not optional_ml" --cov=hybrid_trader --cov-report=term-missing

test-ml:
	pytest -m optional_ml -q

check: lint typecheck test-core

check-all: check test-ml

sample:
	hybrid-trader generate-sample --output data/sample_btc_4h.csv --bars 1800

snapshot:
	hybrid-trader create-snapshot --input data/sample_btc_4h.csv --config configs/btc_spot_4h_smoke.yaml --output data/snapshots/sample --source synthetic-smoke

features:
	hybrid-trader foundation-features --snapshot data/snapshots/sample --output data/features/naive --model naive --context-length 64 --min-history 32 --horizon 3

benchmark:
	hybrid-trader benchmark --snapshot data/snapshots/sample --config configs/btc_spot_4h_smoke.yaml --feature-cache data/features/naive --output artifacts/smoke

smoke: sample snapshot features benchmark

phase2c-plan:
	hybrid-trader phase2c-plan --spec configs/phase2c_btc_4h.yaml
