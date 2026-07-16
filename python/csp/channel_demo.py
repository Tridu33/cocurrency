"""
channel_demo.py — CSP-style communication via a custom Channel class.

Demonstrates:
  - A Channel that supports send/receive (like Go's chan).
  - Both unbuffered (synchronous) and buffered modes.
  - Select-like behaviour via non-blocking try_send / try_recv.
  - Multiple goroutine-like threads communicating over channels.
"""

import threading
import queue
import time
import random
from collections.abc import Callable


class ChannelClosed(Exception):
    """Raised when operating on a closed channel."""


class Channel:
    """
    A CSP-style channel for communicating between threads.

    Capabilities:
      - send(item): blocks until someone receives (unbuffered) or
                    until there is space in the buffer (buffered).
      - recv(): blocks until an item is available.
      - try_send(item): non-blocking send; returns True on success.
      - try_recv(): non-blocking receive; returns (item, True) or (None, False).
      - close(): prevents further sends; remaining buffered items can still be received.
    """

    def __init__(self, maxsize: int = 0):
        self._buf: queue.Queue = queue.Queue(maxsize)
        self._closed = False
        self._lock = threading.Lock()
        self._send_event = threading.Event()
        self._recv_event = threading.Event()

    def send(self, item) -> None:
        """Send an item into the channel. Blocks if the buffer is full."""
        while True:
            with self._lock:
                if self._closed:
                    raise ChannelClosed("send on closed channel")
                if not self._buf.full():
                    self._buf.put_nowait(item)
                    self._recv_event.set()
                    self._recv_event.clear()
                    return
            # Buffer full — wait for a receiver to drain it.
            self._send_event.wait(timeout=0.001)

    def recv(self):
        """
        Receive an item from the channel. Blocks if the buffer is empty.
        Returns None if the channel is closed and the buffer is empty.
        """
        while True:
            with self._lock:
                try:
                    item = self._buf.get_nowait()
                    self._send_event.set()
                    self._send_event.clear()
                    return item
                except queue.Empty:
                    if self._closed:
                        return None
            # Buffer empty — wait for a sender.
            self._recv_event.wait(timeout=0.001)

    def try_send(self, item) -> bool:
        """Non-blocking send. Returns True if the item was sent."""
        with self._lock:
            if self._closed:
                raise ChannelClosed("send on closed channel")
            if not self._buf.full():
                self._buf.put_nowait(item)
                self._recv_event.set()
                self._recv_event.clear()
                return True
            return False

    def try_recv(self):
        """Non-blocking receive. Returns (item, True) or (None, False)."""
        with self._lock:
            try:
                item = self._buf.get_nowait()
                self._send_event.set()
                self._send_event.clear()
                return item, True
            except queue.Empty:
                return None, False

    def close(self) -> None:
        """Close the channel. Subsequent sends raise ChannelClosed."""
        with self._lock:
            self._closed = True
            self._recv_event.set()

    def __len__(self) -> int:
        with self._lock:
            return self._buf.qsize()


def _worker_sender(ch: Channel, items: list, name: str) -> None:
    """Send items into the channel."""
    for item in items:
        time.sleep(random.uniform(0.01, 0.03))
        ch.send(item)
        print(f"  [{name}] sent {item}")
    print(f"  [{name}] done")
    ch.close()


def _worker_receiver(ch: Channel, count: int, name: str, results: list) -> None:
    """Receive items from the channel."""
    received = 0
    while received < count:
        item = ch.recv()
        if item is None:
            break
        results.append(item)
        received += 1
        print(f"  [{name}] received {item}")
    print(f"  [{name}] done (got {received} items)")


def demo_channel() -> None:
    """Run a CSP channel demo."""
    print("=== CSP Channel Demo ===\n")

    # Unbuffered channel (synchronous handoff)
    print("--- Unbuffered Channel ---")
    ch = Channel(maxsize=0)
    results: list = []

    sender = threading.Thread(target=_worker_sender, args=(ch, [1, 2, 3], "S1"))
    receiver = threading.Thread(target=_worker_receiver, args=(ch, 3, "R1", results))

    receiver.start()
    sender.start()
    sender.join()
    receiver.join()
    print(f"Received items: {results}")
    assert results == [1, 2, 3]
    print()

    # Buffered channel
    print("--- Buffered Channel (maxsize=3) ---")
    ch2 = Channel(maxsize=3)
    results2: list = []

    s_threads = [
        threading.Thread(target=_worker_sender, args=(ch2, [10, 20, 30], "S1")),
        threading.Thread(target=_worker_sender, args=(ch2, [40, 50, 60], "S2")),
    ]
    r_threads = [
        threading.Thread(target=_worker_receiver, args=(ch2, 3, "R1", results2)),
        threading.Thread(target=_worker_receiver, args=(ch2, 3, "R2", results2)),
    ]

    for t in r_threads + s_threads:
        t.start()
    for t in s_threads + r_threads:
        t.join()

    results2.sort()
    print(f"Received items: {results2}")
    assert results2 == [10, 20, 30, 40, 50, 60]
    print()

    # Non-blocking operations
    print("--- Non-blocking operations ---")
    ch3 = Channel(maxsize=2)
    ok = ch3.try_send("hello")
    print(f"try_send('hello') -> {ok}")
    item, ok = ch3.try_recv()
    print(f"try_recv() -> ({item!r}, {ok})")
    assert item == "hello"
    item, ok = ch3.try_recv()
    print(f"try_recv() on empty -> ({item!r}, {ok})")
    assert not ok
    print()

    print("CSP Channel demo passed.")


if __name__ == "__main__":
    demo_channel()
