// =============================================================================
// csp / promise_chain.js
//
// Concurrency Paradigm: Communicating Sequential Processes (CSP-like)
//
// CSP (Hoare, 1978) models concurrency with independent processes that
// communicate ONLY through synchronous channels.  In Go, goroutines + channels
// are the canonical realization.  JavaScript has no built-in channel type, but
// Promises can serve as a **single-value channel analog**: a pending Promise
// is a buffered channel of capacity 1; `.then()` attaches a receiver; `.resolve()`
// sends the value.
//
// Mapping (Promise ~ Channel):
//   new Promise()      ->  channel creation
//   resolve(value)     ->  send value into channel (fulfills exactly one reader)
//   promise.then(fn)   ->  receive value from channel
//   Promise.all(...)   ->  fan-in / join multiple channels
//   promise chain      ->  sequential process (one step after another)
//
// Limitations vs Go channels:
//   - Promise can only deliver ONE value (single-shot channel).
//   - There's no built-in select/alt (though Promise.race approximates it).
//   - Back-pressure / buffering require manual implementation.
//   - Channel closing is not expressible directly.
//============================================================================

// ---------------------------------------------------------------------------
// Helper - a channel-alike factory for demonstration
// ---------------------------------------------------------------------------

/**
 * Creates a single-value channel (a promise + its resolver).
 *
 * @returns {{ promise: Promise, send: (value) => void }}
 */
function channel() {
  let send;
  const promise = new Promise((resolve) => {
    send = resolve;
  });
  return { promise, send };
}

// ---------------------------------------------------------------------------
// Process 1 - Producer (sender)
// ---------------------------------------------------------------------------

/**
 * Simulates a process that computes values and sends them into channels.
 * Each computation is wrapped in setTimeout to simulate async work.
 */
function producerProcess(name, values, channels) {
  console.log("  [" + name + "] starting...");

  // Start with the first value immediately
  let idx = 0;

  /**
   * Recursive helper - send each value through the channel chain.
   * `.then()` acts as the "receive and react" step, and returning
   * a new channel from within the handler creates a sequential pipeline.
   */
  function step() {
    if (idx >= values.length) {
      console.log("  [" + name + "] all values sent, done");
      return;
    }

    const value = values[idx];
    idx++;

    // SEND: resolve the current channel's promise with the value.
    // Only one receiver (the attached `.then()`) will consume it.
    channels.send(value);

    // Wait for the receiver to acknowledge before sending the next value.
    // This is the CSP "synchronous send" property: the sender waits until
    // the receiver is ready.
    return channels.ack.promise.then(() => {
      // Receiver acknowledged - start next send cycle
      step();
    });
  }

  // Kick off the first send.  setTimeout lets the receiver set up first.
  setTimeout(step, 0);
}

// ---------------------------------------------------------------------------
// Process 2 - Consumer (receiver)
// ---------------------------------------------------------------------------

function consumerProcess(name, channels, onValue) {
  console.log("  [" + name + "] starting...");

  /**
   * Recursive receiver - each `.then()` is a "receive from channel".
   *
   * CSP semantics:
   *   - The receiver blocks (here: returns a promise chain) until a value
   *     arrives.
   *   - Communication is synchronous: both sender and receiver wait for
   *     each other.
   */
  function receive() {
    return channels.receive.promise.then((value) => {
      onValue(value);

      // After processing, acknowledge so the sender can proceed.
      const ack = channel();
      channels.ack.send(value);   // acknowledge (notify sender)
      channels.receive = ack;     // set up the next receive channel
      return receive();           // wait for next value
    });
  }

  return receive();
}

// ---------------------------------------------------------------------------
// Run the CSP-like pipeline
// ---------------------------------------------------------------------------

console.log("=== CSP-like communication via Promise chains ===\n");
console.log("Promises act as single-value channels.  `.then()` is the receive");
console.log("operation, and resolve() is the send.  The pattern is similar to");
console.log("Go's goroutines + channels, but limited to one value per channel.\n");

// Set up channels between the producer and consumer.
// Each "channel" is a promise + resolve function pair.
const dataChan = channel();   // data channel
const ackChan = channel();   // acknowledgment channel (back-pressure)

const comm = {
  send: (val) => dataChan.send(val),          // producer writes here
  receive: dataChan,                           // consumer reads from here
  ack: ackChan,                                // consumer writes ack here
};

