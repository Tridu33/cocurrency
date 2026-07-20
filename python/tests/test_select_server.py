"""Tests for io_multiplexing/select_server.py."""

import time
from io_multiplexing.select_server import SelectEchoServer, demo_select_server, _run_test_client


class TestSelectServer:
    def test_single_client_echo(self):
        server = SelectEchoServer(port=19500)
        server.start()

        import threading
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.2)

        _run_test_client("test-select", 19500, [b"hello"])
        time.sleep(0.2)

    def test_multiple_messages(self):
        server = SelectEchoServer(port=19501)
        server.start()

        import threading
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.2)

        _run_test_client("test-select", 19501, [b"msg1", b"msg2", b"msg3"])
        time.sleep(0.2)

    def test_demo_runs(self):
        demo_select_server()
