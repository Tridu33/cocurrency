# Shared Memory? No, Lua Is Single-Threaded

Lua does **not** support shared-memory concurrency.  There are no
parallel threads, no mutexes, no atomics built into the language.

## Coroutines Are Cooperative, Not Parallel

Lua's `coroutine` library provides *cooperative multitasking* within a
single OS thread:

- **One thread.**  Only one Lua state runs at a time.  At any given
  instant only one coroutine is executing.
- **Explicit yielding.**  A coroutine runs until it calls
  `coroutine.yield()` or returns.  The scheduler (your code) decides
  when to resume another coroutine.
- **No preemption.**  The running coroutine cannot be interrupted from
  outside.  This means you never need locks for data shared between
  coroutines -- but also means a long-running coroutine blocks
  everything.

## No Race Conditions (But No True Parallelism)

Because coroutines are non-preemptive:

- ✅ **No data races** -- memory is not accessed concurrently.
- ✅ **No locks / atomics needed** -- state is safe by construction.
- ❌ **No CPU parallelism** -- even on a multi-core machine, only one
  coroutine runs at a time.

## What About Libraries?

- **LuaLanes / lua-llthreads** -- spawn separate Lua states in real OS
  threads (or processes).  These do *not* share memory; they communicate
  via message passing.
- **LuaSocket / Copas** -- use coroutines to manage asynchronous I/O
  within one thread.
- **Lua's `buffer` library (recent)** -- provides a coroutine-based
  producer/consumer pipe, still single-threaded.

For true parallelism in Lua, boot additional Lua states in separate OS
threads/processes and pass messages between them.  The core language
itself remains single-threaded and cooperative.
