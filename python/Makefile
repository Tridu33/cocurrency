"""
Makefile for Python concurrency examples.

Targets:
  make test       — Run all tests (excludes slow benchmarks)
  make test-all   — Run ALL tests including benchmarks
  make test-one   — Run a specific test file (usage: make test-one FILE=tests/test_bank_account.py)
  make demo       — Run all demo scripts
  make demo-one   — Run a specific demo (usage: make demo-one FILE=shared_memory_lock/bank_account.py)
  make clean      — Remove __pycache__ and .pyc files
  make check      — Run flake8 linting
  help            — Show this help
"""

PYTHON := python3
PYTEST := $(PYTHON) -m pytest
FLAKE8 := $(PYTHON) -m flake8

# Test flags
TEST_FLAGS := -v --tb=short --asyncio-mode=auto
SLOW_FLAGS := --runslow

# Default target
.PHONY: help
help:
	@echo "Python Concurrency Examples Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  make test       — Run all tests (excludes slow benchmarks)"
	@echo "  make test-all   — Run ALL tests including benchmarks"
	@echo "  make test-one FILE=<path> — Run a specific test file"
	@echo "  make demo       — Run all demo scripts"
	@echo "  make demo-one FILE=<path> — Run a specific demo"
	@echo "  make clean      — Remove __pycache__ and .pyc files"
	@echo "  make check      — Run flake8 linting"
	@echo ""

# ---- Tests ----

.PHONY: test
test:
	@echo "Running all tests (excluding slow benchmarks)..."
	PYTHONPATH=. $(PYTEST) $(TEST_FLAGS) tests/ -x

.PHONY: test-all
test-all:
	@echo "Running ALL tests (including benchmarks)..."
	PYTHONPATH=. $(PYTEST) $(TEST_FLAGS) $(SLOW_FLAGS) tests/ -x

.PHONY: test-one
test-one:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make test-one FILE=tests/test_bank_account.py"; \
		exit 1; \
	fi
	PYTHONPATH=. $(PYTEST) $(TEST_FLAGS) $(FILE) -x

# ---- Demos ----

DEMO_FILES := \
	shared_memory_lock/bank_account.py \
	shared_memory_lock/thread_producer_consumer.py \
	csp/channel_demo.py \
	actor/print_server.py \
	stm/stm_model.py \
	stackless_coroutine/yield_fibonacci.py \
	stackless_coroutine/asyncio_producer_consumer.py \
	stackless_coroutine/stackless_vs_stackful.py \
	stackful_coroutine/greenlet_demo.py \
	continuation_cps/continuation_cps.py \
	t9_combinations.py

.PHONY: demo
demo:
	@for f in $(DEMO_FILES); do \
		echo "=== Running $$f ==="; \
		PYTHONPATH=. $(PYTHON) $$f; \
		echo ""; \
	done
	@echo "All demos completed."

.PHONY: demo-one
demo-one:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make demo-one FILE=shared_memory_lock/bank_account.py"; \
		exit 1; \
	fi
	PYTHONPATH=. $(PYTHON) $(FILE)

# ---- Maintenance ----

.PHONY: clean
clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete
	@echo "Done."

.PHONY: check
check:
	$(FLAKE8) --max-line-length=100 \
		--ignore=E402,W503 \
		shared_memory_lock/ csp/ actor/ stm/ \
		stackless_coroutine/ stackful_coroutine/ continuation_cps/ \
		t9_combinations.py tests/

# ---- Setup ----

.PHONY: install
install:
	pip install -r requirements.txt

.PHONY: install-dev
install-dev:
	pip install -r requirements-dev.txt
