# Makefile for Java concurrency examples
#
# Targets:
#   all        — compile all .java files
#   clean      — remove all .class files
#   run-bank   — run the BankAccount demo (shared-memory / lock / deadlock)
#   run-fib    — run the FibonacciGenerator demo (virtual-thread generator)
#   run-csp    — run the CSP channel demo
#   run-actor  — run the PrintServer actor demo
#   run-stm    — run the STM simulation demo
#
# Requirements: JDK >= 21 (for virtual threads)
#
# Usage:
#   make          # compile everything
#   make run-bank # compile + run BankAccount
#   make run-fib  # compile + run FibonacciGenerator
#   make run-all  # compile + run all demos
#   make clean    # delete generated .class files

JAVAC         = javac
JAVA          = java

SRC_BANK      = shared_memory_lock/BankAccount.java
SRC_FIB       = stackless_coroutine/FibonacciGenerator.java
SRC_CSP       = csp/ChannelDemo.java
SRC_ACTOR     = actor/PrintServer.java
SRC_STM       = stm/BankSTM.java

CLASS_BANK    = shared_memory_lock/BankAccount.class
CLASS_FIB     = stackless_coroutine/FibonacciGenerator.class
CLASS_CSP     = csp/ChannelDemo.class
CLASS_ACTOR   = actor/PrintServer.class
CLASS_STM     = stm/BankSTM.class

.PHONY: all clean run-bank run-fib run-csp run-actor run-stm run-all

# ---- Build everything ---------------------------------------------------
all: $(CLASS_BANK) $(CLASS_FIB) $(CLASS_CSP) $(CLASS_ACTOR) $(CLASS_STM)

$(CLASS_BANK): $(SRC_BANK)
	$(JAVAC) $(SRC_BANK)

$(CLASS_FIB): $(SRC_FIB)
	$(JAVAC) $(SRC_FIB)

$(CLASS_CSP): $(SRC_CSP)
	$(JAVAC) $(SRC_CSP)

$(CLASS_ACTOR): $(SRC_ACTOR)
	$(JAVAC) $(SRC_ACTOR)

$(CLASS_STM): $(SRC_STM)
	$(JAVAC) $(SRC_STM)

# ---- Run targets --------------------------------------------------------
run-bank: $(CLASS_BANK)
	cd shared_memory_lock && $(JAVA) BankAccount

run-fib: $(CLASS_FIB)
	cd stackless_coroutine && $(JAVA) FibonacciGenerator

run-csp: $(CLASS_CSP)
	cd csp && $(JAVA) ChannelDemo

run-actor: $(CLASS_ACTOR)
	cd actor && $(JAVA) PrintServer

run-stm: $(CLASS_STM)
	cd stm && $(JAVA) BankSTM

run-all: run-bank run-fib run-csp run-actor run-stm

# ---- Clean --------------------------------------------------------------
clean:
	find . -name '*.class' -delete
