.PHONY: all clean test test-csp

all: actor/print_server.beam actor/bank_account.beam process_demo.beam csp/channel_demo.beam

actor/%.beam: actor/%.erl
	erlc -o actor/ $<

csp/%.beam: csp/%.erl
	erlc -o csp/ $<

process_demo.beam: process_demo.erl
	erlc $<

test: all
	cd actor && erl -noshell -eval "print_server:test(), halt()."
	cd actor && erl -noshell -eval "bank_account:test(), halt()."
	erl -noshell -eval "process_demo:test(), halt()."

test-csp: csp/channel_demo.beam
	cd csp && erl -noshell -eval "channel_demo:test(), halt()."

clean:
	rm -f actor/*.beam csp/*.beam *.beam erl_crash.dump
