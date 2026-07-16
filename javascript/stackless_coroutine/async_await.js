// =============================================================================
// stackless_coroutine / async_await.js
//
// Concurrency Paradigm: Stackless Coroutine (async/await)
//
// async/await is syntactic sugar over Promises.  Like generators, async
// functions are **stackless coroutines**: each `await` suspends the function
// frame without blocking the OS thread, and the runtime (microtask queue)
// resumes it when the awaited Promise settles.
//
// The key difference from function* generators:
//   - async/await is **implicitly scheduled** — the event loop resumes the
//     coroutine automatically when the awaited promise resolves.
//   - function* requires explicit .next() calls by a driver loop.
//
// Here we demonstrate cooperative multitasking: multiple async coroutines
// interleave their work on a single thread, yielding to each other at
// each await point.
//
// Mapping:
//   async function  →  coroutine definition
//   await promise   →  suspend coroutine, schedule resume on promise settle
//   event loop      →  implicit scheduler / cooperative multitasking runtime
//============================================================================

import { setTimeout } from "node:timers/promises";

// ---------------------------------------------------------------------------
// Helper — a "sleep" that yields control back to the event loop
// ---------------------------------------------------------------------------

/**
 * Creates a promise that resolves after `ms` milliseconds.
 * Awaiting it suspends the current coroutine and lets other tasks run.
 */
const sleep = setTimeout;

// ---------------------------------------------------------------------------
// Coroutine A — simulates periodic work (polling sensor data)
// ---------------------------------------------------------------------------

async function sensorPoller(id, intervalMs, totalReadings) {
  console.log(`  [Sensor-${id}] STARTED`);

  for (let i = 1; i <= totalReadings; i++) {
    // Simulate reading a sensor value
    const reading = Math.round(Math.random() * 100);

    // --- SUSPEND: yield to the event loop for `intervalMs` ---
    // While this coroutine sleeps, other coroutines (or the mainline)
    // can run.  This is *cooperative multitasking*: each await is an
    // explicit yield point.
    await sleep(intervalMs);

    console.log(`  [Sensor-${id}] reading #${i}: ${reading}`);
  }

  console.log(`  [Sensor-${id}] DONE`);
}

// ---------------------------------------------------------------------------
// Coroutine B — simulates a watchdog that checks a condition periodically
// ---------------------------------------------------------------------------

async function watchdog(timeoutMs) {
  console.log("  [Watchdog] STARTED (will fire in %d ms)", timeoutMs);

  await sleep(timeoutMs);

  console.log("  [Watchdog] ALERT! No response within %d ms", timeoutMs);
}

// ---------------------------------------------------------------------------
// Coroutine C — simulates a burst of sequential async I/O calls
// ---------------------------------------------------------------------------

async function dataProcessor() {
  console.log("  [Processor] STARTED");

  // Each step is an awaited async operation.  Between them, other
  // coroutines can interleave their work.
  const step1 = await Promise.resolve("fetched metadata");
  console.log("  [Processor] step 1:", step1);
  //           ^-- yield point

  const step2 = await Promise.resolve("downloaded payload");
  console.log("  [Processor] step 2:", step2);
  //           ^-- yield point

  const step3 = await Promise.resolve("transformed data");
  console.log("  [Processor] step 3:", step3);
  //           ^-- yield point

  console.log("  [Processor] DONE");
}

// ---------------------------------------------------------------------------
// Cooperative multitasking — run all coroutines concurrently
// ---------------------------------------------------------------------------

console.log("=== Stackless Coroutines with async/await (cooperative multitasking) ===\n");
console.log("All coroutines are launched simultaneously. The event loop");
console.log("interleaves their execution at each `await` point.\n");

// Launch all three coroutines.  They run *concurrently* on a single thread.
// Each `await` yields control; the event loop chooses which coroutine to
// resume next.  This is cooperative, NOT preemptive — a coroutine must
// hit an await for others to run.

const tasks = await Promise.all([
  sensorPoller("A", 15, 4),    // 4 readings, 15ms apart
  sensorPoller("B", 25, 3),    // 3 readings, 25ms apart
  watchdog(60),                 // alert after 60ms
  dataProcessor(),              // 3 sequential steps
]);

console.log("\n=== All coroutines completed ===");

// ---------------------------------------------------------------------------
// Error handling — awaited rejections behave like thrown exceptions
// ---------------------------------------------------------------------------

console.log("\n--- Error handling in async coroutines ---\n");

async function flakyOperation(shouldFail) {
  await sleep(10);
  if (shouldFail) {
    throw new Error("Something went wrong!");
  }
  return "OK";
}

// Errors propagate naturally — the reject becomes an exception at the await.
try {
  const result = await flakyOperation(true);  // will throw
  console.log("Result:", result);
} catch (err) {
  console.log("Caught from async coroutine:", err.message);
}

// ---------------------------------------------------------------------------
// Key takeaway
// ---------------------------------------------------------------------------
//
// async/await = stackless coroutines because:
//   - Each await suspends only the current async frame, not the native stack.
//   - The runtime (microtask queue) automatically schedules resumption.
//   - Multiple async functions interleave on a single thread (concurrency,
//     not parallelism).
//   - The "stack" of awaited calls is reconstructed from the Promise chain;
//     you cannot await inside a synchronous callback without making the
//     callback async too.
//
// This is the same stackless model as generators, but with implicit
// scheduling via the event loop rather than explicit .next() calls.
//============================================================================
