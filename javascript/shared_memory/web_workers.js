// =============================================================================
// shared_memory / web_workers.js
//
// Concurrency Paradigm: Shared Memory with Web Workers
//
// JavaScript is single-threaded by design, but Web Workers provide true
// OS-level threads.  Workers communicate with the main thread via message
// passing (postMessage / onmessage), which copies data by default.
//
// For *shared memory*, the EventTarget / postMessage API is augmented by:
//   - SharedArrayBuffer — a fixed-length raw binary buffer shared between
//     threads with no copying.  Access is race-condition-free only when
//     combined with Atomic operations.
//   - Atomics — static methods (Atomics.load, Atomics.store, Atomics.add,
//     Atomics.wait, Atomics.notify) that provide synchronisation primitives
//     on SharedArrayBuffer views.
//
// IMPORTANT BROWSER LIMITATIONS:
//   1. SharedArrayBuffer requires Cross-Origin-Opener-Policy and
//      Cross-Origin-Embedder-Policy headers (COOP/COEP) to be set.
//   2. Not available in older browsers / Node.js without --experimental-worker.
//   3. Shared memory is low-level — no built-in locking (spin-locks / mutexes
//      must be built on Atomics).
//   4. No shared JavaScript objects — only raw binary data in the buffer.
//   5. Workers have no DOM access, no shared scope, no global state.
//
// NODE.JS NOTE:
//   Node.js supports worker_threads with SharedArrayBuffer similarly.
//   This file is conceptual — running it in pure Node without a Worker
//   instantiation is a no-op.  See the module-level comment for how to
//   actually run the workers.
//============================================================================

// ---------------------------------------------------------------------------
// Inline Worker code (as a string for demo — normally a separate file)
// ---------------------------------------------------------------------------

/**
 * This is the code that would run inside a Web Worker.
 *
 * The worker receives a SharedArrayBuffer via postMessage, reads and writes
 * to it using Atomics for synchronisation, and notifies the main thread
 * when work is complete.
 *
 * In a real application you would write this as a separate .js file and
 * create the worker with `new Worker("worker-file.js")`.
 */
const WORKER_CODE = `
// Worker scope — no window, no DOM.
// 'self' refers to the Worker's global scope.

self.onmessage = function (event) {
  const { sharedBuffer, workerId } = event.data;

  // Create a typed view over the shared buffer.
  // Int32Array gives us 32-bit signed integers.
  const view = new Int32Array(sharedBuffer);

  const start = performance.now();

  // --- Worker computation ---
  // Atomically add 1 to slot 0 (a shared counter).
  // Atomics.add returns the OLD value atomically — no race.
  for (let i = 0; i < 100; i++) {
    Atomics.add(view, 0, 1);
  }

  // --- Sync point: notify the main thread ---
  // Store the worker's ID in slot 1.
  Atomics.store(view, 1, workerId);

  // Notify the main thread that this worker is done.
  // (Atomics.notify wakes up a thread waiting on Atomics.wait.)
  Atomics.notify(view, 1, 1);

  const elapsed = performance.now() - start;
  self.postMessage({ type: "done", workerId, elapsed });
};
`;

// ---------------------------------------------------------------------------
// Main-thread setup (conceptual — requires a real browser/Worker environment)
// ---------------------------------------------------------------------------

/**
 * SharedArrayBuffer with Atomics — Shared Memory Pattern
 *
 * Steps:
 *   1. Create a SharedArrayBuffer of N bytes.
 *   2. Create workers, passing a reference to the buffer.
 *   3. Each worker atomically mutates the buffer.
 *   4. The main thread uses Atomics.load / Atomics.wait to read results.
 */

console.log("=== Shared Memory with Web Workers (conceptual) ===\n");
console.log("This code demonstrates the pattern but CANNOT run here because");
console.log("it requires a real browser or Node.js worker_threads environment.\n");
console.log("See the text below for the actual executable approach.\n");

// --- Pattern (would run in a browser with COOP/COEP headers) ---

/**
 * // STEP 1 — Allocate shared memory (4 KiB = 1024 int32s)
 * const sharedBuffer = new SharedArrayBuffer(4 * 1024);
 *
 * // Zero-initialise the first few slots
 * const view = new Int32Array(sharedBuffer);
 * Atomics.store(view, 0, 0);  // counter
 * Atomics.store(view, 1, 0);  // worker-id slot
 * Atomics.store(view, 2, 0);  // flag slot
 *
 * // STEP 2 — Spawn workers
 * const worker1 = new Worker("worker.js");
 * const worker2 = new Worker("worker.js");
 *
 * worker1.postMessage({ sharedBuffer, workerId: 1 });
 * worker2.postMessage({ sharedBuffer, workerId: 2 });
 *
 * // STEP 3 — Wait for workers (Atomics.wait blocks the main thread!
 * //          In browsers this is only allowed in a Worker, not the main
 * //          thread.  So the "main" thread here would itself be a Worker.)
 * Atomics.wait(view, 1, 0);  // block until slot 1 changes
 * Atomics.wait(view, 2, 0);  // block until slot 2 changes
 *
 * // STEP 4 — Read results
 * console.log("Final counter:", Atomics.load(view, 0));
 */

// ---------------------------------------------------------------------------
// Thread Synchronisation with Atomics — Spin-lock example
// ---------------------------------------------------------------------------

console.log("--- Atomics-based Spin Lock (mutex via compare-and-swap) ---\n");

