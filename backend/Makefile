.PHONY: format lint check test install-dev

# Directories to format/lint: default this repo only; root Makefile passes all services.
PYTHON_DIRS ?= .

# Install development dependencies
install-dev:
	pip install -r requirements-dev.txt
	pre-commit install

# Format code (run from backend/ or via root: make format). Use python -m so venv is enough.
format:
	python -m black $(PYTHON_DIRS)
	python -m isort $(PYTHON_DIRS)

# Lint code
lint:
	python -m flake8 $(PYTHON_DIRS)
	python -m mypy $(PYTHON_DIRS) --ignore-missing-imports

# Check code formatting without making changes
check:
	python -m black --check $(PYTHON_DIRS)
	python -m isort --check $(PYTHON_DIRS)
	python -m flake8 $(PYTHON_DIRS)

# Run all checks
all: format lint
