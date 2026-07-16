"""
print_server.py — Actor-model print server using queue.Queue + thread + reply_to.

Demonstrates:
  - An actor (PrintServer) with a mailbox (queue.Queue).
  - Message-passing with a reply_to pattern for request-response.
  - Thread-based actor execution.
  - Clean shutdown via a sentinel message.
"""

import threading
import queue
import dataclasses
import time


@dataclasses.dataclass
class PrintJob:
    """A print job message."""
    text: str
    reply_to: queue.Queue | None = None


@dataclasses.dataclass
class Shutdown:
    """Sentinel message to shut down the actor."""
    pass


class PrintServer:
    """
    An actor that processes print jobs from its mailbox.

    Messages are placed in the mailbox via `tell()` (fire-and-forget)
    or `ask()` (request-response via reply_to).
    """

    def __init__(self):
        self._mailbox: queue.Queue = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._running = False

    def start(self) -> None:
        """Start the actor's event loop in a background thread."""
        self._running = True
        self._thread.start()
        print("  [PrintServer] started")

    def tell(self, text: str) -> None:
        """Fire-and-forget: send a message with no reply."""
        self._mailbox.put(PrintJob(text=text))

    def ask(self, text: str) -> str:
        """
        Request-response: send a message and wait for a reply.
        The PrintServer echoes back a confirmation.
        """
        reply_q: queue.Queue = queue.Queue()
        self._mailbox.put(PrintJob(text=text, reply_to=reply_q))
        result = reply_q.get()
        return result

    def stop(self) -> None:
        """Send a shutdown signal and wait for the thread to finish."""
        self._mailbox.put(Shutdown())
        self._thread.join()
        print("  [PrintServer] stopped")

    def _run(self) -> None:
        """Process messages from the mailbox until Shutdown."""
        while self._running:
            msg = self._mailbox.get()
            if isinstance(msg, Shutdown):
                self._running = False
                break
            self._handle(msg)

    def _handle(self, msg: PrintJob) -> None:
        """Handle a single print job."""
        time.sleep(0.02)  # simulate processing
        output = f"[PrintServer] printed: {msg.text}"
        print(f"  {output}")
        if msg.reply_to is not None:
            msg.reply_to.put(output)


def demo_print_server() -> None:
    """Run an actor-model print-server demo."""
    print("=== Actor: PrintServer Demo ===\n")

    server = PrintServer()
    server.start()

    # Fire-and-forget messages
    server.tell("Hello, World!")
    server.tell("Printing document #1")
    server.tell("Printing document #2")

    # Request-response
    reply = server.ask("Urgent report")
    print(f"  [Client] got reply: {reply}")

    time.sleep(0.1)

    # More fire-and-forget
    server.tell("Final document")

    time.sleep(0.1)

    server.stop()

    print("\nPrintServer demo passed.")


if __name__ == "__main__":
    demo_print_server()
