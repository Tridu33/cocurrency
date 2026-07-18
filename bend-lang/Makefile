# Makefile for Bend-lang concurrency examples
#
# Targets:
#   make check       — Syntax-check all .bend files
#   make run         — Run all demo scripts and verify they produce correct results
#   make run-one     — Run a specific demo (usage: make run-one FILE=actor/print_server.bend)
#   make clean       — Remove temporary files

BEND := bend
CHECK_FLAGS :=
RUN_FLAGS :=

# All bend files
BEND_FILES := \
	actor/print_server.bend \
	csp/channel_demo.bend \
	shared_memory/bank_account.bend \
	shared_memory/producer_consumer.bend \
	continuation_cps/continuation_cps.bend \
	stackless_coroutine/yield_fibonacci.bend \
	stackful_coroutine/deep_recursion.bend \
	stm/stm_model.bend \
	t9_combinations.bend

# Default target
.PHONY: help
help:
	@echo "Bend-lang Concurrency Examples"
	@echo ""
	@echo "A high-level, massively parallel programming language"
	@echo ""
	@echo "Targets:"
	@echo "  make check       — Syntax-check all .bend files"
	@echo "  make run         — Run all demo scripts"
	@echo "  make run-one FILE=<path> — Run a specific demo"
	@echo "  make clean       — Remove temporary files"
	@echo ""

# ---- Syntax Check ----

.PHONY: check
check:
	@echo "Syntax-checking all Bend files..."
	@failed=0; \
	for f in $(BEND_FILES); do \
		echo -n "  $$f ... "; \
		if $(BEND) check $$f $(CHECK_FLAGS) 2>/dev/null; then \
			echo "OK"; \
		else \
			echo "FAIL"; \
			failed=1; \
		fi; \
	done; \
	if [ $$failed -eq 0 ]; then \
		echo "All files OK."; \
	else \
		echo "Some files FAILED."; \
		exit 1; \
	fi

# ---- Run All ----

.PHONY: run
run:
	@echo "Running all Bend demos..."
	@for f in $(BEND_FILES); do \
		echo "=== $$f ==="; \
		$(BEND) run-rs $$f $(RUN_FLAGS); \
		echo ""; \
	done
	@echo "All demos completed."

# ---- Run One ----

.PHONY: run-one
run-one:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make run-one FILE=actor/print_server.bend"; \
		exit 1; \
	fi
	$(BEND) run-rs $(FILE) $(RUN_FLAGS)

# ---- Clean ----

.PHONY: clean
clean:
	@echo "Cleaning up..."
	@echo "Done."

# ---- Install Dependencies ----

.PHONY: install
install:
	@echo "Bend is already installed at:"
	@which $(BEND)
	@$(BEND) --version
