.PHONY: clean
.PHONY: format
.PHONY: format-check
.PHONY: install-dev
.PHONY: lint-check
.PHONY: package
.PHONY: test

PY_VERSION  := 3.13
VENV_DIR    := emr-venv

clean:
	rm -rf dist/ logs/ temp/ .venv/ $(VENV_DIR)

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
	uv python install $(PY_VERSION)
	
	# Create a self-contained venv using uv's Python
	rm -rf $(VENV_DIR)
	PY313=$$(uv python find $(PY_VERSION)) && \
	"$$PY313" -m venv $(VENV_DIR)
	
	$(VENV_DIR)/bin/python -m pip install --upgrade pip
	$(VENV_DIR)/bin/pip install .
	
	mkdir -p dist
	cd $(VENV_DIR) && zip -r ../dist/crab-compensation.zip .


start-local:
	uv run --env-file dev.conf start --year 2024

test:
	uv run --env-file dev.conf pytest
