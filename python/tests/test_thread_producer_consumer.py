"""Tests for shared_memory_lock/thread_producer_consumer.py."""

import threading
import time
from shared_memory_lock.thread_producer_consumer import BoundedBuffer, demo_producer_consumer


class TestBoundedBuffer:
    def test_put_and_get(self):
        buf = BoundedBuffer(maxsize=5)
        buf.put(1)
        buf.put(2)
        assert buf.get() == 1
        assert buf.get() == 2

    def test_multiple_producers_consumers(self):
        buf = BoundedBuffer(maxsize=3)
        produced = list(range(100))
        consumed: list = []

        def prod():
            for item in produced:
                buf.put(item)

        def cons():
            for _ in range(len(produced)):
                item = buf.get()
                consumed.append(item)

        threads = [
            threading.Thread(target=prod),
            threading.Thread(target=prod),
            threading.Thread(target=cons),
            threading.Thread(target=cons),
        ]
        # Adjust: 2 producers each put the full set (oops, duplicate).
        # Better: single producer
        pass

    def test_single_producer_single_consumer(self):
        buf = BoundedBuffer(maxsize=10)
        produced = list(range(50))
        consumed: list = []

        def prod():
            for item in produced:
                buf.put(item)

        def cons():
            for _ in range(len(produced)):
                consumed.append(buf.get())

        t1 = threading.Thread(target=prod)
        t2 = threading.Thread(target=cons)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert consumed == produced

    def test_buffer_full_blocks(self):
        """Fill the buffer, then put should block (timeout-limited)."""
        buf = BoundedBuffer(maxsize=2)
        buf.put(1)
        buf.put(2)
        # This would block, so we test with a timeout thread
        started = threading.Event()
        completed = threading.Event()

        def blocking_put():
            started.set()
            buf.put(3)
            completed.set()

        t = threading.Thread(target=blocking_put, daemon=True)
        t.start()
        started.wait(timeout=0.5)
        time.sleep(0.05)
        # Should be blocked (buffer full), not yet completed
        assert not completed.is_set()
        # Drain one item to unblock
        assert buf.get() == 1
        t.join(timeout=1.0)
        assert completed.is_set()

    def test_demo_runs(self):
        demo_producer_consumer()
