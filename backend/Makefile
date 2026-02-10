.PHONY: format lint check test install-dev

# Install development dependencies
install-dev:
	pip install -r requirements-dev.txt
	pre-commit install

# Format code with Black (run from backend/ or via root: make -C backend format)
format:
	black .
	isort .

# Lint code
lint:
	flake8 .
	mypy . --ignore-missing-imports

# Check code formatting without making changes
check:
	black --check .
	isort --check .
	flake8 .

# Run all checks
all: format lint
