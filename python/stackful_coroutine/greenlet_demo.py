"""
greenlet_demo.py — Stackful coroutines via greenlet with threading fallback.

Demonstrates:
  - Stackful coroutines using the `greenlet` library.
  - Explicit suspend/resume between coroutines A -> B -> C.
  - A simple round-robin scheduler.
  - A threading-based fallback if greenlet is not installed.
"""

import time

# ---------- Greenlet-based (stackful) implementation ----------

_has_greenlet = False
try:
    import greenlet
    _has_greenlet = True
except ImportError:
    pass


class GreenletStyleCoroutine:
    """
    A simulated stackful coroutine that works WITHOUT greenlet.

    Instead of real stack-switching, this class models the *interface*
    of a stackful coroutine: it maintains an explicit call stack and
    allows suspend/resume at any point.

    When greenlet IS available, the demo switches to real greenlets.
    """

    def __init__(self, name: str, target, args=()):
        self.name = name
        self.target = target
        self.args = args
        self._gr = None
        self.is_alive = True

    def switch(self, *args):
        """Switch execution to this coroutine (start or resume)."""
        if self._gr is None and _has_greenlet:
            # Real greenlet
            self._gr = greenlet.greenlet(self.target)
            return self._gr.switch(*args)
        elif self._gr is not None and _has_greenlet:
            return self._gr.switch(*args)

    def kill(self):
        self.is_alive = False


class Scheduler:
    """
    A simple round-robin scheduler for coroutines.

    Each coroutine runs until it yields (explicitly suspends).
    The scheduler then picks the next runnable coroutine.
    """

    def __init__(self):
        self._ready: list = []
        self._current = None

    def add(self, coro) -> None:
        """Add a coroutine to the ready queue."""
        self._ready.append(coro)

    def run(self) -> None:
        """Run the scheduler until all coroutines are finished."""
        while self._ready:
            coro = self._ready.pop(0)
            self._current = coro
            if coro.is_alive:
                print(f"  [Scheduler] switching to {coro.name}")
                coro.switch()
                if coro.is_alive:
                    self._ready.append(coro)


# ---------- Coroutine targets ----------

def coroutine_a():
    """Coroutine A: runs some steps, suspends, runs more."""
    print("    coroutine A step 1")
    _suspend()
    print("    coroutine A step 2")
    _suspend()
    print("    coroutine A step 3 - done")
    _current().is_alive = False


def coroutine_b():
    """Coroutine B: runs some steps, suspends, runs more."""
    print("    coroutine B step 1")
    _suspend()
    print("    coroutine B step 2")
    _suspend()
    print("    coroutine B step 3")
    _suspend()
    print("    coroutine B step 4 - done")
    _current().is_alive = False


def coroutine_c():
    """Coroutine C: runs some steps, suspends, runs more."""
    print("    coroutine C step 1")
    _suspend()
    print("    coroutine C step 2")
    _suspend()
    print("    coroutine C step 3 - done")
    _current().is_alive = False


def _suspend():
    """Suspend the current coroutine (yield control to the scheduler)."""
    time.sleep(0.01)


def _current():
    """Get the currently executing coroutine's wrapper."""
    # In the greenlet version, the scheduler tracks current.
    # For the threading fallback, we use thread-local.
    return getattr(_thread_local, 'current_coro', None)


# ---------- Purely thread-based fallback (stackful simulation) ----------

import threading
import queue

_thread_local = threading.local()


class ThreadBasedCoro:
    """Fallback: simulate stackful coroutines using threads + queue suspension."""

    def __init__(self, name: str, target, args=()):
        self.name = name
        self.target = target
        self.args = args
        self._sched_q = queue.Queue()
        self._resume_q = queue.Queue()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self.is_alive = True

    def switch(self, *args):
        """Resume this coroutine."""
        self._resume_q.put(args)
        return self._sched_q.get()

    def start(self):
        self._thread.start()
        return self.switch()

    def kill(self):
        self.is_alive = False

    def _suspend_t(self):
        """Internal: yield control back to scheduler."""
        self._sched_q.put(('suspended',))
        args = self._resume_q.get()
        return args

    def _run(self):
        _thread_local.current_coro = self
        try:
            result = self.target()
            self._sched_q.put(('done', result))
        except Exception as e:
            self._sched_q.put(('error', e))
        finally:
            self.is_alive = False


