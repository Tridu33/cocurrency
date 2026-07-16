/**
 * SuspendFibonacci.kt
 *
 * Demonstrates Kotlin's stackless coroutines via:
 *   1) sequence { yield(...) } builder — lightweight generator
 *   2) suspend function with deep recursion (the call-chain is
 *      stackless because each call can suspend/resume)
 *
 * These use the stdlib's built-in coroutines, NOT kotlinx.
 *
 * Compile: kotlinc -cp /usr/share/java/kotlinx-coroutines-core-1.0.1.jar \
 *                  -d out stackless_coroutine/SuspendFibonacci.kt
 * Run:     kotlin -cp /usr/share/java/kotlinx-coroutines-core-1.0.1.jar:out \
 *                  SuspendFibonacciKt
 */

import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.launch
import kotlinx.coroutines.delay
import kotlin.sequences.sequence

// -----------------------------------------------------------------
// Stackless generator via sequence builder
// Every `yield` is a suspension point — the frame is saved on the
// heap, not the call stack.
// -----------------------------------------------------------------
fun fibonacciSequence(): Sequence<Long> = sequence {
    var a = 0L
    var b = 1L

    yield(a) // suspend point
    yield(b) // suspend point

    while (true) {
        val next = a + b
        yield(next) // suspend point
        a = b
        b = next
    }
}

// -----------------------------------------------------------------
// A suspend function that recurses deeply.
// Because Kotlin's suspend model is stackless, deep chains do not
// blow the stack — the continuation is heap-allocated.
// Note: the Fibonacci logic itself is O(2^n) — this is intentional
//       to keep the example simple, not performant.
// -----------------------------------------------------------------
suspend fun deepFibonacci(n: Long): Long {
    return when {
        n < 0L  -> throw IllegalArgumentException("n must be non-negative")
        n <= 1L -> n
        else    -> deepFibonacci(n - 1) + deepFibonacci(n - 2)
    }
}

fun main() = runBlocking {
    println("=== Sequence builder (stackless generator) ===")
    println("First 20 Fibonacci numbers via sequence + yield:")
    println(fibonacciSequence().take(20).toList())

    println()

    println("=== Deep recursion via suspend function ===")
    println("Computing fibonacci(10) inside a launch coroutine...")

    launch {
        val result = deepFibonacci(10)
        println("fibonacci(10) = $result")
    }

    delay(500)

    println()
    println("Note: the recursive suspend calls never overflow the stack")
    println("because the coroutine frame is heap-allocated at each")
    println("suspension point.")
    delay(500)
}
