// =============================================================================
// stackless_coroutine / generator_fibonacci.js
//
// Concurrency Paradigm: Stackless Coroutine
//
// JavaScript generator functions (function*) are stackless coroutines:
// they suspend execution via `yield` without preserving the full call-stack.
// Each yield saves only the generator's internal state (the "execution frame"),
// not the native stack.  This is the defining property of a *stackless*
// coroutine — the coroutine cannot yield from inside a nested function call.
//
// Mapping:
//   function*   →  coroutine definition
//   yield       →  suspend / hand control back to the scheduler
//   .next()     →  resume the coroutine with a value
//
// Compare with stackful coroutines (e.g. Lua coroutines, Java fibers) which
// preserve the entire call stack and can yield from deep in a call chain.
//============================================================================

// ---------------------------------------------------------------------------
// Fibonacci — infinite lazy sequence via a stackless coroutine
// ---------------------------------------------------------------------------

/**
 * Generator function that produces the Fibonacci sequence on demand.
 *
 * Each `yield` suspends the function; the caller receives the current value.
 * On the next `.next()` the function resumes right after the yield, with all
 * local variables (`a`, `b`, `temp`) intact in the generator's suspended state.
 *
 * Because this is a *stackless* coroutine, the yield is at the top-level of
 * the generator body — it cannot be placed inside a nested helper that the
 * generator calls (the helper would need to be a generator itself).
 */
function* fibonacciGenerator() {
  let a = 0;
  let b = 1;

  while (true) {
    yield a;           // SUSPEND: hand `a` to the consumer
    const temp = a + b;
    a = b;
    b = temp;
  }
}

// ---------------------------------------------------------------------------
// Consumer — resume the coroutine repeatedly to fetch values
// ---------------------------------------------------------------------------

console.log("=== Fibonacci (stackless coroutine via generator) ===\n");

const fib = fibonacciGenerator();   // no code runs yet — returns an iterator

console.log("First 15 Fibonacci numbers:");
const values = [];
for (let i = 0; i < 15; i++) {
  values.push(fib.next().value);    // RESUME → get next value
}
console.log(values.join(", "));

console.log("\n--- Manual step-by-step ---\n");

const fib2 = fibonacciGenerator();
console.log("next():", fib2.next()); // { value: 0, done: false }
console.log("next():", fib2.next()); // { value: 1, done: false }
console.log("next():", fib2.next()); // { value: 1, done: false }
console.log("next():", fib2.next()); // { value: 2, done: false }
console.log("next():", fib2.next()); // { value: 3, done: false }

// ---------------------------------------------------------------------------
// Two-way communication — send values back into the generator
// ---------------------------------------------------------------------------

console.log("\n--- Two-way communication (sending values into generator) ---\n");

/**
 * A generator that lets the caller influence the sequence.
 * The value passed to .next() replaces the yield expression.
 */
function* interactiveFibonacci() {
  let a = 0;
  let b = 1;

  while (true) {
    const reset = yield a;   // yield current, then receive external value
    if (reset === true) {
      a = 0;
      b = 1;
    } else if (typeof reset === "number") {
      a = reset;
      b = a + 1;
    } else {
      const temp = a + b;
      a = b;
      b = temp;
    }
  }
}

const fib3 = interactiveFibonacci();
console.log(fib3.next().value);         // 0  (initial)
console.log(fib3.next().value);         // 1  (normal step)
console.log(fib3.next().value);         // 1  (normal step)
console.log(fib3.next().value);         // 2  (normal step)
console.log(fib3.next(true).value);     // 0  (reset via sent value)
console.log(fib3.next().value);         // 1  (continues after reset)

// ---------------------------------------------------------------------------
// Key takeaway
// ---------------------------------------------------------------------------
//
// Generators = stackless coroutines because:
//   - State is held in the Generator object (not the native stack).
//   - `yield` only works directly inside the function* body.
//   - No nested activation frames — each suspend/resume cycle is cheap.
//   - The runtime schedules the coroutine explicitly via .next().
//
// This stands in contrast to:
//   - async/await (also stackless, but scheduled by the microtask queue).
//   - Web Workers (thread-like, preemptive, no shared stack).
//   - SharedArrayBuffer (true shared memory, no coroutines at all).
//============================================================================
