##############################################################################
# Makefile for /tridu33/cocurrency/haskell/
#
# Concurrency paradigms in Haskell:
#   stm/STMBank.hs         -- STM (Software Transactional Memory) bank transfer
#   continuation_cps/ContMonadHanoi.hs -- Continuation monad / CPS (Tower of Hanoi)
#   stackful/ProcessDemo.hs -- GHC lightweight threads / stackful coroutines
#   shared_memory/BankAccount.hs -- Shared memory via MVar
#   actor/PrintServer.hs   -- Actor model via MVar mailbox
#
# Usage:
#   make           -- build all targets
#   make clean     -- remove build artifacts
#   make run-all   -- build and run all examples
##############################################################################

HC      = ghc
HCFLAGS = -O2 -Wall
THREADED = -threaded

.PHONY: all clean run-all run-stm run-hanoi run-proc run-bank run-actor

all: stm/STMBank continuation_cps/ContMonadHanoi stackful/ProcessDemo shared_memory/BankAccount actor/PrintServer

##############################################################################
# STMBank -- needs the stm package for TVar/STM
##############################################################################

stm/STMBank: stm/STMBank.hs
	$(HC) $(HCFLAGS) $(THREADED) -package stm -o $@ $<

##############################################################################
# ContMonadHanoi -- uses Control.Monad.Cont from mtl (auto-exposed)
##############################################################################

continuation_cps/ContMonadHanoi: continuation_cps/ContMonadHanoi.hs
	$(HC) $(HCFLAGS) -o $@ $<

##############################################################################
# ProcessDemo -- uses forkIO / MVar from base + concurrent
##############################################################################

stackful/ProcessDemo: stackful/ProcessDemo.hs
	$(HC) $(HCFLAGS) $(THREADED) -o $@ $<

##############################################################################
# BankAccount -- shared memory via MVar
##############################################################################

shared_memory/BankAccount: shared_memory/BankAccount.hs
	$(HC) $(HCFLAGS) $(THREADED) -o $@ $<

##############################################################################
# PrintServer -- actor via MVar
##############################################################################

actor/PrintServer: actor/PrintServer.hs
	$(HC) $(HCFLAGS) $(THREADED) -o $@ $<

##############################################################################
# Utilities
##############################################################################

clean:
	rm -f stm/STMBank stm/STMBank.o stm/STMBank.hi
	rm -f continuation_cps/ContMonadHanoi continuation_cps/ContMonadHanoi.o continuation_cps/ContMonadHanoi.hi
	rm -f stackful/ProcessDemo stackful/ProcessDemo.o stackful/ProcessDemo.hi
	rm -f shared_memory/BankAccount shared_memory/BankAccount.o shared_memory/BankAccount.hi
	rm -f actor/PrintServer actor/PrintServer.o actor/PrintServer.hi

run-all: all
	@echo ""
	@echo "========== Running STM Bank Transfer =========="
	./stm/STMBank
	@echo ""
	@echo "========== Running Cont Monad Hanoi =========="
	./continuation_cps/ContMonadHanoi
	@echo ""
	@echo "========== Running Process Demo =========="
	./stackful/ProcessDemo
	@echo ""
	@echo "========== Running Bank Account =========="
	./shared_memory/BankAccount
	@echo ""
	@echo "========== Running Print Server =========="
	./actor/PrintServer

run-stm: stm/STMBank
	./stm/STMBank

run-hanoi: continuation_cps/ContMonadHanoi
	./continuation_cps/ContMonadHanoi

run-proc: stackful/ProcessDemo
	./stackful/ProcessDemo

run-bank: shared_memory/BankAccount
	./shared_memory/BankAccount

run-actor: actor/PrintServer
	./actor/PrintServer
