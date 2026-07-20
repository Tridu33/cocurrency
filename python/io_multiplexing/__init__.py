"""
I/O multiplexing and proactor pattern concurrent server examples.

Demonstrates:
  - select  — POSIX select() for I/O readiness notification (level-triggered)
  - poll    — POSIX poll() with improved scalability (level-triggered)
  - epoll   — Linux epoll with both level-triggered and edge-triggered modes
  - NIO     — Reactor pattern (non-blocking I/O + event demultiplexing)
  - Proactor — Completion-based async I/O (initiate + completion handler)
"""
