/**
 * ThreadDemo.kt
 *
 * Paradigm: Stackful Coroutine (via threads)
 *
 * Kotlin coroutines are stackless by default. This demo uses
 * traditional threads to demonstrate stackful semantics:
 * each thread has its own full call stack that is preserved
 * when the thread blocks.
 *
 * Compare with: Lua coroutines (stackful), Go goroutines (stackful)
 *
 * Compile: kotlinc -d out stackful_coroutine/ThreadDemo.kt
 * Run:     java -cp /usr/share/java/kotlin-stdlib.jar:out ThreadDemoKt
 */

import java.util.concurrent.LinkedBlockingQueue

fun main(args: Array<String>) {
    println("=== Stackful Coroutine via Threads ===\n")

    val results = LinkedBlockingQueue<String>()

    // Worker 1 — simulates a stackful coroutine with a full call stack
    val thread1 = Thread {
        worker("A", listOf(1, 2, 3), results)
    }

    // Worker 2
    val thread2 = Thread {
        worker("B", listOf(4, 5, 6), results)
    }

    thread1.start()
    thread2.start()

    // Collect results (like a scheduler)
    for (i in 1..6) {
        println("  [Main] got: " + results.take())
    }

    thread1.join()
    thread2.join()

    println("\n=== Key insight ===")
    println("Threads are stackful: each thread has a full call stack.")
    println("When a thread blocks on LinkedBlockingQueue.take(), the")
    println("entire call stack is preserved. This is the same model")
    println("as Go goroutines and Lua coroutines.")
}

/** A worker with nested calls that can "suspend" at any depth. */
fun worker(name: String, items: List<Int>, results: LinkedBlockingQueue<String>) {
    for (item in items) {
        println("  [$name] processing item $item")
        val result = deepProcess(name, item)
        results.put(result)
    }
    println("  [$name] DONE")
}

fun deepProcess(name: String, item: Int): String {
    return if (item % 2 == 0) {
        evenHandler(name, item)
    } else {
        oddHandler(name, item)
    }
}

fun evenHandler(name: String, item: Int): String {
    Thread.sleep(10)
    return "$name processed even item $item"
}

fun oddHandler(name: String, item: Int): String {
    Thread.sleep(10)
    return "$name processed odd item $item"
}
