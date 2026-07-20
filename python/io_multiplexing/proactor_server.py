"""
proactor_server.py — Proactor-pattern concurrent server (completion-based).

Demonstrates:
  - The Proactor pattern: completion-based async I/O.
  - How the Proactor differs from the Reactor: the OS performs the
    I/O operation and notifies on COMPLETION, not readiness.
  - Built with asyncio's high-level streams API (Protocol/Transport),
    which abstracts the underlying proactor/reactor mechanism.
  - Two variants:
      1. Callback-style: explicit completion handlers (os-level proactor feel).
      2. async/await style: coroutine-based — the modern Python way.

Proactor vs Reactor — the key difference:

  Reactor (readiness-based):
    1. App registers fd + "I want to read" + handler
    2. Reactor: "fd is readable now" → calls handler.on_read()
    3. Handler calls sock.recv() — this is a SYNCHRONOUS call
       that reads from kernel buffer (already in memory).
    4. Handler processes data.

  Proactor (completion-based):
    1. App initiates async_read(fd, buffer, completion_handler)
    2. OS kernel reads data from fd into buffer ASYNCHRONOUSLY
    3. OS: "read complete, N bytes in buffer" → calls completion_handler
    4. Completion handler processes data that OS already read.
    5. App NEVER calls recv() — the OS did it.

  On Linux, true async I/O (like Windows IOCP) is available via:
    - io_uring (kernel 5.1+) — the modern Linux proactor
    - POSIX AIO (aio_read/aio_write) — limited, often emulated with threads
  Python's asyncio ProactorEventLoop uses IOCP on Windows; on Linux,
  asyncio uses the SelectorEventLoop (reactor) by default. However,
  the high-level asyncio streams API *feels* like a proactor because
  `await reader.read()` hands you data that has already been read —
  you never touch the fd directly.

This demo:
  - Variant A: explicit callback Proactor using asyncio Protocols
    (Transport/Protocol = the asyncio proactor abstraction).
  - Variant B: coroutine-based server using asyncio.start_server
    (the modern, clean way — still proactor semantics at the API level).
"""

import asyncio
import time
from typing import Optional


# ==================================================================
# Variant A — Callback-style Proactor (Protocol/Transport)
# ==================================================================

class EchoProtocol(asyncio.Protocol):
    """
    Protocol handler — like a "completion handler" in the proactor model.

    The Transport is the proactor engine:
      - It initiates reads (no explicit recv() call by us).
      - It calls data_received() when data HAS BEEN READ (completion).
      - We never call recv() — data is handed to us.

    This is the PROACTOR pattern: "initiate operation → get called on completion".
    """

    def __init__(self):
        self._transport: Optional[asyncio.Transport] = None
        self._peer: str = "unknown"

    # --- Proactor completion callbacks ---

    def connection_made(self, transport: asyncio.Transport) -> None:
        """Called when a connection has been ESTABLISHED (accept complete)."""
        self._transport = transport
        peer = transport.get_extra_info("peername")
        self._peer = f"{peer[0]}:{peer[1]}" if peer else "unknown"
        print(f"  [Proactor-cb] connection_made: {self._peer}")

    def data_received(self, data: bytes) -> None:
        """
        Called when data has BEEN READ into a buffer (read complete).

        This is the core proactor callback. We do NOT call recv() —
        data is already in `data` because the proactor (transport)
        initiated and completed the read for us.

        Contrast with Reactor: on_read() → we call sock.recv() ourselves.
        """
        print(f"  [Proactor-cb] data_received: {len(data)}B from {self._peer}")

        # Process and echo: upper-case
        response = data.upper()
        # Initiate a write — completion will call... nothing explicit,
        # transport.write() is fire-and-forget at the API level.
        # Under the hood, the proactor queues the write and handles
        # buffering / backpressure.
        if self._transport:
            self._transport.write(response)
            print(f"  [Proactor-cb] write initiated: {len(response)}B to {self._peer}")

    def connection_lost(self, exc: Optional[Exception]) -> None:
        """Called when the connection is closed (close complete)."""
        reason = exc if exc else "clean shutdown"
        print(f"  [Proactor-cb] connection_lost: {self._peer}  ({reason})")

    def eof_received(self) -> bool:
        """Called when the peer sends EOF (half-close)."""
        print(f"  [Proactor-cb] eof_received: {self._peer}")
        return False  # False → transport will close our side too


