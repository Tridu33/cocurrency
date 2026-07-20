"""Tests for io_multiplexing/proactor_server.py."""

import asyncio
import pytest
from io_multiplexing.proactor_server import (
    ProactorCallbackServer,
    ProactorCoroutineServer,
    demo_proactor_callback,
    demo_proactor_async,
    demo_proactor,
    _test_async_client,
)


class TestProactorCallback:
    @pytest.mark.asyncio
    async def test_single_client(self):
        server = ProactorCallbackServer(port=19511)
        await server.start()

        server_task = asyncio.create_task(server.serve_forever())
        await asyncio.sleep(0.2)

        await _test_async_client("127.0.0.1", 19511, [b"pcb"])

        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_multiple_messages(self):
        server = ProactorCallbackServer(port=19512)
        await server.start()

        server_task = asyncio.create_task(server.serve_forever())
        await asyncio.sleep(0.2)

        await _test_async_client("127.0.0.1", 19512, [b"msg1", b"msg2", b"msg3"])

        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

    def test_demo_runs(self):
        demo_proactor_callback()


class TestProactorAsync:
    @pytest.mark.asyncio
    async def test_single_client(self):
        server = ProactorCoroutineServer(port=19513)
        await server.start()

        server_task = asyncio.create_task(server.serve_forever())
        await asyncio.sleep(0.2)

        await _test_async_client("127.0.0.1", 19513, [b"pasync"])

        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_multiple_clients(self):
        server = ProactorCoroutineServer(port=19514)
        await server.start()

        server_task = asyncio.create_task(server.serve_forever())
        await asyncio.sleep(0.2)

        await _test_async_client("127.0.0.1", 19514, [b"a", b"bb", b"ccc", b"dddd"])

        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass

    def test_demo_runs(self):
        demo_proactor_async()


def test_demo_proactor_runs():
    """Test that the combined proactor demo runs."""
    demo_proactor()
