.PHONY: help install test lint format check-all report docker-build docker-run clean

DOCKER_IMAGE = yourusername/calctl
VERSION = 0.1.0

# ============================================================================
# Help
# ============================================================================
help:
	@echo "Available targets:"
	@echo "  install       - Install package and dev dependencies"
	@echo "  test          - Run all tests with coverage"
	@echo "  test-unit     - Run unit tests only"
	@echo "  lint          - Run all linters (ruff, mypy, bandit)"
	@echo "  format        - Auto-format code with ruff"
	@echo "  check-all     - Run tests + linting"
	@echo "  report        - Generate all reports"
	@echo "  docker-build  - Build Docker image"
	@echo "  docker-run    - Run Docker container"
	@echo "  clean         - Remove generated files"

# ============================================================================
# Installation
# ============================================================================
install:
	pip install -e ".[dev]"

# ============================================================================
# Testing with Coverage (≥ 70%)
# ============================================================================
test:
	@echo "Running tests with coverage..."
	@mkdir -p reports
	pytest tests/ -v \
		--cov=src/calctl \
		--cov-report=html:reports/coverage \
		--cov-report=xml:reports/coverage.xml \
		--cov-report=term-missing \
		--cov-fail-under=70
	@echo "✓ Coverage report: reports/coverage/index.html"

test-unit:
	pytest tests/unit/ -v -m unit --cov=src/calctl --cov-report=term

test-integration:
	pytest tests/integration/ -v -m integration

test-e2e:
	pytest tests/e2e/ -v -m e2e

test-bats:
	bats tests/bats/

# ============================================================================
# Static Analysis
# ============================================================================
lint-ruff:
	@echo "Running ruff..."
	@mkdir -p reports
	ruff check src/ --output-format=json > reports/ruff.json || true
	ruff check src/ --output-format=full

lint-mypy:
	@echo "Running mypy..."
	@mkdir -p reports
	mypy src/calctl --html-report reports/mypy --txt-report reports || true

lint-bandit:
	@echo "Running bandit..."
	@mkdir -p reports
	bandit -r src/calctl -f json -o reports/bandit.json || true
	bandit -r src/calctl -f txt

lint: lint-ruff lint-mypy lint-bandit
	@echo "✓ All linting complete"

format:
	ruff check src/ --fix
	ruff format src/

# ============================================================================
# Documentation
# ============================================================================
docs-build:
	mkdocs build --strict

docs-serve:
	mkdocs serve

# ============================================================================
# Complete Check
# ============================================================================
check-all: lint test docs-build
	@echo "✓ All checks passed!"

# ============================================================================
# Reports Generation
# ============================================================================
report:
	@mkdir -p reports
	@echo "Generating all reports..."
	pytest tests/ --cov=src/calctl \
		--cov-report=html:reports/coverage \
		--cov-report=xml:reports/coverage.xml
	ruff check src/ --output-format=json > reports/ruff.json || true
	mypy src/calctl --html-report reports/mypy || true
	bandit -r src/calctl -f json -o reports/bandit.json || true
	bandit -r src/calctl -f html -o reports/bandit.html || true
	mkdocs build --site-dir reports/docs || true
	@echo "✓ All reports generated in reports/"

# ============================================================================
# Docker
# ============================================================================
docker-build:
	docker build -t $(DOCKER_IMAGE):$(VERSION) -t $(DOCKER_IMAGE):latest .

docker-run:
	docker run --rm -v $(PWD)/data:/data $(DOCKER_IMAGE):latest

docker-test:
	docker run --rm $(DOCKER_IMAGE):latest --version

docker-push:
	docker push $(DOCKER_IMAGE):$(VERSION)
	docker push $(DOCKER_IMAGE):latest

# ============================================================================
# Package Building
# ============================================================================
build:
	python -m build

# ============================================================================
# Cleanup
# ============================================================================
clean:
	rm -rf reports/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf dist/
	rm -rf build/
	rm -rf site/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true