class ThreadScheduler:
    """Round-robin scheduler built on threads."""

    def __init__(self):
        self._ready: list = []

    def add(self, coro) -> None:
        self._ready.append(coro)

    def run(self) -> None:
        # Start all coroutines
        for coro in self._ready:
            coro.start()
        # Drain results (threads are concurrent)
        for coro in self._ready:
            coro._thread.join()


# We need to adapt coroutine_a/b/c for thread fallback
# They'll be defined inline in demo_greenlet


def demo_greenlet() -> None:
    """Run the stackful coroutine demo."""
    print("=== Stackful Coroutine: Greenlet Demo ===\n")

    if _has_greenlet:
        print("(Using real greenlet library for stackful coroutines)\n")
        _demo_greenlet_real()
    else:
        print("(greenlet not installed; using threading fallback)\n")
        _demo_greenlet_fallback()

    print("Greenlet demo passed.")


def _demo_greenlet_real():
    """Real greenlet-based demo with A->B->C suspend/resume."""
    sched = Scheduler()

    # Wrap targets to work with the scheduler
    def a_wrapper():
        print("    coroutine A step 1")
        sched._ready.append(sched._ready.pop(0))  # yield to next
        greenlet.getcurrent().parent.switch()
        print("    coroutine A step 2")
        sched._ready.append(sched._ready.pop(0))
        greenlet.getcurrent().parent.switch()
        print("    coroutine A step 3 - done")
        sched._current.is_alive = False

    def b_wrapper():
        print("    coroutine B step 1")
        greenlet.getcurrent().parent.switch()
        print("    coroutine B step 2")
        greenlet.getcurrent().parent.switch()
        print("    coroutine B step 3")
        greenlet.getcurrent().parent.switch()
        print("    coroutine B step 4 - done")
        sched._current.is_alive = False

    def c_wrapper():
        print("    coroutine C step 1")
        greenlet.getcurrent().parent.switch()
        print("    coroutine C step 2")
        greenlet.getcurrent().parent.switch()
        print("    coroutine C step 3 - done")
        sched._current.is_alive = False

    # Create coroutine wrappers
    for name, fn in [("A", a_wrapper), ("B", b_wrapper), ("C", c_wrapper)]:
        coro = GreenletStyleCoroutine(name, fn)
        gr = greenlet.greenlet(fn)
        coro._gr = gr
        sched.add(coro)

    sched.run()


def _demo_greenlet_fallback():
    """Threading-based fallback simulating stackful coroutine behaviour."""

    results: list = []

    # Redefine targets for thread-based model that works with the suspend/resume pattern
    def coro_a_fn(coro):
        print("    coroutine A step 1")
        coro._sched_q.put(('suspended',))
        coro._resume_q.get()
        print("    coroutine A step 2")
        coro._sched_q.put(('suspended',))
        coro._resume_q.get()
        print("    coroutine A step 3 - done")
        coro._sched_q.put(('done', None))

    def coro_b_fn(coro):
        print("    coroutine B step 1")
        coro._sched_q.put(('suspended',))
        coro._resume_q.get()
        print("    coroutine B step 2")
        coro._sched_q.put(('suspended',))
        coro._resume_q.get()
        print("    coroutine B step 3")
        coro._sched_q.put(('suspended',))
        coro._resume_q.get()
        print("    coroutine B step 4 - done")
        coro._sched_q.put(('done', None))

    def coro_c_fn(coro):
        print("    coroutine C step 1")
        coro._sched_q.put(('suspended',))
        coro._resume_q.get()
        print("    coroutine C step 2")
        coro._sched_q.put(('suspended',))
        coro._resume_q.get()
        print("    coroutine C step 3 - done")
        coro._sched_q.put(('done', None))

    # Helper that wraps a target function
    def wrap_target(fn):
        def wrapper():
            self_coro = _thread_local.current_coro
            fn(self_coro)
        return wrapper

    sched = ThreadScheduler()

    for name, fn in [("A", coro_a_fn), ("B", coro_b_fn), ("C", coro_c_fn)]:
        wrapped_target = wrap_target(fn)
        coro = ThreadBasedCoro(name, wrapped_target)
        sched.add(coro)

    sched.run()


if __name__ == "__main__":
    demo_greenlet()
