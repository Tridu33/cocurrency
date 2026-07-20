"""
epoll_server.py — Concurrent echo server using select.epoll() (Linux-specific).

Demonstrates:
  - epoll-based I/O multiplexing, the most scalable Linux mechanism.
  - Level-triggered (LT, default) vs edge-triggered (ET, EPOLLET flag) modes.
  - Single-threaded event loop with per-fd epoll registration.
  - The practical difference between LT and ET, and the programming
    discipline ET demands.

Key concepts:
  - **Level-Triggered (LT)**: epoll reports an fd as ready as long as
    data is available. This is the default mode. Safe and forgiving —
    you can read partial data and the fd will be reported again.
    Equivalent behaviour to select/poll.

  - **Edge-Triggered (ET)**: epoll reports an fd as ready ONLY when
    new data arrives (state transition from "not ready" to "ready").
    You MUST read until EAGAIN in one go, otherwise you may never be
    notified again and data is "lost" (stuck in the kernel buffer).
    ET is more efficient (fewer wakeups) but harder to get right.

  - epoll scales O(1) with respect to the number of watched fds —
    it uses an RB-tree internally and only returns ready fds.

  - EPOLLONESHOT: fd is automatically disabled after one event,
    preventing a single fd from starving others (re-arm with
    epoll.modify() after handling).

EPOLL event flags used:
  - EPOLLIN        — data available to read
  - EPOLLOUT       — ready for writing
  - EPOLLET        — edge-triggered mode
  - EPOLLONESHOT   — one-shot notification (auto-disable after event)
  - EPOLLRDHUP     — peer closed connection (or shut down write half)
  - EPOLLHUP       — hang-up
  - EPOLLERR       — error condition
"""

import select
import socket
import time
from enum import Enum
from typing import Dict


class TriggerMode(Enum):
    LEVEL = "LT"
    EDGE = "ET"


