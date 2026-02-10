# Delegates to backend for format/lint/check. Run from repo root.
.PHONY: format lint check all install-dev

format:
	$(MAKE) -C backend format

lint:
	$(MAKE) -C backend lint

check:
	$(MAKE) -C backend check

all: format lint

install-dev:
	$(MAKE) -C backend install-dev
