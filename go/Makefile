.PHONY: all clean run-csp run-shared run-actor run-stackless run-all

all: csp_deep_dive/demo shared_memory/demo actor/demo stackless_coroutine/demo

csp_deep_dive/demo: csp_deep_dive/main.go
	go build -o csp_deep_dive/demo ./csp_deep_dive/

shared_memory/demo: shared_memory/main.go
	go build -o shared_memory/demo ./shared_memory/

actor/demo: actor/main.go
	go build -o actor/demo ./actor/

stackless_coroutine/demo: stackless_coroutine/fibonacci.go
	go build -o stackless_coroutine/demo ./stackless_coroutine/

run-csp: csp_deep_dive/demo
	./csp_deep_dive/demo

run-shared: shared_memory/demo
	./shared_memory/demo

run-actor: actor/demo
	./actor/demo

run-stackless: stackless_coroutine/demo
	./stackless_coroutine/demo

run-all: all
	@echo "=== CSP Demo ===" && ./csp_deep_dive/demo
	@echo "=== Shared Memory Demo ===" && ./shared_memory/demo
	@echo "=== Actor Demo ===" && ./actor/demo
	@echo "=== Stackless Demo ===" && ./stackless_coroutine/demo

clean:
	rm -f csp_deep_dive/demo shared_memory/demo actor/demo stackless_coroutine/demo
