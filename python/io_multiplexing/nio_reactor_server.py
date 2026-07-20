"""
nio_reactor_server.py — Reactor-pattern concurrent server (Java-NIO-style).

Demonstrates:
  - The Reactor pattern: a synchronous event demultiplexer (Dispatcher)
    waits for I/O events and dispatches them to registered Handlers.
  - Built atop asyncio (which itself wraps epoll/kqueue/IOCP).
  - Non-blocking I/O with callback-based dispatch — the "NIO way".
  - Single-threaded concurrency: one reactor thread handles all clients.

Reactor pattern (vs Proactor):
  ┌────────── Reactor (readiness-based) ──────────┐
  │  App registers handler + interest             │
  │  Reactor waits for "fd ready to read"         │
  │  Reactor calls handler.on_read()              │
  │  Handler calls sock.recv() — data is ready    │
  │  Handler calls sock.send() — may or may not   │
  │  be ready; if not, buffer and register write  │
  │  interest with reactor.                       │
  └────────────────────────────────────────────────┘

  ┌────────── Proactor (completion-based) ─────────┐
  │  App initiates async read + callback          │
  │  OS reads data in background                  │
  │  OS notifies "read complete, here's the data" │
  │  Callback is invoked with the result          │
  │  App NEVER calls recv() — OS did it already   │
  └────────────────────────────────────────────────┘

In this demo we implement a Reactor-style dispatcher with asyncio
primitives, demonstrating the core ideas behind Java NIO's
Selector / SelectionKey / Channel model, but in Python.

Components:
  - Reactor (Dispatcher): the event loop — waits on readiness events.
  - Acceptor: handles new connections, creates EchoHandlers.
  - EchoHandler: handles read/write events for one client connection.
  - Demultiplexer: asyncio's selector-based event loop (epoll underneath).
"""

import asyncio
import socket
import time
from typing import Dict, Optional, Set


# ==================================================================
# Reactor / Dispatcher
# ==================================================================

