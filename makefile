.PHONY: clean
.PHONY: format
.PHONY: format-check
.PHONY: install-dev
.PHONY: lint-check
.PHONY: package
.PHONY: test

clean:
	rm -rf dist/ logs/ temp/ .venv/

format:
	uv run black src

format-check:
	uv run black --check src

install-dev:
	uv sync

install-prod:

lint-check:
	uv run pylint src

package:
	mkdir -p dist
	uv sync --no-dev
	cd .venv && zip -r ../dist/crab-compensation.zip .


start-local:
	uv run --env-file dev.conf start --year 2024

test:
	uv run --env-file dev.conf pytest