class ProactorCallbackServer:
    """
    Proactor-pattern server using asyncio Protocol/Transport callbacks.

    The event loop + transport = the proactor engine.
    The Protocol subclass = our completion handler.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 9096):
        self._host = host
        self._port = port
        self._server: Optional[asyncio.AbstractServer] = None

    async def start(self) -> None:
        """Create the server — this registers our protocol factory."""
        loop = asyncio.get_running_loop()

        # loop.create_server() with a protocol factory is the proactor setup:
        # "When a connection is accepted, create a Protocol instance and
        #  call connection_made(). When data arrives, call data_received()."
        self._server = await loop.create_server(
            EchoProtocol,
            self._host,
            self._port,
        )
        print(f"[Proactor-cb] Listening on {self._host}:{self._port}")
        print("[Proactor-cb] Callback-style: Protocol.data_received() = completion handler")

    async def serve_forever(self) -> None:
        """Run until stopped."""
        print("[Proactor-cb] Event loop started (Ctrl-C to stop)\n")
        try:
            # Keep running — the proactor (event loop) handles all I/O
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            pass
        finally:
            await self._cleanup()

    async def _cleanup(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        print("[Proactor-cb] Server stopped.")


# ==================================================================
# Variant B — Coroutine-style Proactor (async/await streams)
# ==================================================================

class ProactorCoroutineServer:
    """
    Proactor-pattern server using async/await with asyncio streams.

    This is the modern, clean Python way. Each client is handled by
    a coroutine — `await reader.read()` hands us data that has ALREADY
    been read by the proactor. `writer.write()` + `await writer.drain()`
    initiates a write and waits for completion.

    The key proactor semantic:
      await reader.read(N)  → "initiates a read; I resume when it completes"
      await writer.drain()  → "initiates a flush; I resume when it drains"
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 9097):
        self._host = host
        self._port = port
        self._server: Optional[asyncio.AbstractServer] = None
        self._client_count = 0

    async def start(self) -> None:
        """Start the server; client_connected_cb is the handler factory."""
        self._server = await asyncio.start_server(
            self._handle_client,
            self._host,
            self._port,
        )
        print(f"[Proactor-async] Listening on {self._host}:{self._port}")
        print("[Proactor-async] Coroutine-style: await reader.read() = initiate + complete")

    async def serve_forever(self) -> None:
        """Run the proactor event loop."""
        print("[Proactor-async] Event loop started (Ctrl-C to stop)\n")
        try:
            async with self._server:  # type: ignore[union-attr]
                await self._server.serve_forever()  # type: ignore[union-attr]
        except asyncio.CancelledError:
            pass
        finally:
            await self._cleanup()

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """
        Handle one client connection — pure proactor semantics.

        Every `await reader.read()` is:
          1. Initiate: "kernel, please read from this fd."
          2. Suspend: this coroutine yields.
          3. Complete: kernel wakes us, data is in `data` — we never
             called recv().

        Every `await writer.drain()` is:
          1. Initiate: "kernel, flush the write buffer."
          2. Suspend: yield until buffer drains.
          3. Complete: buffer drained, we can write more.
        """
        self._client_count += 1
        client_id = self._client_count
        peer = writer.get_extra_info("peername")
        peer_str = f"{peer[0]}:{peer[1]}" if peer else "?"
        print(f"  [Proactor-async] Client #{client_id} connected: {peer_str}")

        try:
            while True:
                # --- Proactor read ---
                # "Initiate a read. Call me back when N bytes are available."
                data = await reader.read(4096)
                if not data:
                    # EOF — peer closed
                    print(f"  [Proactor-async] Client #{client_id} EOF (read returned empty)")
                    break

                print(
                    f"  [Proactor-async] Client #{client_id}"
                    f" read complete: {len(data)}B"
                )

                # Process
                response = data.upper()

                # --- Proactor write ---
                # "Initiate a write. Call me back when it's flushed."
                writer.write(response)
                await writer.drain()
                print(
                    f"  [Proactor-async] Client #{client_id}"
                    f" write complete: {len(response)}B"
                )

        except (ConnectionResetError, BrokenPipeError):
            print(f"  [Proactor-async] Client #{client_id} connection reset")
        finally:
            writer.close()
            await writer.wait_closed()
            print(f"  [Proactor-async] Client #{client_id} disconnected: {peer_str}")

    async def _cleanup(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        print("[Proactor-async] Server stopped.")


# ==================================================================
# Demos
# ==================================================================

async def _test_async_client(host: str, port: int, messages: list[bytes]) -> None:
    """Async test client using asyncio streams."""
    for msg in messages:
        reader, writer = await asyncio.open_connection(host, port)
        writer.write(msg)
        await writer.drain()
        reply = await reader.read(4096)
        expected = msg.upper()
        assert reply == expected, f"Expected {expected!r}, got {reply!r}"
        print(f"  [async-client] sent={msg!r}  →  echo={reply!r}")
        writer.close()
        await writer.wait_closed()


async def _run_proactor_cb_demo() -> None:
    """Run the callback-style proactor demo."""
    print("=" * 62)
    print("=== Proactor Pattern — Callback-Style (Protocol/Transport) ===")
    print("=" * 62)
    print()
    print("Flow: data arrives → Transport reads it → Protocol.data_received(data)")
    print("      We NEVER call recv(). Data is handed to us on completion.")
    print()

    server = ProactorCallbackServer(port=9096)
    await server.start()

    # Run server in background
    server_task = asyncio.create_task(server.serve_forever())
    await asyncio.sleep(0.2)

    await _test_async_client("127.0.0.1", 9096, [b"proactor", b"callback"])
    await asyncio.sleep(0.2)

    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass

    print("Proactor callback demo passed.\n")


async def _run_proactor_async_demo() -> None:
    """Run the coroutine-style proactor demo."""
    print("=" * 62)
    print("=== Proactor Pattern — Coroutine-Style (async/await) ===")
    print("=" * 62)
    print()
    print("Flow: await reader.read(N) → proactor reads → we get data")
    print("      await writer.drain() → proactor writes → we continue")
    print()

    server = ProactorCoroutineServer(port=9097)
    await server.start()

    server_task = asyncio.create_task(server.serve_forever())
    await asyncio.sleep(0.2)

    await _test_async_client("127.0.0.1", 9097, [b"proactor", b"async", b"demo"])
    await asyncio.sleep(0.2)

    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        pass

    print("Proactor async demo passed.\n")


def demo_proactor_callback() -> None:
    """Entry-point wrapper for the callback-style proactor demo."""
    print("\n=== Proactor Server: Callback-Style ===\n")
    asyncio.run(_run_proactor_cb_demo())


def demo_proactor_async() -> None:
    """Entry-point wrapper for the coroutine-style proactor demo."""
    print("\n=== Proactor Server: Coroutine-Style ===\n")
    asyncio.run(_run_proactor_async_demo())


def demo_proactor() -> None:
    """Run both proactor demos."""
    demo_proactor_callback()
    demo_proactor_async()


if __name__ == "__main__":
    demo_proactor()