// Start both processes.
// In CSP terms, they are "active" simultaneously, communicating via channels.
const values = [10, 20, 30, 40, 50];

const producer = producerProcess("Producer", values, comm);
const consumer = consumerProcess("Consumer", comm, (val) => {
  console.log("  [Consumer] received " + val + ", processing...");
});

// ---------------------------------------------------------------------------
// Fan-in example - Promise.all as channel join
// ---------------------------------------------------------------------------

console.log("\n--- Fan-in (Promise.all as channel join) ---\n");

/**
 * Create N "processes" that each send one value through their own channel.
 * Promise.all joins them - it awaits all channels simultaneously.
 */

function worker(name, delayMs, result) {
  // Each worker returns a "channel" - a promise that resolves with its result
  return new Promise((resolve) => {
    console.log("    [Worker-" + name + "] working for " + delayMs + "ms...");
    setTimeout(() => {
      console.log("    [Worker-" + name + "] done, sending \"" + result + "\"");
      resolve(result);   // "send" value through this worker's channel
    }, delayMs);
  });
}

// Launch all workers concurrently.  Each one is an independent "process"
// that sends a value on its own channel.  Promise.all joins them.
// Use a self-executing async function for top-level await compatibility
(async () => {
  const allResults = await Promise.all([
    worker("A", 30, "result-A"),
    worker("B", 10, "result-B"),
    worker("C", 20, "result-C"),
  ]);

  console.log("\n  Fan-in complete, all results:", allResults);

  // -----------------------------------------------------------------------
  // Select-like pattern - Promise.race as channel alt
  // -----------------------------------------------------------------------

  console.log("\n--- Select / Alt (Promise.race as channel alt) ---\n");

  function timeoutChannel(ms, value) {
    return new Promise((resolve) => setTimeout(() => resolve(value), ms));
  }

  // Promise.race ~ Go's select: whichever channel delivers first wins.
  const winner = await Promise.race([
    timeoutChannel(50, "fast response"),
    timeoutChannel(100, "slow response"),
    timeoutChannel(200, "too slow"),
  ]);

  console.log("  Race winner:", winner);
  // -> "fast response" (shortest timeout wins)

  // -----------------------------------------------------------------------
  // Unbuffered channel handshake simulation
  // -----------------------------------------------------------------------

  console.log("\n--- Unbuffered channel handshake (rendezvous) ---\n");

  /**
   * In CSP, an unbuffered channel send blocks until a receiver is ready.
   * We simulate this with a promise pair: the sender resolves a promise that
   * the receiver is waiting on, and vice versa.
   */
  async function rendezvousExample() {
    // Two handshake promises - a "ready" signal each way
    let receiverReady;
    const senderReady = new Promise((r) => { receiverReady = r; });

    let senderDone;
    const receiverDone = new Promise((r) => { senderDone = r; });

    // Sender "process"
    const sender = (async () => {
      console.log("    Sender waiting for receiver to be ready...");
      await senderReady;                    // block until receiver is ready
      console.log("    Sender -> sends value");
      receiverReady("VALUE");              // unblock receiver
      await receiverDone;                   // wait for receiver to acknowledge
      console.log("    Sender done");
    })();

    // Receiver "process"
    const receiver = (async () => {
      console.log("    Receiver waiting to receive...");
      receiverReady("ready");              // signal sender we are ready
      const value = await senderReady;     // receive the value
      console.log("    Receiver <- got:", value);
      senderDone("ack");                   // acknowledge
      console.log("    Receiver done");
    })();

    await Promise.all([sender, receiver]);
  }

  await rendezvousExample();
})();

// ---------------------------------------------------------------------------
// Key takeaway
// ---------------------------------------------------------------------------
//
// Promises as channel analogs:
//   - Promise.resolve(value) = send on channel
//   - .then(fn)             = receive from channel
//   - Promise.all([...])    = fan-in / join
//   - Promise.race([...])   = select / alt
//
// JavaScript promises are NOT full CSP channels:
//   - Single-shot only (no multiple sends over same promise).
//   - No buffering, no channel close, no range loops.
//   - But they capture the ESSENCE of CSP: communicating sequential
//     processes via message passing, not shared state.
//============================================================================
