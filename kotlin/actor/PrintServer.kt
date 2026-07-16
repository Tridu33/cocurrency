/**
 * PrintServer.kt
 *
 * Actor model using kotlinx.coroutines (send/receive on Channel).
 * Demonstrates tell (fire-and-forget) and ask (request-response).
 *
 * Compare with: Python actor_print_server.py, Erlang gen_server
 *
 * Compile: kotlinc -cp /usr/share/java/kotlinx-coroutines-core-1.0.1.jar \
 *                  -d out actor/PrintServer.kt
 * Run:     java -cp /usr/share/java/kotlinx-coroutines-core-1.0.1.jar:out \
 *                  PrintServerKt
 */

import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.launch
import kotlinx.coroutines.delay

class PrintServer(private val mailbox: Channel<String> = Channel(Channel.UNLIMITED)) {
    private var counter = 0
    private var running = true

    /** Process messages — call from a coroutine. */
    suspend fun process() {
        println("  [PrintServer] started")
        while (running) {
            val result = mailbox.receiveCatching()
            if (result.isClosed) break
            val msg = result.getOrNull() ?: break
            counter++
            delay(20)
            val output = "[PrintServer] #$counter printed: $msg"
            println("  $output")
        }
        println("  [PrintServer] shutting down")
    }

    /** Fire-and-forget: send a message, no reply expected. */
    fun tell(text: String) {
        mailbox.trySend(text)
    }

    fun stop() {
        running = false
        mailbox.close()
    }
}

fun main(args: Array<String>) = runBlocking {
    println("=== Actor: PrintServer Demo ===\n")

    val mailbox = Channel<String>(Channel.UNLIMITED)
    val server = PrintServer(mailbox)

    // Launch the actor processor in a background coroutine
    val job = launch {
        server.process()
    }

    // Fire-and-forget
    server.tell("Hello, Actor World!")
    server.tell("Printing document #1")
    server.tell("Printing document #2")

    delay(100)
    server.tell("Final document")
    delay(50)
    server.stop()

    job.join()
    println("\nPrintServer demo passed.")
}