class EpollEchoServer:
    """
    Single-threaded echo server using epoll.

    Supports two trigger modes:
      - LEVEL  (default, LT):  safe, forgiving — epoll keeps reporting.
      - EDGE   (ET, EPOLLET):  efficient, demanding — read-until-EAGAIN required.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9092,
        mode: TriggerMode = TriggerMode.LEVEL,
        use_oneshot: bool = False,
    ):
        self._host = host
        self._port = port
        self._mode = mode
        self._use_oneshot = use_oneshot
        self._server_sock: socket.socket | None = None
        self._epoll = select.epoll()
        self._send_bufs: Dict[int, bytes] = {}
        self._fd_to_sock: Dict[int, socket.socket] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self) -> None:
        """Bind, listen, and register the server fd with epoll."""
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.setblocking(False)
        self._server_sock.bind((self._host, self._port))
        self._server_sock.listen(128)

        srv_fd = self._server_sock.fileno()
        self._fd_to_sock[srv_fd] = self._server_sock

        events = select.EPOLLIN
        if self._mode == TriggerMode.EDGE:
            events |= select.EPOLLET
        if self._use_oneshot:
            events |= select.EPOLLONESHOT

        self._epoll.register(srv_fd, events)

        oneshot_str = "+ONESHOT" if self._use_oneshot else ""
        print(
            f"[epoll-{self._mode.value}] Listening on {self._host}:{self._port}"
            f"  ({self._mode.value}{oneshot_str})"
        )

    def serve_forever(self) -> None:
        """Run the epoll-based event loop."""
        label = f"epoll-{self._mode.value}"
        print(f"[{label}] Event loop started (Ctrl-C to stop)")

        try:
            while True:
                # epoll.poll(timeout) → list of (fd, event_mask)
                events = self._epoll.poll(1.0)

                for fd, event in events:
                    if fd == self._server_sock.fileno():
                        self._accept_client(event)
                    else:
                        if self._mode == TriggerMode.EDGE:
                            self._handle_io_et(fd, event)
                        else:
                            self._handle_io_lt(fd, event)

        except KeyboardInterrupt:
            print(f"\n[{label}] Shutting down...")
        finally:
            self._cleanup()

    # ------------------------------------------------------------------
    # Internal — level-triggered I/O (safe, partial reads OK)
    # ------------------------------------------------------------------

    def _handle_io_lt(self, fd: int, event: int) -> None:
        """Handle I/O in level-triggered (LT) mode."""
        sock = self._fd_to_sock.get(fd)
        if sock is None:
            return

        if event & (select.EPOLLERR | select.EPOLLHUP):
            self._close_client(fd)
            return

        if event & select.EPOLLIN:
            try:
                data = sock.recv(4096)
            except (ConnectionResetError, ConnectionAbortedError):
                data = b""

            if not data:
                self._close_client(fd)
                return

            # LT is forgiving: we can read partial data; epoll will
            # report this fd again if more data remains.
            self._send_bufs.setdefault(fd, b"")
            self._send_bufs[fd] += data.upper()

            # Re-arm with EPOLLOUT so we can flush
            self._rearm(fd, select.EPOLLIN | select.EPOLLOUT)
            print(f"[epoll-LT] fd={fd}  recv {len(data)}B, re-armed R/W")

        if event & select.EPOLLOUT:
            self._flush_send(fd, sock)

    # ------------------------------------------------------------------
    # Internal — edge-triggered I/O (must drain completely)
    # ------------------------------------------------------------------

    def _handle_io_et(self, fd: int, event: int) -> None:
        """
        Handle I/O in edge-triggered (ET) mode.

        CRITICAL: In ET mode, we MUST read until EAGAIN. If we only
        read part of the available data, we will NOT be notified again
        (no new state transition), and the unread data is effectively
        "lost" until the client sends more.
        """
        sock = self._fd_to_sock.get(fd)
        if sock is None:
            return

        if event & (select.EPOLLERR | select.EPOLLHUP):
            self._close_client(fd)
            return

        # --- Read until EAGAIN (ET demands this) ---
        if event & select.EPOLLIN:
            total_read = 0
            while True:
                try:
                    data = sock.recv(4096)
                except BlockingIOError:
                    # EAGAIN / EWOULDBLOCK — kernel buffer drained
                    break
                except (ConnectionResetError, ConnectionAbortedError):
                    self._close_client(fd)
                    return

                if not data:
                    # EOF — peer closed
                    self._close_client(fd)
                    return

                self._send_bufs.setdefault(fd, b"")
                self._send_bufs[fd] += data.upper()
                total_read += len(data)

            if total_read > 0:
                # Re-arm so we get notified for writes
                self._rearm(fd, select.EPOLLIN | select.EPOLLOUT)
                print(f"[epoll-ET] fd={fd}  drained {total_read}B, re-armed R/W")

        # --- Write as much as we can ---
        if event & select.EPOLLOUT:
            self._flush_send(fd, sock)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _flush_send(self, fd: int, sock: socket.socket) -> None:
        """Write buffered data; re-arm read-only when done."""
        buf = self._send_bufs.get(fd)
        if not buf:
            self._rearm(fd, select.EPOLLIN)
            return

        if self._mode == TriggerMode.EDGE:
            # ET write: try to send as much as possible in one shot
            try:
                n = sock.send(buf)
            except BlockingIOError:
                return  # kernel send-buffer full; wait for next EPOLLOUT
            except (ConnectionResetError, BrokenPipeError):
                self._close_client(fd)
                return
        else:
            # LT write: single send is fine; epoll re-notifies if needed
            try:
                n = sock.send(buf)
            except (ConnectionResetError, BrokenPipeError):
                self._close_client(fd)
                return

        if n > 0:
            self._send_bufs[fd] = buf[n:]
            if not self._send_bufs[fd]:
                self._rearm(fd, select.EPOLLIN)
            print(
                f"[epoll-{self._mode.value}] fd={fd}  sent {n}B,"
                f" remaining {len(self._send_bufs[fd])}B"
            )

    def _rearm(self, fd: int, events: int) -> None:
        """Re-register interest; respects EPOLLET and EPOLLONESHOT flags."""
        if self._mode == TriggerMode.EDGE:
            events |= select.EPOLLET
        if self._use_oneshot:
            events |= select.EPOLLONESHOT
        try:
            self._epoll.modify(fd, events)
        except OSError:
            pass  # fd may already be closed

    def _accept_client(self, server_event: int) -> None:
        """Accept new clients. In ET mode, accept until EAGAIN."""
        assert self._server_sock is not None

        if not (server_event & select.EPOLLIN):
            return

        # ET accept loop: accept ALL pending connections (not just one)
        while True:
            try:
                conn, addr = self._server_sock.accept()
            except BlockingIOError:
                break  # no more pending connections (ET-safe)

            conn.setblocking(False)
            fd = conn.fileno()
            self._fd_to_sock[fd] = conn
            self._send_bufs[fd] = b""

            events = select.EPOLLIN
            if self._mode == TriggerMode.EDGE:
                events |= select.EPOLLET
            if self._use_oneshot:
                events |= select.EPOLLONESHOT

            self._epoll.register(fd, events)
            print(
                f"[epoll-{self._mode.value}] Accepted {addr}  (fd={fd})"
                f"  clients={len(self._fd_to_sock)-1}"
            )

        # Re-arm server fd if ONESHOT
        if self._use_oneshot:
            self._rearm(self._server_sock.fileno(), select.EPOLLIN)

    def _close_client(self, fd: int) -> None:
        """Unregister and close client."""
        sock = self._fd_to_sock.pop(fd, None)
        if sock:
            try:
                self._epoll.unregister(fd)
            except (OSError, FileNotFoundError):
                pass
            try:
                sock.close()
            except OSError:
                pass
        self._send_bufs.pop(fd, None)
        print(
            f"[epoll-{self._mode.value}] Closed fd={fd}"
            f"  remaining={len(self._fd_to_sock)-1}"
        )

    def _cleanup(self) -> None:
        """Close server and all clients."""
        for fd in list(self._fd_to_sock.keys()):
            if fd != self._server_sock.fileno():  # type: ignore[union-attr]
                self._close_client(fd)
        if self._server_sock:
            try:
                self._epoll.unregister(self._server_sock.fileno())
            except (OSError, FileNotFoundError):
                pass
            try:
                self._epoll.close()
            except OSError:
                pass
            self._server_sock.close()
        print(f"[epoll-{self._mode.value}] Server stopped.")


# ------------------------------------------------------------------
# Demos
# ------------------------------------------------------------------

def demo_epoll_lt() -> None:
    """Demonstrate epoll in level-triggered mode."""
    import threading
    from io_multiplexing.select_server import _run_test_client

    print("=== epoll Echo Server (Level-Triggered) ===\n")
    print("LT behaviour: epoll keeps reporting ready fds — same as select/poll.\n")

    server = EpollEchoServer(port=9098, mode=TriggerMode.LEVEL)
    server.start()

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.2)

    _run_test_client("epoll-LT", 9098, [b"alpha", b"beta", b"gamma"])

    time.sleep(0.3)
    print("epoll LT demo passed.\n")


def demo_epoll_et() -> None:
    """Demonstrate epoll in edge-triggered mode."""
    import threading
    from io_multiplexing.select_server import _run_test_client

    print("=== epoll Echo Server (Edge-Triggered) ===\n")
    print("ET behaviour: NOTIFIED ONCE per state change; MUST drain buffer.\n")
    print("If handler does not read until EAGAIN, data is STUCK in kernel buffer.\n")

    server = EpollEchoServer(port=9093, mode=TriggerMode.EDGE)
    server.start()

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.2)

    _run_test_client("epoll-ET", 9093, [b"edge", b"triggered", b"demo"])

    time.sleep(0.3)
    print("epoll ET demo passed.\n")


def demo_epoll_oneshot() -> None:
    """Demonstrate epoll in edge-triggered + EPOLLONESHOT mode."""
    import threading
    from io_multiplexing.select_server import _run_test_client

    print("=== epoll Echo Server (ET + EPOLLONESHOT) ===\n")
    print("ONESHOT: fd auto-disabled after each event — must be re-armed.\n")
    print("Prevents a busy fd from starving other connections.\n")

    server = EpollEchoServer(port=9094, mode=TriggerMode.EDGE, use_oneshot=True)
    server.start()

    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.2)

    _run_test_client("epoll-ONESHOT", 9094, [b"oneshot"])

    time.sleep(0.3)
    print("epoll ET+ONESHOT demo passed.\n")


if __name__ == "__main__":
    demo_epoll_lt()
    demo_epoll_et()
    demo_epoll_oneshot()