/**
 * Implements a simple mutex using Atomics.compareExchange.
 *
 * Atomics.compareExchange(typedArray, index, expected, value)
 *   - Atomically: if typedArray[index] === expected, set it to value.
 *   - Returns the OLD value.
 *
 * If old value === expected, we acquired the lock.
 * Otherwise, another thread holds it — we spin (busy-wait).
 */
class SpinLock {
  /**
   * @param {Int32Array} view  — view over a SharedArrayBuffer
   * @param {number}      slot — index of the lock word (0 = unlocked, 1 = locked)
   */
  constructor(view, slot) {
    this.view = view;
    this.slot = slot;
  }

  /**
   * Acquire the lock — spin until we own it.
   * Atomics.compareExchange returns 0 (unlocked) on success, 1 on failure.
   */
  lock() {
    while (true) {
      // Try to atomically swap 0 → 1.  If the old value was 0, we win.
      const old = Atomics.compareExchange(this.view, this.slot, 0, 1);
      if (old === 0) return;  // acquired!
      // Otherwise another thread holds the lock — hint CPU we are spinning.
      Atomics.pause?.();      // x86 PAUSE / ARM YIELD (optional)
    }
  }

  /**
   * Release the lock — reset to 0.
   */
  unlock() {
    // A simple store is safe here because only the lock holder releases.
    Atomics.store(this.view, this.slot, 0);
  }

  /**
   * Execute a critical section under the lock.
   * @param {Function} fn
   */
  critical(fn) {
    this.lock();
    try {
      fn();
    } finally {
      this.unlock();
    }
  }
}

console.log("SpinLock defined (requires SharedArrayBuffer + Workers to test).\n");

// ---------------------------------------------------------------------------
// Node.js worker_threads example (can actually run)
// ---------------------------------------------------------------------------

console.log("--- Node.js worker_threads version (can actually be run) ---\n");
console.log("Run with:  node shared_memory/web_workers.js\n");

// Use Node.js worker_threads when available
let nodeExample = null;

try {
  const { Worker } = await import("node:worker_threads");
  nodeExample = true;
} catch {
  nodeExample = false;
}

if (nodeExample) {
  console.log("Node.js worker_threads detected — running shared-memory demo...\n");
  await runNodeWorkers();
} else {
  console.log("(Node.js worker_threads not available — run in a browser instead)");
}

// ===========================================================================
// Node.js worker_threads implementation
// ===========================================================================

async function runNodeWorkers() {
  const { Worker } = await import("node:worker_threads");
  const { fileURLToPath } = await import("node:url");

  // Create shared memory
  const sab = new SharedArrayBuffer(4 * 4); // 4 int32 slots
  const view = new Int32Array(sab);
  Atomics.store(view, 0, 0);  // counter
  Atomics.store(view, 1, 0);  // ready-flag 1
  Atomics.store(view, 2, 0);  // ready-flag 2
  Atomics.store(view, 3, 0);  // done-flag

  // Worker code as a string (eval'd in the worker).
  // In production you'd have a separate .js file.
  const workerCode = `
    const { parentPort } = require("worker_threads");

    parentPort.on("message", (msg) => {
      const { sab, id } = msg;
      const view = new Int32Array(sab);

      // Do work: atomically increment the counter 50 times
      for (let i = 0; i < 50; i++) {
        Atomics.add(view, 0, 1);
      }

      // Signal completion
      Atomics.store(view, id, id);       // store our ID into our slot
      Atomics.notify(view, id, 1);       // wake up the main thread
      parentPort.postMessage("done");
    });
  `;

  const __filename = fileURLToPath(import.meta.url);

  // Launch two workers
  const w1 = new Worker(workerCode, { eval: true });
  const w2 = new Worker(workerCode, { eval: true });

  console.log("  Main thread: sending SharedArrayBuffer to worker 1...");
  w1.postMessage({ sab, id: 1 });

  console.log("  Main thread: sending SharedArrayBuffer to worker 2...");
  w2.postMessage({ sab, id: 2 });

  // Main thread waits for both workers via Atomics.wait.
  // (Atomics.wait blocks the current thread, which is fine in Node.)
  console.log("  Main thread: waiting for worker 1...");
  Atomics.wait(view, 1, 0);

  console.log("  Main thread: waiting for worker 2...");
  Atomics.wait(view, 2, 0);

  const finalCount = Atomics.load(view, 0);
  console.log("\n  === Result ===");
  console.log("  Final counter value:", finalCount);
  console.log("  Expected (2 workers × 50 increments):", 100);
  console.log("  Race condition? :", finalCount !== 100 ? "YES!" : "NO (correct)");

  // Clean up
  w1.terminate();
  w2.terminate();
}

// ---------------------------------------------------------------------------
// Key takeaway
// ---------------------------------------------------------------------------
//
// Shared memory in JavaScript:
//   - SharedArrayBuffer provides low-level shared memory between Workers.
//   - Atomics provides synchronisation (atomic read-modify-write, wait/notify).
//   - Shared memory is DANGEROUS: race conditions, data tearing, deadlocks.
//   - Browser deployment requires COOP/COEP HTTP headers.
//   - For most use cases, message passing (postMessage) is safer and simpler.
//
// Compare to:
//   - Erlang/Elixir: no shared memory, all message passing.
//   - Java/C++: true shared memory with mutexes, condition variables.
//   - Go: shares by communicating (prefers channels, but sync.Mutex exists).
//
// JavaScript's shared memory is closest to C++20's atomic operations on
// shared memory — low-level, explicit, and easy to get wrong.
//============================================================================
