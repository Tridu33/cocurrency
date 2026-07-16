# Makefile for Kotlin concurrency examples
#
# Prerequisites:
#   - Java JDK 17+
#   - Kotlin 2.x (via SDKMAN: sdk install kotlin)
#   - kotlinx-coroutines-core-jvm (bundled with Kotlin 2.x)
#
# Usage:
#   make all          Build everything
#   make channel      Build and run CSP/Channel demo
#   make fibonacci    Build and run SuspendFibonacci demo
#   make mutex        Build and run Mutex demo
#   make actor        Build and run PrintServer actor demo
#   make stackful     Build and run Stackful Thread demo
#   make cps          Build and run CPS Fibonacci demo
#   make clean        Remove build artifacts

# For SDKMAN-installed Kotlin:
KOTLIN_HOME := $(HOME)/.sdkman/candidates/kotlin/current
KOTLINC     := $(KOTLIN_HOME)/bin/kotlinc

STDLIB      := $(KOTLIN_HOME)/lib/kotlin-stdlib.jar
COROUTINES  := $(KOTLIN_HOME)/lib/kotlinx-coroutines-core-jvm.jar

CLASSPATH   := $(STDLIB):$(COROUTINES)
OUT_DIR     := out

# ---- Targets -----------------------------------------------------------

.PHONY: all channel fibonacci mutex actor stackful cps clean

all: channel fibonacci mutex actor stackful cps

# Build everything
$(OUT_DIR):
	mkdir -p $(OUT_DIR)

$(OUT_DIR)/csp/ChannelDemoKt.class: csp/ChannelDemo.kt | $(OUT_DIR)
	$(KOTLINC) \
		-cp $(CLASSPATH) \
		-d $(OUT_DIR) \
		csp/ChannelDemo.kt

$(OUT_DIR)/stackless_coroutine/SuspendFibonacciKt.class: stackless_coroutine/SuspendFibonacci.kt | $(OUT_DIR)
	$(KOTLINC) \
		-cp $(CLASSPATH) \
		-d $(OUT_DIR) \
		stackless_coroutine/SuspendFibonacci.kt

$(OUT_DIR)/shared_memory/MutexDemoKt.class: shared_memory/MutexDemo.kt | $(OUT_DIR)
	$(KOTLINC) \
		-cp $(CLASSPATH) \
		-d $(OUT_DIR) \
		shared_memory/MutexDemo.kt

$(OUT_DIR)/actor/PrintServerKt.class: actor/PrintServer.kt | $(OUT_DIR)
	$(KOTLINC) \
		-cp $(CLASSPATH) \
		-d $(OUT_DIR) \
		actor/PrintServer.kt

$(OUT_DIR)/stackful_coroutine/ThreadDemoKt.class: stackful_coroutine/ThreadDemo.kt | $(OUT_DIR)
	$(KOTLINC) \
		-cp $(CLASSPATH) \
		-d $(OUT_DIR) \
		stackful_coroutine/ThreadDemo.kt

$(OUT_DIR)/continuation_cps/CPSFibonacciKt.class: continuation_cps/CPSFibonacci.kt | $(OUT_DIR)
	$(KOTLINC) \
		-cp $(CLASSPATH) \
		-d $(OUT_DIR) \
		continuation_cps/CPSFibonacci.kt

channel: $(OUT_DIR)/csp/ChannelDemoKt.class
	java -cp $(CLASSPATH):$(OUT_DIR) ChannelDemoKt

fibonacci: $(OUT_DIR)/stackless_coroutine/SuspendFibonacciKt.class
	java -cp $(CLASSPATH):$(OUT_DIR) SuspendFibonacciKt

mutex: $(OUT_DIR)/shared_memory/MutexDemoKt.class
	java -cp $(CLASSPATH):$(OUT_DIR) MutexDemoKt

actor: $(OUT_DIR)/actor/PrintServerKt.class
	java -cp $(CLASSPATH):$(OUT_DIR) PrintServerKt

stackful: $(OUT_DIR)/stackful_coroutine/ThreadDemoKt.class
	java -cp $(CLASSPATH):$(OUT_DIR) ThreadDemoKt

cps: $(OUT_DIR)/continuation_cps/CPSFibonacciKt.class
	java -cp $(CLASSPATH):$(OUT_DIR) CPSFibonacciKt

clean:
	rm -rf $(OUT_DIR)
