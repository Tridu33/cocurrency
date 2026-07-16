"""Tests for csp/channel_demo.py."""

import threading
import pytest
from csp.channel_demo import Channel, ChannelClosed, demo_channel


class TestChannel:
    def test_send_recv_unbuffered(self):
        ch = Channel(maxsize=0)
        results: list = []

        def sender():
            ch.send(42)

        def receiver():
            results.append(ch.recv())

        t1 = threading.Thread(target=sender)
        t2 = threading.Thread(target=receiver)
        t2.start()
        t1.start()
        t1.join()
        t2.join()
        assert results == [42]

    def test_send_recv_buffered(self):
        ch = Channel(maxsize=5)
        ch.send(1)
        ch.send(2)
        assert ch.recv() == 1
        assert ch.recv() == 2

    def test_try_send_try_recv(self):
        ch = Channel(maxsize=2)
        assert ch.try_send("a") is True
        assert ch.try_send("b") is True
        assert ch.try_send("c") is False  # buffer full
        val, ok = ch.try_recv()
        assert ok and val == "a"
        val, ok = ch.try_recv()
        assert ok and val == "b"
        val, ok = ch.try_recv()
        assert not ok

    def test_close_prevents_send(self):
        ch = Channel(maxsize=3)
        ch.send(1)
        ch.close()
        with pytest.raises(ChannelClosed):
            ch.send(2)
        # Can still receive buffered items
        assert ch.recv() == 1
        # After buffer drained, recv returns None
        assert ch.recv() is None

    def test_concurrent(self):
        ch = Channel(maxsize=10)
        n = 100
        results: list = []

        def sender():
            for i in range(n):
                ch.send(i)

        def receiver():
            for _ in range(n):
                results.append(ch.recv())

        ts = [threading.Thread(target=sender), threading.Thread(target=receiver)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()

        results.sort()
        assert results == list(range(n))

    def test_demo_runs(self):
        demo_channel()
