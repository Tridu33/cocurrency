# Makefile for Scala concurrency examples
#
# Targets:
#   all            — Build everything (default)
#   run-actor      — Build and run the actor example
#   run-bank       — Build and run the shared-memory example
#   run-csp        — Build and run the CSP channel example
#   run-stackless  — Build and run the stackless Fibonacci example
#   run-stackful   — Build and run the stackful thread demo
#   run-all        — Build and run all demos
#   clean          — Remove compiled class files
#
# Requirements: scalac + scala on PATH (Scala 2.13+ / 3.x)

SCALAC  ?= scalac
SCALA   ?= scala
SCALAFLAGS ?=

SRC_DIR  ?= .
BUILD_DIR ?= build

ACTOR_SRC   := $(SRC_DIR)/actor/PrintServer.scala
BANK_SRC    := $(SRC_DIR)/shared_memory/BankAccount.scala
CSP_SRC     := $(SRC_DIR)/csp/ChannelDemo.scala
STACKLESS_SRC := $(SRC_DIR)/stackless_coroutine/FibonacciGen.scala
STACKFUL_SRC  := $(SRC_DIR)/stackful_coroutine/ThreadDemo.scala

ACTOR_CLS   := $(BUILD_DIR)/PrintServer.class
BANK_CLS    := $(BUILD_DIR)/BankAccount.class
CSP_CLS     := $(BUILD_DIR)/ChannelDemo.class
STACKLESS_CLS := $(BUILD_DIR)/FibonacciGen.class
STACKFUL_CLS  := $(BUILD_DIR)/ThreadDemo.class

.PHONY: all run-actor run-bank run-csp run-stackless run-stackful run-all clean

all: $(ACTOR_CLS) $(BANK_CLS) $(CSP_CLS) $(STACKLESS_CLS) $(STACKFUL_CLS)

$(BUILD_DIR)/%.class: $(SRC_DIR)/**/%.scala
	@mkdir -p $(BUILD_DIR)
	$(SCALAC) $(SCALAFLAGS) -d $(BUILD_DIR) $(filter %.scala,$^)

$(ACTOR_CLS): $(ACTOR_SRC)
	@mkdir -p $(BUILD_DIR)
	$(SCALAC) $(SCALAFLAGS) -d $(BUILD_DIR) $(ACTOR_SRC)

$(BANK_CLS): $(BANK_SRC)
	@mkdir -p $(BUILD_DIR)
	$(SCALAC) $(SCALAFLAGS) -d $(BUILD_DIR) $(BANK_SRC)

$(CSP_CLS): $(CSP_SRC)
	@mkdir -p $(BUILD_DIR)
	$(SCALAC) $(SCALAFLAGS) -d $(BUILD_DIR) $(CSP_SRC)

$(STACKLESS_CLS): $(STACKLESS_SRC)
	@mkdir -p $(BUILD_DIR)
	$(SCALAC) $(SCALAFLAGS) -d $(BUILD_DIR) $(STACKLESS_SRC)

$(STACKFUL_CLS): $(STACKFUL_SRC)
	@mkdir -p $(BUILD_DIR)
	$(SCALAC) $(SCALAFLAGS) -d $(BUILD_DIR) $(STACKFUL_SRC)

run-actor: $(ACTOR_CLS)
	$(SCALA) -classpath $(BUILD_DIR) PrintServer

run-bank: $(BANK_CLS)
	$(SCALA) -classpath $(BUILD_DIR) BankAccount

run-csp: $(CSP_CLS)
	$(SCALA) -classpath $(BUILD_DIR) ChannelDemo

run-stackless: $(STACKLESS_CLS)
	$(SCALA) -classpath $(BUILD_DIR) FibonacciGen

run-stackful: $(STACKFUL_CLS)
	$(SCALA) -classpath $(BUILD_DIR) ThreadDemo

run-all: run-bank run-actor run-csp run-stackless run-stackful

clean:
	rm -rf $(BUILD_DIR)
