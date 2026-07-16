"""
thread_producer_consumer.py — Producer-consumer with threading.Condition.

Demonstrates:
  - A bounded buffer (queue) protected by a Condition.
  - Producer threads adding items.
  - Consumer threads removing items.
  - Proper signalling and predicate-based waiting.
"""

import threading
import time
import random


class BoundedBuffer:
    """A thread-safe bounded buffer using Condition."""

    def __init__(self, maxsize: int = 10):
        self.maxsize = maxsize
        self._buf: list = []
        self._cond = threading.Condition()

    def put(self, item) -> None:
        """Add an item to the buffer; blocks if full."""
        with self._cond:
            while len(self._buf) >= self.maxsize:
                self._cond.wait()
            self._buf.append(item)
            print(f"  Produced {item:>4}   | buffer size = {len(self._buf)}")
            self._cond.notify_all()

    def get(self):
        """Remove and return an item; blocks if empty."""
        with self._cond:
            while not self._buf:
                self._cond.wait()
            item = self._buf.pop(0)
            print(f"  Consumed {item:>4}   | buffer size = {len(self._buf)}")
            self._cond.notify_all()
            return item


def producer(buf: BoundedBuffer, items: list[int], ident: str) -> None:
    """Produce items into the buffer."""
    for item in items:
        time.sleep(random.uniform(0.01, 0.05))
        buf.put(item)
    print(f"  [{ident}] finished")


def consumer(buf: BoundedBuffer, count: int, ident: str, results: list) -> None:
    """Consume `count` items from the buffer."""
    for _ in range(count):
        time.sleep(random.uniform(0.02, 0.06))
        item = buf.get()
        results.append(item)
    print(f"  [{ident}] finished")


def demo_producer_consumer() -> None:
    """Run a demo of the producer-consumer pattern."""
    print("=== Producer-Consumer with Condition Demo ===\n")

    buf = BoundedBuffer(maxsize=5)

    # Two producers, two consumers
    producer_items = [
        list(range(1, 11)),       # producer 1: 1..10
        list(range(101, 111)),    # producer 2: 101..110
    ]

    consumed: list = []
    prod_threads = []
    for i, items in enumerate(producer_items):
        t = threading.Thread(target=producer, args=(buf, items, f"P{i+1}"))
        prod_threads.append(t)
        t.start()

    cons_threads = []
    for i in range(2):
        t = threading.Thread(target=consumer, args=(buf, 10, f"C{i+1}", consumed))
        cons_threads.append(t)
        t.start()

    for t in prod_threads + cons_threads:
        t.join()

    consumed.sort()
    expected = sorted(list(range(1, 11)) + list(range(101, 111)))
    print(f"\nAll items consumed: {consumed}")
    assert consumed == expected, f"Mismatch: {consumed} != {expected}"
    print("OK: all produced items were consumed exactly once.")


if __name__ == "__main__":
    demo_producer_consumer()
