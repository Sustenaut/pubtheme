# pubtheme: Eleventy themes for publet reading bundles.
.PHONY: help venv node functional lock sync-check example

help: ## Available targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*## /\t/'

venv: ## Create .venv from the hash-locked test requirements
	python3 -m venv .venv
	.venv/bin/pip install --quiet --require-hashes -r tests/requirements.lock

node: ## Install the themes' pinned packages
	npm ci --no-audit --no-fund

functional: ## The Gherkin suite against bin/pubtheme
	cd tests && PUBTHEME_BIN_DIR=$(CURDIR)/bin ../.venv/bin/pytest -q $(PYTEST_ARGS)

lock: ## Pin tests/requirements.txt with hashes
	.venv/bin/pubkit lock

sync-check: ## Fail if pubkit's managed files drifted
	.venv/bin/pubkit sync --check

example: ## Build the sustenaut theme from the test bundles into _site/
	rm -rf _site && bin/pubtheme build --bundles=tests/testdata/publication-0 --out=_site
