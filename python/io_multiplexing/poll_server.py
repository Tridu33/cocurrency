"""
poll_server.py — Concurrent echo server using select.poll().

Demonstrates:
  - poll()-based I/O multiplexing (POSIX, more scalable than select).
  - Level-triggered behaviour (default; no edge-triggered option in poll).
  - Single-threaded event loop with per-fd event registration.
  - poll() returns a list of (fd, event) tuples — no need to rebuild
    fd sets on every iteration, unlike select().

Key differences from select():
  - No FD_SETSIZE limit — poll() uses a dynamically-sized pollfd array.
  - poll() returns only the fds that are ready (O(k) where k = ready count),
    vs select() which scans all watched fds (O(n)).
  - Registration is explicit via register()/modify()/unregister() instead
    of passing in reconstructed fd sets every call.
  - poll() is level-triggered: as long as data is readable, POLLIN will
    be reported every time poll() is called.

POLL event flags used:
  - POLLIN   — data available to read
  - POLLOUT  — ready for writing
  - POLLHUP  — hang-up (client disconnected)
  - POLLERR  — error condition
"""

import select
import socket
import time
from typing import Dict


class PollEchoServer:
    """Single-threaded echo server using select.poll()."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9091):
        self._host = host
        self._port = port
        self._server_sock: socket.socket | None = None
        self._poller = select.poll()
        self._send_bufs: Dict[int, bytes] = {}
        self._recv_bufs: Dict[int, bytearray] = {}
        # fd → socket map
        self._fd_to_sock: Dict[int, socket.socket] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Bind, listen, and register the server fd with the poller."""
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.setblocking(False)
        self._server_sock.bind((self._host, self._port))
        self._server_sock.listen(128)

        srv_fd = self._server_sock.fileno()
        self._fd_to_sock[srv_fd] = self._server_sock
        # Register interest in readability (accept events)
        self._poller.register(srv_fd, select.POLLIN)

        print(f"[poll] Listening on {self._host}:{self._port}  (LT — level-triggered)")

    def serve_forever(self) -> None:
        """Run the poll()-based event loop."""
        print("[poll] Event loop started (Ctrl-C to stop)")

        try:
            while True:
                # poll(timeout_ms) → list of (fd, event_mask)
                events = self._poller.poll(1000)  # 1 s timeout

                for fd, event in events:
                    if fd == self._server_sock.fileno():
                        self._accept_client(event)
                    else:
                        self._handle_io(fd, event)

        except KeyboardInterrupt:
            print("\n[poll] Shutting down...")
        finally:
            self._cleanup()

    # ------------------------------------------------------------------
    # Internal — connection lifecycle
    # ------------------------------------------------------------------

    def _accept_client(self, server_event: int) -> None:
        """Accept a new client; register it with the poller."""
        assert self._server_sock is not None

        if not (server_event & select.POLLIN):
            return

        try:
            conn, addr = self._server_sock.accept()
        except BlockingIOError:
            return

        conn.setblocking(False)
        fd = conn.fileno()
        self._fd_to_sock[fd] = conn
        self._recv_bufs[fd] = bytearray()
        self._send_bufs[fd] = b""
        # Register for read events initially
        self._poller.register(fd, select.POLLIN)
        print(f"[poll] Accepted {addr}  (fd={fd})  registered={len(self._fd_to_sock)} clients")

    def _handle_io(self, fd: int, event: int) -> None:
        """Handle read/write/error/hangup events for a client fd."""
        sock = self._fd_to_sock.get(fd)
        if sock is None:
            return

        # Error or hangup — close immediately
        if event & (select.POLLERR | select.POLLHUP):
            self._close_client(fd)
            return

        # Readable
        if event & select.POLLIN:
            self._handle_read(fd, sock)

        # Writable (may be in same event if both POLLIN|POLLOUT registered)
        if event & select.POLLOUT:
            self._handle_write(fd, sock)

    def _handle_read(self, fd: int, sock: socket.socket) -> None:
        """Read from client; if data received, echo by queuing into send_buf."""
        try:
            data = sock.recv(4096)
        except (ConnectionResetError, ConnectionAbortedError):
            data = b""

        if not data:
            self._close_client(fd)
            return

        # Echo back (upper-cased)
        self._recv_bufs.setdefault(fd, bytearray()).extend(data)
        self._send_bufs.setdefault(fd, b"")
        self._send_bufs[fd] += data.upper()

        # Switch to monitoring both read AND write readiness
        self._poller.modify(fd, select.POLLIN | select.POLLOUT)
        print(f"[poll] fd={fd}  recv {len(data)}B, switched to R/W")

    def _handle_write(self, fd: int, sock: socket.socket) -> None:
        """Flush pending send data; switch back to read-only when done."""
        buf = self._send_bufs.get(fd)
        if not buf:
            # Spurious POLLOUT — switch back to read-only
            self._poller.modify(fd, select.POLLIN)
            return

        try:
            n = sock.send(buf)
        except (ConnectionResetError, BrokenPipeError):
            self._close_client(fd)
            return

        if n > 0:
            self._send_bufs[fd] = buf[n:]
            if not self._send_bufs[fd]:
                # All buffered data sent — switch back to read-only
                self._poller.modify(fd, select.POLLIN)
            print(f"[poll] fd={fd}  sent {n}B, remaining {len(self._send_bufs[fd])}B")

    def _close_client(self, fd: int) -> None:
        """Unregister and close a client."""
        sock = self._fd_to_sock.pop(fd, None)
        if sock:
            try:
                self._poller.unregister(fd)
            except (KeyError, OSError):
                pass
            try:
                sock.close()
            except OSError:
                pass
        self._recv_bufs.pop(fd, None)
        self._send_bufs.pop(fd, None)
        print(f"[poll] Closed fd={fd}  remaining={len(self._fd_to_sock)-1}")

    def _cleanup(self) -> None:
        """Close server and all clients."""
        for fd in list(self._fd_to_sock.keys()):
            if fd != (self._server_sock and self._server_sock.fileno()):
                self._close_client(fd)
        if self._server_sock:
            try:
                self._poller.unregister(self._server_sock.fileno())
            except (KeyError, OSError):
                pass
            self._server_sock.close()
        print("[poll] Server stopped.")


# ------------------------------------------------------------------
# Demo
# ------------------------------------------------------------------

def demo_poll_server() -> None:
    """Demonstrate the poll()-based server with a driven client test."""
    import threading
    from io_multiplexing.select_server import _run_test_client

    print("=== poll() Echo Server (Level-Triggered) ===\n")

    server = PollEchoServer(port=9091)
    server.start()

    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.2)

    _run_test_client("poll", 9091, [b"hello", b"poll", b"test"])

    time.sleep(0.3)
    print("[demo] Test complete.\n")
    print("poll() demo passed.")


if __name__ == "__main__":
    demo_poll_server()