class Reactor:
    """
    Synchronous event demultiplexer.

    Watches registered (fd, event_mask) pairs and dispatches ready
    events to the associated handler callback.

    In real Java NIO, this is java.nio.channels.Selector.
    In this Python demo, we use asyncio's AbstractEventLoop which
    wraps epoll/kqueue under the hood.
    """

    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        # fd → (reader_callback, writer_callback)
        self._handlers: Dict[int, tuple] = {}
        self._read_watchers: Dict[int, asyncio.Handle] = {}
        self._write_watchers: Dict[int, asyncio.Handle] = {}

    def register_read(self, fd: int, callback) -> None:
        """Register interest in readability for fd."""
        if self._loop is None:
            return
        self._handlers.setdefault(fd, (None, None))
        r, w = self._handlers[fd]
        self._handlers[fd] = (callback, w)
        self._add_read_watcher(fd, callback)

    def register_write(self, fd: int, callback) -> None:
        """Register interest in writability for fd."""
        if self._loop is None:
            return
        self._handlers.setdefault(fd, (None, None))
        r, w = self._handlers[fd]
        self._handlers[fd] = (r, callback)
        self._add_write_watcher(fd, callback)

    def unregister_write(self, fd: int) -> None:
        """Remove write interest (keep read if registered)."""
        if fd in self._write_watchers:
            self._write_watchers[fd].cancel()
            del self._write_watchers[fd]

    def unregister_all(self, fd: int) -> None:
        """Remove all interest for fd."""
        if fd in self._read_watchers:
            self._read_watchers[fd].cancel()
            del self._read_watchers[fd]
        if fd in self._write_watchers:
            self._write_watchers[fd].cancel()
            del self._write_watchers[fd]
        self._handlers.pop(fd, None)

    def attach_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Attach to an asyncio event loop."""
        self._loop = loop

    # ------------------------------------------------------------------
    # Internal — asyncio fd watchers
    # ------------------------------------------------------------------

    def _add_read_watcher(self, fd: int, callback) -> None:
        loop = self._loop
        if loop is None:
            return

        # Remove previous watcher
        if fd in self._read_watchers:
            self._read_watchers[fd].cancel()

        # Use loop.add_reader — this is the "selector.register(fd, OP_READ)"
        # equivalent in Python.
        loop.add_reader(fd, callback)

        # Store a cancel handle
        self._read_watchers[fd] = _CancelHandle(fd, loop.remove_reader)

    def _add_write_watcher(self, fd: int, callback) -> None:
        loop = self._loop
        if loop is None:
            return

        if fd in self._write_watchers:
            self._write_watchers[fd].cancel()

        loop.add_writer(fd, callback)
        self._write_watchers[fd] = _CancelHandle(fd, loop.remove_writer)


class _CancelHandle:
    """Minimal asyncio.Handle-like for cancellation tracking."""

    def __init__(self, fd: int, remover):
        self._fd = fd
        self._remover = remover
        self._cancelled = False

    def cancel(self) -> None:
        if not self._cancelled:
            self._cancelled = True
            try:
                self._remover(self._fd)
            except (OSError, ValueError):
                pass


# ==================================================================
# Handlers (the "NIO" part — non-blocking I/O handlers)
# ==================================================================

class EchoHandler:
    """
    Handles non-blocking I/O for a single client connection.

    In Java NIO terms: this is the handler attached to a SelectionKey
    for a SocketChannel. Reactor calls on_read() when the channel is
    readable, on_write() when writable.
    """

    def __init__(self, reactor: Reactor, sock: socket.socket, addr: tuple):
        self._reactor = reactor
        self._sock = sock
        self._addr = addr
        self._fd = sock.fileno()
        self._send_buf: bytes = b""
        self._closed = False

        # Register read interest with the reactor
        self._reactor.register_read(self._fd, self.on_read)
        print(f"  [NIO-Handler] Created for {addr}  (fd={self._fd})")

    # ------------------------------------------------------------------
    # Event callbacks (called by Reactor when fd is ready)
    # ------------------------------------------------------------------

    def on_read(self) -> None:
        """Reactor callback: fd is readable."""
        if self._closed:
            return

        try:
            data = self._sock.recv(4096)
        except (BlockingIOError, InterruptedError):
            return  # spurious
        except (ConnectionResetError, ConnectionAbortedError):
            data = b""

        if not data:
            self._close()
            return

        # Process and echo back (upper-case)
        self._send_buf += data.upper()
        print(
            f"  [NIO-Handler] fd={self._fd}  recv {len(data)}B,"
            f" queued {len(self._send_buf)}B for send"
        )

        # Register write interest to flush
        self._reactor.register_write(self._fd, self.on_write)

    def on_write(self) -> None:
        """Reactor callback: fd is writable."""
        if self._closed:
            return

        if not self._send_buf:
            # Nothing left to send; remove write interest
            self._reactor.unregister_write(self._fd)
            return

        try:
            n = self._sock.send(self._send_buf)
        except BlockingIOError:
            return  # kernel buffer full, try again later
        except (ConnectionResetError, BrokenPipeError):
            self._close()
            return

        if n > 0:
            self._send_buf = self._send_buf[n:]
            print(
                f"  [NIO-Handler] fd={self._fd}  sent {n}B,"
                f" remaining {len(self._send_buf)}B"
            )

        if not self._send_buf:
            self._reactor.unregister_write(self._fd)

    # ------------------------------------------------------------------
    # Teardown
    # ------------------------------------------------------------------

    def _close(self) -> None:
        """Clean up resources."""
        if self._closed:
            return
        self._closed = True
        self._reactor.unregister_all(self._fd)
        try:
            self._sock.close()
        except OSError:
            pass
        print(f"  [NIO-Handler] Closed fd={self._fd} ({self._addr})")


class Acceptor:
    """
    Accepts new connections and creates EchoHandlers.

    In Java NIO: the handler registered for ServerSocketChannel OP_ACCEPT.
    """

    def __init__(self, reactor: Reactor, server_sock: socket.socket):
        self._reactor = reactor
        self._sock = server_sock
        self._fd = server_sock.fileno()
        reactor.register_read(self._fd, self.on_accept)

    def on_accept(self) -> None:
        """Reactor callback: server fd is readable (new connection)."""
        while True:
            try:
                conn, addr = self._sock.accept()
            except BlockingIOError:
                break  # no more pending connections

            conn.setblocking(False)
            EchoHandler(self._reactor, conn, addr)
            print(f"  [NIO-Acceptor] Accepted {addr}")


# ==================================================================
# NIO Reactor Server
# ==================================================================

class NIOReactorServer:
    """
    Reactor-pattern concurrent server.

    Wraps an asyncio event loop as the reactor/dispatcher, with
    non-blocking I/O handlers for each connection.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 9095):
        self._host = host
        self._port = port
        self._reactor = Reactor()
        self._server_sock: Optional[socket.socket] = None
        self._acceptor: Optional[Acceptor] = None

    def start(self) -> None:
        """Bind server socket and set up reactor."""
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.setblocking(False)
        self._server_sock.bind((self._host, self._port))
        self._server_sock.listen(128)

        print(f"[NIO-Reactor] Listening on {self._host}:{self._port}")

    def serve_forever(self) -> None:
        """Run the reactor event loop."""
        assert self._server_sock is not None

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._reactor.attach_loop(loop)

        # Register acceptor with reactor
        self._acceptor = Acceptor(self._reactor, self._server_sock)

        print("[NIO-Reactor] Event loop started (Ctrl-C to stop)")
        print("[NIO-Reactor] Pattern: Initiate → Register Interest → Callback on Ready\n")

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            print("\n[NIO-Reactor] Shutting down...")
        finally:
            self._cleanup(loop)

    def _cleanup(self, loop: asyncio.AbstractEventLoop) -> None:
        """Stop the event loop and close sockets."""
        loop.stop()
        # Let pending callbacks finish
        pending = asyncio.all_tasks(loop)
        if pending:
            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        loop.close()

        if self._server_sock:
            try:
                self._server_sock.close()
            except OSError:
                pass
        print("[NIO-Reactor] Server stopped.")


# ==================================================================
# Demo
# ==================================================================

def demo_nio_reactor() -> None:
    """Demonstrate the NIO Reactor-pattern server."""
    import threading
    from io_multiplexing.select_server import _run_test_client

    print("=" * 62)
    print("=== NIO Reactor-Pattern Echo Server ===")
    print("=" * 62)
    print()
    print("Architecture:")
    print("  Reactor (event loop)")
    print("    ├── Acceptor  (OP_ACCEPT → new EchoHandler)")
    print("    ├── EchoHandler#1 (OP_READ / OP_WRITE)")
    print("    ├── EchoHandler#2 ...")
    print("    └── EchoHandler#N")
    print()
    print("Flow:  data arrives → reactor wakes → handler.on_read()")
    print("       handler processes, queues reply → registers OP_WRITE")
    print("       reactor wakes → handler.on_write() flushes send buffer")
    print()

    server = NIOReactorServer(port=9095)
    server.start()

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.3)

    _run_test_client("NIO-reactor", 9095, [b"hello", b"nio", b"reactor"])

    time.sleep(0.3)
    print("NIO Reactor demo passed.\n")


if __name__ == "__main__":
    demo_nio_reactor()
