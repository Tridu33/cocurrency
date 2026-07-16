"""Tests for actor/print_server.py."""

import time
from actor.print_server import PrintServer, demo_print_server


class TestPrintServer:
    def test_tell(self):
        server = PrintServer()
        server.start()
        server.tell("hello")
        server.tell("world")
        time.sleep(0.1)
        server.stop()

    def test_ask(self):
        server = PrintServer()
        server.start()
        reply = server.ask("test message")
        assert "printed: test message" in reply
        server.stop()

    def test_multiple_asks(self):
        server = PrintServer()
        server.start()
        replies = []
        for msg in ["msg1", "msg2", "msg3"]:
            replies.append(server.ask(msg))
        for r in replies:
            assert "printed:" in r
        server.stop()

    def test_then_ask(self):
        server = PrintServer()
        server.start()
        server.tell("fire and forget")
        time.sleep(0.05)
        reply = server.ask("request")
        assert "printed: request" in reply
        server.stop()

    def test_demo_runs(self):
        demo_print_server()
