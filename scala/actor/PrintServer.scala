/**
 * PrintServer.scala
 *
 * A minimal actor implementation in pure Scala (no external library).
 * Uses a Thread-based actor with a concurrent mailbox and a react loop
 * to demonstrate the actor model with pattern-matched messages.
 */

import scala.collection.mutable.Queue
import java.util.concurrent.LinkedBlockingQueue

// ---------------------------------------------------------------------------
// Minimal actor infrastructure
// ---------------------------------------------------------------------------

sealed trait Message

case class PrintJob(document: String, pages: Int) extends Message
case object Shutdown                                extends Message
case class StatusRequest(requester: SimpleActor)    extends Message
case class StatusResponse(totalJobs: Int)           extends Message

/**
 * A simple Thread-based actor with a concurrent mailbox.
 *
 * The actor runs an event loop on a dedicated thread. Messages are
 * enqueued by any thread and processed sequentially by the actor's
 * thread, guaranteeing no shared-memory races inside the actor.
 */
class SimpleActor(name: String, behavior: PartialFunction[Message, Unit]) {

  private val mailbox = new LinkedBlockingQueue[Message]()

  private val thread = new Thread {
    override def run(): Unit = {
      var running = true
      try {
        while (running) {
          val msg = mailbox.take() // blocks until a message arrives
          if (behavior.isDefinedAt(msg)) behavior(msg)
          msg match {
            case Shutdown => running = false
            case _        =>
          }
        }
      } catch {
        case _: InterruptedException => // normal shutdown
      }
    }
  }

  thread.setDaemon(true)
  thread.start()

  /** Send a message to this actor (non-blocking). */
  def !(msg: Message): Unit = {
    mailbox.put(msg)
  }

  /** Wait for the actor thread to finish. */
  def join(): Unit = thread.join()
}

// ---------------------------------------------------------------------------
// PrintServer — an actor that manages a global print queue
// ---------------------------------------------------------------------------

class PrintServer extends SimpleActor("print-server", PrintServer.behavior)

object PrintServer {

  /** Shared mutable state lives *inside* the actor's closure, not on a
   *  global variable. The actor's thread owns it and races are impossible
   *  because only the react loop touches it.
   */
  private def behavior: PartialFunction[Message, Unit] = {
    var jobCounter   = 0
    var totalPages   = 0
    val pendingQueue = Queue.empty[PrintJob]

    {
      case job @ PrintJob(doc, pages) =>
        jobCounter += 1
        totalPages += pages
        pendingQueue.enqueue(job)
        println("[PrintServer] queued #" + jobCounter + ": '" + doc + "' (" + pages + " pages)  " +
                "[queue depth = " + pendingQueue.size + "]")

        // Process all jobs currently in the queue (simulates a printer).
        while (pendingQueue.nonEmpty) {
          val current = pendingQueue.dequeue()
          println("[PrintServer] printing '" + current.document + "' " +
                  "(" + current.pages + " pages)...")
          Thread.sleep(200) // simulate print time
          println("[PrintServer] done: '" + current.document + "'")
        }

      case StatusRequest(requester) =>
        println("[PrintServer] status request received (served " + jobCounter + " jobs, " + totalPages + " pages)")
        requester ! StatusResponse(jobCounter)

      case Shutdown =>
        println("[PrintServer] shutting down after " + jobCounter + " jobs (" + totalPages + " pages)")
    }
  }

  // -----------------------------------------------------------------------
  // Demo
  // -----------------------------------------------------------------------
  def main(args: Array[String]): Unit = {
    println("=== PrintServer Actor Demo ===\n")

    val server  = new PrintServer()
    val monitor = new SimpleActor("monitor", {
      case StatusResponse(jobs) =>
        println("[Monitor] PrintServer has completed " + jobs + " job(s).")
      case Shutdown =>
        println("[Monitor] shutting down.")
    })

    // Send print jobs from the "main" thread (could be any actor).
    server ! PrintJob("report-q3.pdf",  3)
    server ! PrintJob("invoice-2024.pdf", 1)
    server ! PrintJob("manual-v2.pdf",  2)

    // Ask for a status report.
    server ! StatusRequest(monitor)

    // Give the system a moment to process.
    Thread.sleep(500)

    // More jobs after the first batch.
    server ! PrintJob("timesheet.pdf", 1)
    server ! PrintJob("handbook.pdf",  5)

    // Shut down both actors.
    server  ! Shutdown
    monitor ! Shutdown

    server.join()
    monitor.join()

    println("\n=== PrintServer shutdown cleanly ===")
  }
}
