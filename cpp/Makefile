CXX = g++
CXXFLAGS = -std=c++11 -pthread -Wall -Wextra
CXX20FLAGS = -std=c++20 -fcoroutines -pthread -Wall -Wextra

.PHONY: all clean run-actor run-csp run-prodcons run-deadlock run-fib

all: shared_memory_lock/producer_consumer shared_memory_lock/deadlock stackless_coroutine/fibonacci actor/print_server csp/channel_demo

shared_memory_lock/producer_consumer: shared_memory_lock/producer_consumer.cpp
	$(CXX) $(CXXFLAGS) -o $@ $^

shared_memory_lock/deadlock: shared_memory_lock/deadlock.cpp
	$(CXX) $(CXXFLAGS) -o $@ $^

stackless_coroutine/fibonacci: stackless_coroutine/fibonacci.cpp
	$(CXX) $(CXX20FLAGS) -o $@ $^

actor/print_server: actor/print_server.cpp
	$(CXX) $(CXXFLAGS) -o $@ $^

csp/channel_demo: csp/channel_demo.cpp
	$(CXX) $(CXXFLAGS) -o $@ $^

run-actor: actor/print_server
	./actor/print_server

run-csp: csp/channel_demo
	./csp/channel_demo

run-prodcons: shared_memory_lock/producer_consumer
	./shared_memory_lock/producer_consumer

run-deadlock: shared_memory_lock/deadlock
	timeout 3 ./shared_memory_lock/deadlock || true

run-fib: stackless_coroutine/fibonacci
	./stackless_coroutine/fibonacci

clean:
	rm -f shared_memory_lock/producer_consumer shared_memory_lock/deadlock stackless_coroutine/fibonacci actor/print_server csp/channel_demo
