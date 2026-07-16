/**
 * MutexDemo.kt
 *
 * Demonstrates Kotlin's Mutex (shared-memory + locking) from
 * kotlinx.coroutines.sync.
 *
 * Shows:
 *   1) Correct concurrent counter using Mutex.withLock
 *   2) Race-condition counter without synchronisation for comparison
 *
 * Compile: kotlinc -cp /usr/share/java/kotlinx-coroutines-core-1.0.1.jar \
 *                  -d out shared_memory/MutexDemo.kt
 * Run:     kotlin -cp /usr/share/java/kotlinx-coroutines-core-1.0.1.jar:out \
 *                  MutexDemoKt
 */

import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

fun main() = runBlocking {
    println("=== Shared Counter with Mutex ===")
    val mutex = Mutex()
    var safeCounter = 0

    val safeJobs = List(100) {
        launch {
            repeat(1000) {
                // withLock acquires the mutex, executes the block, then releases
                mutex.withLock {
                    safeCounter++
                }
            }
        }
    }
    safeJobs.forEach { it.join() }

    println("Safe counter value : $safeCounter")
    println("Expected           : ${100 * 1000}")
    println("Match              : ${safeCounter == 100 * 1000}")

    println()

    // -----------------------------------------------------------------
    // Without mutex — demonstrates a data race.
    // Because ++ is not atomic, the final value is almost certainly
    // less than the expected total.
    // -----------------------------------------------------------------
    println("=== Unsafe Counter (no synchronisation) ===")
    var unsafeCounter = 0

    val unsafeJobs = List(100) {
        launch {
            repeat(1000) {
                unsafeCounter++ // race!
            }
        }
    }
    unsafeJobs.forEach { it.join() }

    println("Unsafe counter value: $unsafeCounter")
    println("Expected            : ${100 * 1000}")
    println("Match               : ${unsafeCounter == 100 * 1000}")
    println("(A mismatch confirms the data race.)")
}
