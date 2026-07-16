/**
 * ThreadDemo.scala
 *
 * Paradigm: Stackful Coroutine (via Thread + BlockingQueue)
 *
 * Scala/Java threads are stackful: each thread has its own call stack.
 * When a thread blocks on queue.take(), the full call stack is preserved.
 * This is the same model as Go goroutines and Lua coroutines.
 *
 * This demo simulates a worker that can "suspend" at any call depth
 * and be "resumed" later — the defining property of stackful coroutines.
 *
 * Compile:  scalac -d build stackful_coroutine/ThreadDemo.scala
 * Run:      scala -classpath build ThreadDemo
 */

import java.util.concurrent.{LinkedBlockingQueue, BlockingQueue}

object ThreadDemo {

  /** A "suspendable" worker simulation. */
  class SuspendableWorker(name: String, workItems: Seq[Int]) {
    private val mailbox = new LinkedBlockingQueue[String]()

    private val thread = new Thread {
      override def run(): Unit = {
        var depth = 0
        for (item <- workItems) {
          println("  [" + name + "] step " + item + " (depth=" + depth + ")")
          Thread.sleep(10)

          // Simulate nested call that can "suspend"
          val result = innerProcess(item, depth)
          depth = result

          // "Suspend" — thread blocks here, stack is preserved
          try {
            mailbox.put(name + " completed item " + item)
          } catch {
            case _: InterruptedException => // exit
          }
        }
        println("  [" + name + "] DONE")
      }
    }

    thread.start()

    def waitForNextResult(): String = mailbox.take()

    def join(): Unit = thread.join()
  }

  private def innerProcess(item: Int, depth: Int): Int = {
    // Simulate deep call chain (stackful = we can suspend from any depth)
    if (item % 2 == 0) {
      evenHandler(item, depth)
    } else {
      oddHandler(item, depth)
    }
  }

  private def evenHandler(item: Int, depth: Int): Int = {
    println("    (evenHandler depth=" + depth + ")")
    depth + 2
  }

  private def oddHandler(item: Int, depth: Int): Int = {
    println("    (oddHandler depth=" + depth + ")")
    depth + 1
  }

  def main(args: Array[String]): Unit = {
    println("=== Stackful Coroutine via Thread ===\n")

    val worker1 = new SuspendableWorker("W1", Seq(1, 2, 3))
    val worker2 = new SuspendableWorker("W2", Seq(4, 5, 6))

    // Main thread collects results (like a scheduler)
    for (_ <- 0 until 3) {
      println("  [Main] result: " + worker1.waitForNextResult())
      println("  [Main] result: " + worker2.waitForNextResult())
    }

    worker1.join()
    worker2.join()

    println("\n=== Key insight ===")
    println("Threads are stackful: each thread has a full call stack.")
    println("When a thread blocks (e.g., on queue.take()), the entire")
    println("stack is preserved. This is the same model as Go goroutines")
    println("(stackful) vs Python generators (stackless).")
  }
}
