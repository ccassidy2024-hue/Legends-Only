.PHONY: install catalog episodes episodes-write test lint all clean

install:
	pip install -e ".[dev]"

catalog:
	python -m grainsys.catalog

# Episode Ledger: validate entries against the schema and check the generated
# summary is current. Fails if any entry has market_outcomes_reviewed: true.
episodes:
	python -m grainsys.episodes

episodes-write:
	python -m grainsys.episodes --write

test:
	pytest -q

lint:
	ruff check src tests

# Stage-appropriate reproducibility gate: no proprietary data required.
# Every empirical memo number must eventually survive an expanded `make all`
# from a clean clone. At this foundation stage, lint + tests are the gate.
all: lint episodes test
	@echo "OK - foundation checks passed (no proprietary data required)"

clean:
	rm -rf outputs/tables/* outputs/charts/* outputs/reports/* catalog/catalog.csv
	rm -rf .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
