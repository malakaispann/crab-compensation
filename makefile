.PHONY: format
.PHONY: format-check
.PHONY: install-dev
.PHONY: install-prod
.PHONY: lint-check
.PHONY: test


format:
	uv run black src

format-check:
	uv run black --check src

install-dev:
	uv sync

install-prod:
	uv sync --no-dev

lint-check:
	uv run pylint src

start-local:
	uv run --env-file dev.conf start --year 2024

test:
	uv run --env-file dev.conf pytest
