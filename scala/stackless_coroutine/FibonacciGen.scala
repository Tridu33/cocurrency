/**
 * FibonacciGen.scala
 *
 * Paradigm: Stackless Coroutine (via Iterator)
 *
 * Scala's Iterator is a stackless generator: state is held in the
 * heap-allocated iterator object, not on the call stack.
 * Compare with: Python yield, C++20 co_yield, JS generators
 *
 * NOTE: Uses Stream (Scala 2.11 compatible) instead of LazyList (2.13+).
 *
 * Compile:  scalac -d build stackless_coroutine/FibonacciGen.scala
 * Run:      scala -classpath build FibonacciGen
 */

object FibonacciGen {

  /** Fibonacci as a stackless Iterator — state on heap, not stack. */
  def fibonacciIterator(limit: Int): Iterator[Long] = new Iterator[Long] {
    private var a = 0L
    private var b = 1L
    private var count = 0

    override def hasNext: Boolean = count < limit

    override def next(): Long = {
      if (!hasNext) throw new NoSuchElementException()
      val result = a
      val next = a + b
      a = b
      b = next
      count += 1
      result
    }
  }

  /** Fibonacci via Stream (Scala 2.11 compatible). */
  def fibonacciStream: Stream[Long] = {
    def loop(a: Long, b: Long): Stream[Long] = a #:: loop(b, a + b)
    loop(0, 1)
  }

  def main(args: Array[String]): Unit = {
    println("=== Stackless Coroutine: Fibonacci Generator ===\n")

    println("--- fibonacciIterator(20) ---")
    val it = fibonacciIterator(20)
    var i = 0
    while (it.hasNext) {
      println("  fib(" + i + ") = " + it.next())
      i += 1
    }

    println("\n--- fibonacciStream (first 15) ---")
    fibonacciStream.take(15).zipWithIndex.foreach { case (v, idx) =>
      println("  fib(" + idx + ") = " + v)
    }

    println("\n=== Key insight ===")
    println("Iterator and Stream are stackless: each element's")
    println("state is heap-allocated. This is the same model as")
    println("Python generators and C++20 coroutines.")
  }
}
