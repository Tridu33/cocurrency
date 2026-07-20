"""Tests for io_multiplexing/nio_reactor_server.py."""

import time
from io_multiplexing.nio_reactor_server import NIOReactorServer, demo_nio_reactor
from io_multiplexing.select_server import _run_test_client


class TestNIOReactor:
    def test_single_client(self):
        server = NIOReactorServer(port=19509)
        server.start()

        import threading
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.4)

        _run_test_client("test-NIO", 19509, [b"nio"])

    def test_multiple_messages(self):
        server = NIOReactorServer(port=19510)
        server.start()

        import threading
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.4)

        _run_test_client("test-NIO", 19510, [b"alpha", b"beta", b"gamma"])

    def test_demo_runs(self):
        demo_nio_reactor()
