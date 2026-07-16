import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;

/**
 * FibonacciGenerator.java
 *
 * Compares Java 21 virtual threads (STACKFUL coroutines) with the
 * STACKLESS coroutine pattern found in languages such as Python
 * (yield) or C++20 (co_yield / co_return).
 *
 * ┌─────────────────────────────────────────────────────────────────┐
 * │  Stackless coroutine ── only the topmost stack frame is saved   │
 * │  at a suspension point; the call chain is unwound.  Every       │
 * │  function that may suspend must be annotated (async, co_yield). │
 * │                                                                 │
 * │  Stackful coroutine  ── the entire call stack is preserved      │
 * │  when the thread parks; nested method calls are resumed         │
 * │  transparently.  No special annotations needed.                 │
 * └─────────────────────────────────────────────────────────────────┘
 *
 * This example implements a Fibonacci "generator" using a virtual
 * thread that yields values into a BlockingQueue, mimicking the
 * yield/resume cycle of a stackless generator.
 *
 * Compile:  javac stackless_coroutine/FibonacciGenerator.java
 * Run:      cd stackless_coroutine && java FibonacciGenerator
 */
public class FibonacciGenerator {

    // ---------------------------------------------------------------
    // Traditional sequential approach (no coroutine)
    // ---------------------------------------------------------------
    /**
     * Pre-compute Fibonacci numbers in a plain loop.  No concurrency,
     * no suspension — just a straightforward sequence.
     */
    public static void generateTraditional(int count) {
        System.out.println("\n--- Traditional (sequential, no coroutine) ---\n");

        int[] fib = new int[count];
        fib[0] = 0;
        if (count > 1) fib[1] = 1;

        for (int i = 2; i < count; i++) {
            fib[i] = fib[i - 1] + fib[i - 2];
        }

        for (int i = 0; i < count; i++) {
            System.out.println("  fib[" + i + "] = " + fib[i]);
        }
    }

    // ---------------------------------------------------------------
    // Generator pattern via a virtual thread (stackful coroutine)
    // ---------------------------------------------------------------
    /**
     * Generate Fibonacci numbers using a java.util.concurrent virtual
     * thread that "yields" each value into a bounded BlockingQueue.
     *
     * The generator thread produces one value, then blocks on
     * {@code queue.put(...)} until the consumer polls it.  This
     * back-and-forth is the same logical flow as a stackless
     * generator's yield/resume cycle.
     *
     * However, because virtual threads are STACKFUL, the generator
     * could call deeply nested helper methods and still suspend
     * correctly — something true stackless coroutines cannot do
     * without every intermediate function carrying an annotation.
     */
    public static void generateWithVirtualThread(int count) throws InterruptedException {
        System.out.println("\n--- Virtual-thread generator (stackful) ---\n");

        /*
         * Bounded queue (capacity = 2) creates natural back-pressure.
         * The producer blocks on put() when the queue is full, giving
         * the consumer time to catch up — just like a bounded channel
         * in Go or a generator that yields to its caller.
         */
        BlockingQueue<Integer> queue = new LinkedBlockingQueue<>(2);

        // ---- Generator (virtual thread) ----
        Thread generator = Thread.startVirtualThread(() -> {
            try {
                int a = 0, b = 1;
                for (int i = 0; i < count; i++) {
                    // "Yield" the current value — blocks if queue is full
                    queue.put(a);
                    System.out.println("    [Generator] yielded " + a);

                    int next = a + b;
                    a = b;
                    b = next;
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        });

        // ---- Consumer (main thread) ----
        for (int i = 0; i < count; i++) {
            Integer value = queue.poll(2, TimeUnit.SECONDS);
            if (value == null) {
                System.out.println("    [Consumer] timeout — generator stalled?");
                break;
            }
            System.out.println("    [Consumer] received " + value);
        }

        generator.join(1000);
        System.out.println("\n  Generator thread alive after consumption: "
            + generator.isAlive());
    }

    // ---------------------------------------------------------------
    // Main
    // ---------------------------------------------------------------
    public static void main(String[] args) throws InterruptedException {
        System.out.println("=== Stackless vs. Stackful Coroutines (Java 21+) ===");
        System.out.println("  Java version                                     : "
            + System.getProperty("java.version"));
        System.out.println("  Is virtual thread-supported                      : "
            + (Runtime.version().feature() >= 21));
        System.out.println();

        System.out.println("┌─ Background ──────────────────────────────────────────────┐");
        System.out.println("│ Java virtual threads are STACKFUL coroutines.              │");
        System.out.println("│ They preserve the entire call stack when parked (e.g.      │");
        System.out.println("│ BlockingQueue.put()).  True stackless coroutines           │");
        System.out.println("│ (Python generators, C++20 coroutines) save only the        │");
        System.out.println("│ topmost activation frame.                                  │");
        System.out.println("│                                                             │");
        System.out.println("│ Advantage of STACKFUL: any method can suspend without       │");
        System.out.println("│ being annotated async/await.                               │");
        System.out.println("│ Disadvantage: heavier memory footprint per suspension       │");
        System.out.println("│ point (entire stack retained).                              │");
        System.out.println("└─────────────────────────────────────────────────────────────┘");

        generateTraditional(10);
        generateWithVirtualThread(10);

        System.out.println("\n=== Done ===");
    }
}
