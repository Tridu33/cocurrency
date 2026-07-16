# Makefile -- run Lua concurrency examples
#
# Targets
#   make all        -- run every example
#   make consumer   -- producer-consumer pattern
#   make fib        -- Fibonacci generator
#   make nesting    -- deep nesting (stackful) demo
#   make bank       -- shared memory bank account
#   make channel    -- CSP channel demo
#   make actor      -- actor print server demo
#   make stm        -- STM bank transfer demo
#   make stackless  -- stackless fibonacci generator
#   make cps        -- CPS fibonacci demo
#   make clean      -- remove temporary files (none currently)

LUA ?= lua

.PHONY: all consumer fib nesting bank channel actor stm stackless cps clean

all: consumer fib nesting bank channel actor stm stackless cps

consumer:
	@echo "=== Producer / Consumer ==="
	$(LUA) stackful_coroutine/producer_consumer.lua
	@echo ""

fib:
	@echo "=== Fibonacci Generator ==="
	$(LUA) stackful_coroutine/fibonacci.lua
	@echo ""

nesting:
	@echo "=== Deep Nesting (Stackful) ==="
	$(LUA) stackful_coroutine/deep_nesting.lua
	@echo ""

bank:
	@echo "=== Shared Memory Bank Account ==="
	$(LUA) shared_memory/bank_account.lua
	@echo ""

channel:
	@echo "=== CSP Channel Demo ==="
	$(LUA) csp/channel.lua
	@echo ""

actor:
	@echo "=== Actor Print Server ==="
	$(LUA) actor/print_server.lua
	@echo ""

stm:
	@echo "=== STM Bank Transfer ==="
	$(LUA) stm/stm_bank.lua
	@echo ""

stackless:
	@echo "=== Stackless Fibonacci ==="
	$(LUA) stackless_coroutine/fibonacci_gen.lua
	@echo ""

cps:
	@echo "=== CPS Fibonacci ==="
	$(LUA) continuation_cps/fib_cps.lua
	@echo ""

clean:
	@echo "Nothing to clean."
