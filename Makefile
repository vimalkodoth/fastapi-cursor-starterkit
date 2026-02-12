# Format/lint/check all Python services. Run from repo root (uses backend venv when present).
# Top-level dirs with Python: add any new service here and in .pre-commit-config.yaml.
PYTHON_SERVICES = backend logger services
# Paths relative to backend/ for make -C backend (covers all of services/, including dataservice and any new subservices)
PYTHON_DIRS = . $(addprefix ../,$(filter-out backend,$(PYTHON_SERVICES)))

.PHONY: format lint check all install-dev

format:
	$(MAKE) -C backend format PYTHON_DIRS="$(PYTHON_DIRS)"

lint:
	$(MAKE) -C backend lint PYTHON_DIRS="$(PYTHON_DIRS)"

check:
	$(MAKE) -C backend check PYTHON_DIRS="$(PYTHON_DIRS)"

all: format lint

install-dev:
	$(MAKE) -C backend install-dev
