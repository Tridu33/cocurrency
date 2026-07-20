"""Tests for io_multiplexing/epoll_server.py."""

import time
from io_multiplexing.epoll_server import (
    EpollEchoServer,
    TriggerMode,
    demo_epoll_lt,
    demo_epoll_et,
    demo_epoll_oneshot,
)
from io_multiplexing.select_server import _run_test_client


class TestEpollLT:
    def test_single_client(self):
        server = EpollEchoServer(port=19504, mode=TriggerMode.LEVEL)
        server.start()

        import threading
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.2)

        _run_test_client("test-epoll-LT", 19504, [b"lt"])

    def test_multiple_messages(self):
        server = EpollEchoServer(port=19505, mode=TriggerMode.LEVEL)
        server.start()

        import threading
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.2)

        _run_test_client("test-epoll-LT", 19505, [b"one", b"two", b"three"])

    def test_demo_lt_runs(self):
        demo_epoll_lt()


class TestEpollET:
    def test_single_client(self):
        server = EpollEchoServer(port=19506, mode=TriggerMode.EDGE)
        server.start()

        import threading
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.2)

        _run_test_client("test-epoll-ET", 19506, [b"edge"])

    def test_multiple_messages(self):
        server = EpollEchoServer(port=19507, mode=TriggerMode.EDGE)
        server.start()

        import threading
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.2)

        _run_test_client("test-epoll-ET", 19507, [b"et1", b"et2", b"et3"])

    def test_demo_et_runs(self):
        demo_epoll_et()


class TestEpollOneShot:
    def test_single_client(self):
        server = EpollEchoServer(port=19508, mode=TriggerMode.EDGE, use_oneshot=True)
        server.start()

        import threading
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.2)

        _run_test_client("test-epoll-1SHOT", 19508, [b"oneshot"])

    def test_demo_oneshot_runs(self):
        demo_epoll_oneshot()
