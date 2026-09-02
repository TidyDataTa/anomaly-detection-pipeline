.PHONY: install dev lint format test run dry-run clean

install:            ## Install the runtime dependencies
	pip install -r requirements.txt

dev:                ## Install lint & test dependencies
	pip install -r requirements-dev.txt

lint:               ## Static checks
	ruff check .
	ruff format --check .

format:             ## Apply formatting
	ruff format .
	ruff check --fix .

test:               ## Run the test suite
	pytest -q

run:                ## Run every metric that is due today
	python -m anomaly_detection

dry-run:            ## Run the checks without writing or alerting
	python -m anomaly_detection --dry-run --verbose

clean:
	rm -rf .pytest_cache .ruff_cache **/__pycache__
