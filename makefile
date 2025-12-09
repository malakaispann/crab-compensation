.PHONY: clean
.PHONY: format
.PHONY: format-check
.PHONY: install-dev
.PHONY: install-prod
.PHONY: lint-check
.PHONY: package
.PHONY: package-module
.PHONY: package-dependencies
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
	uv sync --no-dev

lint-check:
	uv run pylint src

package: package-dependencies package-module

package-dependencies:
	mkdir -p dist
	uv export --format requirements.txt --no-dev > dist/requirements.txt
	uv pip install --requirements dist/requirements.txt --target dist/dependencies --python-platform x86_64-manylinux_2_28 --only-binary :all:
	cd dist/dependencies && zip -r ../dependencies.zip .

package-module:
	uv build


start-local:
	uv run --env-file dev.conf start --year 2024

test:
	uv run --env-file dev.conf pytest
