/**
 * ChannelDemo.scala
 *
 * Paradigm: CSP (Communicating Sequential Processes)
 *
 * CSP channel using BlockingQueue + Thread.
 * Demonstrates producer-consumer communication via channels.
 *
 * Compare with: Go channel, Java ChannelDemo, Python channel_demo
 *
 * Compile:  scalac -d build csp/ChannelDemo.scala
 * Run:      scala -classpath build ChannelDemo
 */

import java.util.concurrent.LinkedBlockingQueue

class Channel[T](capacity: Int = 0) {
  private val queue = if (capacity > 0) new LinkedBlockingQueue[T](capacity)
                      else new LinkedBlockingQueue[T]()

  def send(item: T): Unit = queue.put(item)

  def recv(): T = queue.take()

  def trySend(item: T): Boolean = queue.offer(item)

  def tryRecv(): T = queue.poll()

  def size: Int = queue.size()
}

object ChannelDemo {
  def main(args: Array[String]): Unit = {
    println("=== CSP Channel Demo (Scala) ===\n")

    // Demo 1: Unbuffered channel
    println("--- Unbuffered Channel ---")
    val ch = new Channel[Int]()

    val producer = new Thread {
      override def run(): Unit = {
        for (i <- 0 until 5) {
          val v = i * 10
          println("  Producer sending: " + v)
          ch.send(v)
        }
      }
    }
    producer.setName("Producer")

    val consumer = new Thread {
      override def run(): Unit = {
        for (_ <- 0 until 5) {
          val v = ch.recv()
          println("  Consumer received: " + v)
          Thread.sleep(50)
        }
      }
    }
    consumer.setName("Consumer")

    producer.start()
    consumer.start()
    producer.join()
    consumer.join()
    println()

    // Demo 2: Buffered channel
    println("--- Buffered Channel (capacity=3) ---")
    val buf = new Channel[Int](3)

    val fastProd = new Thread {
      override def run(): Unit = {
        for (i <- 0 until 6) {
          buf.send(i)
          println("  Produced " + i + " (buffer=" + buf.size + "/3)")
        }
      }
    }

    val slowCons = new Thread {
      override def run(): Unit = {
        for (_ <- 0 until 6) {
          val v = buf.recv()
          println("  Consumed " + v)
          Thread.sleep(100)
        }
      }
    }

    fastProd.start()
    slowCons.start()
    fastProd.join()
    slowCons.join()
    println()

    println("=== Summary ===")
    println("Scala's BlockingQueue provides CSP-like semantics.")
    println("Like Java, Scala has no native channel type or select{},")
    println("but the Thread + Queue pattern achieves the same goal.")
  }
}
