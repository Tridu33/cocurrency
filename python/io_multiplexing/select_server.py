"""
select_server.py — Concurrent echo server using select.select().

Demonstrates:
  - select()-based I/O multiplexing (POSIX standard, portable).
  - Level-triggered behaviour: select() keeps reporting a ready fd
    as long as data is available.
  - Single-threaded concurrent connection handling via event loop.
  - Non-blocking sockets with manual read/write readiness tracking.

Key concepts:
  - select() monitors three fd sets: readable, writable, exceptional.
  - It's level-triggered: if data arrives and you don't read it,
    the next select() call will report the fd as readable again.
  - FD_SETSIZE limit (typically 1024) restricts the number of
    monitored fds — poll/epoll remove this limitation.
  - O(n) scan: select() scans all fds on every call.
"""

import select
import socket
import sys
import time
from typing import Dict


class SelectEchoServer:
    """Single-threaded echo server using select.select()."""

    def __init__(self, host: str = "127.0.0.1", port: int = 9090):
        self._host = host
        self._port = port
        self._server_sock: socket.socket | None = None
        self._running = False
        # Per-client send buffers (data queued but not yet written)
        self._send_bufs: Dict[int, bytes] = {}
        # Per-client recv buffers (partial reads)
        self._recv_bufs: Dict[int, bytearray] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Bind and listen; non-blocking, ready for the event loop."""
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.setblocking(False)
        self._server_sock.bind((self._host, self._port))
        self._server_sock.listen(128)
        print(f"[select] Listening on {self._host}:{self._port}  (LT — level-triggered)")

    def stop(self) -> None:
        """Signal the event loop to stop and clean up."""
        self._running = False

    def serve_forever(self) -> None:
        """Run the select()-based event loop."""
        assert self._server_sock is not None

        # fd → socket map (for lookups after select returns)
        fd_to_sock: Dict[int, socket.socket] = {
            self._server_sock.fileno(): self._server_sock
        }

        # We only track readable set; writable set is updated per-iteration
        # based on whether we have buffered data to send.
        read_fds: set[int] = {self._server_sock.fileno()}

        self._running = True
        print("[select] Event loop started (Ctrl-C to stop)")

        try:
            while self._running:
                # Build write-fd set: any fd that has pending send data
                write_fds: set[int] = {
                    fd for fd, buf in self._send_bufs.items() if buf
                }

                try:
                    rlist, wlist, _ = select.select(read_fds, write_fds, [], 1.0)
                except (OSError, ValueError) as e:
                    # fd was closed externally (e.g. server shutdown)
                    if not self._running:
                        break
                    print(f"[select] select error: {e}, cleaning up...")
                    break

                for ready_fd in rlist:
                    if ready_fd == self._server_sock.fileno():
                        self._accept_client(fd_to_sock, read_fds)
                    else:
                        self._handle_read(ready_fd, fd_to_sock)

                for ready_fd in wlist:
                    self._handle_write(ready_fd, fd_to_sock, read_fds)

        except KeyboardInterrupt:
            print("\n[select] Shutting down...")
        finally:
            self._cleanup(fd_to_sock, read_fds)

    # ------------------------------------------------------------------
    # Internal — connection lifecycle
    # ------------------------------------------------------------------

    def _accept_client(
        self,
        fd_to_sock: Dict[int, socket.socket],
        read_fds: set[int],
    ) -> None:
        """Accept a new client and register its fd."""
        assert self._server_sock is not None
        try:
            conn, addr = self._server_sock.accept()
        except BlockingIOError:
            return  # spurious wakeup

        conn.setblocking(False)
        fd = conn.fileno()
        fd_to_sock[fd] = conn
        read_fds.add(fd)
        self._recv_bufs[fd] = bytearray()
        self._send_bufs[fd] = b""
        print(f"[select] Accepted {addr}  (fd={fd})")

    def _handle_read(
        self,
        fd: int,
        fd_to_sock: Dict[int, socket.socket],
    ) -> None:
        """Read data from a client fd. Echo it back by queuing into send_buf."""
        sock = fd_to_sock.get(fd)
        if sock is None:
            return

        try:
            data = sock.recv(4096)
        except (ConnectionResetError, ConnectionAbortedError):
            data = b""

        if not data:
            self._close_client(fd, fd_to_sock)
            return

        # Echo: queue the data back to the client (upper-cased to show it worked)
        self._recv_bufs.setdefault(fd, bytearray()).extend(data)
        self._send_bufs.setdefault(fd, b"")
        self._send_bufs[fd] += data.upper()
        print(f"[select] fd={fd}  recv {len(data)}B, send_buf now {len(self._send_bufs[fd])}B")

    def _handle_write(
        self,
        fd: int,
        fd_to_sock: Dict[int, socket.socket],
        read_fds: set[int],
    ) -> None:
        """Flush pending send data for a writable fd."""
        sock = fd_to_sock.get(fd)
        buf = self._send_bufs.get(fd)
        if sock is None or not buf:
            return

        try:
            n = sock.send(buf)
        except (ConnectionResetError, BrokenPipeError):
            self._close_client(fd, fd_to_sock, read_fds)
            return

        if n > 0:
            self._send_bufs[fd] = buf[n:]
            print(f"[select] fd={fd}  sent {n}B, remaining {len(self._send_bufs[fd])}B")

    def _close_client(
        self,
        fd: int,
        fd_to_sock: Dict[int, socket.socket],
        read_fds: set[int] | None = None,
    ) -> None:
        """Clean up a disconnected client."""
        if read_fds is None:
            read_fds = set()
        sock = fd_to_sock.pop(fd, None)
        if sock:
            try:
                sock.close()
            except OSError:
                pass
        read_fds.discard(fd)
        self._recv_bufs.pop(fd, None)
        self._send_bufs.pop(fd, None)
        print(f"[select] Closed fd={fd}")

    def _cleanup(
        self,
        fd_to_sock: Dict[int, socket.socket],
        read_fds: set[int],
    ) -> None:
        """Close all client connections and the server socket."""
        for fd in list(fd_to_sock.keys()):
            if fd != self._server_sock.fileno():  # type: ignore[union-attr]
                self._close_client(fd, fd_to_sock, read_fds)
        if self._server_sock:
            self._server_sock.close()
        print("[select] Server stopped.")


# ------------------------------------------------------------------
# Demo — run a standalone server (connect with: nc 127.0.0.1 9090)
# ------------------------------------------------------------------

def demo_select_server() -> None:
    """Demonstrate the select()-based server with a driven client test."""
    import threading

    print("=== select() Echo Server (Level-Triggered) ===\n")

    server = SelectEchoServer(port=9090)
    server.start()

    # Drive the server in a background thread
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.2)

    # --- Client test ---
    _run_test_client("select", 9090, [b"hello", b"world"])

    time.sleep(0.3)
    # Signal shutdown via KeyboardInterrupt-like behaviour
    print("[demo] Test complete — server thread will be cleaned up on exit.\n")
    print("select() demo passed.")


# ------------------------------------------------------------------
# Shared test helper
# ------------------------------------------------------------------

def _run_test_client(label: str, port: int, messages: list[bytes]) -> None:
    """Connect, send messages, receive echoed (upper-cased) replies, print results."""
    print(f"[{label}-client] Connecting to 127.0.0.1:{port} ...")
    sock = socket.create_connection(("127.0.0.1", port), timeout=2)
    sock.settimeout(2)

    for msg in messages:
        sock.sendall(msg)
        reply = sock.recv(4096)
        expected = msg.upper()
        assert reply == expected, f"Expected {expected!r}, got {reply!r}"
        print(f"  [{label}-client] sent={msg!r}  →  echo={reply!r}")

    sock.close()
    print(f"  [{label}-client] All {len(messages)} messages echoed correctly.\n")


if __name__ == "__main__":
    demo_select_server()
