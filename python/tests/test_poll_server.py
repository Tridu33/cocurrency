"""Tests for io_multiplexing/poll_server.py."""

import time
from io_multiplexing.poll_server import PollEchoServer, demo_poll_server
from io_multiplexing.select_server import _run_test_client


class TestPollServer:
    def test_single_client_echo(self):
        server = PollEchoServer(port=19502)
        server.start()

        import threading
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.2)

        _run_test_client("test-poll", 19502, [b"echo"])
        time.sleep(0.2)

    def test_multiple_messages(self):
        server = PollEchoServer(port=19503)
        server.start()

        import threading
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.2)

        _run_test_client("test-poll", 19503, [b"a", b"bb", b"ccc"])
        time.sleep(0.2)

    def test_demo_runs(self):
        demo_poll_server()
