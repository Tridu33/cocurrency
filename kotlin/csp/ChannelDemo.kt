/**
 * ChannelDemo.kt
 *
 * Demonstrates Kotlin coroutines Channel (CSP-style concurrency).
 * Requires: kotlinx-coroutines-core (1.0.1+)
 *
 * Compile: kotlinc -cp /usr/share/java/kotlinx-coroutines-core-1.0.1.jar \
 *                  -d out csp/ChannelDemo.kt
 * Run:     kotlin -cp /usr/share/java/kotlinx-coroutines-core-1.0.1.jar:out \
 *                  ChannelDemoKt
 */

import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.delay

fun main() = runBlocking {
    // -----------------------------------------------------------------
    // 1. Unbuffered channel (Rendezvous) — sender blocks until receiver
    //    is ready, and vice versa.
    // -----------------------------------------------------------------
    println("=== Unbuffered Channel (Rendezvous) ===")
    val unbuffered = Channel<Int>()

    launch {
        for (x in 1..5) {
            println("[producer] sending $x ...")
            unbuffered.send(x)
            println("[producer] sent $x")
        }
        unbuffered.close()
        println("[producer] channel closed")
    }

    launch {
        for (value in unbuffered) {
            println("[consumer] received $value")
            delay(300) // slow consumer forces rendezvous each time
        }
    }

    delay(2500)
    println()

    // -----------------------------------------------------------------
    // 2. Buffered channel — sender can enqueue up to `capacity` items
    //    before blocking.
    // -----------------------------------------------------------------
    println("=== Buffered Channel (capacity = 3) ===")
    val buffered = Channel<Int>(3)

    launch {
        for (x in 1..5) {
            println("[fast producer] sending $x ...")
            buffered.send(x)
            println("[fast producer] sent $x")
        }
        buffered.close()
        println("[fast producer] channel closed")
    }

    launch {
        for (value in buffered) {
            println("[slow consumer] consumed $value")
            delay(500)
        }
    }

    delay(4000)
    println("\nAll channel demos complete.")
}
