// =============================================================================
// actor / print_server.js
//
// Concurrency Paradigm: Actor Model
//
// A simple actor-based print server using a dedicated EventEmitter for
// message dispatching.  Each actor owns a private mailbox and processes
// messages sequentially on its own "turn" (microtask).
//
// Compare with: Python actor_print_server.py, Erlang gen_server
// =============================================================================

import { EventEmitter } from "node:events";
import { setTimeout } from "node:timers/promises";

// ---------------------------------------------------------------------------
// Actor: PrintServer
// ---------------------------------------------------------------------------

class PrintServer {
  #mailbox = new EventEmitter();
  #counter = 0;
  #running = false;

  constructor() {
    this.#mailbox.setMaxListeners(100);
  }

  start() {
    this.#running = true;
    // The actor processes messages one at a time
    this.#mailbox.on("message", async (msg) => {
      if (!this.#running) return;

      this.#counter++;
      await setTimeout(20); // simulate print time

      const output = `[PrintServer] #${this.#counter} printed: ${msg.text}`;
      console.log(`  ${output}`);

      if (msg.replyCallback) {
        msg.replyCallback(output);
      }
    });

    console.log("  [PrintServer] started");
  }

  /** Fire-and-forget: send a message, no reply expected. */
  tell(text) {
    this.#mailbox.emit("message", { text, replyCallback: null });
  }

  /** Request-response: send a message and wait for reply. */
  async ask(text) {
    return new Promise((resolve) => {
      this.#mailbox.emit("message", {
        text,
        replyCallback: (reply) => resolve(reply),
      });
    });
  }

  stop() {
    this.#running = false;
    this.#mailbox.removeAllListeners("message");
    console.log("  [PrintServer] stopped");
  }
}

// ---------------------------------------------------------------------------
// Demo
// ---------------------------------------------------------------------------

console.log("=== Actor: PrintServer Demo ===\n");

const server = new PrintServer();
server.start();

// Fire-and-forget messages
server.tell("Hello, Actor World!");
server.tell("Printing document #1");
server.tell("Printing document #2");

// Request-response
const reply = await server.ask("Urgent report");
console.log(`  [Client] got reply: ${reply}`);

await setTimeout(50);

server.tell("Final document");
await setTimeout(50);
server.stop();

console.log("\nPrintServer demo passed.");
